"""Application services for generic document processing."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
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
    DocumentProcessingEvent,
    DocumentProcessingResult,
    DocumentProcessingRun,
    IdempotencyKey,
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
from .structuring import DocumentChunker, DocumentQualityChecker


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
        self._chunker = DocumentChunker()
        self._quality = DocumentQualityChecker()
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
            next_event_seq=1,
            provenance={
                "actor": actor,
                "documentId": str(document.id),
                "category": document.category,
                "candidateLabels": candidate_labels
                or [{"label": document.category, "displayName": document.category}],
                "extractionSchemaRef": extraction_schema_ref,
            },
        )
        session.add(run)
        version.processing_status = "PROCESSING"
        document.status = "PROCESSING"
        await session.flush()
        await self._record_event(
            session,
            run=run,
            event_type="document.processing.started",
            stage="PENDING",
            actor=actor,
            payload={"profileRef": profile.ref, "attempt": run.attempt},
        )
        if profile.ref == "document-profile://business-structuring@1":
            event_id = uuid7()
            run.provenance = {
                **run.provenance,
                "executionMode": "TEMPORAL",
                "temporalWorkflowId": f"document-processing/{run.id}",
            }
            session.add(
                OutboxEvent(
                    id=event_id,
                    tenant_id=tenant_id,
                    aggregate_id=document.id,
                    destination="document-temporal",
                    partition_key=str(run.id),
                    source_id=run.id,
                    type="document.processing.requested",
                    payload={
                        "tenantId": str(tenant_id),
                        "projectId": str(project_id),
                        "documentId": str(document.id),
                        "documentVersionId": str(version.id),
                        "processingRunId": str(run.id),
                    },
                )
            )
            await self._audit.append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=actor,
                action="document.processing.requested",
                resource_type="document_processing_run",
                resource_id=str(run.id),
                metadata={"profileRef": profile.ref, "executionMode": "TEMPORAL"},
            )
            await self._record_event(
                session,
                run=run,
                event_type="document.processing.requested",
                stage="PENDING",
                actor=actor,
                payload={"temporalWorkflowId": run.provenance["temporalWorkflowId"]},
            )
            return run
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

    async def execute_pending_run(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        processing_run_id: UUID,
    ) -> DocumentProcessingRun:
        run = await self.get_run(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            processing_run_id=processing_run_id,
        )
        if run.status in {"READY", "REVIEW_REQUIRED", "FAILED", "CANCELLED"}:
            return run
        version = await session.scalar(
            select(BusinessDocumentVersion).where(
                BusinessDocumentVersion.id == run.business_document_version_id,
                BusinessDocumentVersion.tenant_id == tenant_id,
                BusinessDocumentVersion.project_id == project_id,
            )
        )
        if version is None:
            raise LookupError("DOCUMENT_VERSION_NOT_FOUND")
        document = await session.scalar(
            select(BusinessDocument).where(
                BusinessDocument.id == version.business_document_id,
                BusinessDocument.tenant_id == tenant_id,
                BusinessDocument.project_id == project_id,
            )
        )
        if document is None:
            raise LookupError("DOCUMENT_NOT_FOUND")
        labels = [
            dict(value)
            for value in run.provenance.get("candidateLabels") or []
            if isinstance(value, dict)
        ]
        await self._execute_run(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            document=document,
            version=version,
            run=run,
            profile_ref=run.profile_ref,
            candidate_labels=labels
            or [{"label": document.category, "displayName": document.category}],
            extraction_schema_ref=(
                str(run.provenance["extractionSchemaRef"])
                if run.provenance.get("extractionSchemaRef")
                else None
            ),
            actor=str(run.provenance.get("actor") or "system"),
            blob_content=None,
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
        idempotency_key: str,
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
        request_hash = canonical_hash(
            {
                "documentId": str(document_id),
                "documentVersionId": str(version.id),
                "profileRef": profile_ref,
                "candidateLabels": candidate_labels or [],
                "extractionSchemaRef": extraction_schema_ref,
            }
        )
        existing_key = await session.get(
            IdempotencyKey,
            {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "operation": "document.processing.reprocess",
                "key": idempotency_key,
            },
        )
        if existing_key is not None:
            if existing_key.request_hash != request_hash:
                raise DocumentProcessingError("IDEMPOTENCY_KEY_REUSED")
            existing_run = await session.get(
                DocumentProcessingRun, existing_key.response_ref
            )
            if (
                existing_run is None
                or existing_run.tenant_id != tenant_id
                or existing_run.project_id != project_id
            ):
                raise RuntimeError("document reprocess idempotency record is invalid")
            return existing_run
        run = await self.start_for_version(
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
        session.add(
            IdempotencyKey(
                tenant_id=tenant_id,
                project_id=project_id,
                operation="document.processing.reprocess",
                key=idempotency_key,
                request_hash=request_hash,
                response_ref=run.id,
                expires_at=datetime.now(UTC) + timedelta(days=30),
            )
        )
        await session.flush()
        return run

    async def cancel(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
        actor: str,
        idempotency_key: str,
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
        run = await session.scalar(
            select(DocumentProcessingRun)
            .where(
                DocumentProcessingRun.business_document_version_id == version.id,
                DocumentProcessingRun.tenant_id == tenant_id,
                DocumentProcessingRun.project_id == project_id,
            )
            .order_by(DocumentProcessingRun.attempt.desc())
            .limit(1)
            .with_for_update()
        )
        if run is None:
            raise LookupError("PROCESSING_RUN_NOT_FOUND")
        request_hash = canonical_hash(
            {"documentId": str(document.id), "processingRunId": str(run.id)}
        )
        existing_key = await session.get(
            IdempotencyKey,
            {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "operation": "document.processing.cancel",
                "key": idempotency_key,
            },
        )
        if existing_key is not None:
            if existing_key.request_hash != request_hash:
                raise DocumentProcessingError("IDEMPOTENCY_KEY_REUSED")
            return run
        if run.status in {"READY", "FAILED"}:
            raise DocumentProcessingError("PROCESSING_ALREADY_TERMINAL")
        now = datetime.now(UTC)
        run.status = "CANCELLED"
        run.current_stage = "CANCELLED"
        run.completed_at = now
        version.processing_status = "CANCELLED"
        document.status = "AVAILABLE"
        await self._record_event(
            session,
            run=run,
            event_type="document.processing.cancelled",
            stage="CANCELLED",
            actor=actor,
            payload={"documentId": str(document.id)},
        )
        event_id = uuid7()
        session.add_all(
            [
                IdempotencyKey(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    operation="document.processing.cancel",
                    key=idempotency_key,
                    request_hash=request_hash,
                    response_ref=run.id,
                    expires_at=now + timedelta(days=30),
                ),
                OutboxEvent(
                    id=event_id,
                    tenant_id=tenant_id,
                    aggregate_id=run.id,
                    destination="document-temporal",
                    partition_key=str(run.id),
                    source_id=event_id,
                    type="document.processing.cancel.requested",
                    payload={
                        "tenantId": str(tenant_id),
                        "projectId": str(project_id),
                        "processingRunId": str(run.id),
                    },
                ),
            ]
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="document.processing.cancelled",
            resource_type="document_processing_run",
            resource_id=str(run.id),
            metadata={"documentId": str(document.id)},
        )
        return run

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

    async def list_events(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version_id: UUID,
        after: int = 0,
        limit: int = 200,
    ) -> list[DocumentProcessingEvent]:
        run = await self.latest_run_for_version(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version_id=version_id,
        )
        if run is None:
            return []
        return list(
            (
                await session.scalars(
                    select(DocumentProcessingEvent)
                    .where(
                        DocumentProcessingEvent.processing_run_id == run.id,
                        DocumentProcessingEvent.tenant_id == tenant_id,
                        DocumentProcessingEvent.project_id == project_id,
                        DocumentProcessingEvent.event_seq > after,
                    )
                    .order_by(DocumentProcessingEvent.event_seq)
                    .limit(min(500, max(1, limit)))
                )
            ).all()
        )

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
        await self._record_event(
            session,
            run=run,
            event_type="document.scan.completed",
            stage="SCANNING",
            actor=actor,
            payload={"scanStatus": blob.scan_status, "sizeBytes": len(content)},
            input_hash=version.sha256,
            tool_ref="tool://document/security-scan@1",
        )
        maximum_bytes = int(
            profile.parser_policy.get("maxFileBytes", 200 * 1024 * 1024)
        )
        if len(content) > maximum_bytes:
            raise DocumentProcessingError(
                "DOCUMENT_SIZE_LIMIT_EXCEEDED",
                f"size={len(content)};limit={maximum_bytes}",
            )
        detected = _detect_media_type(content, version.filename, version.media_type)
        await self._record_event(
            session,
            run=run,
            event_type="document.type.detected",
            stage="SCANNING",
            actor=actor,
            payload={
                "declaredMediaType": version.media_type,
                "detectedMediaType": detected,
                "mismatch": detected != version.media_type,
            },
            input_hash=version.sha256,
            tool_ref="tool://document/detect-type@1",
        )
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
            media_type=detected,
            content=content,
        )
        run.parser_ref = parser_ref
        await self._record_event(
            session,
            run=run,
            event_type="document.parse.completed",
            stage="PARSING",
            actor=actor,
            payload={
                "parserRef": parser_ref,
                "pageCount": len(parsed.pages),
                "tableCount": len(parsed.tables),
                "sheetCount": len(parsed.sheets),
            },
            input_hash=version.sha256,
            output_hash=canonical_hash(
                {
                    "pages": len(parsed.pages),
                    "tables": len(parsed.tables),
                    "sheets": len(parsed.sheets),
                    "textExcerpt": parsed.text_excerpt,
                }
            ),
            tool_ref="tool://document/parse-native@2",
        )
        warnings.extend(parsed.warnings)
        page_count = max(
            len(parsed.pages),
            int(parsed.embedded_metadata.get("pageCount") or 0),
        )
        maximum_pages = int(profile.parser_policy.get("maxPageCount", 500))
        if page_count > maximum_pages:
            raise DocumentProcessingError(
                "DOCUMENT_PAGE_LIMIT_EXCEEDED",
                f"pages={page_count};limit={maximum_pages}",
            )
        page_batch_size = max(
            1, int(profile.parser_policy.get("pageBatchSize", 10))
        )
        page_batches = [
            list(range(start, min(page_count + 1, start + page_batch_size)))
            for start in range(1, page_count + 1, page_batch_size)
        ]
        selected_ocr_pages = {
            int(value)
            for value in parsed.layout.get("ocrPages") or []
            if isinstance(value, int | str) and str(value).isdigit()
        }
        ocr_page_batches = [
            [page for page in batch if page in selected_ocr_pages]
            for batch in page_batches
        ]
        ocr_page_batches = [batch for batch in ocr_page_batches if batch]
        large_document = (
            page_count
            >= int(profile.parser_policy.get("largeFilePageThreshold", 50))
            or len(content)
            >= int(
                profile.parser_policy.get(
                    "largeFileByteThreshold", 25 * 1024 * 1024
                )
            )
            or int(parsed.embedded_metadata.get("rowCount") or 0)
            >= int(
                profile.parser_policy.get(
                    "largeSpreadsheetRowThreshold", 100_000
                )
            )
        )
        parsed = parsed.model_copy(
            update={
                "layout": {
                    **parsed.layout,
                    "detectedMediaType": detected,
                    "largeDocument": large_document,
                    "pageBatchSize": page_batch_size,
                    "pageBatches": page_batches,
                }
            }
        )
        if large_document:
            warnings.append("LARGE_DOCUMENT_SEGMENTED")

        if parsed.needs_ocr:
            run.status = "OCR_PROCESSING"
            run.current_stage = "OCR_PROCESSING"
            await session.flush()
            if not self._ocr.available:
                quality_flags.append("OCR_NOT_CONFIGURED")
                warnings.append("当前环境未配置 OCR")
                parsed = parsed.model_copy(
                    update={"chunks": self._chunker.chunk(parsed)}
                )
                compact, content_ref = await self._prepare_persisted_content(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    version=version,
                    parsed=parsed,
                )
                envelope = ProcessingResultEnvelope(
                    status="REVIEW_REQUIRED",
                    documentType=None,
                    content=compact,
                    extractions=[],
                    evidence=[],
                    artifacts=(
                        [
                            {
                                "kind": "STRUCTURED_CONTENT",
                                "artifactRef": content_ref,
                            }
                        ]
                        if content_ref
                        else []
                    ),
                    qualityFlags=quality_flags,
                    warnings=warnings,
                    provenance={
                        "processingRunId": str(run.id),
                        "profileRef": profile.ref,
                        "parserRef": parser_ref,
                        "ocr": {"available": False, "provider": self._ocr.name},
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
                    status="REVIEW_REQUIRED",
                )
                return
            ocr_result = self._ocr_document(
                media_type=detected,
                content=content,
                page_batches=ocr_page_batches or page_batches,
            )
            ocr_text = str(ocr_result.get("text") or "")
            ocr_pages = [
                dict(item)
                for item in ocr_result.get("pages") or []
                if isinstance(item, dict)
            ]
            ocr_paragraphs = [
                {
                    "index": index,
                    "text": str(page.get("text") or ""),
                    "page": page.get("page", index),
                    "sourceKind": "OCR",
                    "bbox": page.get("bbox"),
                }
                for index, page in enumerate(ocr_pages, start=1)
                if str(page.get("text") or "").strip()
            ]
            ocr_tables = [
                self._normalized_ocr_table(item, index)
                for index, item in enumerate(
                    (
                        table
                        for table in ocr_result.get("tables") or []
                        if isinstance(table, dict)
                    ),
                    start=1,
                )
            ]
            blocks = [
                {**dict(item), "sourceKind": "OCR"}
                for item in ocr_result.get("blocks") or []
                if isinstance(item, dict)
            ]
            merged_pages = {
                int(page.get("page") or index): dict(page)
                for index, page in enumerate(parsed.pages, start=1)
            }
            for page in ocr_pages:
                page_number = int(page.get("page") or 0)
                if page_number > 0:
                    merged_pages[page_number] = {
                        **page,
                        "page": page_number,
                        "sourceKind": "OCR",
                        "routeReason": "NATIVE_TEXT_INSUFFICIENT",
                    }
            native_paragraphs = [
                dict(item)
                for item in parsed.paragraphs
                if int(item.get("page") or 0) not in selected_ocr_pages
            ]
            merged_text = "\n\n".join(
                str(page.get("text") or "")
                for _, page in sorted(merged_pages.items())
            ).strip()
            parsed = parsed.model_copy(
                update={
                    "pages": [
                        page for _, page in sorted(merged_pages.items())
                    ],
                    "paragraphs": [*native_paragraphs, *ocr_paragraphs],
                    "tables": [*parsed.tables, *ocr_tables],
                    "layout": {
                        **parsed.layout,
                        "blocks": blocks,
                        "ocrProvider": f"ocr://{self._ocr.name}@{self._ocr.version}",
                        "ocrPageBatches": ocr_page_batches or page_batches,
                    },
                    "text_excerpt": (merged_text or ocr_text)[:4000],
                    "needs_ocr": False,
                    "warnings": [*parsed.warnings, "OCR_APPLIED"],
                }
            )
            await self._record_event(
                session,
                run=run,
                event_type="document.ocr.completed",
                stage="OCR_PROCESSING",
                actor=actor,
                payload={
                    "provider": self._ocr.name,
                    "version": self._ocr.version,
                    "pageBatches": ocr_page_batches or page_batches,
                    "blockCount": len(blocks),
                    "tableCount": len(ocr_tables),
                },
                input_hash=version.sha256,
                output_hash=canonical_hash(ocr_result),
                tool_ref="tool://document/ocr-layout@1",
            )

        chunks = self._chunker.chunk(parsed)
        parsed = parsed.model_copy(update={"chunks": chunks})

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
        await self._record_event(
            session,
            run=run,
            event_type="document.classification.completed",
            stage="CLASSIFYING",
            actor=actor,
            payload={
                "classifierRef": self._classifier.ref,
                "label": classification.label,
                "confidence": classification.confidence,
            },
            output_hash=canonical_hash(
                classification.model_dump(mode="json", by_alias=True)
            ),
        )
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
        await self._record_event(
            session,
            run=run,
            event_type="document.extraction.completed",
            stage="EXTRACTING",
            actor=actor,
            payload={
                "extractorRefs": extractor_refs,
                "fieldCount": len(extracted),
            },
            output_hash=canonical_hash(
                [
                    value.model_dump(mode="json", by_alias=True)
                    for value in extracted
                ]
            ),
        )

        run.status = "QUALITY_CHECK"
        run.current_stage = "QUALITY_CHECK"
        await session.flush()
        quality = self._quality.check(
            content=parsed,
            classification=classification,
            extractions=extracted,
            classification_threshold=classification_threshold,
            extraction_threshold=float(
                profile.quality_thresholds.get("extraction", 0.85)
            ),
            critical_extraction_threshold=float(
                profile.quality_thresholds.get("criticalExtraction", 0.95)
            ),
            ocr_threshold=float(profile.quality_thresholds.get("ocr", 0.90)),
        )
        for flag in quality["flags"]:
            if flag not in quality_flags:
                quality_flags.append(flag)
        for field in extracted:
            for flag in field.quality_flags:
                if flag not in quality_flags:
                    quality_flags.append(flag)
        await self._record_event(
            session,
            run=run,
            event_type="document.quality.checked",
            stage="QUALITY_CHECK",
            actor=actor,
            payload={
                "qualityRef": self._quality.ref,
                "passed": quality["passed"],
                "flags": quality["flags"],
            },
            output_hash=canonical_hash(quality),
            tool_ref="tool://document/quality-check@1",
        )

        compact, content_ref = await self._prepare_persisted_content(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version=version,
            parsed=parsed,
        )

        needs_field_review = any(
            field.review_status in {"PENDING", "UNCONFIRMED"} for field in extracted
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
            evidence=[
                *classification.evidence,
                *[
                    evidence
                    for field in extracted
                    for evidence in field.evidence_refs
                ],
            ],
            organization={
                "suggestedName": self._suggested_document_name(
                    version.filename, classification, extracted
                ),
                "category": classification.confirmed_label or classification.label,
                "tags": self._suggested_tags(classification, extracted),
            },
            quality=quality,
            artifacts=(
                [
                    {
                        "kind": "STRUCTURED_CONTENT",
                        "artifactRef": content_ref,
                    }
                ]
                if content_ref
                else []
            ),
            qualityFlags=quality_flags,
            warnings=warnings,
            provenance={
                "processingRunId": str(run.id),
                "profileRef": profile.ref,
                "parserRef": parser_ref,
                "detectedMediaType": detected,
                "classifierRef": self._classifier.ref,
                "extractorRefs": extractor_refs,
                "chunkerRef": self._chunker.ref,
                "qualityRef": self._quality.ref,
                "processingPlan": {
                    "largeDocument": large_document,
                    "pageBatchSize": page_batch_size,
                    "pageBatches": page_batches,
                },
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

    def _ocr_document(
        self,
        *,
        media_type: str,
        content: bytes,
        page_batches: list[list[int]],
    ) -> dict[str, Any]:
        batches = page_batches or [[]]
        combined_pages: list[dict[str, Any]] = []
        combined_tables: list[dict[str, Any]] = []
        combined_blocks: list[dict[str, Any]] = []
        for batch in batches:
            value = self._ocr.recognize(
                media_type=media_type,
                content=content,
                pages=batch or None,
            )
            combined_pages.extend(
                dict(item)
                for item in value.get("pages") or []
                if isinstance(item, dict)
            )
            combined_tables.extend(
                dict(item)
                for item in value.get("tables") or []
                if isinstance(item, dict)
            )
            combined_blocks.extend(
                dict(item)
                for item in value.get("blocks") or []
                if isinstance(item, dict)
            )
        combined_pages.sort(key=lambda item: int(item.get("page") or 0))
        unique_pages = {
            int(item.get("page") or index): item
            for index, item in enumerate(combined_pages, start=1)
        }
        combined_pages = [
            value for _, value in sorted(unique_pages.items())
        ]
        return {
            "text": "\n\n".join(
                str(item.get("text") or "") for item in combined_pages
            ).strip(),
            "pages": combined_pages,
            "tables": combined_tables,
            "blocks": combined_blocks,
        }

    def _normalized_ocr_table(
        self, table: dict[str, Any], ordinal: int
    ) -> dict[str, Any]:
        rows = [
            [str(value) for value in row]
            for row in table.get("rows") or table.get("cells") or []
            if isinstance(row, list)
        ]
        width = max((len(row) for row in rows), default=0)
        normalized = [row + [""] * (width - len(row)) for row in rows]
        return {
            **table,
            "tableId": str(table.get("tableId") or f"ocr-table-{ordinal}"),
            "name": str(table.get("name") or f"OCR Table {ordinal}"),
            "columns": normalized[0] if normalized else [],
            "rows": normalized,
            "rowCount": len(normalized),
            "columnCount": width,
            "sourceKind": "OCR",
            "evidenceRefs": list(table.get("evidenceRefs") or []),
        }

    def _suggested_document_name(
        self,
        filename: str,
        classification: Any,
        extracted: list[Any],
    ) -> str:
        title = next(
            (
                str(field.machine_value).strip()
                for field in extracted
                if field.field_path == "document.title" and field.machine_value
            ),
            "",
        )
        if title:
            return title[:200]
        label = str(classification.display_name or classification.label).strip()
        return f"{label}-{filename}"[:200] if label else filename[:200]

    def _suggested_tags(
        self, classification: Any, extracted: list[Any]
    ) -> list[str]:
        tags = [str(classification.label)]
        if any(field.review_status == "PENDING" for field in extracted):
            tags.append("REVIEW_REQUIRED")
        return list(dict.fromkeys(tag for tag in tags if tag))

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
        await self._record_event(
            session,
            run=run,
            event_type="document.result.published",
            stage=status,
            actor=actor,
            payload={
                "resultId": str(result.id),
                "resultVersion": result.result_version,
                "status": status,
            },
            output_hash=canonical_hash(result.result),
            tool_ref="tool://document/result-persist@1",
        )
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
        await self._record_event(
            session,
            run=run,
            event_type="document.processing.failed",
            stage="FAILED",
            actor=actor,
            payload={"errorCode": code, "detail": detail[:500]},
        )

    async def _record_event(
        self,
        session: AsyncSession,
        *,
        run: DocumentProcessingRun,
        event_type: str,
        stage: str,
        actor: str,
        payload: dict[str, Any],
        input_hash: str | None = None,
        output_hash: str | None = None,
        tool_ref: str | None = None,
    ) -> DocumentProcessingEvent:
        event = DocumentProcessingEvent(
            tenant_id=run.tenant_id,
            project_id=run.project_id,
            processing_run_id=run.id,
            business_document_version_id=run.business_document_version_id,
            event_seq=int(run.next_event_seq or 1),
            type=event_type,
            stage=stage,
            payload=_sanitize_jsonable(payload),
            input_hash=input_hash,
            output_hash=output_hash,
            tool_ref=tool_ref,
            actor_id=actor,
        )
        run.next_event_seq = int(run.next_event_seq or 1) + 1
        session.add(event)
        await session.flush()
        return event

    def _read_blob_bytes(self, blob: BlobObject) -> bytes:
        root = self._storage_root
        path = root / blob.object_key
        if not path.is_file():
            raise DocumentProcessingError("BLOB_CONTENT_UNAVAILABLE", str(path))
        return path.read_bytes()

    async def _prepare_persisted_content(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version: BusinessDocumentVersion,
        parsed: Any,
    ) -> tuple[Any, str | None]:
        if not _content_too_large(parsed):
            return parsed, None
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
                "tables": [
                    {
                        **table,
                        "rows": list(table.get("rows") or [])[:20],
                    }
                    for table in parsed.tables[:10]
                ],
                "chunks": [
                    {
                        **chunk,
                        "text": str(chunk.get("text") or "")[:500],
                    }
                    for chunk in parsed.chunks[:10]
                ],
            }
        )
        return compact, content_ref

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

    async def publish(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
        actor: str,
        idempotency_key: str,
    ) -> DocumentProcessingResult:
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
        latest = await self._processing.latest_result(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version_id=version.id,
            result_type="STRUCTURED_PACKAGE",
        )
        if latest is None:
            raise LookupError("STRUCTURED_PACKAGE_NOT_FOUND")
        request_hash = canonical_hash(
            {
                "documentId": str(document_id),
                "resultId": str(latest.id),
                "resultVersion": latest.result_version,
            }
        )
        existing_key = await session.get(
            IdempotencyKey,
            {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "operation": "document.structured.publish",
                "key": idempotency_key,
            },
        )
        if existing_key is not None:
            if existing_key.request_hash != request_hash:
                raise DocumentProcessingError("IDEMPOTENCY_KEY_REUSED")
            existing_result = await session.get(
                DocumentProcessingResult, existing_key.response_ref
            )
            if existing_result is None:
                raise RuntimeError("document publish idempotency record is invalid")
            return existing_result
        if latest.status not in {"READY", "CONFIRMED"}:
            raise DocumentProcessingError("STRUCTURED_PACKAGE_REVIEW_REQUIRED")
        now = datetime.now(UTC)
        payload = {
            **dict(latest.result),
            "publication": {
                "publishedAt": now.isoformat(),
                "publishedBy": actor,
                "sourceResultId": str(latest.id),
                "sourceResultVersion": latest.result_version,
            },
        }
        published = DocumentProcessingResult(
            tenant_id=tenant_id,
            project_id=project_id,
            business_document_version_id=version.id,
            result_type="STRUCTURED_PACKAGE",
            result_version=latest.result_version + 1,
            status="READY",
            schema_ref=latest.schema_ref,
            producer_ref=latest.producer_ref,
            result=payload,
            evidence=list(latest.evidence or []),
            confirmed_by=actor,
            confirmed_at=now,
        )
        session.add(published)
        await session.flush()
        document.status = "AVAILABLE"
        version.processing_status = "READY"
        session.add(
            IdempotencyKey(
                tenant_id=tenant_id,
                project_id=project_id,
                operation="document.structured.publish",
                key=idempotency_key,
                request_hash=request_hash,
                response_ref=published.id,
                expires_at=now + timedelta(days=30),
            )
        )
        event_id = uuid7()
        session.add(
            OutboxEvent(
                id=event_id,
                tenant_id=tenant_id,
                aggregate_id=document.id,
                destination="nats",
                partition_key=str(document.id),
                source_id=event_id,
                type="document.result.published",
                payload={
                    "documentId": str(document.id),
                    "documentVersionId": str(version.id),
                    "resultId": str(published.id),
                    "resultVersion": published.result_version,
                },
            )
        )
        run = await self._processing.latest_run_for_version(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version_id=version.id,
        )
        if run is not None:
            await self._processing._record_event(
                session,
                run=run,
                event_type="document.result.published",
                stage="READY",
                actor=actor,
                payload={
                    "resultId": str(published.id),
                    "resultVersion": published.result_version,
                },
                input_hash=canonical_hash(latest.result),
                output_hash=canonical_hash(payload),
                tool_ref="tool://document/publish@1",
            )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="document.result.published",
            resource_type="document_processing_result",
            resource_id=str(published.id),
            metadata={
                "documentId": str(document.id),
                "resultVersion": published.result_version,
            },
        )
        return published

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
        run = await self._processing.latest_run_for_version(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version_id=version.id,
        )
        if run is not None:
            await self._processing._record_event(
                session,
                run=run,
                event_type="document.review.decided",
                stage=status,
                actor=actor,
                payload={
                    "action": action,
                    "resultId": str(result.id),
                    "resultVersion": result.result_version,
                    "status": status,
                },
                input_hash=canonical_hash(previous.result),
                output_hash=canonical_hash(payload),
                tool_ref="tool://document/review@1",
            )
        event_id = uuid7()
        session.add(
            OutboxEvent(
                id=event_id,
                tenant_id=tenant_id,
                aggregate_id=document.id,
                destination="nats",
                partition_key=str(document.id),
                source_id=event_id,
                type="document.review.decided",
                payload={
                    "documentId": str(document.id),
                    "documentVersionId": str(version.id),
                    "resultId": str(result.id),
                    "resultVersion": result.result_version,
                    "status": status,
                },
            )
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
    if content.startswith(b"PK"):
        try:
            import io
            import zipfile

            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = set(archive.namelist())
                if "mimetype" in names:
                    package_type = (
                        archive.read("mimetype")
                        .decode("ascii", errors="replace")
                        .strip()
                    )
                    if package_type.startswith(
                        "application/vnd.oasis.opendocument."
                    ):
                        return package_type
                if "word/document.xml" in names:
                    return (
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    )
                if "xl/workbook.xml" in names or any(
                    name.startswith("xl/worksheets/") for name in names
                ):
                    return (
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    )
                if "ppt/presentation.xml" in names or any(
                    name.startswith("ppt/slides/") for name in names
                ):
                    return (
                        "application/vnd.openxmlformats-officedocument."
                        "presentationml.presentation"
                    )
        except (OSError, zipfile.BadZipFile):
            pass
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:2] == b"\xff\xd8":
        return "image/jpeg"
    if content[:4] in {b"II*\x00", b"MM\x00*"}:
        return "image/tiff"
    if lower.endswith(".md"):
        return "text/markdown"
    if lower.endswith(".txt"):
        return "text/plain"
    if lower.endswith(".csv"):
        return "text/csv"
    if lower.endswith(".json"):
        return "application/json"
    return declared


def _compatible_media(detected: str, declared: str) -> bool:
    if declared in {"", "application/octet-stream", "binary/octet-stream"}:
        return True
    aliases = {
        "image/jpg": "image/jpeg",
        "text/x-markdown": "text/markdown",
    }
    return aliases.get(detected, detected) == aliases.get(declared, declared)


def _content_too_large(parsed: Any) -> bool:
    size = len(
        json.dumps(
            parsed.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
        ).encode("utf-8")
    )
    return size > 256 * 1024
