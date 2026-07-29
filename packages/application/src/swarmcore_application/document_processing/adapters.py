"""OCR, classifier, and schema-driven extractor adapters."""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .contracts import (
    ClassificationResult,
    DocumentProcessingProfile,
    ExtractionField,
    ParsedContent,
)


class OcrAdapter(Protocol):
    name: str
    version: str

    @property
    def available(self) -> bool: ...

    def recognize(
        self,
        *,
        media_type: str,
        content: bytes,
        pages: list[int] | None = None,
    ) -> dict[str, Any]: ...


class UnconfiguredOcrAdapter:
    name = "unconfigured"
    version = "1"

    @property
    def available(self) -> bool:
        return False

    def recognize(
        self, *, media_type: str, content: bytes, pages: list[int] | None = None
    ) -> dict[str, Any]:
        raise RuntimeError("OCR_NOT_CONFIGURED")


class EnvHttpOcrAdapter:
    """Optional remote OCR provider configured via SWARMCORE_OCR_ENDPOINT."""

    name = "http-ocr"
    version = "2"

    def __init__(
        self,
        endpoint: str | None = None,
        *,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._endpoint = endpoint or os.getenv("SWARMCORE_OCR_ENDPOINT", "").strip()
        self._api_key = (
            api_key
            if api_key is not None
            else os.getenv("SWARMCORE_OCR_API_KEY", "").strip()
        )
        self._timeout_seconds = timeout_seconds or float(
            os.getenv("SWARMCORE_OCR_TIMEOUT_SECONDS", "120")
        )

    @property
    def available(self) -> bool:
        return bool(self._endpoint)

    def recognize(
        self, *, media_type: str, content: bytes, pages: list[int] | None = None
    ) -> dict[str, Any]:
        if not self.available:
            raise RuntimeError("OCR_NOT_CONFIGURED")
        payload = json.dumps(
            {
                "mediaType": media_type,
                "contentBase64": base64.b64encode(content).decode("ascii"),
                "pages": pages,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        request = Request(self._endpoint, data=payload, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("OCR_PROVIDER_UNAVAILABLE") from exc
        if not isinstance(result, dict) or not str(result.get("text") or "").strip():
            raise RuntimeError("OCR_EMPTY_RESULT")
        result_pages = result.get("pages")
        if result_pages is None:
            result["pages"] = [{"page": 1, "text": str(result["text"])}]
        elif not isinstance(result_pages, list):
            raise RuntimeError("OCR_INVALID_RESULT")
        return result


class TesseractOcrAdapter:
    """Local OCR adapter configured with explicit executable paths."""

    name = "tesseract"
    version = "1"

    def __init__(
        self,
        tesseract_cmd: str,
        *,
        pdftoppm_cmd: str | None = None,
        language: str | None = None,
    ) -> None:
        self._tesseract_cmd = Path(tesseract_cmd)
        self._pdftoppm_cmd = Path(pdftoppm_cmd) if pdftoppm_cmd else None
        self._language = (
            language
            or os.getenv("SWARMCORE_TESSERACT_LANG")
            or "chi_sim+eng"
        )

    @property
    def available(self) -> bool:
        return self._tesseract_cmd.is_file()

    def recognize(
        self,
        *,
        media_type: str,
        content: bytes,
        pages: list[int] | None = None,
    ) -> dict[str, Any]:
        if not self.available:
            raise RuntimeError("OCR_NOT_CONFIGURED")
        with tempfile.TemporaryDirectory(prefix="swarmcore-ocr-") as temp:
            root = Path(temp)
            inputs = self._prepare_inputs(
                root=root,
                media_type=media_type,
                content=content,
                selected_pages=pages,
            )
            page_results: list[dict[str, Any]] = []
            blocks: list[dict[str, Any]] = []
            for page_number, input_path in inputs:
                completed = subprocess.run(
                    [
                        str(self._tesseract_cmd),
                        str(input_path),
                        "stdout",
                        "-l",
                        self._language,
                        "tsv",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=120,
                )
                if completed.returncode != 0:
                    raise RuntimeError("OCR_PROVIDER_UNAVAILABLE")
                page_blocks = self._parse_tsv(completed.stdout, page_number)
                blocks.extend(page_blocks)
                page_text = " ".join(
                    str(block["text"]) for block in page_blocks
                ).strip()
                confidences = [
                    float(block["confidence"])
                    for block in page_blocks
                    if block.get("confidence") is not None
                ]
                page_results.append(
                    {
                        "page": page_number,
                        "text": page_text,
                        "confidence": (
                            sum(confidences) / len(confidences)
                            if confidences
                            else 0.0
                        ),
                        "blocks": page_blocks,
                    }
                )
        text = "\n\n".join(str(item["text"]) for item in page_results).strip()
        if not text:
            raise RuntimeError("OCR_EMPTY_RESULT")
        return {"text": text, "pages": page_results, "blocks": blocks, "tables": []}

    @staticmethod
    def _parse_tsv(value: str, page_number: int) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        for line in value.splitlines()[1:]:
            cells = line.split("\t", 11)
            if len(cells) != 12 or not cells[11].strip():
                continue
            try:
                left, top, width, height = map(int, cells[6:10])
                confidence = max(0.0, min(1.0, float(cells[10]) / 100))
                block_number = int(cells[2])
                paragraph_number = int(cells[3])
                line_number = int(cells[4])
                word_number = int(cells[5])
            except ValueError:
                continue
            blocks.append(
                {
                    "page": page_number,
                    "text": cells[11].strip(),
                    "bbox": [left, top, left + width, top + height],
                    "confidence": confidence,
                    "sourceKind": "OCR",
                    "block": block_number,
                    "paragraph": paragraph_number,
                    "line": line_number,
                    "word": word_number,
                }
            )
        return blocks

    def _prepare_inputs(
        self,
        *,
        root: Path,
        media_type: str,
        content: bytes,
        selected_pages: list[int] | None,
    ) -> list[tuple[int, Path]]:
        if media_type != "application/pdf":
            suffix = ".png" if media_type == "image/png" else ".jpg"
            image_path = root / f"source{suffix}"
            image_path.write_bytes(content)
            return [(1, image_path)]
        if self._pdftoppm_cmd is None or not self._pdftoppm_cmd.is_file():
            raise RuntimeError("PDF_OCR_RENDERER_NOT_CONFIGURED")
        source = root / "source.pdf"
        source.write_bytes(content)
        prefix = root / "page"
        command = [
            str(self._pdftoppm_cmd),
            "-png",
            "-r",
            "220",
        ]
        if selected_pages:
            command.extend(
                [
                    "-f",
                    str(min(selected_pages)),
                    "-l",
                    str(max(selected_pages)),
                ]
            )
        command.extend([str(source), str(prefix)])
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError("PDF_OCR_RENDER_FAILED")
        rendered = sorted(root.glob("page-*.png"))
        allowed = set(selected_pages or [])
        first_page = min(selected_pages) if selected_pages else 1
        return [
            (first_page + index - 1, path)
            for index, path in enumerate(rendered, start=1)
            if not allowed or first_page + index - 1 in allowed
        ]


def build_ocr_adapter() -> OcrAdapter:
    endpoint = os.getenv("SWARMCORE_OCR_ENDPOINT", "").strip()
    if endpoint:
        return EnvHttpOcrAdapter(endpoint)
    tesseract_cmd = os.getenv("SWARMCORE_TESSERACT_CMD", "").strip()
    if tesseract_cmd:
        return TesseractOcrAdapter(
            tesseract_cmd,
            pdftoppm_cmd=os.getenv("SWARMCORE_PDFTOPPM_CMD", "").strip() or None,
        )
    return UnconfiguredOcrAdapter()


class DocumentClassifier(Protocol):
    name: str
    version: str

    def classify(
        self,
        *,
        filename: str,
        media_type: str,
        text_excerpt: str,
        candidate_labels: list[dict[str, str]],
        profile: DocumentProcessingProfile,
    ) -> ClassificationResult: ...


class LabelCandidateClassifier:
    name = "label-candidates"
    version = "1"

    def classify(
        self,
        *,
        filename: str,
        media_type: str,
        text_excerpt: str,
        candidate_labels: list[dict[str, str]],
        profile: DocumentProcessingProfile,
    ) -> ClassificationResult:
        if not candidate_labels:
            return ClassificationResult(
                label="unclassified",
                displayName="未分类",
                confidence=0.0,
                alternatives=[],
                evidence=[],
                provenance={"classifier": self.ref},
            )
        haystack = f"{filename}\n{text_excerpt}".lower()
        scored: list[tuple[float, dict[str, str], str]] = []
        for item in candidate_labels:
            label = item["label"]
            display = item.get("displayName") or label
            tokens = [
                label.lower(),
                *[part for part in re.split(r"[-_\s]+", label.lower()) if part],
            ]
            hits = sum(1 for token in tokens if token and token in haystack)
            confidence = min(0.99, 0.35 + 0.2 * hits)
            if label.lower() in filename.lower():
                confidence = min(0.99, confidence + 0.25)
            scored.append((confidence, item, display))
        scored.sort(key=lambda row: row[0], reverse=True)
        best_confidence, best, display_name = scored[0]
        alternatives = [
            {"label": item["label"], "displayName": display, "confidence": confidence}
            for confidence, item, display in scored[1:4]
        ]
        evidence = []
        if best_confidence >= 0.35:
            evidence.append(
                {
                    "source": "filename_and_text",
                    "text": filename[:200],
                    "page": 1,
                }
            )
        return ClassificationResult(
            label=best["label"],
            displayName=display_name,
            confidence=round(best_confidence, 4),
            alternatives=alternatives,
            evidence=evidence,
            provenance={"classifier": self.ref, "mediaType": media_type},
        )

    @property
    def ref(self) -> str:
        return f"classifier://{self.name}@{self.version}"


@dataclass(frozen=True)
class ExtractionSchema:
    schema_ref: str
    fields: tuple[dict[str, Any], ...]


class SchemaDrivenExtractor:
    name = "schema-rules"
    version = "2"

    def extract(
        self,
        *,
        content: ParsedContent,
        schema: ExtractionSchema,
        classification: ClassificationResult,
        profile: DocumentProcessingProfile,
    ) -> list[ExtractionField]:
        text = content.text_excerpt or "\n".join(
            str(page.get("text", "")) for page in content.pages
        )
        results: list[ExtractionField] = []
        threshold = float(profile.quality_thresholds.get("extraction", 0.75))
        for field in schema.fields:
            path = str(field["fieldPath"])
            display = str(field.get("displayName") or path)
            value_type = str(field.get("valueType") or "string")
            patterns = [str(item) for item in field.get("patterns", [])]
            machine_value = None
            evidence: list[dict[str, Any]] = []
            quality_flags: list[str] = []
            confidence = 0.0
            for pattern in patterns:
                match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
                if match:
                    candidate = (
                        match.group(1) if match.lastindex else match.group(0)
                    ).strip()
                    if field.get("placeholderAware") and _is_placeholder(candidate):
                        machine_value = None
                        quality_flags.append("PLACEHOLDER_NOT_FILLED")
                    else:
                        machine_value = candidate
                    confidence = 0.92
                    evidence.append(
                        {
                            "page": _evidence_page(content, match.group(0)),
                            "text": match.group(0)[:500],
                            "pattern": pattern,
                        }
                    )
                    break
            if machine_value is None and field.get("fallbackFromFilename"):
                machine_value = classification.label
                confidence = 0.4
                evidence.append(
                    {"page": 1, "text": classification.label, "source": "classification"}
                )
            review_status: Literal[
                "AUTO_ACCEPTED", "PENDING", "CONFIRMED", "CORRECTED", "UNCONFIRMED"
            ] = (
                "UNCONFIRMED"
                if "PLACEHOLDER_NOT_FILLED" in quality_flags
                else "AUTO_ACCEPTED"
                if confidence >= threshold
                else "PENDING"
            )
            results.append(
                ExtractionField(
                    fieldPath=path,
                    displayName=display,
                    value=machine_value,
                    valueType=value_type,
                    critical=bool(field.get("critical", False)),
                    confidence=confidence,
                    reviewStatus=review_status,
                    evidenceRefs=evidence,
                    machineValue=machine_value,
                    confirmedValue=None,
                    qualityFlags=quality_flags,
                )
            )
        return results

    @property
    def ref(self) -> str:
        return f"extractor://{self.name}@{self.version}"


# Built-in generic schemas used by demo packs; business-specific fields stay in pack assets.
GENERIC_TEXT_SCHEMA = ExtractionSchema(
    schema_ref="schema://document/generic-text@1",
    fields=(
        {
            "fieldPath": "document.title",
            "displayName": "标题",
            "valueType": "string",
            "patterns": [r"(?im)^(?:标题|title)\s*[:\N{FULLWIDTH COLON}]\s*(.+)$"],
        },
        {
            "fieldPath": "document.party",
            "displayName": "主体",
            "valueType": "string",
            "patterns": [
                r"(?im)^(?:主体|party)\s*[:\N{FULLWIDTH COLON}]\s*(.+)$"
            ],
        },
        {
            "fieldPath": "document.amount",
            "displayName": "金额",
            "valueType": "string",
            "patterns": [
                r"(?im)(?:金额|amount)\s*[:\N{FULLWIDTH COLON}]?\s*"
                r"([¥\N{YEN SIGN}]?\s*\d[\d,]*(?:\.\d+)?)"
            ],
        },
    ),
)

CONTRACT_STRUCTURE_SCHEMA = ExtractionSchema(
    schema_ref="schema://document/contract-structure@1",
    fields=(
        {
            "fieldPath": "document.title",
            "displayName": "文档标题",
            "valueType": "string",
            "patterns": [
                r"(?im)^(Digital Outcomes and Specialists 4 Framework Agreement"
                r"(?:\s+Call-Off Contract(?:\s+v\d+)?)?)$",
                r"(?im)^(?:标题|title)\s*[:\N{FULLWIDTH COLON}]\s*(.+)$",
            ],
            "critical": True,
        },
        {
            "fieldPath": "contract.reference",
            "displayName": "合同/框架编号",
            "valueType": "string",
            "patterns": [r"\b(RM\d+(?:\.\d+)*)\b"],
            "critical": True,
        },
        {
            "fieldPath": "contract.buyer",
            "displayName": "买方",
            "valueType": "string",
            "patterns": [
                r"(?im)^(?:Buyer|买方)(?:['\u2019]s)?\s*(?:name)?\s*[:\N{FULLWIDTH COLON}]?\s*(.+)$"
            ],
            "placeholderAware": True,
            "critical": True,
        },
        {
            "fieldPath": "contract.supplier",
            "displayName": "供应商",
            "valueType": "string",
            "patterns": [
                r"(?im)^(?:Supplier|供应商)(?:['\u2019]s)?\s*(?:name)?\s*"
                r"[:\N{FULLWIDTH COLON}]?\s*(.+)$"
            ],
            "placeholderAware": True,
            "critical": True,
        },
        {
            "fieldPath": "contract.value",
            "displayName": "合同金额",
            "valueType": "string",
            "patterns": [
                r"(?im)^(?:Call-Off Contract value|合同金额)\s*[:\N{FULLWIDTH COLON}]?\s*(.+)$"
            ],
            "placeholderAware": True,
            "critical": True,
        },
        {
            "fieldPath": "contract.partA",
            "displayName": "Part A",
            "valueType": "string",
            "patterns": [r"(?im)^(Part A\s*[-\u2013]\s*Order Form)$"],
        },
        {
            "fieldPath": "contract.partB",
            "displayName": "Part B",
            "valueType": "string",
            "patterns": [
                r"(?im)^(Part B\s*[-\u2013]\s*Terms and conditions)$"
            ],
        },
        {
            "fieldPath": "contract.partC",
            "displayName": "Part C",
            "valueType": "string",
            "patterns": [r"(?im)^(Part C\s*[-\u2013]\s*The Schedules)$"],
        },
    ),
)


def schema_for_ref(schema_ref: str | None) -> ExtractionSchema | None:
    if not schema_ref:
        return None
    if schema_ref == CONTRACT_STRUCTURE_SCHEMA.schema_ref:
        return CONTRACT_STRUCTURE_SCHEMA
    if schema_ref in {
        "schema://document/generic-text@1",
        "schema://contract/document-extraction@1",
        "schema://contract/post-evaluation-input@2",
    }:
        return GENERIC_TEXT_SCHEMA
    return ExtractionSchema(schema_ref=schema_ref, fields=GENERIC_TEXT_SCHEMA.fields)


_PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)\bclick (?:here )?to enter\b"),
    re.compile(r"(?i)^enter (?:information|text|date|name|.* here)"),
    re.compile(r"(?i)^buyer to insert"),
    re.compile(r"(?i)^\[[^\]]+\]$"),
    re.compile(r"(?i)^x{2,}(?:\s+\w+)?$"),
    re.compile(r"(?i)^(?:tbc|tbd|n/?a|not applicable)$"),
)


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().rstrip(".")
    return not normalized or any(
        pattern.search(normalized) for pattern in _PLACEHOLDER_PATTERNS
    )


def _evidence_page(content: ParsedContent, matched_text: str) -> int:
    needle = matched_text.strip()
    for page in content.pages:
        if needle and needle in str(page.get("text") or ""):
            try:
                return int(page.get("page") or 1)
            except (TypeError, ValueError):
                return 1
    return 1
