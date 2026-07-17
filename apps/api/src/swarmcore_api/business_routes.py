from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_application import CapabilityPackService, RuleSetService, WorkbenchService
from swarmcore_capability_contract_integrity import MANIFEST, REFERENCES, SCHEMAS
from swarmcore_governance import BlobCapabilityIssuer
from swarmcore_persistence.models import (
    Evaluation,
    Finding,
    RuleSetDraft,
    WorkItem,
    WorkItemRevision,
)
from swarmcore_registry import CapabilityReferenceCatalog

from .business_schemas import (
    AttachmentUploadHandle,
    CapabilityPackListResponse,
    CapabilityPackSnapshot,
    CompleteAttachmentRequest,
    CreateRuleSetRequest,
    CreateWorkItemRequest,
    EnableCapabilityPackRequest,
    EvaluationSnapshot,
    FindingActionRequest,
    FindingListResponse,
    FindingSnapshot,
    InitiateAttachmentRequest,
    ReportListResponse,
    ReportSnapshot,
    RuleSetDraftSnapshot,
    RuleSetValidationResponse,
    RuleSetVersionSnapshot,
    UpdateRuleSetDraftRequest,
    UpdateWorkItemRequest,
    ValidateRuleSetRequest,
    WorkItemListResponse,
    WorkItemSnapshot,
)
from .dependencies import (
    RequestScope,
    authorize_rest,
    db_session,
    request_scope,
    require_idempotency_key,
)

router = APIRouter(prefix="/v1", dependencies=[Depends(authorize_rest)])
capability_packs = CapabilityPackService(
    CapabilityReferenceCatalog.from_iterable(REFERENCES),
    trusted_manifests=(MANIFEST,),
)
rule_sets = RuleSetService()
workbench = WorkbenchService(capability_packs, schemas=SCHEMAS, rule_sets=rule_sets)

Scope = Annotated[RequestScope, Depends(request_scope)]
Session = Annotated[AsyncSession, Depends(db_session)]
IdempotencyKey = Annotated[str, Depends(require_idempotency_key)]


@router.get(
    "/projects/{project_id}/capability-packs",
    response_model=CapabilityPackListResponse,
)
async def list_capability_packs(
    scope: Scope, session: Session
) -> CapabilityPackListResponse:
    await capability_packs.ensure_trusted(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    rows = await capability_packs.list_project(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    return CapabilityPackListResponse(
        items=[
            CapabilityPackSnapshot(
                packId=pack.id,
                name=pack.name,
                versionId=version.id,
                version=version.version,
                contentHash=version.content_hash,
                manifest=version.manifest,
                enabled=binding is not None and binding.status == "ENABLED",
                bindingStatus=binding.status if binding is not None else None,
            )
            for pack, version, binding in rows
        ]
    )


@router.post(
    "/projects/{project_id}/capability-packs/{version_id}:enable",
    response_model=CapabilityPackSnapshot,
)
async def enable_capability_pack(
    version_id: UUID,
    body: EnableCapabilityPackRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> CapabilityPackSnapshot:
    await capability_packs.ensure_trusted(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    binding = await capability_packs.enable(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        version_id=version_id,
        configuration=body.configuration,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    rows = await capability_packs.list_project(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    pack, version, _ = next(row for row in rows if row[1].id == version_id)
    return CapabilityPackSnapshot(
        packId=pack.id,
        name=pack.name,
        versionId=version.id,
        version=version.version,
        contentHash=version.content_hash,
        manifest=version.manifest,
        enabled=True,
        bindingStatus=binding.status,
    )


@router.post(
    "/projects/{project_id}/capability-packs/{version_id}:disable",
    response_model=CapabilityPackSnapshot,
)
async def disable_capability_pack(
    version_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> CapabilityPackSnapshot:
    binding = await capability_packs.disable(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        version_id=version_id,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    rows = await capability_packs.list_project(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    pack, version, _ = next(row for row in rows if row[1].id == version_id)
    return CapabilityPackSnapshot(
        packId=pack.id,
        name=pack.name,
        versionId=version.id,
        version=version.version,
        contentHash=version.content_hash,
        manifest=version.manifest,
        enabled=False,
        bindingStatus=binding.status,
    )


@router.post(
    "/projects/{project_id}/work-items",
    response_model=WorkItemSnapshot,
    status_code=201,
)
async def create_work_item(
    body: CreateWorkItemRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> WorkItemSnapshot:
    item, revision = await workbench.create_work_item(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_item_type=body.work_item_type,
        payload=body.payload,
        owner=body.owner,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return _work_item_snapshot(item, revision)


@router.get(
    "/projects/{project_id}/work-items",
    response_model=WorkItemListResponse,
)
async def list_work_items(
    scope: Scope,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> WorkItemListResponse:
    items, total = await workbench.list_work_items(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        limit=limit,
        offset=offset,
    )
    snapshots: list[WorkItemSnapshot] = []
    for item in items:
        _, revision = await workbench.get_work_item(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            work_item_id=item.id,
        )
        snapshots.append(_work_item_snapshot(item, revision))
    return WorkItemListResponse(items=snapshots, total=total)


@router.get(
    "/projects/{project_id}/work-items/{work_item_id}",
    response_model=WorkItemSnapshot,
)
async def get_work_item(
    work_item_id: UUID, scope: Scope, session: Session
) -> WorkItemSnapshot:
    item, revision = await workbench.get_work_item(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_item_id=work_item_id,
    )
    return _work_item_snapshot(item, revision)


@router.put(
    "/projects/{project_id}/work-items/{work_item_id}",
    response_model=WorkItemSnapshot,
)
async def update_work_item(
    work_item_id: UUID,
    body: UpdateWorkItemRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
    if_match: Annotated[str, Header(alias="If-Match")],
) -> WorkItemSnapshot:
    item, revision = await workbench.update_work_item(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_item_id=work_item_id,
        payload=body.payload,
        owner=body.owner,
        expected_revision=_etag_revision(if_match),
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return _work_item_snapshot(item, revision)


@router.post(
    "/projects/{project_id}/work-items/{work_item_id}/attachments:initiate",
    response_model=AttachmentUploadHandle,
    status_code=201,
)
async def initiate_attachment(
    work_item_id: UUID,
    body: InitiateAttachmentRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
    request: Request,
) -> AttachmentUploadHandle:
    blob, attachment_id = await workbench.initiate_attachment(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_item_id=work_item_id,
        document_type=body.document_type,
        filename=body.filename,
        media_type=body.media_type,
        size_bytes=body.size_bytes,
        sha256=body.sha256,
        retention_days=body.retention_days,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    token = BlobCapabilityIssuer(
        request.app.state.settings.artifact_capability_secret.encode()
    ).issue(
        action="blob.write",
        tenant_id=str(scope.tenant_id),
        project_id=str(scope.project_id),
        blob_id=str(blob.id),
        subject_id=scope.actor_id,
    )
    return AttachmentUploadHandle(
        attachmentId=attachment_id,
        blobId=blob.id,
        uploadRef=f"/internal/v1/blobs/{blob.id}",
        capabilityToken=token,
        objectKey=blob.object_key,
        status=blob.status,
    )


@router.post(
    "/projects/{project_id}/attachments/{attachment_id}:complete",
    response_model=AttachmentUploadHandle,
)
async def complete_attachment(
    attachment_id: UUID,
    body: CompleteAttachmentRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> AttachmentUploadHandle:
    attachment = await workbench.complete_attachment(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        attachment_id=attachment_id,
        actual_sha256=body.sha256,
        scan_status=body.scan_status,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return AttachmentUploadHandle(
        attachmentId=attachment.id,
        blobId=attachment.blob_id,
        uploadRef=f"/internal/v1/blobs/{attachment.blob_id}",
        capabilityToken=None,
        objectKey="",
        status="AVAILABLE",
    )


@router.post(
    "/projects/{project_id}/work-items/{work_item_id}:execute",
    response_model=EvaluationSnapshot,
    status_code=202,
)
async def execute_work_item(
    work_item_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> EvaluationSnapshot:
    evaluation = await workbench.execute(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_item_id=work_item_id,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
        submitted_scopes=scope.scopes,
        auth_context_hash=scope.auth_context_hash,
    )
    return _evaluation_snapshot(evaluation)


@router.get(
    "/projects/{project_id}/evaluations/{evaluation_id}",
    response_model=EvaluationSnapshot,
)
async def get_evaluation(
    evaluation_id: UUID, scope: Scope, session: Session
) -> EvaluationSnapshot:
    return _evaluation_snapshot(
        await workbench.get_evaluation(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            evaluation_id=evaluation_id,
        )
    )


@router.get(
    "/projects/{project_id}/work-items/{work_item_id}/findings",
    response_model=FindingListResponse,
)
async def list_findings(
    work_item_id: UUID, scope: Scope, session: Session
) -> FindingListResponse:
    values = await workbench.list_findings(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_item_id=work_item_id,
    )
    return FindingListResponse(items=[_finding_snapshot(value) for value in values])


@router.post(
    "/projects/{project_id}/findings/{finding_id}:act",
    response_model=FindingSnapshot,
)
async def act_on_finding(
    finding_id: UUID,
    body: FindingActionRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> FindingSnapshot:
    value = await workbench.act_on_finding(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        finding_id=finding_id,
        action=body.action,
        reason=body.reason,
        assignee=body.assignee,
        expires_at=body.expires_at,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return _finding_snapshot(value)


@router.get(
    "/projects/{project_id}/evaluations/{evaluation_id}/reports",
    response_model=ReportListResponse,
)
async def list_reports(
    evaluation_id: UUID, scope: Scope, session: Session
) -> ReportListResponse:
    values = await workbench.list_reports(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        evaluation_id=evaluation_id,
    )
    return ReportListResponse(
        items=[
            ReportSnapshot(
                reportId=value.id,
                evaluationId=value.evaluation_id,
                format=value.format,
                templateVersion=value.template_version,
                resultSchemaVersion=value.result_schema_version,
                content=value.content,
                contentHash=value.content_hash,
                createdAt=value.created_at,
            )
            for value in values
        ]
    )


@router.post(
    "/projects/{project_id}/rule-sets",
    response_model=RuleSetDraftSnapshot,
    status_code=201,
)
async def create_rule_set(
    body: CreateRuleSetRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> RuleSetDraftSnapshot:
    value, draft = await rule_sets.create(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        name=body.name,
        purpose=body.purpose,
        rules=body.rules,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return RuleSetDraftSnapshot(
        ruleSetId=value.id, draftId=draft.id, revision=draft.revision, rules=draft.rules
    )


@router.put(
    "/projects/{project_id}/rule-set-drafts/{draft_id}",
    response_model=RuleSetDraftSnapshot,
)
async def update_rule_set_draft(
    draft_id: UUID,
    body: UpdateRuleSetDraftRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
    if_match: Annotated[str, Header(alias="If-Match")],
) -> RuleSetDraftSnapshot:
    draft = await rule_sets.update_draft(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        draft_id=draft_id,
        expected_revision=_etag_revision(if_match),
        rules=body.rules,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return RuleSetDraftSnapshot(
        ruleSetId=draft.rule_set_id,
        draftId=draft.id,
        revision=draft.revision,
        rules=draft.rules,
    )


@router.post(
    "/projects/{project_id}/rule-set-drafts/{draft_id}:validate",
    response_model=RuleSetValidationResponse,
)
async def validate_rule_set_draft(
    draft_id: UUID,
    body: ValidateRuleSetRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> RuleSetValidationResponse:
    del idempotency_key
    draft = await session.scalar(
        select(RuleSetDraft).where(
            RuleSetDraft.id == draft_id,
            RuleSetDraft.tenant_id == scope.tenant_id,
            RuleSetDraft.project_id == scope.project_id,
        )
    )
    if draft is None:
        raise LookupError("rule set draft not found")
    normalized, preview = rule_sets.validate(draft.rules, attachments=body.attachments)
    return RuleSetValidationResponse(
        valid=True,
        normalizedRules=normalized.model_dump(mode="json", by_alias=True),
        preview=preview.model_dump(mode="json", by_alias=True) if preview is not None else None,
    )


@router.post(
    "/projects/{project_id}/rule-set-drafts/{draft_id}:publish",
    response_model=RuleSetVersionSnapshot,
)
async def publish_rule_set_draft(
    draft_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> RuleSetVersionSnapshot:
    value = await rule_sets.publish(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        draft_id=draft_id,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return RuleSetVersionSnapshot(
        ruleSetId=value.rule_set_id,
        ruleSetVersionId=value.id,
        version=value.version,
        schemaVersion=value.schema_version,
        contentHash=value.content_hash,
        rules=value.rules,
    )


def _work_item_snapshot(item: WorkItem, revision: WorkItemRevision) -> WorkItemSnapshot:
    return WorkItemSnapshot(
        workItemId=item.id,
        workItemType=item.work_item_type,
        schemaVersion=item.schema_version,
        payload=item.payload,
        status=item.status,
        owner=item.owner,
        revisionId=revision.id,
        revision=revision.revision,
        payloadHash=revision.payload_hash,
        createdAt=item.created_at,
        updatedAt=item.updated_at,
    )


def _evaluation_snapshot(evaluation: Evaluation) -> EvaluationSnapshot:
    return EvaluationSnapshot(
        evaluationId=evaluation.id,
        workItemId=evaluation.work_item_id,
        workItemRevisionId=evaluation.work_item_revision_id,
        runId=evaluation.run_id,
        status=evaluation.status,
        result=evaluation.result,
        capabilityPackVersionId=evaluation.capability_pack_version_id,
        ruleSetVersionId=evaluation.rule_set_version_id,
        planHash=evaluation.plan_hash,
        attachmentManifestHash=evaluation.attachment_manifest_hash,
        registrySnapshot=evaluation.registry_snapshot,
        createdAt=evaluation.created_at,
    )


def _finding_snapshot(finding: Finding) -> FindingSnapshot:
    return FindingSnapshot(
        findingId=finding.id,
        workItemId=finding.work_item_id,
        evaluationId=finding.evaluation_id,
        ruleKey=finding.rule_key,
        code=finding.code,
        category=finding.category,
        severity=finding.severity,
        status=finding.status,
        title=finding.title,
        detail=finding.detail,
        evidence=finding.evidence,
    )


def _etag_revision(value: str) -> int:
    normalized = value.strip().strip('W/').strip('"')
    try:
        return int(normalized)
    except ValueError as exc:
        raise ValueError("If-Match must contain the current numeric revision") from exc
