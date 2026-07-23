from __future__ import annotations

import html
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
    Evaluation,
    Finding,
    FindingAction,
    IdempotencyKey,
    OutboxEvent,
    ProjectCapabilityDecisionBinding,
    Report,
    RuleSetVersion,
    Run,
    RunCommand,
    WorkItem,
    WorkItemAttachment,
    WorkItemRevision,
    WorkItemSubject,
)
from swarmcore_persistence.repositories import canonical_hash

from .capability_packs import CapabilityPackService
from .decision_assets import DecisionExecutionService, normalize_decision
from .document_library import DocumentLibraryService
from .integrity import AttachmentInput, IntegrityResult, IntegrityRuleDocument, evaluate_integrity
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
            {"workItemType": work_item_type, "payload": payload, "owner": owner}
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
        available_categories = {document.category for document, _, _ in document_versions}
        if any(
            requirement.required and requirement.category not in available_categories
            for requirement in manifest.spec.documents
        ):
            raise ValueError("DOCUMENT_SELECTION_REQUIRED")
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
        rule_version = None
        if manifest.spec.rules is not None:
            rule_version = await self._rule_sets.select_version(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                payload=revision.payload,
            )
        elif decision_bindings:
            rule_version = await session.get(
                RuleSetVersion, decision_bindings[0].rule_set_version_id
            )
            if rule_version is None or rule_version.status != "PUBLISHED":
                raise ValueError("DECISION_VERSION_NOT_PUBLISHED")
        evaluation_id = uuid7()
        input_data: dict[str, Any] = {
            "workItemId": str(item.id),
            "workItemRevisionId": str(revision.id),
            "evaluationId": str(evaluation_id),
            "payload": revision.payload,
            "attachments": [self._attachment_payload(value) for value in attachments],
            "documents": [
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
            ],
            "attachmentManifestHash": attachment_hash,
            "configuration": dict(binding.configuration),
        }
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
        self._validate_schema(manifest.spec.input_schema, input_data)
        strategy_snapshot = pack_version.dependency_snapshot.get("strategy", {})
        strategy_version_id = strategy_snapshot.get("strategyVersionId")
        if not isinstance(strategy_version_id, str):
            raise RuntimeError("capability pack strategy version snapshot is missing")
        run, command = await self._runs.create(
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
        frozen_decisions = [
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
            business_work_key=manifest.metadata.name,
            documents=document_versions,
        )
        if rule_version is not None and manifest.spec.rules is not None:
            result = evaluate_integrity(
                rule_set_version_id=str(rule_version.id),
                document=IntegrityRuleDocument.model_validate(rule_version.rules),
                attachments=[
                    AttachmentInput.model_validate(self._attachment_payload(value))
                    for value in attachments
                ],
                attachment_manifest_hash=attachment_hash,
            )
            await self._record_result(
                session,
                item=item,
                evaluation=evaluation,
                result=result,
                actor=actor,
            )
            await self._complete_inline_run(
                session,
                run=run,
                command=command,
                output=result.model_dump(mode="json", by_alias=True),
            )
        elif frozen_decisions:
            frozen = frozen_decisions[0]
            decision_version = await session.get(RuleSetVersion, frozen.rule_set_version_id)
            if decision_version is None:
                raise RuntimeError("frozen decision version is missing")
            envelope = normalize_decision(decision_version.rules)
            if envelope.type == "CHECKLIST":
                result = evaluate_integrity(
                    rule_set_version_id=str(decision_version.id),
                    document=IntegrityRuleDocument.model_validate(envelope.definition),
                    attachments=[
                        AttachmentInput.model_validate(self._attachment_payload(value))
                        for value in attachments
                    ],
                    attachment_manifest_hash=attachment_hash,
                )
                output = result.model_dump(mode="json", by_alias=True)
                await self._decision_executions.record(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    evaluation_decision_id=frozen.id,
                    execution_key=f"assessment:{evaluation.id}:{frozen.slot}",
                    attempt=1,
                    status="SUCCEEDED",
                    input_value=input_data,
                    output=output,
                    matched_rule_ids=[value.rule_key for value in result.findings],
                    duration_ms=0,
                    run_id=run.id,
                )
                await self._record_result(
                    session,
                    item=item,
                    evaluation=evaluation,
                    result=result,
                    actor=actor,
                )
                await self._complete_inline_run(session, run=run, command=command, output=output)
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

    async def _complete_inline_run(
        self,
        session: AsyncSession,
        *,
        run: Run,
        command: RunCommand,
        output: dict[str, Any],
    ) -> None:
        now = datetime.now(UTC)
        temporal_outbox = await session.scalar(
            select(OutboxEvent)
            .where(
                OutboxEvent.destination == "temporal",
                OutboxEvent.source_id == command.id,
            )
            .with_for_update()
        )
        if temporal_outbox is None:
            raise RuntimeError("inline run command outbox is missing")
        temporal_outbox.status = "DELIVERED"
        temporal_outbox.delivered_at = now
        temporal_outbox.locked_by = None
        temporal_outbox.locked_until = None
        command.status = "APPLIED"
        command.applied_at = now
        command.result = {"mode": "inline"}
        for event_type, payload in (
            ("run.validating", {}),
            ("run.queued", {}),
            ("run.started", {}),
            ("run.completed", {"output": output}),
        ):
            await self._runs.events.append(
                session,
                tenant_id=run.tenant_id,
                project_id=run.project_id,
                run_id=run.id,
                transition_id=uuid7(),
                event_type=event_type,
                payload=payload,
                occurred_at=now,
            )
        run.output = output

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

    def _validate_schema(self, schema_ref: str, value: dict[str, Any]) -> None:
        schema = self._schemas.get(schema_ref)
        if schema is not None:
            Draft202012Validator(schema).validate(value)

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
    if pack_name == "contract-post-evaluation":
        return (
            pack_name,
            work_item_type,
            "document-integrity",
            "performance-plan-collection",
            "invoice-assurance",
            "deviation-analysis",
            "procurement-supplier-risk",
            "report-generation",
        )
    return (pack_name, work_item_type)


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
