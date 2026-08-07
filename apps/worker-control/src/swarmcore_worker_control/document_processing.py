from __future__ import annotations

import hashlib
import io
import json
import zipfile
from typing import Any
from uuid import UUID
from xml.etree import ElementTree

from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from swarmcore_application import DocumentProcessingService
from swarmcore_application.document_processing.limits import (
    MAX_SPREADSHEET_ROWS,
    ArchiveBudget,
    DocumentLimitError,
)
from swarmcore_domain import uuid7
from swarmcore_governance import ArtifactStore
from swarmcore_persistence import tenant_transaction
from swarmcore_persistence.models import (
    BlobObject,
    BusinessDocumentVersion,
    DocumentProcessingEvent,
    DocumentProcessingRun,
    OutboxEvent,
)
from temporalio import activity
from temporalio.exceptions import ApplicationError

_ODS_TABLE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
_XLSX_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


class DocumentProcessingActivities:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        *,
        artifact_store: ArtifactStore,
    ) -> None:
        self._sessions = sessions
        self._artifact_store = artifact_store
        self._processing = DocumentProcessingService(object_store=artifact_store)

    @activity.defn(name="plan_document_processing")
    async def plan(self, input_value: dict[str, Any]) -> dict[str, Any]:
        tenant_id, project_id, run_id = _scope(input_value)
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            run, version, blob = await self._source_rows(session, tenant_id, project_id, run_id)
            source = await self._read_blob(blob)
            groups, page_count, row_count = _processing_groups(
                source, version.media_type, version.filename
            )
            large = page_count >= 50 or len(source) >= 25 * 1024 * 1024 or row_count >= 100_000
            if not large:
                groups = []
            run.status = "PARSING"
            run.current_stage = "PARSING"
            run.provenance = {
                **run.provenance,
                "processingPlan": {
                    "largeDocument": large,
                    "pageCount": page_count,
                    "rowCount": row_count,
                    "groupCount": len(groups),
                    "pageBatchSize": 10,
                    "maxParallelism": 4,
                    "groups": groups,
                },
            }
            event_id = uuid7()
            session.add(
                OutboxEvent(
                    id=event_id,
                    tenant_id=tenant_id,
                    aggregate_id=run.id,
                    destination="nats",
                    partition_key=str(run.id),
                    source_id=event_id,
                    type="document.processing.segmented",
                    payload={
                        "processingRunId": str(run.id),
                        "largeDocument": large,
                        "groupCount": len(groups),
                        "pageCount": page_count,
                        "rowCount": row_count,
                        "maxParallelism": 4,
                    },
                )
            )
            _add_processing_event(
                session,
                run,
                event_type="document.processing.segmented",
                stage="PARSING",
                actor=str(run.provenance.get("actor") or "system"),
                payload={
                    "largeDocument": large,
                    "groupCount": len(groups),
                    "pageCount": page_count,
                    "rowCount": row_count,
                    "maxParallelism": 4,
                },
                tool_ref="tool://document/segment-plan@1",
            )
            return {
                "processingRunId": str(run.id),
                "largeDocument": large,
                "pageCount": page_count,
                "rowCount": row_count,
                "groups": groups,
            }

    @activity.defn(name="process_document_group")
    async def process_group(self, input_value: dict[str, Any]) -> dict[str, Any]:
        tenant_id, project_id, run_id = _scope(input_value)
        group = dict(input_value["group"])
        group_key = str(group["key"])
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            run, version, blob = await self._source_rows(session, tenant_id, project_id, run_id)
            existing = await session.scalar(
                select(BlobObject).where(
                    BlobObject.tenant_id == tenant_id,
                    BlobObject.project_id == project_id,
                    BlobObject.metadata_json["processingRunId"].astext == str(run_id),
                    BlobObject.metadata_json["groupKey"].astext == group_key,
                )
            )
            if existing is not None:
                return _group_receipt(group, existing)
            source = await self._read_blob(blob)
            payload = _extract_group(source, version.media_type, group)
            content = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
            artifact_id = uuid7()
            object_key = (
                f"{tenant_id}/{project_id}/document-processing/{run_id}/"
                f"groups/{group_key}-{artifact_id}.json"
            )
            await self._artifact_store.put(object_key, content)
            artifact = BlobObject(
                id=artifact_id,
                tenant_id=tenant_id,
                project_id=project_id,
                object_key=object_key,
                version=1,
                filename=f"{group_key}.json",
                media_type="application/json",
                size_bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                status="AVAILABLE",
                scan_status="CLEAN",
                retention_until=blob.retention_until,
                metadata_json={
                    "kind": "document-processing-group",
                    "processingRunId": str(run_id),
                    "groupKey": group_key,
                    "group": group,
                },
            )
            session.add(artifact)
            event_id = uuid7()
            session.add(
                OutboxEvent(
                    id=event_id,
                    tenant_id=tenant_id,
                    aggregate_id=run.id,
                    destination="nats",
                    partition_key=str(run.id),
                    source_id=event_id,
                    type="document.processing.group.completed",
                    payload={
                        "processingRunId": str(run.id),
                        "groupKey": group_key,
                        "artifactRef": f"blob://{artifact.id}",
                        "sha256": artifact.sha256,
                        "itemCount": int(payload.get("itemCount") or 0),
                    },
                )
            )
            _add_processing_event(
                session,
                run,
                event_type="document.page-batch.completed",
                stage="PARSING",
                actor=str(run.provenance.get("actor") or "system"),
                payload={
                    "groupKey": group_key,
                    "group": group,
                    "artifactRef": f"blob://{artifact.id}",
                    "itemCount": int(payload.get("itemCount") or 0),
                },
                output_hash=artifact.sha256,
                tool_ref="tool://document/parse-native@2",
            )
            return _group_receipt(group, artifact)

    @activity.defn(name="finalize_document_processing")
    async def finalize(self, input_value: dict[str, Any]) -> dict[str, Any]:
        tenant_id, project_id, run_id = _scope(input_value)
        group_receipts = [
            dict(value) for value in input_value.get("groups") or [] if isinstance(value, dict)
        ]
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            run = await self._processing.get_run(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                processing_run_id=run_id,
            )
            run.provenance = {
                **run.provenance,
                "groupArtifacts": group_receipts,
            }
            run = await self._processing.execute_pending_run(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                processing_run_id=run_id,
            )
            return {
                "processingRunId": str(run.id),
                "status": run.status,
                "currentStage": run.current_stage,
                "groupCount": len(group_receipts),
            }

    async def _source_rows(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
        run_id: UUID,
    ) -> tuple[DocumentProcessingRun, BusinessDocumentVersion, BlobObject]:
        run = await session.scalar(
            select(DocumentProcessingRun)
            .where(
                DocumentProcessingRun.id == run_id,
                DocumentProcessingRun.tenant_id == tenant_id,
                DocumentProcessingRun.project_id == project_id,
            )
            .with_for_update()
        )
        if run is None:
            raise LookupError("PROCESSING_RUN_NOT_FOUND")
        if run.status == "CANCELLED":
            raise ApplicationError(
                "DOCUMENT_PROCESSING_CANCELLED",
                non_retryable=True,
            )
        version = await session.scalar(
            select(BusinessDocumentVersion).where(
                BusinessDocumentVersion.id == run.business_document_version_id,
                BusinessDocumentVersion.tenant_id == tenant_id,
                BusinessDocumentVersion.project_id == project_id,
            )
        )
        if version is None:
            raise LookupError("DOCUMENT_VERSION_NOT_FOUND")
        blob = await session.scalar(
            select(BlobObject).where(
                BlobObject.id == version.blob_id,
                BlobObject.tenant_id == tenant_id,
                BlobObject.project_id == project_id,
            )
        )
        if blob is None:
            raise LookupError("BLOB_NOT_FOUND")
        if blob.scan_status != "CLEAN":
            raise ValueError(f"SECURITY_SCAN_FAILED:{blob.scan_status}")
        return run, version, blob

    async def _read_blob(self, blob: BlobObject) -> bytes:
        content = await self._artifact_store.get(blob.object_key)
        if hashlib.sha256(content).hexdigest() != blob.sha256:
            raise ValueError("DOCUMENT_HASH_MISMATCH")
        return content


def _scope(input_value: dict[str, Any]) -> tuple[UUID, UUID, UUID]:
    return (
        UUID(str(input_value["tenantId"])),
        UUID(str(input_value["projectId"])),
        UUID(str(input_value["processingRunId"])),
    )


def _processing_groups(
    source: bytes, media_type: str, filename: str
) -> tuple[list[dict[str, Any]], int, int]:
    if source.startswith(b"%PDF") or media_type == "application/pdf":
        page_count = len(PdfReader(io.BytesIO(source)).pages)
        return (
            [
                {
                    "key": f"pages-{start:04d}-{min(page_count, start + 9):04d}",
                    "kind": "PAGES",
                    "pageStart": start,
                    "pageEnd": min(page_count, start + 9),
                }
                for start in range(1, page_count + 1, 10)
            ],
            page_count,
            0,
        )
    if (
        filename.lower().endswith(".xlsx")
        or media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        try:
            with zipfile.ZipFile(io.BytesIO(source)) as archive:
                budget = ArchiveBudget(archive)
                sheet_names = sorted(
                    name
                    for name in archive.namelist()
                    if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
                )
                row_counts = [_xlsx_row_count(budget.read(name)) for name in sheet_names]
            return (
                [
                    {
                        "key": f"sheet-{index:04d}",
                        "kind": "SHEET",
                        "sheetIndex": index,
                        "sourcePath": name,
                        "rowCount": row_counts[index - 1],
                    }
                    for index, name in enumerate(sheet_names, start=1)
                ],
                0,
                sum(row_counts),
            )
        except DocumentLimitError:
            raise
        except (ElementTree.ParseError, zipfile.BadZipFile):
            return [], 0, 0
    if filename.lower().endswith(".ods") or media_type.endswith("spreadsheet"):
        try:
            with zipfile.ZipFile(io.BytesIO(source)) as archive:
                root = ElementTree.fromstring(ArchiveBudget(archive).read("content.xml"))
            sheets = root.findall(f".//{{{_ODS_TABLE}}}table")
            row_counts = [_ods_row_count(sheet) for sheet in sheets]
            groups = [
                {
                    "key": f"sheet-{index:04d}",
                    "kind": "SHEET",
                    "sheetIndex": index,
                    "sheetName": sheet.attrib.get(f"{{{_ODS_TABLE}}}name", ""),
                    "rowCount": row_counts[index - 1],
                }
                for index, sheet in enumerate(sheets, start=1)
            ]
            return groups, 0, sum(row_counts)
        except DocumentLimitError:
            raise
        except (
            KeyError,
            ValueError,
            ElementTree.ParseError,
            zipfile.BadZipFile,
        ):
            return [], 0, 0
    return [], 0, 0


def _xlsx_row_count(content: bytes) -> int:
    count = 0
    for _, node in ElementTree.iterparse(io.BytesIO(content), events=("end",)):
        if node.tag == f"{{{_XLSX_MAIN}}}row":
            count += 1
            if count > MAX_SPREADSHEET_ROWS:
                raise DocumentLimitError("DOCUMENT_SPREADSHEET_ROW_LIMIT_EXCEEDED")
        node.clear()
    return count


def _ods_row_count(sheet: ElementTree.Element) -> int:
    count = 0
    for row in sheet.findall(f".//{{{_ODS_TABLE}}}table-row"):
        count += int(row.attrib.get(f"{{{_ODS_TABLE}}}number-rows-repeated", "1"))
        if count > MAX_SPREADSHEET_ROWS:
            raise DocumentLimitError("DOCUMENT_SPREADSHEET_ROW_LIMIT_EXCEEDED")
    return count


def _extract_group(source: bytes, media_type: str, group: dict[str, Any]) -> dict[str, Any]:
    if group.get("kind") == "PAGES":
        reader = PdfReader(io.BytesIO(source))
        pages = []
        for page_number in range(int(group["pageStart"]), int(group["pageEnd"]) + 1):
            text = reader.pages[page_number - 1].extract_text() or ""
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                    "sourceKind": "NATIVE",
                    "contentHash": hashlib.sha256(text.encode()).hexdigest(),
                }
            )
        return {
            "schemaVersion": "schema://document-processing/group@1",
            "group": group,
            "mediaType": media_type,
            "pages": pages,
            "itemCount": len(pages),
        }
    return {
        "schemaVersion": "schema://document-processing/group@1",
        "group": group,
        "mediaType": media_type,
        "itemCount": int(group.get("rowCount") or 0),
    }


def _group_receipt(group: dict[str, Any], artifact: BlobObject) -> dict[str, Any]:
    return {
        "groupKey": str(group["key"]),
        "artifactRef": f"blob://{artifact.id}",
        "sha256": artifact.sha256,
        "sizeBytes": artifact.size_bytes,
    }


def _add_processing_event(
    session: AsyncSession,
    run: DocumentProcessingRun,
    *,
    event_type: str,
    stage: str,
    actor: str,
    payload: dict[str, Any],
    output_hash: str | None = None,
    tool_ref: str | None = None,
) -> None:
    session.add(
        DocumentProcessingEvent(
            tenant_id=run.tenant_id,
            project_id=run.project_id,
            processing_run_id=run.id,
            business_document_version_id=run.business_document_version_id,
            event_seq=int(run.next_event_seq or 1),
            type=event_type,
            stage=stage,
            payload=payload,
            output_hash=output_hash,
            tool_ref=tool_ref,
            actor_id=actor,
        )
    )
    run.next_event_seq = int(run.next_event_seq or 1) + 1
