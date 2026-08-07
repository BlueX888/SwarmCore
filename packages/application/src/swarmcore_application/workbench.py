from __future__ import annotations

import html
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

from jsonschema import Draft202012Validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import FindingStatus, can_transition_finding, uuid7
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.errors import PersistenceConflictError
from swarmcore_persistence.models import (
    BlobObject,
    BusinessDocument,
    BusinessDocumentVersion,
    Evaluation,
    Finding,
    FindingAction,
    IdempotencyKey,
    OutboxEvent,
    ProjectCapabilityDecisionBinding,
    Report,
    RuleSetVersion,
    WorkItem,
    WorkItemAttachment,
    WorkItemRevision,
    WorkItemSubject,
)
from swarmcore_persistence.repositories import canonical_hash
from swarmcore_registry import CapabilityPackManifest

from .capability_packs import CapabilityPackService
from .decision_assets import DecisionExecutionService
from .document_library import DocumentLibraryService
from .integrity import IntegrityResult
from .rule_sets import RuleSetService
from .services import RunService


class WorkbenchService:
    def __init__(
        self,
        capability_packs: CapabilityPackService,
        *,
        schemas: dict[str, dict[str, Any]] | None = None,
        runs: RunService | None = None,
        rule_sets: RuleSetService | None = None,
    ) -> None:
        self._capability_packs = capability_packs
        self._schemas = schemas or {}
        self._runs = runs or RunService()
        self._rule_sets = rule_sets or RuleSetService()
        self._audit = AuditRepository()
        self._decision_executions = DecisionExecutionService()
        self._documents = DocumentLibraryService()

    @staticmethod
    def _select_strategy_snapshot(
        manifest: CapabilityPackManifest,
        dependency_snapshot: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        selected = dependency_snapshot.get("strategy")
        if not isinstance(selected, dict):
            raise RuntimeError("capability pack strategy version snapshot is missing")
        if not manifest.spec.strategies.operations:
            return dict(selected)
        operation = str(payload.get("operation") or "").strip().upper()
        strategy_ref = manifest.spec.strategies.operations.get(operation)
        if strategy_ref is None:
            raise ValueError(f"CAPABILITY_OPERATION_UNSUPPORTED: {operation or 'MISSING'}")
        snapshots = dependency_snapshot.get("strategies")
        if not isinstance(snapshots, dict):
            raise RuntimeError("capability pack operation strategy snapshots are missing")
        operation_snapshot = snapshots.get(operation)
        if not isinstance(operation_snapshot, dict):
            raise RuntimeError(
                f"capability pack operation strategy snapshot is missing: {operation}"
            )
        if operation_snapshot.get("ref") != strategy_ref:
            raise RuntimeError(
                f"capability pack operation strategy snapshot does not match: {operation}"
            )
        return dict(operation_snapshot)

    async def list_work_items(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[WorkItem], int]:
        filters = (
            WorkItem.tenant_id == tenant_id,
            WorkItem.project_id == project_id,
        )
        total = await session.scalar(select(func.count()).select_from(WorkItem).where(*filters))
        items = list(
            await session.scalars(
                select(WorkItem)
                .where(*filters)
                .order_by(WorkItem.updated_at.desc(), WorkItem.id)
                .offset(offset)
                .limit(limit)
            )
        )
        return items, int(total or 0)

    async def get_work_item(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_item_id: UUID,
    ) -> tuple[WorkItem, WorkItemRevision]:
        item = await session.scalar(
            select(WorkItem).where(
                WorkItem.id == work_item_id,
                WorkItem.tenant_id == tenant_id,
                WorkItem.project_id == project_id,
            )
        )
        if item is None:
            raise LookupError("work item not found")
        return item, await self._current_revision(session, item)

    async def get_evaluation(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        evaluation_id: UUID,
    ) -> Evaluation:
        evaluation = await session.scalar(
            select(Evaluation).where(
                Evaluation.id == evaluation_id,
                Evaluation.tenant_id == tenant_id,
                Evaluation.project_id == project_id,
            )
        )
        if evaluation is None:
            raise LookupError("evaluation not found")
        return evaluation

    async def list_findings(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_item_id: UUID,
    ) -> list[Finding]:
        return list(
            await session.scalars(
                select(Finding)
                .where(
                    Finding.tenant_id == tenant_id,
                    Finding.project_id == project_id,
                    Finding.work_item_id == work_item_id,
                )
                .order_by(Finding.severity.desc(), Finding.created_at, Finding.id)
            )
        )

    async def list_reports(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        evaluation_id: UUID,
    ) -> list[Report]:
        return list(
            await session.scalars(
                select(Report)
                .where(
                    Report.tenant_id == tenant_id,
                    Report.project_id == project_id,
                    Report.evaluation_id == evaluation_id,
                )
                .order_by(Report.format)
            )
        )

    async def create_work_item(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_item_type: str,
        business_work_key: str | None = None,
        payload: dict[str, Any],
        owner: str | None,
        idempotency_key: str,
        actor: str,
    ) -> tuple[WorkItem, WorkItemRevision]:
        pack_version, manifest, binding = await self._capability_packs.resolve_enabled(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_type=work_item_type,
        )
        del pack_version, binding
        schema_ref = manifest.spec.work_item_schema
        if schema_ref is None:
            if manifest.spec.case is None:
                raise ValueError("CAPABILITY_PACK_CASE_INVALID")
            schema_ref = manifest.spec.case.schema_ref
        self._validate_schema(schema_ref, payload)
        request_hash = canonical_hash(
            {
                "workItemType": work_item_type,
                "businessWorkKey": business_work_key,
                "payload": payload,
                "owner": owner,
            }
        )
        existing = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation="work-item.create",
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing is not None:
            item = await session.get(WorkItem, existing)
            if item is None:
                raise RuntimeError("work item idempotency record is invalid")
            revision = await self._current_revision(session, item)
            return item, revision
        item = WorkItem(
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_type=work_item_type,
            business_work_key=business_work_key,
            schema_version=schema_ref,
            payload=payload,
            status="DRAFT",
            owner=owner,
            revision_number=1,
        )
        session.add(item)
        await session.flush()
        revision = await self._add_revision(session, item=item, actor=actor)
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation="work-item.create",
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=item.id,
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="work-item.create",
            resource_type="work_item",
            resource_id=str(item.id),
        )
        return item, revision

    async def update_work_item(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_item_id: UUID,
        payload: dict[str, Any],
        owner: str | None,
        expected_revision: int,
        idempotency_key: str,
        actor: str,
        copy_subjects: bool = True,
        subject_fingerprint: list[dict[str, str]] | None = None,
    ) -> tuple[WorkItem, WorkItemRevision]:
        item = await self._get_item_for_update(
            session, tenant_id=tenant_id, project_id=project_id, work_item_id=work_item_id
        )
        self._validate_schema(item.schema_version, payload)
        request_hash = canonical_hash(
            {
                "workItemId": str(work_item_id),
                "expectedRevision": expected_revision,
                "payload": payload,
                "owner": owner,
                "subjects": subject_fingerprint,
            }
        )
        operation = f"work-item.update:{work_item_id}"
        existing = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing is not None:
            revision = await session.get(WorkItemRevision, existing)
            if revision is None:
                raise RuntimeError("work item revision idempotency record is invalid")
            return item, revision
        if item.revision_number != expected_revision:
            raise PersistenceConflictError(
                f"work item revision is {item.revision_number}, expected {expected_revision}"
            )
        previous = await self._current_revision(session, item)
        item.payload = payload
        item.owner = owner
        item.revision_number += 1
        item.status = "DRAFT"
        revision = await self._add_revision(session, item=item, actor=actor)
        await self._copy_attachments(session, previous=previous, target=revision)
        if copy_subjects:
            await self._copy_subjects(session, previous=previous, target=revision)
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=revision.id,
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="work-item.update",
            resource_type="work_item",
            resource_id=str(item.id),
            metadata={"revision": revision.revision},
        )
        return item, revision

    async def initiate_attachment(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_item_id: UUID,
        document_type: str,
        filename: str,
        media_type: str,
        size_bytes: int,
        sha256: str,
        retention_days: int,
        idempotency_key: str,
        actor: str,
    ) -> tuple[BlobObject, UUID]:
        if Path(filename).name != filename or not filename:
            raise ValueError("BLOB_FILENAME_INVALID")
        if size_bytes <= 0 or len(sha256) != 64:
            raise ValueError("BLOB_METADATA_INVALID")
        request_hash = canonical_hash(
            {
                "workItemId": str(work_item_id),
                "documentType": document_type,
                "filename": filename,
                "mediaType": media_type,
                "sizeBytes": size_bytes,
                "sha256": sha256.lower(),
                "retentionDays": retention_days,
            }
        )
        operation = f"attachment.initiate:{work_item_id}"
        existing_blob_id = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing_blob_id is not None:
            existing_blob = await session.get(BlobObject, existing_blob_id)
            if existing_blob is None:
                raise RuntimeError("attachment idempotency record is invalid")
            return existing_blob, UUID(str(existing_blob.metadata_json["attachmentId"]))
        item = await self._get_item_for_update(
            session, tenant_id=tenant_id, project_id=project_id, work_item_id=work_item_id
        )
        revision = await self._current_revision(session, item)
        evaluated = await session.scalar(
            select(Evaluation.id).where(Evaluation.work_item_revision_id == revision.id).limit(1)
        )
        if evaluated is not None:
            previous = revision
            item.revision_number += 1
            item.status = "DRAFT"
            revision = await self._add_revision(session, item=item, actor=actor)
            await self._copy_attachments(session, previous=previous, target=revision)
            await self._copy_subjects(session, previous=previous, target=revision)
        attachment_id = uuid7()
        blob_id = uuid7()
        blob = BlobObject(
            id=blob_id,
            tenant_id=tenant_id,
            project_id=project_id,
            object_key=f"{tenant_id}/{project_id}/blob/{blob_id}/v1",
            version=1,
            filename=filename,
            media_type=media_type,
            size_bytes=size_bytes,
            sha256=sha256.lower(),
            status="PENDING",
            scan_status="PENDING",
            retention_until=datetime.now(UTC) + timedelta(days=retention_days),
            metadata_json={
                "attachmentId": str(attachment_id),
                "workItemId": str(item.id),
                "revisionId": str(revision.id),
                "documentType": document_type,
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
        return blob, attachment_id

    async def complete_attachment(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        attachment_id: UUID,
        actual_sha256: str,
        scan_status: str,
        idempotency_key: str,
        actor: str,
    ) -> WorkItemAttachment:
        blob = await session.scalar(
            select(BlobObject)
            .where(
                BlobObject.tenant_id == tenant_id,
                BlobObject.project_id == project_id,
                BlobObject.metadata_json["attachmentId"].astext == str(attachment_id),
            )
            .with_for_update()
        )
        if blob is None:
            raise LookupError("attachment upload not found")
        if blob.status != "AVAILABLE" or blob.scan_status != "CLEAN":
            raise PersistenceConflictError("blob upload and scan have not completed")
        if actual_sha256.lower() != blob.sha256:
            raise ValueError("BLOB_HASH_MISMATCH")
        if scan_status != "CLEAN" or scan_status != blob.scan_status:
            raise ValueError("BLOB_SCAN_REJECTED")
        request_hash = canonical_hash(
            {
                "attachmentId": str(attachment_id),
                "sha256": actual_sha256,
                "scanStatus": scan_status,
            }
        )
        operation = f"attachment.complete:{attachment_id}"
        existing_id = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing_id is not None:
            existing = await session.get(WorkItemAttachment, existing_id)
            if existing is None:
                raise RuntimeError("attachment completion idempotency record is invalid")
            return existing
        metadata = blob.metadata_json
        attachment = WorkItemAttachment(
            id=attachment_id,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_id=UUID(str(metadata["workItemId"])),
            revision_id=UUID(str(metadata["revisionId"])),
            blob_id=blob.id,
            document_type=str(metadata["documentType"]),
        )
        session.add(attachment)
        await session.flush()
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=attachment.id,
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="blob.complete",
            resource_type="blob_object",
            resource_id=str(blob.id),
            metadata={"sha256": blob.sha256, "sizeBytes": blob.size_bytes},
        )
        return attachment

    async def execute(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_item_id: UUID,
        idempotency_key: str,
        actor: str,
        submitted_scopes: tuple[str, ...] = (),
        auth_context_hash: str = "unknown",
    ) -> Evaluation:
        item = await self._get_item_for_update(
            session, tenant_id=tenant_id, project_id=project_id, work_item_id=work_item_id
        )
        revision = await self._current_revision(session, item)
        pack_version, manifest, binding = await self._capability_packs.resolve_enabled(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_type=item.work_item_type,
        )
        execution_permission = self._required_execution_permission(manifest)
        if execution_permission not in manifest.spec.permissions:
            raise ValueError(f"CAPABILITY_PERMISSION_MISSING: {execution_permission}")
        execution_payload = self._execution_payload(
            manifest.metadata.name,
            revision.payload,
        )
        existing = await session.scalar(
            select(Evaluation).where(
                Evaluation.project_id == project_id,
                Evaluation.work_item_revision_id == revision.id,
                Evaluation.capability_pack_version_id == pack_version.id,
                Evaluation.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return existing
        attachments = await self._attachments(session, revision.id)
        subjects = list(
            await session.scalars(
                select(WorkItemSubject).where(WorkItemSubject.work_item_revision_id == revision.id)
            )
        )
        decision_bindings = list(
            await session.scalars(
                select(ProjectCapabilityDecisionBinding).where(
                    ProjectCapabilityDecisionBinding.project_capability_binding_id == binding.id
                )
            )
        )
        if manifest.spec.case is not None and manifest.spec.case.subjects_required and not subjects:
            raise ValueError("CASE_SUBJECT_REQUIRED")
        decision_slots = {value.slot for value in decision_bindings}
        if any(
            value.required and value.slot not in decision_slots for value in manifest.spec.decisions
        ):
            raise ValueError("DECISION_BINDING_REQUIRED")
        business_work_keys = _business_work_keys(
            manifest.metadata.name,
            item.work_item_type,
        )
        document_versions = await self._documents.current_versions_for_work(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            business_work_keys=business_work_keys,
            business_object_ids=tuple(value.business_object_id for value in subjects),
        )
        selection = execution_payload.get("documentSelection", {})
        if not isinstance(selection, dict):
            selection = {}
        include_ids = {str(value) for value in selection.get("includeVersionIds", [])}
        exclude_ids = {str(value) for value in selection.get("excludeVersionIds", [])}
        baseline_ids = {str(value) for value in selection.get("baselineVersionIds", [])}
        available_version_ids = {str(row[1].id) for row in document_versions}
        if (include_ids | baseline_ids) - available_version_ids:
            raise ValueError("DOCUMENT_SELECTION_INVALID")
        if (include_ids | baseline_ids) & exclude_ids:
            raise ValueError("DOCUMENT_SELECTION_INVALID")
        document_versions = [row for row in document_versions if str(row[1].id) not in exclude_ids]
        if manifest.metadata.name == "deviation-analysis":
            baseline_categories = {
                "SCOPE_BASELINE",
                "SCHEDULE_BASELINE",
                "COST_BASELINE",
            }
            for category in baseline_categories:
                candidates = [row for row in document_versions if row[0].category == category]
                selected_baselines = [row for row in candidates if str(row[1].id) in baseline_ids]
                if len(candidates) > 1 and not selected_baselines:
                    raise ValueError("BASELINE_SELECTION_REQUIRED")
                if selected_baselines:
                    document_versions = [
                        row
                        for row in document_versions
                        if row[0].category != category or row in selected_baselines
                    ]
        requirements = manifest.spec.document_requirements()
        requirements_by_category = {
            requirement.category: requirement for requirement in requirements
        }
        documents_by_category: dict[
            str, list[tuple[BusinessDocument, BusinessDocumentVersion, BlobObject]]
        ] = {}
        for row in document_versions:
            documents_by_category.setdefault(row[0].category, []).append(row)
        selected_documents: list[tuple[BusinessDocument, BusinessDocumentVersion, BlobObject]] = []
        for requirement in requirements:
            rows = documents_by_category.get(requirement.category, [])
            rows.sort(
                key=lambda row: (
                    0 if str(row[1].id) in include_ids else 1,
                    -row[1].version,
                    str(row[0].id),
                )
            )
            limit = requirement.max_count if requirement.max_count is not None else len(rows)
            selected_documents.extend(rows[:limit])
        for category in sorted(set(documents_by_category) - set(requirements_by_category)):
            selected_documents.extend(documents_by_category[category])
        document_versions = selected_documents[:100]
        selected_counts: dict[str, int] = {}
        for document, _, _ in document_versions:
            selected_counts[document.category] = selected_counts.get(document.category, 0) + 1
        if any(
            requirement.required
            and selected_counts.get(requirement.category, 0) < requirement.min_count
            for requirement in manifest.spec.document_requirements()
        ):
            raise ValueError("DOCUMENT_SELECTION_REQUIRED")
        if (
            self._schema_requires_non_empty(manifest.spec.input_schema, "documents")
            and not document_versions
        ):
            raise ValueError("DOCUMENT_SELECTION_REQUIRED")
        if (
            manifest.api_version == "swarmcore.io/v2"
            and self._schema_requires_non_empty(manifest.spec.input_schema, "subjects")
            and not subjects
        ):
            raise ValueError("CASE_SUBJECT_REQUIRED")
        attachment_hash = canonical_hash(
            {
                "attachments": [
                    {
                        "attachmentId": str(attachment.id),
                        "blobId": str(blob.id),
                        "documentType": attachment.document_type,
                        "sha256": blob.sha256,
                    }
                    for attachment, blob in attachments
                ],
                "documents": [
                    {
                        "documentId": str(document.id),
                        "documentVersionId": str(version.id),
                        "blobId": str(blob.id),
                        "version": version.version,
                        "sha256": version.sha256,
                    }
                    for document, version, blob in document_versions
                ],
            }
        )
        selection_hash = canonical_hash(
            {
                "algorithm": f"{manifest.metadata.name}-document-selection@1",
                "includeVersionIds": sorted(include_ids),
                "excludeVersionIds": sorted(exclude_ids),
                "baselineVersionIds": sorted(baseline_ids),
                "selectedVersionIds": sorted(
                    str(version.id) for _, version, _ in document_versions
                ),
            }
        )
        baseline_hash = canonical_hash(
            [
                {
                    "category": document.category,
                    "documentVersionId": str(version.id),
                    "sha256": version.sha256,
                }
                for document, version, _ in document_versions
                if document.category in {"SCOPE_BASELINE", "SCHEDULE_BASELINE", "COST_BASELINE"}
            ]
        )
        configuration_hash = canonical_hash(
            {
                "binding": binding.configuration,
                "currency": execution_payload.get("currency", "CNY"),
                "timezone": execution_payload.get("timezone", "Asia/Shanghai"),
                "dimensions": execution_payload.get("dimensions", ["TIME", "CONTENT", "COST"]),
                "thresholds": execution_payload.get("thresholds", {}),
                "approval": execution_payload.get("approval", {}),
                "approvalRules": execution_payload.get("approvalRules", {}),
            }
        )
        rule_version = None
        if manifest.spec.rules is not None:
            rule_version = await self._rule_sets.select_version(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                payload=execution_payload,
            )
        elif decision_bindings:
            rule_version = await session.get(
                RuleSetVersion, decision_bindings[0].rule_set_version_id
            )
            if rule_version is None or rule_version.status != "PUBLISHED":
                raise ValueError("DECISION_VERSION_NOT_PUBLISHED")
        attachment_payloads = [self._attachment_payload(value) for value in attachments]
        attachment_payloads.extend(
            self._document_attachment_payload(value) for value in document_versions
        )
        document_payloads = [
            {
                "documentId": str(document.id),
                "documentVersionId": str(version.id),
                "blobId": str(blob.id),
                "name": document.name,
                "category": document.category,
                "filename": version.filename,
                "mediaType": version.media_type,
                "sizeBytes": version.size_bytes,
                "sha256": version.sha256,
                "version": version.version,
            }
            for document, version, blob in document_versions
        ]
        evaluation_id = uuid7()
        input_data: dict[str, Any] = {
            "workItemId": str(item.id),
            "workItemRevisionId": str(revision.id),
            "evaluationId": str(evaluation_id),
            "payload": execution_payload,
            "attachments": attachment_payloads,
            "attachmentManifestHash": attachment_hash,
            "configuration": dict(binding.configuration),
        }
        if self._schema_has_property(manifest.spec.input_schema, "documents"):
            input_data["documents"] = document_payloads
        if self._schema_has_property(manifest.spec.input_schema, "resources"):
            input_data["resources"] = {}
        if self._requires_selection_provenance(manifest.metadata.name):
            input_data.update(
                {
                    "selectionManifestHash": selection_hash,
                    "baselineHash": baseline_hash,
                    "configurationHash": configuration_hash,
                }
            )
        if manifest.api_version == "swarmcore.io/v2":
            input_data["subjects"] = [
                {
                    "subjectKey": value.subject_key,
                    "role": value.role,
                    "businessObjectId": str(value.business_object_id),
                    "businessObjectVersionId": str(value.business_object_version_id),
                }
                for value in subjects
            ]
        if rule_version is not None:
            input_data.update(
                {
                    "ruleSetVersionId": str(rule_version.id),
                    "rules": dict(rule_version.rules),
                }
            )
        if self._schema_has_property(manifest.spec.input_schema, "upstreamEvaluations"):
            input_data["upstreamEvaluations"] = await self._upstream_evaluations(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                current_work_item_id=item.id,
                subjects=subjects,
            )
        self._validate_schema(manifest.spec.input_schema, input_data)
        strategy_snapshot = self._select_strategy_snapshot(
            manifest,
            pack_version.dependency_snapshot,
            execution_payload,
        )
        strategy_version_id = strategy_snapshot.get("strategyVersionId")
        if not isinstance(strategy_version_id, str):
            raise RuntimeError("capability pack strategy version snapshot is missing")
        run, _ = await self._runs.create(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            strategy_version_id=UUID(strategy_version_id),
            input_data=input_data,
            idempotency_key=f"workbench:{idempotency_key}",
            initiated_by=actor,
            submitted_scopes=submitted_scopes,
            auth_context_hash=auth_context_hash,
        )
        request_hash = canonical_hash(
            {
                "revisionId": str(revision.id),
                "packVersionId": str(pack_version.id),
                "attachmentManifestHash": attachment_hash,
                "bindingConfigurationHash": canonical_hash(binding.configuration),
                "strategyRef": strategy_snapshot.get("ref"),
            }
        )
        evaluation = Evaluation(
            id=evaluation_id,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_id=item.id,
            work_item_revision_id=revision.id,
            capability_pack_version_id=pack_version.id,
            rule_set_version_id=rule_version.id if rule_version is not None else None,
            run_id=run.id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            status="RUNNING",
            strategy_version_id=run.strategy_version_id,
            plan_hash=run.plan_hash,
            registry_snapshot={
                **dict(pack_version.dependency_snapshot),
                "selectedStrategy": dict(strategy_snapshot),
                "businessWorkKey": item.business_work_key,
                "manifestPermissions": list(manifest.spec.permissions),
                "executionPermission": execution_permission,
                "bindingConfiguration": dict(binding.configuration),
                "bindingConfigurationHash": canonical_hash(binding.configuration),
            },
            attachment_manifest_hash=attachment_hash,
            input_schema_version=manifest.spec.input_schema,
            output_schema_version=manifest.spec.output_schema,
            report_template_version=manifest.spec.report.template,
            policy_revision=run.policy_revision,
        )
        session.add(evaluation)
        await session.flush()
        _ = [
            await self._decision_executions.freeze(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                evaluation_id=evaluation.id,
                binding=value,
            )
            for value in decision_bindings
        ]
        await self._documents.freeze_usage(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            evaluation=evaluation,
            business_work_key=item.business_work_key or manifest.metadata.name,
            documents=document_versions,
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="evaluation.execute",
            resource_type="evaluation",
            resource_id=str(evaluation.id),
            run_id=run.id,
        )
        return evaluation

    @staticmethod
    def _requires_selection_provenance(manifest_name: str) -> bool:
        return manifest_name in {
            "contract-performance",
            "deviation-analysis",
            "document-structuring",
            "invoice-assurance",
            "procurement-supplier-risk",
        }

    @staticmethod
    def _required_execution_permission(manifest: CapabilityPackManifest) -> str:
        return "case.assess" if manifest.spec.case is not None else "work-item.execute"

    @staticmethod
    async def _upstream_evaluations(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        current_work_item_id: UUID,
        subjects: list[WorkItemSubject],
    ) -> list[dict[str, Any]]:
        subject_ids = tuple(dict.fromkeys(value.business_object_id for value in subjects))
        if not subject_ids:
            return []
        rows = await session.execute(
            select(Evaluation, WorkItem.business_work_key, WorkItem.work_item_type)
            .join(WorkItem, WorkItem.id == Evaluation.work_item_id)
            .join(
                WorkItemSubject,
                WorkItemSubject.work_item_revision_id == Evaluation.work_item_revision_id,
            )
            .where(
                Evaluation.tenant_id == tenant_id,
                Evaluation.project_id == project_id,
                Evaluation.status == "SUCCEEDED",
                Evaluation.result.is_not(None),
                WorkItem.id != current_work_item_id,
                WorkItemSubject.business_object_id.in_(subject_ids),
            )
            .order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
            .limit(100)
        )
        upstream: list[dict[str, Any]] = []
        seen_work_keys: set[str] = set()
        for evaluation, business_work_key, work_item_type in rows:
            key = str(business_work_key or work_item_type)
            if key in {"contract-post-evaluation", "contract-post-evaluation-case"}:
                continue
            if key in seen_work_keys or not isinstance(evaluation.result, dict):
                continue
            seen_work_keys.add(key)
            upstream.append(
                {
                    "evaluationId": str(evaluation.id),
                    "businessWorkKey": key,
                    "outputSchemaVersion": evaluation.output_schema_version,
                    "resultHash": canonical_hash(evaluation.result),
                    "result": dict(evaluation.result),
                }
            )
            if len(upstream) == 20:
                break
        return upstream

    @staticmethod
    def _execution_payload(
        manifest_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if manifest_name != "invoice-assurance":
            return payload
        return {
            **payload,
            "fieldConfirmations": list(payload.get("fieldConfirmations") or []),
            "humanVerification": dict(payload.get("humanVerification") or {}),
            "enterprisePublicStatusEvidence": dict(
                payload.get("enterprisePublicStatusEvidence") or {}
            ),
        }

    async def act_on_finding(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        finding_id: UUID,
        action: str,
        reason: str | None,
        assignee: str | None,
        expires_at: datetime | None,
        idempotency_key: str,
        actor: str,
    ) -> Finding:
        request_hash = canonical_hash(
            {
                "findingId": str(finding_id),
                "action": action,
                "reason": reason,
                "assignee": assignee,
                "expiresAt": expires_at.isoformat() if expires_at is not None else None,
            }
        )
        operation = f"finding.act:{finding_id}"
        existing_id = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing_id is not None:
            existing = await session.get(Finding, existing_id)
            if existing is None:
                raise RuntimeError("finding action idempotency record is invalid")
            return existing
        finding = await session.scalar(
            select(Finding)
            .where(
                Finding.id == finding_id,
                Finding.tenant_id == tenant_id,
                Finding.project_id == project_id,
            )
            .with_for_update()
        )
        if finding is None:
            raise LookupError("finding not found")
        targets = {
            "ACKNOWLEDGE": FindingStatus.ACKNOWLEDGED,
            "WAIVE": FindingStatus.WAIVED,
            "RESOLVE": FindingStatus.RESOLVED,
            "REOPEN": FindingStatus.OPEN,
        }
        current = FindingStatus(finding.status)
        if action == "ASSIGN":
            target = current
            if not assignee:
                raise ValueError("finding assignment requires an assignee")
        else:
            try:
                target = targets[action]
            except KeyError as exc:
                raise ValueError("unsupported finding action") from exc
            if not can_transition_finding(current, target):
                raise PersistenceConflictError(
                    f"finding cannot transition from {current} to {target}"
                )
        if action == "WAIVE" and not reason:
            raise ValueError("finding waiver requires a reason")
        action_record = await self._append_finding_action(
            session,
            finding=finding,
            action=action,
            target=target,
            actor=actor,
            reason=reason,
            assignee=assignee,
            expires_at=expires_at,
        )
        await self._emit(
            session,
            tenant_id=tenant_id,
            aggregate_id=finding.id,
            source_id=action_record.id,
            event_type="finding.action-recorded",
            payload={
                "findingId": str(finding.id),
                "action": action,
                "status": finding.status,
            },
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action=f"finding.{action.lower()}",
            resource_type="finding",
            resource_id=str(finding.id),
            metadata={"reason": reason, "assignee": assignee},
        )
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=finding.id,
        )
        return finding

    async def _record_result(
        self,
        session: AsyncSession,
        *,
        item: WorkItem,
        evaluation: Evaluation,
        result: IntegrityResult,
        actor: str,
    ) -> None:
        if evaluation.status == "SUCCEEDED":
            return
        active_keys = {finding.rule_key for finding in result.findings}
        existing = list(
            await session.scalars(
                select(Finding).where(Finding.work_item_id == item.id).with_for_update()
            )
        )
        by_key = {finding.rule_key: finding for finding in existing}
        for result_finding in result.findings:
            finding = by_key.get(result_finding.rule_key)
            if finding is None:
                finding = Finding(
                    tenant_id=item.tenant_id,
                    project_id=item.project_id,
                    work_item_id=item.id,
                    evaluation_id=evaluation.id,
                    rule_key=result_finding.rule_key,
                    code=result_finding.code,
                    category=result_finding.category,
                    severity=result_finding.severity,
                    status="OPEN",
                    title=result_finding.title,
                    detail=result_finding.detail,
                    evidence=result_finding.evidence,
                )
                session.add(finding)
                await session.flush()
                action_record = await self._append_finding_action(
                    session,
                    finding=finding,
                    action="OPEN",
                    target=FindingStatus.OPEN,
                    actor="system",
                    reason="deterministic rule finding",
                )
                await self._record_automatic_finding_change(
                    session,
                    finding=finding,
                    action_record=action_record,
                    action="OPEN",
                    evaluation=evaluation,
                )
            else:
                finding.evaluation_id = evaluation.id
                finding.code = result_finding.code
                finding.category = result_finding.category
                finding.severity = result_finding.severity
                finding.title = result_finding.title
                finding.detail = result_finding.detail
                finding.evidence = result_finding.evidence
                if finding.status in {"RESOLVED", "WAIVED"}:
                    action_record = await self._append_finding_action(
                        session,
                        finding=finding,
                        action="REOPEN",
                        target=FindingStatus.OPEN,
                        actor="system",
                        reason="finding reappeared in deterministic re-evaluation",
                    )
                    await self._record_automatic_finding_change(
                        session,
                        finding=finding,
                        action_record=action_record,
                        action="REOPEN",
                        evaluation=evaluation,
                    )
        for finding in existing:
            if finding.rule_key not in active_keys and finding.status in {"OPEN", "ACKNOWLEDGED"}:
                finding.resolved_by_evaluation_id = evaluation.id
                action_record = await self._append_finding_action(
                    session,
                    finding=finding,
                    action="AUTO_RESOLVE",
                    target=FindingStatus.RESOLVED,
                    actor="system",
                    reason="new evidence satisfies the deterministic rule",
                )
                await self._record_automatic_finding_change(
                    session,
                    finding=finding,
                    action_record=action_record,
                    action="AUTO_RESOLVE",
                    evaluation=evaluation,
                )
        result_payload = result.model_dump(mode="json", by_alias=True)
        self._validate_schema(evaluation.output_schema_version, result_payload)
        evaluation.result = result_payload
        evaluation.status = "SUCCEEDED"
        item.status = "COMPLETED" if result.passed else "IN_REVIEW"
        await self._create_reports(session, evaluation=evaluation, item=item, result=result_payload)
        await self._emit(
            session,
            tenant_id=item.tenant_id,
            aggregate_id=evaluation.id,
            source_id=evaluation.id,
            event_type="evaluation.succeeded",
            payload={
                "evaluationId": str(evaluation.id),
                "workItemId": str(item.id),
                "passed": result.passed,
            },
        )
        del actor

    async def _create_reports(
        self,
        session: AsyncSession,
        *,
        evaluation: Evaluation,
        item: WorkItem,
        result: dict[str, Any],
    ) -> None:
        json_report = Report(
            tenant_id=item.tenant_id,
            project_id=item.project_id,
            work_item_id=item.id,
            evaluation_id=evaluation.id,
            format="JSON",
            template_version=evaluation.report_template_version,
            result_schema_version=evaluation.output_schema_version,
            content=result,
            content_hash=canonical_hash(result),
        )
        html_value = _render_html_report(item, evaluation, result)
        html_report = Report(
            tenant_id=item.tenant_id,
            project_id=item.project_id,
            work_item_id=item.id,
            evaluation_id=evaluation.id,
            format="HTML",
            template_version=evaluation.report_template_version,
            result_schema_version=evaluation.output_schema_version,
            content={"html": html_value},
            content_hash=canonical_hash(html_value),
        )
        session.add_all([json_report, html_report])
        await session.flush()
        for report in (json_report, html_report):
            await self._emit(
                session,
                tenant_id=item.tenant_id,
                aggregate_id=evaluation.id,
                source_id=report.id,
                event_type="report.created",
                payload={
                    "reportId": str(report.id),
                    "evaluationId": str(evaluation.id),
                    "format": report.format,
                    "contentHash": report.content_hash,
                },
            )

    async def _append_finding_action(
        self,
        session: AsyncSession,
        *,
        finding: Finding,
        action: str,
        target: FindingStatus,
        actor: str,
        reason: str | None = None,
        assignee: str | None = None,
        expires_at: datetime | None = None,
    ) -> FindingAction:
        previous = finding.status
        finding.status = target.value
        record = FindingAction(
            tenant_id=finding.tenant_id,
            project_id=finding.project_id,
            finding_id=finding.id,
            action=action,
            from_status=previous,
            to_status=target.value,
            reason=reason,
            assignee=assignee,
            actor_id=actor,
            expires_at=expires_at,
        )
        session.add(record)
        await session.flush()
        return record

    async def _record_automatic_finding_change(
        self,
        session: AsyncSession,
        *,
        finding: Finding,
        action_record: FindingAction,
        action: str,
        evaluation: Evaluation,
    ) -> None:
        await self._audit.append(
            session,
            tenant_id=finding.tenant_id,
            project_id=finding.project_id,
            actor_id="system",
            action=f"finding.{action.lower()}",
            resource_type="finding",
            resource_id=str(finding.id),
            run_id=evaluation.run_id,
            metadata={"evaluationId": str(evaluation.id)},
        )
        await self._emit(
            session,
            tenant_id=finding.tenant_id,
            aggregate_id=finding.id,
            source_id=action_record.id,
            event_type="finding.action-recorded",
            payload={
                "findingId": str(finding.id),
                "evaluationId": str(evaluation.id),
                "action": action,
                "status": finding.status,
            },
        )

    async def _get_item_for_update(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_item_id: UUID,
    ) -> WorkItem:
        item = await session.scalar(
            select(WorkItem)
            .where(
                WorkItem.id == work_item_id,
                WorkItem.tenant_id == tenant_id,
                WorkItem.project_id == project_id,
            )
            .with_for_update()
        )
        if item is None:
            raise LookupError("work item not found")
        return item

    async def _current_revision(self, session: AsyncSession, item: WorkItem) -> WorkItemRevision:
        revision = await session.scalar(
            select(WorkItemRevision).where(
                WorkItemRevision.work_item_id == item.id,
                WorkItemRevision.revision == item.revision_number,
            )
        )
        if revision is None:
            raise RuntimeError("work item current revision is missing")
        return revision

    async def _add_revision(
        self, session: AsyncSession, *, item: WorkItem, actor: str
    ) -> WorkItemRevision:
        revision = WorkItemRevision(
            tenant_id=item.tenant_id,
            project_id=item.project_id,
            work_item_id=item.id,
            revision=item.revision_number,
            schema_version=item.schema_version,
            payload=item.payload,
            payload_hash=canonical_hash(item.payload),
            created_by=actor,
        )
        session.add(revision)
        await session.flush()
        return revision

    async def _copy_attachments(
        self,
        session: AsyncSession,
        *,
        previous: WorkItemRevision,
        target: WorkItemRevision,
    ) -> None:
        values = list(
            await session.scalars(
                select(WorkItemAttachment).where(WorkItemAttachment.revision_id == previous.id)
            )
        )
        session.add_all(
            [
                WorkItemAttachment(
                    tenant_id=value.tenant_id,
                    project_id=value.project_id,
                    work_item_id=value.work_item_id,
                    revision_id=target.id,
                    blob_id=value.blob_id,
                    document_type=value.document_type,
                    label=value.label,
                )
                for value in values
            ]
        )
        await session.flush()

    async def _copy_subjects(
        self,
        session: AsyncSession,
        *,
        previous: WorkItemRevision,
        target: WorkItemRevision,
    ) -> None:
        values = list(
            await session.scalars(
                select(WorkItemSubject).where(WorkItemSubject.work_item_revision_id == previous.id)
            )
        )
        session.add_all(
            [
                WorkItemSubject(
                    tenant_id=value.tenant_id,
                    project_id=value.project_id,
                    work_item_id=value.work_item_id,
                    work_item_revision_id=target.id,
                    business_object_id=value.business_object_id,
                    business_object_version_id=value.business_object_version_id,
                    role=value.role,
                    subject_key=value.subject_key,
                )
                for value in values
            ]
        )
        await session.flush()

    async def _attachments(
        self, session: AsyncSession, revision_id: UUID
    ) -> list[tuple[WorkItemAttachment, BlobObject]]:
        rows = await session.execute(
            select(WorkItemAttachment, BlobObject)
            .join(BlobObject, BlobObject.id == WorkItemAttachment.blob_id)
            .where(
                WorkItemAttachment.revision_id == revision_id,
                BlobObject.status == "AVAILABLE",
                BlobObject.scan_status == "CLEAN",
                BlobObject.retention_until > datetime.now(UTC),
            )
            .order_by(WorkItemAttachment.id)
        )
        return list(rows.tuples())

    @staticmethod
    def _attachment_payload(
        value: tuple[WorkItemAttachment, BlobObject],
    ) -> dict[str, Any]:
        attachment, blob = value
        payload = {
            "attachmentId": str(attachment.id),
            "blobId": str(blob.id),
            "documentType": attachment.document_type,
            "filename": blob.filename,
            "mediaType": blob.media_type,
            "sha256": blob.sha256,
            "version": blob.version,
            "readable": True,
        }
        expires_at = blob.metadata_json.get("documentExpiresAt")
        if expires_at is not None:
            payload["expiresAt"] = expires_at
        return payload

    @staticmethod
    def _document_attachment_payload(
        value: tuple[BusinessDocument, BusinessDocumentVersion, BlobObject],
    ) -> dict[str, Any]:
        document, version, blob = value
        payload = {
            "attachmentId": str(document.id),
            "blobId": str(blob.id),
            "documentType": document.category.lower(),
            "filename": version.filename,
            "mediaType": version.media_type,
            "sha256": version.sha256,
            "version": version.version,
            "readable": True,
        }
        expires_at = blob.metadata_json.get("documentExpiresAt")
        if expires_at is not None:
            payload["expiresAt"] = expires_at
        return payload

    def _validate_schema(self, schema_ref: str, value: dict[str, Any]) -> None:
        schema = self._schemas.get(schema_ref)
        if schema is not None:
            Draft202012Validator(schema).validate(value)

    def _schema_requires_non_empty(self, schema_ref: str, field: str) -> bool:
        schema = self._schemas.get(schema_ref)
        if not isinstance(schema, dict):
            return False
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return False
        field_schema = properties.get(field)
        if not isinstance(field_schema, dict):
            return False
        min_items = field_schema.get("minItems")
        return isinstance(min_items, int) and min_items >= 1

    def _schema_has_property(self, schema_ref: str, field: str) -> bool:
        schema = self._schemas.get(schema_ref)
        if not isinstance(schema, dict):
            return False
        properties = schema.get("properties")
        return isinstance(properties, dict) and field in properties

    async def _idempotent_response(
        self,
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

    async def _emit(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        aggregate_id: UUID,
        source_id: UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        session.add(
            OutboxEvent(
                id=uuid7(),
                tenant_id=tenant_id,
                aggregate_id=aggregate_id,
                destination="nats",
                partition_key=str(aggregate_id),
                source_id=source_id,
                type=event_type,
                payload=payload,
            )
        )
        await session.flush()


def _business_work_keys(pack_name: str, work_item_type: str) -> tuple[str, ...]:
    from .business_works import document_binding_keys

    return document_binding_keys(pack_name, work_item_type)


def _render_html_report(item: WorkItem, evaluation: Evaluation, result: dict[str, Any]) -> str:
    rows = "".join(
        "<li><strong>"
        + html.escape(str(value["code"]))
        + "</strong>: "
        + html.escape(str(value["title"]))
        + "</li>"
        for value in result.get("findings", [])
    )
    verdict = "通过" if result.get("passed") else "未通过"
    return (
        '<!doctype html><html><head><meta charset="utf-8"><title>完整性校验报告</title>'
        "</head><body><h1>完整性校验报告</h1>"
        f"<p>工作项: {html.escape(str(item.id))}</p>"
        f"<p>评估: {html.escape(str(evaluation.id))}</p>"
        f"<p>结论: {verdict}</p><ul>{rows}</ul></body></html>"
    )
