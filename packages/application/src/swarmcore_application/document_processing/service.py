"""Application services for generic document processing."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import uuid7
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import (
    BlobObject,
    BusinessDocument,
    BusinessDocumentVersion,
    DocumentProcessingResult,
    DocumentProcessingRun,
    OutboxEvent,
    UploadBatch,
)
from swarmcore_persistence.repositories import canonical_hash

from .adapters import (
    LabelCandidateClassifier,
    SchemaDrivenExtractor,
    build_ocr_adapter,
    schema_for_ref,
)
from .contracts import (
    DEFAULT_BUSINESS_PROFILE,
    DocumentRequirement,
    ProcessingResultEnvelope,
    resolve_profile,
)
from .parsers import ParserRegistry


class DocumentProcessingError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail or code


class UploadBatchService:
    def __init__(self) -> None:
        self._audit = AuditRepository()

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        source: str,
        context: dict[str, Any],
        actor: str,
        idempotency_key: str,
    ) -> UploadBatch:
        compact = {
            key: value
            for key, value in context.items()
            if key
            in {
                "businessWorkKey",
                "businessObjectIds",
                "caseId",
                "processingProfileRef",
                "classificationLabels",
                "extractionSchemaRef",
            }
        }
        request_hash = canonical_hash(
            {"source": source, "context": compact, "actor": actor}
        )
        existing = await self._idempotent(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation="upload-batch.create",
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing is not None:
            batch = await session.get(UploadBatch, existing)
            if batch is None:
                raise RuntimeError("upload batch idempotency record is invalid")
            return batch
        batch = UploadBatch(
            tenant_id=tenant_id,
            project_id=project_id,
            source=source.strip() or "web",
            context=compact,
            status="OPEN",
            created_by=actor,
        )
        session.add(batch)
        await session.flush()
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation="upload-batch.create",
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=batch.id,
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="document.upload-batch.created",
            resource_type="upload_batch",
            resource_id=str(batch.id),
            metadata={"source": batch.source},
        )
        return batch

    async def get(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        batch_id: UUID,
    ) -> UploadBatch:
        batch = await session.scalar(
            select(UploadBatch).where(
                UploadBatch.id == batch_id,
                UploadBatch.tenant_id == tenant_id,
                UploadBatch.project_id == project_id,
            )
        )
        if batch is None:
            raise LookupError("UPLOAD_BATCH_NOT_FOUND")
        return batch

    async def mark_file_result(
        self,
        session: AsyncSession,
        *,
        batch: UploadBatch,
        succeeded: bool,
    ) -> UploadBatch:
        batch.file_count += 1
        if succeeded:
            batch.succeeded_count += 1
        else:
            batch.failed_count += 1
        if batch.status == "OPEN":
            batch.status = "IN_PROGRESS"
        await session.flush()
        return batch

    async def complete_if_idle(
        self,
        session: AsyncSession,
        *,
        batch: UploadBatch,
    ) -> UploadBatch:
        if batch.file_count > 0 and batch.succeeded_count + batch.failed_count >= batch.file_count:
            batch.status = "COMPLETED" if batch.failed_count == 0 else "COMPLETED_WITH_ERRORS"
            batch.completed_at = datetime.now(UTC)
            await session.flush()
        return batch

    async def _idempotent(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        operation: str,
        key: str,
        request_hash: str,
    ) -> UUID | None:
        from swarmcore_persistence.models import IdempotencyKey

        row = await session.scalar(
            select(IdempotencyKey).where(
                IdempotencyKey.tenant_id == tenant_id,
                IdempotencyKey.project_id == project_id,
                IdempotencyKey.operation == operation,
                IdempotencyKey.key == key,
            )
        )
        if row is None:
            return None
        if row.request_hash != request_hash:
            raise ValueError("IDEMPOTENCY_KEY_CONFLICT")
        return row.response_ref

    async def _record_idempotency(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        operation: str,
        key: str,
        request_hash: str,
        response_ref: UUID,
    ) -> None:
        from datetime import timedelta

        from swarmcore_persistence.models import IdempotencyKey

        session.add(
            IdempotencyKey(
                tenant_id=tenant_id,
                project_id=project_id,
                operation=operation,
                key=key,
                request_hash=request_hash,
                response_ref=response_ref,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        await session.flush()


class DocumentRequirementService:
    """Projects Capability Pack document declarations into generic requirements."""

    def from_pack_documents(
        self,
        documents: Any,
        *,
        default_profile_ref: str | None = None,
    ) -> tuple[str | None, tuple[DocumentRequirement, ...]]:
        profile_ref = default_profile_ref or DEFAULT_BUSINESS_PROFILE.ref
        items: list[Any]
        if documents is None:
            return None, ()
        if isinstance(documents, dict):
            profile_ref = documents.get("processingProfile") or profile_ref
            items = list(documents.get("requirements") or [])
        elif isinstance(documents, list | tuple):
            items = list(documents)
        else:
            raise ValueError("INVALID_DOCUMENT_REQUIREMENTS")
        requirements: list[DocumentRequirement] = []
        for raw in items:
            if hasattr(raw, "model_dump"):
                payload = raw.model_dump(by_alias=True)
            elif isinstance(raw, dict):
                payload = raw
            else:
                raise ValueError("INVALID_DOCUMENT_REQUIREMENT")
            category = str(payload.get("category") or payload.get("key") or "").strip()
            key = str(payload.get("key") or category).strip()
            if not key:
                raise ValueError("DOCUMENT_REQUIREMENT_KEY_REQUIRED")
            labels = payload.get("classificationLabels") or payload.get("classification_labels")
            if not labels and category:
                labels = [category]
            requirements.append(
                DocumentRequirement(
                    key=key,
                    displayName=str(
                        payload.get("displayName")
                        or payload.get("display_name")
                        or category
                        or key
                    ),
                    description=str(payload.get("description") or ""),
                    required=bool(payload.get("required", True)),
                    minCount=int(payload.get("minCount") or payload.get("min_count") or 1),
                    maxCount=payload.get("maxCount", payload.get("max_count")),
                    acceptedMediaTypes=tuple(
                        payload.get("acceptedMediaTypes")
                        or payload.get("accepted_media_types")
                        or ()
                    ),
                    classificationLabels=tuple(labels or ()),
                    processingProfileRef=payload.get("processingProfile")
                    or payload.get("processing_profile_ref")
                    or profile_ref,
                    extractionSchemaRef=payload.get("extractionSchema")
                    or payload.get("extraction_schema_ref"),
                    reviewPolicy=dict(payload.get("reviewPolicy") or {}),
                    category=category or None,
                )
            )
        return profile_ref, tuple(requirements)


class DocumentProcessingService:
    def __init__(
        self,
        *,
        storage_root: Path | None = None,
        parsers: ParserRegistry | None = None,
    ) -> None:
        self._audit = AuditRepository()
        self._parsers = parsers or ParserRegistry()
        self._classifier = LabelCandidateClassifier()
        self._extractor = SchemaDrivenExtractor()
        self._ocr = build_ocr_adapter()
        self._storage_root = storage_root or Path(
            __import__("os").environ.get("SWARMCORE_ARTIFACT_ROOT", ".tmp/artifacts")
        )

    async def start_for_version(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version: BusinessDocumentVersion,
        document: BusinessDocument,
        profile_ref: str | None,
        candidate_labels: list[dict[str, str]] | None,
        extraction_schema_ref: str | None,
        upload_batch_id: UUID | None,
        actor: str,
        blob_content: bytes | None = None,
    ) -> DocumentProcessingRun:
        profile = resolve_profile(profile_ref)
        latest_attempt = await session.scalar(
            select(func.max(DocumentProcessingRun.attempt)).where(
                DocumentProcessingRun.business_document_version_id == version.id,
                DocumentProcessingRun.tenant_id == tenant_id,
                DocumentProcessingRun.project_id == project_id,
            )
        )
        run = DocumentProcessingRun(
            tenant_id=tenant_id,
            project_id=project_id,
            business_document_version_id=version.id,
            upload_batch_id=upload_batch_id,
            profile_ref=profile.ref,
            status="PENDING",
            current_stage="PENDING",
            attempt=int(latest_attempt or 0) + 1,
            provenance={
                "actor": actor,
                "documentId": str(document.id),
                "category": document.category,
            },
        )
        session.add(run)
        version.processing_status = "PROCESSING"
        document.status = "PROCESSING"
        await session.flush()
        await self._execute_run(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            document=document,
            version=version,
            run=run,
            profile_ref=profile.ref,
            candidate_labels=candidate_labels
            or [{"label": document.category, "displayName": document.category}],
            extraction_schema_ref=extraction_schema_ref,
            actor=actor,
            blob_content=blob_content,
        )
        return run

    async def reprocess(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
        actor: str,
        profile_ref: str | None = None,
        candidate_labels: list[dict[str, str]] | None = None,
        extraction_schema_ref: str | None = None,
        blob_content: bytes | None = None,
    ) -> DocumentProcessingRun:
        document = await session.scalar(
            select(BusinessDocument).where(
                BusinessDocument.id == document_id,
                BusinessDocument.tenant_id == tenant_id,
                BusinessDocument.project_id == project_id,
            )
        )
        if document is None:
            raise LookupError("DOCUMENT_NOT_FOUND")
        version = await session.scalar(
            select(BusinessDocumentVersion).where(
                BusinessDocumentVersion.business_document_id == document.id,
                BusinessDocumentVersion.version == document.current_version,
                BusinessDocumentVersion.tenant_id == tenant_id,
                BusinessDocumentVersion.project_id == project_id,
            )
        )
        if version is None:
            raise LookupError("DOCUMENT_VERSION_NOT_FOUND")
        return await self.start_for_version(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version=version,
            document=document,
            profile_ref=profile_ref,
            candidate_labels=candidate_labels,
            extraction_schema_ref=extraction_schema_ref,
            upload_batch_id=None,
            actor=actor,
            blob_content=blob_content,
        )

    async def get_run(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        processing_run_id: UUID,
    ) -> DocumentProcessingRun:
        run = await session.scalar(
            select(DocumentProcessingRun).where(
                DocumentProcessingRun.id == processing_run_id,
                DocumentProcessingRun.tenant_id == tenant_id,
                DocumentProcessingRun.project_id == project_id,
            )
        )
        if run is None:
            raise LookupError("PROCESSING_RUN_NOT_FOUND")
        return run

    async def latest_run_for_version(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version_id: UUID,
    ) -> DocumentProcessingRun | None:
        run = await session.scalar(
            select(DocumentProcessingRun)
            .where(
                DocumentProcessingRun.business_document_version_id == version_id,
                DocumentProcessingRun.tenant_id == tenant_id,
                DocumentProcessingRun.project_id == project_id,
            )
            .order_by(DocumentProcessingRun.attempt.desc())
            .limit(1)
        )
        return run if isinstance(run, DocumentProcessingRun) else None

    async def latest_result(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version_id: UUID,
        result_type: str = "PROCESSING",
    ) -> DocumentProcessingResult | None:
        result = await session.scalar(
            select(DocumentProcessingResult)
            .where(
                DocumentProcessingResult.business_document_version_id == version_id,
                DocumentProcessingResult.tenant_id == tenant_id,
                DocumentProcessingResult.project_id == project_id,
                DocumentProcessingResult.result_type == result_type,
            )
            .order_by(DocumentProcessingResult.result_version.desc())
            .limit(1)
        )
        return result if isinstance(result, DocumentProcessingResult) else None

    async def _execute_run(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document: BusinessDocument,
        version: BusinessDocumentVersion,
        run: DocumentProcessingRun,
        profile_ref: str,
        candidate_labels: list[dict[str, str]],
        extraction_schema_ref: str | None,
        actor: str,
        blob_content: bytes | None,
    ) -> None:
        profile = resolve_profile(profile_ref)
        warnings: list[str] = []
        quality_flags: list[str] = []
        try:
            async with session.begin_nested():
                await self._run_pipeline(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    document=document,
                    version=version,
                    run=run,
                    profile=profile,
                    candidate_labels=candidate_labels,
                    extraction_schema_ref=extraction_schema_ref,
                    actor=actor,
                    blob_content=blob_content,
                    warnings=warnings,
                    quality_flags=quality_flags,
                )
        except DocumentProcessingError as exc:
            await self._fail_run(
                session,
                document=document,
                version=version,
                run=run,
                code=exc.code,
                detail=exc.detail,
                actor=actor,
            )
        except ValueError as exc:
            await self._fail_run(
                session,
                document=document,
                version=version,
                run=run,
                code=str(exc),
                detail=str(exc),
                actor=actor,
            )
        except Exception as exc:
            await self._fail_run(
                session,
                document=document,
                version=version,
                run=run,
                code="DOCUMENT_PROCESSING_FAILED",
                detail=str(exc)[:2000],
                actor=actor,
            )

    async def _run_pipeline(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document: BusinessDocument,
        version: BusinessDocumentVersion,
        run: DocumentProcessingRun,
        profile: Any,
        candidate_labels: list[dict[str, str]],
        extraction_schema_ref: str | None,
        actor: str,
        blob_content: bytes | None,
        warnings: list[str],
        quality_flags: list[str],
    ) -> None:
        run.status = "SCANNING"
        run.current_stage = "SCANNING"
        await session.flush()

        blob = await session.get(BlobObject, version.blob_id)
        if blob is None:
            raise DocumentProcessingError("BLOB_NOT_FOUND")
        if blob.scan_status != "CLEAN":
            raise DocumentProcessingError("SECURITY_SCAN_FAILED", blob.scan_status)
        content = blob_content
        if content is None:
            content = self._read_blob_bytes(blob)
        if hashlib.sha256(content).hexdigest() != version.sha256:
            raise DocumentProcessingError("DOCUMENT_HASH_MISMATCH")
        detected = _detect_media_type(content, version.filename, version.media_type)
        if detected != version.media_type and not _compatible_media(
            detected, version.media_type
        ):
            quality_flags.append("MIME_EXTENSION_MISMATCH")
            warnings.append(f"declared={version.media_type};detected={detected}")

        run.status = "PARSING"
        run.current_stage = "PARSING"
        await session.flush()
        parser_ref, parsed = self._parsers.parse(
            filename=version.filename,
            media_type=version.media_type,
            content=content,
        )
        run.parser_ref = parser_ref
        warnings.extend(parsed.warnings)

        if parsed.needs_ocr:
            run.status = "OCR_PROCESSING"
            run.current_stage = "OCR_PROCESSING"
            await session.flush()
            if not self._ocr.available:
                quality_flags.append("OCR_NOT_CONFIGURED")
                warnings.append("当前环境未配置 OCR")
                envelope = ProcessingResultEnvelope(
                    status="REVIEW_REQUIRED",
                    documentType=None,
                    content=parsed,
                    extractions=[],
                    evidence=[],
                    qualityFlags=quality_flags,
                    warnings=warnings,
                    provenance={
                        "processingRunId": str(run.id),
                        "profileRef": profile.ref,
                        "parserRef": parser_ref,
                        "ocr": {"available": False, "provider": self._ocr.name},
                    },
                )
                await self._persist_result(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    version=version,
                    document=document,
                    run=run,
                    envelope=envelope,
                    actor=actor,
                    status="REVIEW_REQUIRED",
                )
                return
            ocr_result = self._ocr.recognize(
                media_type=version.media_type, content=content
            )
            ocr_text = str(ocr_result.get("text") or "")
            parsed = parsed.model_copy(
                update={
                    "pages": ocr_result.get("pages") or parsed.pages,
                    "text_excerpt": ocr_text[:4000],
                    "needs_ocr": False,
                    "warnings": [*parsed.warnings, "OCR_APPLIED"],
                }
            )

        run.status = "CLASSIFYING"
        run.current_stage = "CLASSIFYING"
        await session.flush()
        classification = self._classifier.classify(
            filename=version.filename,
            media_type=version.media_type,
            text_excerpt=parsed.text_excerpt,
            candidate_labels=candidate_labels,
            profile=profile,
        )
        run.classifier_ref = self._classifier.ref
        classification_threshold = float(
            profile.quality_thresholds.get("classification", 0.7)
        )
        needs_classification_review = classification.confidence < classification_threshold

        run.status = "EXTRACTING"
        run.current_stage = "EXTRACTING"
        await session.flush()
        schema = schema_for_ref(extraction_schema_ref or (
            profile.extraction_schema_refs[0] if profile.extraction_schema_refs else None
        ))
        extracted: list[Any] = []
        extractor_refs: list[str] = []
        if schema is not None:
            extracted = self._extractor.extract(
                content=parsed,
                schema=schema,
                classification=classification,
                profile=profile,
            )
            extractor_refs = [self._extractor.ref]
        run.extractor_refs = extractor_refs

        content_ref = None
        if _content_too_large(parsed):
            content_ref = await self._store_content_artifact(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                version=version,
                parsed=parsed,
            )
            compact = parsed.model_copy(
                update={
                    "paragraphs": parsed.paragraphs[:20],
                    "pages": [
                        {
                            "page": page.get("page", 1),
                            "text": str(page.get("text", ""))[:500],
                        }
                        for page in parsed.pages[:5]
                    ],
                    "sheets": parsed.sheets[:3],
                }
            )
        else:
            compact = parsed

        needs_field_review = any(
            field.review_status == "PENDING" for field in extracted
        )
        status = (
            "REVIEW_REQUIRED"
            if needs_classification_review or needs_field_review or quality_flags
            else "READY"
        )
        if status == "READY":
            for field in extracted:
                if field.review_status == "AUTO_ACCEPTED":
                    field.confirmed_value = field.machine_value
                    field.value = field.machine_value

        envelope = ProcessingResultEnvelope(
            status=status,  # type: ignore[arg-type]
            documentType=classification,
            content=compact,
            extractions=extracted,
            evidence=[*classification.evidence],
            qualityFlags=quality_flags,
            warnings=warnings,
            provenance={
                "processingRunId": str(run.id),
                "profileRef": profile.ref,
                "parserRef": parser_ref,
                "classifierRef": self._classifier.ref,
                "extractorRefs": extractor_refs,
                "attempt": run.attempt,
            },
            contentArtifactRef=content_ref,
        )
        await self._persist_result(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version=version,
            document=document,
            run=run,
            envelope=envelope,
            actor=actor,
            status=status,
        )

    async def _persist_result(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version: BusinessDocumentVersion,
        document: BusinessDocument,
        run: DocumentProcessingRun,
        envelope: ProcessingResultEnvelope,
        actor: str,
        status: str,
    ) -> DocumentProcessingResult:
        latest_version = await session.scalar(
            select(func.max(DocumentProcessingResult.result_version)).where(
                DocumentProcessingResult.business_document_version_id == version.id,
                DocumentProcessingResult.result_type == "PROCESSING",
            )
        )
        result = DocumentProcessingResult(
            tenant_id=tenant_id,
            project_id=project_id,
            business_document_version_id=version.id,
            result_type="PROCESSING",
            result_version=int(latest_version or 0) + 1,
            status=status,
            schema_ref=envelope.schema_version,
            producer_ref=str(run.id),
            result=_sanitize_jsonable(envelope.model_dump(mode="json", by_alias=True)),
            evidence=_sanitize_jsonable(list(envelope.evidence)),
        )
        session.add(result)
        run.status = status
        run.current_stage = status
        run.completed_at = datetime.now(UTC)
        version.processing_status = status
        document.status = "AVAILABLE" if status == "READY" else status
        await session.flush()
        event_id = uuid7()
        session.add(
            OutboxEvent(
                id=event_id,
                tenant_id=tenant_id,
                aggregate_id=document.id,
                destination="nats",
                partition_key=str(document.id),
                source_id=event_id,
                type="document.processing.completed",
                payload={
                    "documentId": str(document.id),
                    "documentVersionId": str(version.id),
                    "processingRunId": str(run.id),
                    "status": status,
                },
            )
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="document.processing.completed",
            resource_type="document_processing_run",
            resource_id=str(run.id),
            metadata={"status": status, "documentId": str(document.id)},
        )
        return result

    async def _fail_run(
        self,
        session: AsyncSession,
        *,
        document: BusinessDocument,
        version: BusinessDocumentVersion,
        run: DocumentProcessingRun,
        code: str,
        detail: str,
        actor: str,
    ) -> None:
        run.status = "FAILED"
        run.current_stage = "FAILED"
        run.error_code = code
        run.error_detail = detail[:2048]
        run.completed_at = datetime.now(UTC)
        version.processing_status = "FAILED"
        document.status = "FAILED"
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=document.tenant_id,
            project_id=document.project_id,
            actor_id=actor,
            action="document.processing.failed",
            resource_type="document_processing_run",
            resource_id=str(run.id),
            metadata={"errorCode": code, "detail": detail[:500]},
        )

    def _read_blob_bytes(self, blob: BlobObject) -> bytes:
        root = self._storage_root
        path = root / blob.object_key
        if not path.is_file():
            raise DocumentProcessingError("BLOB_CONTENT_UNAVAILABLE", str(path))
        return path.read_bytes()

    async def _store_content_artifact(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version: BusinessDocumentVersion,
        parsed: Any,
    ) -> str:
        payload = json.dumps(
            _sanitize_jsonable(parsed.model_dump(mode="json", by_alias=True)),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        blob_id = uuid7()
        object_key = (
            f"{tenant_id}/{project_id}/document-processing/{version.id}/{blob_id}.json"
        )
        target = self._storage_root / object_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        session.add(
            BlobObject(
                id=blob_id,
                tenant_id=tenant_id,
                project_id=project_id,
                object_key=object_key,
                version=1,
                filename=f"processing-{version.id}.json",
                media_type="application/json",
                size_bytes=len(payload),
                sha256=digest,
                status="AVAILABLE",
                scan_status="CLEAN",
                retention_until=datetime.now(UTC).replace(year=datetime.now(UTC).year + 3),
                metadata_json={
                    "kind": "document-processing-content",
                    "documentVersionId": str(version.id),
                },
            )
        )
        await session.flush()
        return f"blob://{blob_id}"


class DocumentReviewService:
    def __init__(self, processing: DocumentProcessingService | None = None) -> None:
        self._processing = processing or DocumentProcessingService()
        self._audit = AuditRepository()

    async def confirm_classification(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
        label: str,
        display_name: str | None,
        actor: str,
        expected_result_version: int | None = None,
    ) -> DocumentProcessingResult:
        document, version, current = await self._load_current(
            session, tenant_id=tenant_id, project_id=project_id, document_id=document_id
        )
        if (
            expected_result_version is not None
            and current.result_version != expected_result_version
        ):
            raise DocumentProcessingError("REVIEW_VERSION_CONFLICT")
        payload = dict(current.result)
        document_type = dict(payload.get("documentType") or {})
        document_type["confirmedLabel"] = label
        document_type["displayName"] = display_name or label
        document_type["confirmedBy"] = actor
        # Preserve machine label/confidence; confirmation is additive.
        payload["documentType"] = document_type
        extractions = list(payload.get("extractions") or [])
        fields_ready = (
            all(
                item.get("reviewStatus")
                in {"AUTO_ACCEPTED", "CONFIRMED", "CORRECTED", "UNCONFIRMED"}
                for item in extractions
            )
            if extractions
            else True
        )
        payload["status"] = "READY" if fields_ready else "REVIEW_REQUIRED"
        return await self._append_review_result(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            document=document,
            version=version,
            previous=current,
            payload=payload,
            actor=actor,
            action="document.classification.confirmed",
        )

    async def confirm_fields(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
        fields: list[dict[str, Any]],
        actor: str,
        expected_result_version: int | None = None,
        accept_high_confidence: bool = False,
    ) -> DocumentProcessingResult:
        document, version, current = await self._load_current(
            session, tenant_id=tenant_id, project_id=project_id, document_id=document_id
        )
        if (
            expected_result_version is not None
            and current.result_version != expected_result_version
        ):
            raise DocumentProcessingError("REVIEW_VERSION_CONFLICT")
        payload = dict(current.result)
        extractions = list(payload.get("extractions") or [])
        updates = {str(item["fieldPath"]): item for item in fields}
        threshold = 0.75
        for item in extractions:
            path = str(item.get("fieldPath"))
            machine_value = item.get("machineValue", item.get("value"))
            item["machineValue"] = machine_value
            if accept_high_confidence and float(item.get("confidence") or 0) >= threshold:
                item["confirmedValue"] = machine_value
                item["value"] = machine_value
                item["reviewStatus"] = "CONFIRMED"
                continue
            update = updates.get(path)
            if update is None:
                continue
            if update.get("unconfirmed"):
                item["reviewStatus"] = "UNCONFIRMED"
                item["confirmedValue"] = None
                continue
            confirmed = update.get("confirmedValue", update.get("value"))
            item["confirmedValue"] = confirmed
            item["value"] = confirmed
            item["reviewStatus"] = (
                "CORRECTED" if confirmed != machine_value else "CONFIRMED"
            )
        payload["extractions"] = extractions
        classification = payload.get("documentType") or {}
        classification_ready = bool(
            classification.get("confirmedLabel")
            or float(classification.get("confidence") or 0) >= 0.7
        )
        fields_ready = all(
            item.get("reviewStatus") in {"AUTO_ACCEPTED", "CONFIRMED", "CORRECTED", "UNCONFIRMED"}
            for item in extractions
        ) if extractions else classification_ready
        payload["status"] = "READY" if classification_ready and fields_ready else "REVIEW_REQUIRED"
        return await self._append_review_result(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            document=document,
            version=version,
            previous=current,
            payload=payload,
            actor=actor,
            action="document.fields.confirmed",
        )

    async def _load_current(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
    ) -> tuple[BusinessDocument, BusinessDocumentVersion, DocumentProcessingResult]:
        document = await session.scalar(
            select(BusinessDocument).where(
                BusinessDocument.id == document_id,
                BusinessDocument.tenant_id == tenant_id,
                BusinessDocument.project_id == project_id,
            )
        )
        if document is None:
            raise LookupError("DOCUMENT_NOT_FOUND")
        version = await session.scalar(
            select(BusinessDocumentVersion).where(
                BusinessDocumentVersion.business_document_id == document.id,
                BusinessDocumentVersion.version == document.current_version,
            )
        )
        if version is None:
            raise LookupError("DOCUMENT_VERSION_NOT_FOUND")
        current = await self._processing.latest_result(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version_id=version.id,
        )
        if current is None:
            raise LookupError("PROCESSING_RESULT_NOT_FOUND")
        return document, version, current

    async def _append_review_result(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document: BusinessDocument,
        version: BusinessDocumentVersion,
        previous: DocumentProcessingResult,
        payload: dict[str, Any],
        actor: str,
        action: str,
    ) -> DocumentProcessingResult:
        status = str(payload.get("status") or "REVIEW_REQUIRED")
        result = DocumentProcessingResult(
            tenant_id=tenant_id,
            project_id=project_id,
            business_document_version_id=version.id,
            result_type="PROCESSING",
            result_version=previous.result_version + 1,
            status=status,
            schema_ref=previous.schema_ref,
            producer_ref=f"review:{actor}",
            result=payload,
            evidence=list(previous.evidence),
            confirmed_by=actor,
            confirmed_at=datetime.now(UTC),
        )
        session.add(result)
        version.processing_status = status
        document.status = "AVAILABLE" if status == "READY" else status
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action=action,
            resource_type="business_document",
            resource_id=str(document.id),
            metadata={
                "resultVersion": result.result_version,
                "status": status,
            },
        )
        return result


def _sanitize_jsonable(value: Any) -> Any:
    """Remove NUL bytes that PostgreSQL JSONB rejects."""
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, list):
        return [_sanitize_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_jsonable(item) for key, item in value.items()}
    return value


def _detect_media_type(content: bytes, filename: str, declared: str) -> str:
    lower = filename.lower()
    if content.startswith(b"%PDF"):
        return "application/pdf"
    if content.startswith(b"PK") and lower.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if content.startswith(b"PK") and lower.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:2] == b"\xff\xd8":
        return "image/jpeg"
    if lower.endswith(".md"):
        return "text/markdown"
    if lower.endswith(".txt"):
        return "text/plain"
    return declared


def _compatible_media(detected: str, declared: str) -> bool:
    aliases = {
        "image/jpg": "image/jpeg",
        "text/x-markdown": "text/markdown",
    }
    return aliases.get(detected, detected) == aliases.get(declared, declared)


def _content_too_large(parsed: Any) -> bool:
    size = len(json.dumps(parsed.model_dump(mode="json", by_alias=True)))
    return size > 24_000
