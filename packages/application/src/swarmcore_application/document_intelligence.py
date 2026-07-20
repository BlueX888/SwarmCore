from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol
from urllib.request import Request, urlopen
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class IntelligenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class EvidenceLocation(IntelligenceModel):
    page: int = Field(ge=1)
    bounding_box: tuple[float, float, float, float] | None = Field(
        default=None, alias="boundingBox"
    )
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("bounding_box")
    @classmethod
    def normalized_box(
        cls, value: tuple[float, float, float, float] | None
    ) -> tuple[float, float, float, float] | None:
        if value is None:
            return None
        left, top, right, bottom = value
        if not all(0 <= item <= 1 for item in value) or left >= right or top >= bottom:
            raise ValueError("boundingBox must be normalized and non-empty")
        return value


class ParsedPage(IntelligenceModel):
    page: int = Field(ge=1)
    text: str


class ParsedDocument(IntelligenceModel):
    provider: str = Field(min_length=1)
    provider_version: str = Field(alias="providerVersion", min_length=1)
    pages: tuple[ParsedPage, ...] = Field(min_length=1)

    @field_validator("pages")
    @classmethod
    def ordered_unique_pages(cls, value: tuple[ParsedPage, ...]) -> tuple[ParsedPage, ...]:
        numbers = [page.page for page in value]
        if numbers != sorted(numbers) or len(numbers) != len(set(numbers)):
            raise ValueError("parsed pages must be unique and ordered")
        return value


class DocumentClassification(IntelligenceModel):
    document_type: str = Field(alias="documentType", min_length=1, max_length=128)
    confidence: float = Field(ge=0, le=1)
    evidence: tuple[EvidenceLocation, ...] = Field(min_length=1)


class ExtractedField(IntelligenceModel):
    name: str = Field(min_length=1, max_length=128)
    value: str | int | float | bool | None
    confidence: float = Field(ge=0, le=1)
    evidence: tuple[EvidenceLocation, ...] = Field(min_length=1)


class AgentExtraction(IntelligenceModel):
    schema_version: str = Field(alias="schemaVersion", min_length=1)
    classification: DocumentClassification
    fields: tuple[ExtractedField, ...]

    @field_validator("fields")
    @classmethod
    def unique_fields(cls, value: tuple[ExtractedField, ...]) -> tuple[ExtractedField, ...]:
        names = [field.name for field in value]
        if len(names) != len(set(names)):
            raise ValueError("extracted field names must be unique")
        return value


class IntelligenceDiagnostic(IntelligenceModel):
    code: str
    stage: Literal["OCR", "CLASSIFICATION", "EXTRACTION", "SCHEMA", "PROVIDER"]
    message: str
    retryable: bool
    attempts: int = Field(ge=1)


class DocumentIntelligenceResult(IntelligenceModel):
    blob_id: str = Field(alias="blobId")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    pipeline_version: str = Field(alias="pipelineVersion")
    status: Literal["COMPLETED", "REVIEW_REQUIRED", "FAILED"]
    extraction: AgentExtraction | None = None
    review_reasons: tuple[str, ...] = Field(default=(), alias="reviewReasons")
    diagnostics: tuple[IntelligenceDiagnostic, ...] = ()


class CrossFileRule(IntelligenceModel):
    key: str = Field(min_length=1, max_length=128)
    field: str = Field(min_length=1, max_length=128)
    document_types: tuple[str, ...] = Field(alias="documentTypes", min_length=2)
    severity: Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"


class CrossFileFinding(IntelligenceModel):
    rule_key: str = Field(alias="ruleKey")
    code: str
    severity: str
    detail: str
    evidence: tuple[EvidenceLocation, ...]
    requires_review: bool = Field(alias="requiresReview")


class DocumentParser(Protocol):
    name: str
    version: str

    async def parse(self, request: dict[str, Any]) -> dict[str, Any]: ...


class HttpDocumentParser:
    """Adapter for a trusted OCR/document parsing provider."""

    def __init__(self, endpoint: str, *, name: str, version: str) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("document provider endpoint must use HTTP(S)")
        self._endpoint = endpoint
        self.name = name
        self.version = version

    async def parse(self, request: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._request, request)

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        token = str(payload["capabilityToken"])
        body = json.dumps(
            {key: value for key, value in payload.items() if key != "capabilityToken"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        request = Request(
            self._endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=120) as response:
            value = json.loads(response.read())
        if not isinstance(value, dict):
            raise ValueError("document provider returned a non-object response")
        return value


class DocumentUnderstandingAgent(Protocol):
    name: str
    version: str

    async def extract(
        self, parsed: ParsedDocument, *, output_schema: dict[str, Any]
    ) -> dict[str, Any]: ...


class IntelligenceStore(Protocol):
    async def get(self, cache_key: str) -> DocumentIntelligenceResult | None: ...
    async def put(self, cache_key: str, result: DocumentIntelligenceResult) -> None: ...


class InMemoryIntelligenceStore:
    def __init__(self) -> None:
        self._values: dict[str, DocumentIntelligenceResult] = {}

    async def get(self, cache_key: str) -> DocumentIntelligenceResult | None:
        return self._values.get(cache_key)

    async def put(self, cache_key: str, result: DocumentIntelligenceResult) -> None:
        self._values.setdefault(cache_key, result)


class SqlIntelligenceStore:
    """Tenant-scoped immutable cache shared by retries and worker processes."""

    def __init__(self, session: Any, *, tenant_id: UUID, project_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._project_id = project_id

    async def get(self, cache_key: str) -> DocumentIntelligenceResult | None:
        from sqlalchemy import select
        from swarmcore_persistence.models import DocumentExtraction

        row = await self._session.scalar(
            select(DocumentExtraction).where(
                DocumentExtraction.tenant_id == self._tenant_id,
                DocumentExtraction.project_id == self._project_id,
                DocumentExtraction.cache_key == cache_key,
            )
        )
        return None if row is None else DocumentIntelligenceResult.model_validate(row.result)

    async def put(self, cache_key: str, result: DocumentIntelligenceResult) -> None:
        from sqlalchemy.dialects.postgresql import insert
        from swarmcore_persistence.models import DocumentExtraction

        statement = (
            insert(DocumentExtraction)
            .values(
                tenant_id=self._tenant_id,
                project_id=self._project_id,
                blob_id=UUID(result.blob_id),
                source_sha256=result.sha256,
                pipeline_version=result.pipeline_version,
                cache_key=cache_key,
                status=result.status,
                result=result.model_dump(mode="json", by_alias=True),
            )
            .on_conflict_do_nothing(constraint="uq_document_extractions_cache_key")
        )
        await self._session.execute(statement)


class DocumentIntelligenceError(RuntimeError):
    def __init__(self, diagnostic: IntelligenceDiagnostic) -> None:
        super().__init__(f"{diagnostic.code}: {diagnostic.message}")
        self.diagnostic = diagnostic


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    timeout_seconds: float = 30
    backoff_seconds: float = 0

    def __post_init__(self) -> None:
        if self.attempts < 1 or self.timeout_seconds <= 0 or self.backoff_seconds < 0:
            raise ValueError("invalid document intelligence retry policy")


class DocumentIntelligenceService:
    def __init__(
        self,
        parser: DocumentParser,
        agent: DocumentUnderstandingAgent,
        store: IntelligenceStore,
        *,
        confidence_threshold: float = 0.8,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("confidence threshold must be between zero and one")
        self._parser = parser
        self._agent = agent
        self._store = store
        self._confidence_threshold = confidence_threshold
        self._retry = retry_policy or RetryPolicy()
        self._locks: dict[str, asyncio.Lock] = {}

    async def process(
        self,
        *,
        blob_id: str,
        sha256: str,
        media_type: str,
        capability_token: str,
        output_schema: dict[str, Any],
        schema_version: str,
    ) -> DocumentIntelligenceResult:
        if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
            raise ValueError("sha256 must be lowercase hexadecimal")
        pipeline_version = (
            f"{self._parser.name}@{self._parser.version}/"
            f"{self._agent.name}@{self._agent.version}/{schema_version}"
        )
        cache_key = hashlib.sha256(f"{sha256}:{pipeline_version}".encode()).hexdigest()
        cached = await self._store.get(cache_key)
        if cached is not None:
            return cached
        lock = self._locks.setdefault(cache_key, asyncio.Lock())
        async with lock:
            cached = await self._store.get(cache_key)
            if cached is not None:
                return cached
            parsed_payload = await self._invoke(
                "OCR",
                lambda: self._parser.parse(
                    {
                        "blobId": blob_id,
                        "sha256": sha256,
                        "mediaType": media_type,
                        "capabilityToken": capability_token,
                    }
                ),
            )
            try:
                parsed = ParsedDocument.model_validate(parsed_payload)
            except ValidationError as exc:
                raise self._schema_error("OCR", exc) from exc
            extraction_payload = await self._invoke(
                "EXTRACTION", lambda: self._agent.extract(parsed, output_schema=output_schema)
            )
            try:
                extraction = AgentExtraction.model_validate(extraction_payload)
            except ValidationError as exc:
                raise self._schema_error("EXTRACTION", exc) from exc
            if extraction.schema_version != schema_version:
                raise self._schema_error("EXTRACTION", ValueError("schema version differs"))
            self._validate_declared_schema(extraction_payload, output_schema)
            reasons = _review_reasons(extraction, self._confidence_threshold)
            result = DocumentIntelligenceResult(
                blobId=blob_id,
                sha256=sha256,
                pipelineVersion=pipeline_version,
                status="REVIEW_REQUIRED" if reasons else "COMPLETED",
                extraction=extraction,
                reviewReasons=reasons,
            )
            await self._store.put(cache_key, result)
            return result

    async def _invoke(
        self,
        stage: Literal["OCR", "CLASSIFICATION", "EXTRACTION", "SCHEMA", "PROVIDER"],
        call: Callable[[], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self._retry.attempts + 1):
            try:
                return await asyncio.wait_for(call(), timeout=self._retry.timeout_seconds)
            except (TimeoutError, ConnectionError, OSError) as exc:
                last_error = exc
                if attempt < self._retry.attempts and self._retry.backoff_seconds:
                    await asyncio.sleep(self._retry.backoff_seconds * attempt)
            except Exception as exc:
                raise DocumentIntelligenceError(
                    IntelligenceDiagnostic(
                        code=f"{stage}_PROVIDER_ERROR",
                        stage=stage,
                        message=str(exc),
                        retryable=False,
                        attempts=attempt,
                    )
                ) from exc
        assert last_error is not None
        raise DocumentIntelligenceError(
            IntelligenceDiagnostic(
                code=f"{stage}_RETRY_EXHAUSTED",
                stage=stage,
                message=str(last_error) or type(last_error).__name__,
                retryable=True,
                attempts=self._retry.attempts,
            )
        ) from last_error

    @staticmethod
    def _schema_error(stage: str, error: Exception) -> DocumentIntelligenceError:
        return DocumentIntelligenceError(
            IntelligenceDiagnostic(
                code="MODEL_OUTPUT_SCHEMA_INVALID",
                stage="SCHEMA",
                message=f"{stage}: {error}",
                retryable=False,
                attempts=1,
            )
        )

    def _validate_declared_schema(
        self, payload: dict[str, Any], output_schema: dict[str, Any]
    ) -> None:
        from jsonschema import Draft202012Validator

        try:
            Draft202012Validator(output_schema).validate(payload)
        except Exception as exc:
            raise self._schema_error("EXTRACTION", exc) from exc


def evaluate_cross_file_consistency(
    results: Sequence[DocumentIntelligenceResult], rules: Sequence[CrossFileRule]
) -> tuple[CrossFileFinding, ...]:
    findings: list[CrossFileFinding] = []
    for rule in rules:
        values: list[tuple[str, ExtractedField]] = []
        review_evidence: list[EvidenceLocation] = []
        for result in results:
            extraction = result.extraction
            if (
                extraction is None
                or extraction.classification.document_type not in rule.document_types
            ):
                continue
            field = next((item for item in extraction.fields if item.name == rule.field), None)
            if field is None or result.status == "REVIEW_REQUIRED":
                review_evidence.extend(
                    extraction.classification.evidence if field is None else field.evidence
                )
            else:
                values.append((extraction.classification.document_type, field))
        if review_evidence:
            findings.append(
                CrossFileFinding(
                    ruleKey=rule.key,
                    code="CROSS_FILE_REVIEW_REQUIRED",
                    severity=rule.severity,
                    detail=f"字段 {rule.field} 的证据缺失或置信度不足, 不能自动判定一致。",
                    evidence=tuple(review_evidence),
                    requiresReview=True,
                )
            )
            continue
        normalized = {_canonical_value(field.value) for _, field in values}
        if len(values) >= 2 and len(normalized) > 1:
            findings.append(
                CrossFileFinding(
                    ruleKey=rule.key,
                    code="CROSS_FILE_VALUE_MISMATCH",
                    severity=rule.severity,
                    detail=f"字段 {rule.field} 在多个文件中不一致。",
                    evidence=tuple(evidence for _, field in values for evidence in field.evidence),
                    requiresReview=False,
                )
            )
    return tuple(sorted(findings, key=lambda item: (item.rule_key, item.code)))


def render_evidence_pdf(
    title: str,
    results: Sequence[DocumentIntelligenceResult],
    findings: Sequence[CrossFileFinding],
) -> bytes:
    lines = [title]
    for result in results:
        lines.append(f"Blob {result.blob_id}: {result.status}")
        if result.extraction is not None:
            lines.append(
                f"Type: {result.extraction.classification.document_type} "
                f"({result.extraction.classification.confidence:.3f})"
            )
            for field in result.extraction.fields:
                pages = ",".join(str(item.page) for item in field.evidence)
                lines.append(
                    f"{field.name}={field.value} confidence={field.confidence:.3f} "
                    f"pages={pages}"
                )
    for finding in findings:
        lines.append(f"{finding.code}: {finding.detail}")
    return _minimal_pdf(lines)


def pdf_report_payload(content: bytes) -> dict[str, Any]:
    return {
        "mediaType": "application/pdf",
        "sha256": hashlib.sha256(content).hexdigest(),
        "contentBase64": base64.b64encode(content).decode("ascii"),
    }


class AccuracyBaseline(IntelligenceModel):
    precision: float = Field(ge=0, le=1)
    recall: float = Field(ge=0, le=1)
    review_rate: float = Field(alias="reviewRate", ge=0, le=1)
    samples: int = Field(ge=1)


def calculate_accuracy_baseline(
    expected: Sequence[set[tuple[str, str]]], results: Sequence[DocumentIntelligenceResult]
) -> AccuracyBaseline:
    if not expected or len(expected) != len(results):
        raise ValueError("expected labels and results must have the same non-zero length")
    true_positive = false_positive = false_negative = reviews = 0
    for labels, result in zip(expected, results, strict=True):
        if result.status == "REVIEW_REQUIRED":
            reviews += 1
        predicted = set()
        if result.extraction is not None:
            predicted = {(field.name, str(field.value)) for field in result.extraction.fields}
        true_positive += len(labels & predicted)
        false_positive += len(predicted - labels)
        false_negative += len(labels - predicted)
    precision = true_positive / (true_positive + false_positive or 1)
    recall = true_positive / (true_positive + false_negative or 1)
    return AccuracyBaseline(
        precision=precision,
        recall=recall,
        reviewRate=reviews / len(results),
        samples=len(results),
    )


def _review_reasons(extraction: AgentExtraction, threshold: float) -> tuple[str, ...]:
    reasons: list[str] = []
    if extraction.classification.confidence < threshold:
        reasons.append("CLASSIFICATION_CONFIDENCE_LOW")
    reasons.extend(
        f"FIELD_CONFIDENCE_LOW:{field.name}"
        for field in extraction.fields
        if field.confidence < threshold
    )
    return tuple(reasons)


def _canonical_value(value: str | int | float | bool | None) -> str:
    if isinstance(value, str):
        return " ".join(value.casefold().split())
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _minimal_pdf(lines: Sequence[str]) -> bytes:
    escaped = [
        line.encode("ascii", "replace")
        .decode("ascii")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        for line in lines
    ]
    stream = "BT /F1 10 Tf 50 790 Td 12 TL " + " ".join(
        f"({line[:140]}) Tj T*" for line in escaped[:58]
    ) + " ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(stream.encode())} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, item in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n{item}\nendobj\n".encode())
    xref = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    payload.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    payload.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(payload)
