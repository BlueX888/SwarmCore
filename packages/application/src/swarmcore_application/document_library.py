from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import uuid7
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import (
    BlobObject,
    BusinessDocument,
    BusinessDocumentVersion,
    BusinessObject,
    BusinessObjectVersion,
    DocumentBusinessObjectLink,
    DocumentProcessingResult,
    DocumentUsageSnapshot,
    DocumentWorkBinding,
    Evaluation,
    IdempotencyKey,
    OutboxEvent,
)
from swarmcore_persistence.repositories import canonical_hash

from .document_processing import DocumentProcessingService


class DocumentLibraryService:
    """Project-scoped document metadata backed by the existing BlobObject gateway."""

    def __init__(
        self,
        *,
        processing: DocumentProcessingService | None = None,
    ) -> None:
        self._audit = AuditRepository()
        self._processing = processing or DocumentProcessingService()

    async def initiate(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        name: str,
        category: str,
        tags: list[str],
        filename: str,
        media_type: str,
        size_bytes: int,
        sha256: str,
        business_object_ids: list[UUID],
        business_work_keys: list[str],
        retention_days: int,
        idempotency_key: str,
        actor: str,
        document_id: UUID | None = None,
    ) -> tuple[BusinessDocument, BlobObject, UUID, int]:
        self._validate_file(filename, size_bytes, sha256)
        normalized_tags = sorted({value.strip() for value in tags if value.strip()})
        normalized_work_keys = sorted(
            {value.strip() for value in business_work_keys if value.strip()}
        )
        request_hash = canonical_hash(
            {
                "documentId": str(document_id) if document_id else None,
                "name": name.strip(),
                "category": category.strip(),
                "tags": normalized_tags,
                "filename": filename,
                "mediaType": media_type,
                "sizeBytes": size_bytes,
                "sha256": sha256.lower(),
                "businessObjectIds": sorted(str(value) for value in business_object_ids),
                "businessWorkKeys": normalized_work_keys,
                "retentionDays": retention_days,
            }
        )
        operation = "document.initiate"
        existing_ref = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing_ref is not None:
            blob = await session.get(BlobObject, existing_ref)
            if blob is None:
                raise RuntimeError("document idempotency record is invalid")
            existing_document = await self.get(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                document_id=UUID(str(blob.metadata_json["documentId"])),
            )
            return (
                existing_document,
                blob,
                UUID(str(blob.metadata_json["documentUploadId"])),
                int(blob.metadata_json["documentVersion"]),
            )

        if document_id is None:
            document = BusinessDocument(
                tenant_id=tenant_id,
                project_id=project_id,
                name=name.strip(),
                category=category.strip(),
                tags=normalized_tags,
                status="UPLOADING",
                current_version=0,
                created_by=actor,
            )
            session.add(document)
            await session.flush()
        else:
            document = await self.get(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                document_id=document_id,
                for_update=True,
            )
            document.name = name.strip()
            document.category = category.strip()
            document.tags = normalized_tags
            document.status = "UPLOADING"

        await self._replace_links(
            session,
            document=document,
            business_object_ids=business_object_ids,
            business_work_keys=normalized_work_keys,
            actor=actor,
        )
        upload_id = uuid7()
        blob_id = uuid7()
        next_version = document.current_version + 1
        blob = BlobObject(
            id=blob_id,
            tenant_id=tenant_id,
            project_id=project_id,
            object_key=f"{tenant_id}/{project_id}/document/{document.id}/v{next_version}/{blob_id}",
            version=next_version,
            filename=filename,
            media_type=media_type,
            size_bytes=size_bytes,
            sha256=sha256.lower(),
            status="PENDING",
            scan_status="PENDING",
            retention_until=datetime.now(UTC) + timedelta(days=retention_days),
            metadata_json={
                "documentId": str(document.id),
                "documentUploadId": str(upload_id),
                "documentVersion": next_version,
                "category": document.category,
            },
        )
        session.add(blob)
        await session.flush()
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=blob.id,
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="document.upload-initiated",
            resource_type="business_document",
            resource_id=str(document.id),
            metadata={"version": next_version, "filename": filename},
        )
        return document, blob, upload_id, next_version

    async def complete(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        upload_id: UUID,
        sha256: str,
        idempotency_key: str,
        actor: str,
        profile_ref: str | None = None,
        candidate_labels: list[dict[str, str]] | None = None,
        extraction_schema_ref: str | None = None,
        upload_batch_id: UUID | None = None,
        blob_content: bytes | None = None,
        start_processing: bool = True,
    ) -> tuple[BusinessDocument, BusinessDocumentVersion]:
        blob = await session.scalar(
            select(BlobObject)
            .where(
                BlobObject.tenant_id == tenant_id,
                BlobObject.project_id == project_id,
                BlobObject.metadata_json["documentUploadId"].astext == str(upload_id),
            )
            .with_for_update()
        )
        if blob is None:
            raise LookupError("DOCUMENT_UPLOAD_NOT_FOUND")
        if blob.status != "AVAILABLE" or blob.scan_status != "CLEAN":
            raise ValueError("DOCUMENT_UPLOAD_NOT_READY")
        if blob.sha256 != sha256.lower():
            raise ValueError("DOCUMENT_HASH_MISMATCH")
        operation = f"document.complete:{upload_id}"
        request_hash = canonical_hash({"uploadId": str(upload_id), "sha256": sha256.lower()})
        existing_ref = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing_ref is not None:
            version = await session.get(BusinessDocumentVersion, existing_ref)
            if version is None:
                raise RuntimeError("document completion idempotency record is invalid")
            document = await self.get(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                document_id=version.business_document_id,
            )
            return document, version

        document = await self.get(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            document_id=UUID(str(blob.metadata_json["documentId"])),
            for_update=True,
        )
        version_number = int(blob.metadata_json["documentVersion"])
        if version_number != document.current_version + 1:
            raise ValueError("DOCUMENT_VERSION_CONFLICT")
        version = BusinessDocumentVersion(
            tenant_id=tenant_id,
            project_id=project_id,
            business_document_id=document.id,
            blob_id=blob.id,
            version=version_number,
            filename=blob.filename,
            media_type=blob.media_type,
            size_bytes=blob.size_bytes,
            sha256=blob.sha256,
            processing_status="PROCESSING" if start_processing else "AVAILABLE",
            created_by=actor,
        )
        session.add(version)
        document.current_version = version_number
        document.status = "PROCESSING" if start_processing else "AVAILABLE"
        await session.flush()
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=version.id,
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
                type="document.available",
                payload={
                    "documentId": str(document.id),
                    "documentVersionId": str(version.id),
                    "version": version.version,
                    "sha256": version.sha256,
                },
            )
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="document.available",
            resource_type="business_document",
            resource_id=str(document.id),
            metadata={
                "documentVersionId": str(version.id),
                "version": version.version,
                "sha256": version.sha256,
                "sizeBytes": version.size_bytes,
            },
        )
        if start_processing:
            labels = candidate_labels
            if not labels:
                labels = [{"label": document.category, "displayName": document.category}]
            await self._processing.start_for_version(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                version=version,
                document=document,
                profile_ref=profile_ref,
                candidate_labels=labels,
                extraction_schema_ref=extraction_schema_ref,
                upload_batch_id=upload_batch_id,
                actor=actor,
                blob_content=blob_content,
            )
        return document, version

    async def resume_pending_upload(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
        idempotency_key: str,
        actor: str,
        profile_ref: str | None = None,
        candidate_labels: list[dict[str, str]] | None = None,
        extraction_schema_ref: str | None = None,
        blob_content: bytes | None = None,
    ) -> tuple[BusinessDocument, BusinessDocumentVersion]:
        """Complete an UPLOADING document whose blob is already AVAILABLE."""
        document = await self.get(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            document_id=document_id,
            for_update=True,
        )
        if document.status != "UPLOADING":
            raise ValueError("DOCUMENT_NOT_PENDING_UPLOAD")
        blob = await session.scalar(
            select(BlobObject)
            .where(
                BlobObject.tenant_id == tenant_id,
                BlobObject.project_id == project_id,
                BlobObject.metadata_json["documentId"].astext == str(document.id),
                BlobObject.status == "AVAILABLE",
                BlobObject.scan_status == "CLEAN",
            )
            .order_by(BlobObject.created_at.desc())
            .limit(1)
            .with_for_update()
        )
        if blob is None:
            raise ValueError("DOCUMENT_UPLOAD_NOT_READY")
        upload_id = UUID(str(blob.metadata_json["documentUploadId"]))
        return await self.complete(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            upload_id=upload_id,
            sha256=blob.sha256,
            idempotency_key=idempotency_key,
            actor=actor,
            profile_ref=profile_ref,
            candidate_labels=candidate_labels,
            extraction_schema_ref=extraction_schema_ref,
            blob_content=blob_content,
        )

    async def list_documents(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        search: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[tuple[BusinessDocument, BusinessDocumentVersion | None]]:
        query = (
            select(BusinessDocument, BusinessDocumentVersion)
            .outerjoin(
                BusinessDocumentVersion,
                (BusinessDocumentVersion.business_document_id == BusinessDocument.id)
                & (BusinessDocumentVersion.version == BusinessDocument.current_version),
            )
            .where(
                BusinessDocument.tenant_id == tenant_id,
                BusinessDocument.project_id == project_id,
            )
        )
        if search and search.strip():
            needle = f"%{search.strip()}%"
            query = query.where(
                or_(
                    BusinessDocument.name.ilike(needle),
                    BusinessDocument.category.ilike(needle),
                )
            )
        if category:
            query = query.where(BusinessDocument.category == category)
        if status:
            query = query.where(BusinessDocument.status == status)
        rows = await session.execute(
            query.order_by(BusinessDocument.updated_at.desc(), BusinessDocument.id)
        )
        return list(rows.tuples())

    async def get(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
        for_update: bool = False,
    ) -> BusinessDocument:
        query = select(BusinessDocument).where(
            BusinessDocument.id == document_id,
            BusinessDocument.tenant_id == tenant_id,
            BusinessDocument.project_id == project_id,
        )
        if for_update:
            query = query.with_for_update()
        document = await session.scalar(query)
        if document is None:
            raise LookupError("DOCUMENT_NOT_FOUND")
        return document

    async def details(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
    ) -> tuple[
        BusinessDocument,
        list[BusinessDocumentVersion],
        list[DocumentBusinessObjectLink],
        list[DocumentWorkBinding],
    ]:
        document = await self.get(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            document_id=document_id,
        )
        versions = list(
            await session.scalars(
                select(BusinessDocumentVersion)
                .where(
                    BusinessDocumentVersion.business_document_id == document.id,
                    BusinessDocumentVersion.tenant_id == tenant_id,
                    BusinessDocumentVersion.project_id == project_id,
                )
                .order_by(BusinessDocumentVersion.version.desc())
            )
        )
        object_links = list(
            await session.scalars(
                select(DocumentBusinessObjectLink).where(
                    DocumentBusinessObjectLink.business_document_id == document.id,
                    DocumentBusinessObjectLink.tenant_id == tenant_id,
                    DocumentBusinessObjectLink.project_id == project_id,
                )
            )
        )
        work_bindings = list(
            await session.scalars(
                select(DocumentWorkBinding).where(
                    DocumentWorkBinding.business_document_id == document.id,
                    DocumentWorkBinding.tenant_id == tenant_id,
                    DocumentWorkBinding.project_id == project_id,
                )
            )
        )
        return document, versions, object_links, work_bindings

    async def current_versions_for_work(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        business_work_keys: tuple[str, ...],
        business_object_ids: tuple[UUID, ...] = (),
    ) -> list[tuple[BusinessDocument, BusinessDocumentVersion, BlobObject]]:
        query = (
            select(BusinessDocument, BusinessDocumentVersion, BlobObject)
            .join(
                DocumentWorkBinding,
                DocumentWorkBinding.business_document_id == BusinessDocument.id,
            )
            .join(
                BusinessDocumentVersion,
                (BusinessDocumentVersion.business_document_id == BusinessDocument.id)
                & (BusinessDocumentVersion.version == BusinessDocument.current_version),
            )
            .join(BlobObject, BlobObject.id == BusinessDocumentVersion.blob_id)
            .where(
                BusinessDocument.tenant_id == tenant_id,
                BusinessDocument.project_id == project_id,
                BusinessDocument.status.in_(("AVAILABLE", "REVIEW_REQUIRED")),
                DocumentWorkBinding.business_work_key.in_(business_work_keys),
                BlobObject.status == "AVAILABLE",
                BlobObject.scan_status == "CLEAN",
                BlobObject.retention_until > datetime.now(UTC),
            )
        )
        if business_object_ids:
            query = query.join(
                DocumentBusinessObjectLink,
                DocumentBusinessObjectLink.business_document_id == BusinessDocument.id,
            ).where(DocumentBusinessObjectLink.business_object_id.in_(business_object_ids))
        rows = await session.execute(query.distinct().order_by(BusinessDocument.id))
        return list(rows.tuples())

    async def freeze_usage(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        evaluation: Evaluation,
        business_work_key: str,
        documents: list[tuple[BusinessDocument, BusinessDocumentVersion, BlobObject]],
    ) -> list[DocumentUsageSnapshot]:
        frozen: list[DocumentUsageSnapshot] = []
        for document, version, blob in documents:
            existing = await session.scalar(
                select(DocumentUsageSnapshot).where(
                    DocumentUsageSnapshot.evaluation_id == evaluation.id,
                    DocumentUsageSnapshot.business_document_version_id == version.id,
                    DocumentUsageSnapshot.business_work_key == business_work_key,
                )
            )
            if existing is not None:
                frozen.append(existing)
                continue
            processing = await session.scalar(
                select(DocumentProcessingResult)
                .where(
                    DocumentProcessingResult.business_document_version_id == version.id,
                    DocumentProcessingResult.tenant_id == tenant_id,
                    DocumentProcessingResult.project_id == project_id,
                    DocumentProcessingResult.result_type == "PROCESSING",
                )
                .order_by(DocumentProcessingResult.result_version.desc())
                .limit(1)
            )
            evidence = [
                {
                    "documentVersionId": str(version.id),
                    "blobId": str(blob.id),
                    "sha256": version.sha256,
                    "mediaType": version.media_type,
                    "sizeBytes": version.size_bytes,
                    "processingStatus": version.processing_status,
                }
            ]
            if processing is not None:
                result_payload = processing.result if isinstance(processing.result, dict) else {}
                document_type = result_payload.get("documentType") or {}
                evidence.append(
                    {
                        "processingResultId": str(processing.id),
                        "processingResultVersion": processing.result_version,
                        "schemaRef": processing.schema_ref,
                        "producerRef": processing.producer_ref,
                        "classification": {
                            "label": document_type.get("label"),
                            "confirmedLabel": document_type.get("confirmedLabel"),
                            "confidence": document_type.get("confidence"),
                        },
                        "provenance": result_payload.get("provenance") or {},
                        "confirmedBy": processing.confirmed_by,
                        "confirmedAt": (
                            processing.confirmed_at.isoformat()
                            if processing.confirmed_at
                            else None
                        ),
                    }
                )
            snapshot = DocumentUsageSnapshot(
                tenant_id=tenant_id,
                project_id=project_id,
                evaluation_id=evaluation.id,
                run_id=evaluation.run_id,
                business_work_key=business_work_key,
                business_document_id=document.id,
                business_document_version_id=version.id,
                blob_id=blob.id,
                document_version=version.version,
                sha256=version.sha256,
                size_bytes=version.size_bytes,
                media_type=version.media_type,
                evidence=evidence,
            )
            session.add(snapshot)
            frozen.append(snapshot)
        await session.flush()
        return frozen

    async def update_bindings(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_id: UUID,
        business_object_ids: list[UUID],
        business_work_keys: list[str],
        actor: str,
    ) -> BusinessDocument:
        document = await self.get(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            document_id=document_id,
            for_update=True,
        )
        await self._replace_links(
            session,
            document=document,
            business_object_ids=business_object_ids,
            business_work_keys=sorted(
                {value.strip() for value in business_work_keys if value.strip()}
            ),
            actor=actor,
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="document.bindings.updated",
            resource_type="business_document",
            resource_id=str(document.id),
            metadata={
                "businessObjectIds": [str(value) for value in business_object_ids],
                "businessWorkKeys": business_work_keys,
            },
        )
        return document

    async def _replace_links(
        self,
        session: AsyncSession,
        *,
        document: BusinessDocument,
        business_object_ids: list[UUID],
        business_work_keys: list[str],
        actor: str,
    ) -> None:
        await session.execute(
            delete(DocumentBusinessObjectLink).where(
                DocumentBusinessObjectLink.business_document_id == document.id
            )
        )
        await session.execute(
            delete(DocumentWorkBinding).where(
                DocumentWorkBinding.business_document_id == document.id
            )
        )
        for object_id in dict.fromkeys(business_object_ids):
            business_object = await session.scalar(
                select(BusinessObject).where(
                    BusinessObject.id == object_id,
                    BusinessObject.tenant_id == document.tenant_id,
                    BusinessObject.project_id == document.project_id,
                    BusinessObject.lifecycle == "ACTIVE",
                )
            )
            if business_object is None:
                raise ValueError("DOCUMENT_BUSINESS_OBJECT_NOT_FOUND")
            version = await session.scalar(
                select(BusinessObjectVersion).where(
                    BusinessObjectVersion.business_object_id == business_object.id,
                    BusinessObjectVersion.version == business_object.current_version,
                )
            )
            if version is None:
                raise ValueError("DOCUMENT_BUSINESS_OBJECT_VERSION_NOT_FOUND")
            session.add(
                DocumentBusinessObjectLink(
                    tenant_id=document.tenant_id,
                    project_id=document.project_id,
                    business_document_id=document.id,
                    business_object_id=business_object.id,
                    business_object_version_id=version.id,
                    relation_type="RELATED",
                    created_by=actor,
                )
            )
        session.add_all(
            [
                DocumentWorkBinding(
                    tenant_id=document.tenant_id,
                    project_id=document.project_id,
                    business_document_id=document.id,
                    business_work_key=key,
                    created_by=actor,
                )
                for key in business_work_keys
            ]
        )
        await session.flush()

    @staticmethod
    def _validate_file(filename: str, size_bytes: int, sha256: str) -> None:
        if not filename or Path(filename).name != filename:
            raise ValueError("DOCUMENT_FILENAME_INVALID")
        if size_bytes <= 0 or len(sha256) != 64:
            raise ValueError("DOCUMENT_METADATA_INVALID")
        try:
            int(sha256, 16)
        except ValueError as exc:
            raise ValueError("DOCUMENT_METADATA_INVALID") from exc

    @staticmethod
    async def _idempotent_response(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        operation: str,
        key: str,
        request_hash: str,
    ) -> UUID | None:
        record = await session.get(IdempotencyKey, (tenant_id, project_id, operation, key))
        if record is None:
            return None
        if record.request_hash != request_hash:
            raise ValueError("IDEMPOTENCY_KEY_REUSED")
        return record.response_ref

    @staticmethod
    async def _record_idempotency(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        operation: str,
        key: str,
        request_hash: str,
        response_ref: UUID,
    ) -> None:
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
