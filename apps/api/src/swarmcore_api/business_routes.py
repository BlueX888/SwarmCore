from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_application import (
    BusinessObjectService,
    CapabilityBindingService,
    CapabilityPackReadinessError,
    CapabilityPackService,
    CaseService,
    CaseSubjectInput,
    ConnectionService,
    DecisionAssetService,
    DecisionExecutionService,
    DocumentLibraryService,
    ResourceCatalogService,
    RuleSetService,
    WorkbenchService,
)
from swarmcore_capability_contract_integrity import (
    MANIFEST,
    MANIFEST_V2,
    REFERENCES,
    SCHEMAS,
    STRATEGIES,
)
from swarmcore_capability_contract_post_evaluation import (
    MANIFEST as POST_EVALUATION_MANIFEST,
)
from swarmcore_capability_contract_post_evaluation import (
    REFERENCES as POST_EVALUATION_REFERENCES,
)
from swarmcore_capability_contract_post_evaluation import (
    SCHEMAS as POST_EVALUATION_SCHEMAS,
)
from swarmcore_capability_contract_post_evaluation import (
    STRATEGIES as POST_EVALUATION_STRATEGIES,
)
from swarmcore_governance import BlobCapabilityIssuer
from swarmcore_persistence.models import (
    BusinessDocument,
    BusinessDocumentVersion,
    CapabilityPack,
    CapabilityPackVersion,
    CapabilityResourceBinding,
    Connection,
    ConnectionVersion,
    DecisionExecution,
    DocumentUsageSnapshot,
    Evaluation,
    EvaluationDecision,
    Finding,
    ProjectCapabilityBinding,
    ProjectCapabilityDecisionBinding,
    ResourceDefinition,
    ResourceSnapshot,
    RuleSetDraft,
    RuleSetVersion,
    WorkItem,
    WorkItemRevision,
)
from swarmcore_registry import CapabilityReferenceCatalog

from .business_schemas import (
    AttachmentUploadHandle,
    BindDecisionRequest,
    BindResourceRequest,
    CapabilityPackListResponse,
    CapabilityPackSnapshot,
    CompleteAttachmentRequest,
    CompleteDocumentUploadRequest,
    CreateBusinessObjectRelationRequest,
    CreateBusinessObjectRequest,
    CreateBusinessObjectVersionRequest,
    CreateCapabilityPackRequest,
    CreateCaseRequest,
    CreateConnectionRequest,
    CreateConnectionVersionRequest,
    CreateDecisionAssetRequest,
    CreateResourceRequest,
    CreateRuleSetRequest,
    CreateWorkItemRequest,
    DocumentListResponse,
    DocumentSnapshot,
    DocumentUploadHandle,
    DocumentVersionSnapshot,
    EnableCapabilityPackRequest,
    EvaluationSnapshot,
    FindingActionRequest,
    FindingListResponse,
    FindingSnapshot,
    InitiateAttachmentRequest,
    InitiateDocumentRequest,
    ReportListResponse,
    ReportSnapshot,
    RuleSetDraftSnapshot,
    RuleSetValidationResponse,
    RuleSetVersionSnapshot,
    UpdateCaseRequest,
    UpdateDecisionDraftRequest,
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
    CapabilityReferenceCatalog.from_iterable((*REFERENCES, *POST_EVALUATION_REFERENCES)),
    trusted_manifests=(MANIFEST, MANIFEST_V2, POST_EVALUATION_MANIFEST),
    trusted_strategies={**STRATEGIES, **POST_EVALUATION_STRATEGIES},
)
rule_sets = RuleSetService()
workbench = WorkbenchService(
    capability_packs,
    schemas={**SCHEMAS, **POST_EVALUATION_SCHEMAS},
    rule_sets=rule_sets,
)
business_objects = BusinessObjectService()
cases = CaseService(workbench, capability_packs)
decision_assets = DecisionAssetService()
decision_executions = DecisionExecutionService()
connections = ConnectionService()
resources = ResourceCatalogService()
bindings = CapabilityBindingService()
documents = DocumentLibraryService()

Scope = Annotated[RequestScope, Depends(request_scope)]
Session = Annotated[AsyncSession, Depends(db_session)]
IdempotencyKey = Annotated[str, Depends(require_idempotency_key)]


def _pack_snapshot(
    pack: CapabilityPack,
    version: CapabilityPackVersion,
    *,
    enabled: bool,
    binding_status: str | None,
    configuration: dict[str, Any] | None = None,
    blockers: list[dict[str, Any]] | None = None,
) -> CapabilityPackSnapshot:
    return CapabilityPackSnapshot(
        packId=pack.id,
        name=pack.name,
        versionId=version.id,
        version=version.version,
        contentHash=version.content_hash,
        manifest=version.manifest,
        enabled=enabled,
        bindingStatus=binding_status,
        configuration=configuration or {},
        blockers=blockers or [],
    )


@router.get(
    "/projects/{project_id}/capability-packs",
    response_model=CapabilityPackListResponse,
)
async def list_capability_packs(scope: Scope, session: Session) -> CapabilityPackListResponse:
    await capability_packs.ensure_trusted(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    rows = await capability_packs.list_project(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    version_ids = [version.id for _, version, _ in rows]
    evaluated_version_ids = set(
        await session.scalars(
            select(Evaluation.capability_pack_version_id).where(
                Evaluation.tenant_id == scope.tenant_id,
                Evaluation.capability_pack_version_id.in_(version_ids),
            )
        )
    ) if version_ids else set()
    items: list[CapabilityPackSnapshot] = []
    for pack, version, binding in rows:
        blockers = await capability_packs.blockers_for_version(
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            version=version,
            session=session,
        )
        enabled = binding is not None and binding.status in {"ENABLED", "DEGRADED"}
        delete_blocker = capability_packs.deletion_blocker(
            pack_name=pack.name,
            version=version.version,
            enabled=enabled,
            has_evaluations=version.id in evaluated_version_ids,
        )
        items.append(
            CapabilityPackSnapshot(
                packId=pack.id,
                name=pack.name,
                versionId=version.id,
                version=version.version,
                contentHash=version.content_hash,
                manifest=version.manifest,
                enabled=enabled,
                bindingStatus=binding.status if binding is not None else None,
                configuration=dict(binding.configuration) if binding is not None else {},
                blockers=blockers,
                deleteBlockedReason=delete_blocker[1] if delete_blocker is not None else None,
            )
        )
    return CapabilityPackListResponse(items=items)


@router.post(
    "/projects/{project_id}/capability-packs",
    response_model=CapabilityPackSnapshot,
    status_code=201,
)
async def create_capability_pack(
    body: CreateCapabilityPackRequest,
    scope: Scope,
    session: Session,
) -> CapabilityPackSnapshot:
    await capability_packs.ensure_trusted(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    version = await capability_packs.publish(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        manifest=body.manifest,
        strategy_version_id=body.strategy_version_id,
        actor=scope.actor_id,
    )
    rows = await capability_packs.list_project(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    pack, _, binding = next(row for row in rows if row[1].id == version.id)
    blockers = await capability_packs.blockers_for_version(
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        version=version,
        session=session,
    )
    return _pack_snapshot(
        pack,
        version,
        enabled=binding is not None and binding.status in {"ENABLED", "DEGRADED"},
        binding_status=binding.status if binding is not None else None,
        configuration=dict(binding.configuration) if binding is not None else {},
        blockers=blockers,
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
) -> CapabilityPackSnapshot | JSONResponse:
    await capability_packs.ensure_trusted(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    try:
        binding = await capability_packs.enable(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            version_id=version_id,
            configuration=body.configuration,
            idempotency_key=idempotency_key,
            actor=scope.actor_id,
        )
    except CapabilityPackReadinessError as exc:
        return JSONResponse(
            status_code=409,
            content={
                "title": "Capability Pack Not Ready",
                "status": 409,
                "code": "CAPABILITY_PACK_NOT_READY",
                "detail": str(exc),
                "blockers": exc.blockers,
            },
            media_type="application/problem+json",
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
        configuration=dict(binding.configuration),
        blockers=[],
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
        configuration=dict(binding.configuration),
        blockers=[],
    )


@router.delete(
    "/projects/{project_id}/capability-packs/{version_id}",
    status_code=204,
)
async def delete_capability_pack(
    version_id: UUID,
    scope: Scope,
    session: Session,
) -> Response:
    await capability_packs.delete_version(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        version_id=version_id,
        actor=scope.actor_id,
    )
    return Response(status_code=204)


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
async def get_work_item(work_item_id: UUID, scope: Scope, session: Session) -> WorkItemSnapshot:
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


def _document_version_snapshot(value: BusinessDocumentVersion) -> DocumentVersionSnapshot:
    return DocumentVersionSnapshot(
        documentVersionId=value.id,
        blobId=value.blob_id,
        version=value.version,
        filename=value.filename,
        mediaType=value.media_type,
        sizeBytes=value.size_bytes,
        sha256=value.sha256,
        processingStatus=value.processing_status,
        createdAt=value.created_at,
    )


def _document_snapshot(
    value: BusinessDocument,
    *,
    current: BusinessDocumentVersion | None = None,
    versions: list[BusinessDocumentVersion] | None = None,
    business_object_ids: list[UUID] | None = None,
    business_work_keys: list[str] | None = None,
) -> DocumentSnapshot:
    return DocumentSnapshot(
        documentId=value.id,
        name=value.name,
        category=value.category,
        tags=list(value.tags),
        status=value.status,
        currentVersion=value.current_version,
        updatedAt=value.updated_at,
        current=_document_version_snapshot(current) if current is not None else None,
        versions=[_document_version_snapshot(item) for item in versions or []],
        businessObjectIds=business_object_ids or [],
        businessWorkKeys=business_work_keys or [],
    )


@router.post(
    "/projects/{project_id}/documents:initiate",
    response_model=DocumentUploadHandle,
    status_code=201,
)
async def initiate_document(
    body: InitiateDocumentRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
    request: Request,
) -> DocumentUploadHandle:
    document, blob, upload_id, version = await documents.initiate(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        name=body.name,
        category=body.category,
        tags=body.tags,
        filename=body.filename,
        media_type=body.media_type,
        size_bytes=body.size_bytes,
        sha256=body.sha256,
        business_object_ids=body.business_object_ids,
        business_work_keys=body.business_work_keys,
        retention_days=body.retention_days,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
        document_id=body.document_id,
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
    return DocumentUploadHandle(
        documentId=document.id,
        uploadId=upload_id,
        blobId=blob.id,
        version=version,
        uploadRef=f"/internal/v1/blobs/{blob.id}",
        capabilityToken=token,
        status=blob.status,
    )


@router.post(
    "/projects/{project_id}/document-uploads/{upload_id}:complete",
    response_model=DocumentSnapshot,
)
async def complete_document(
    upload_id: UUID,
    body: CompleteDocumentUploadRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> DocumentSnapshot:
    document, version = await documents.complete(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        upload_id=upload_id,
        sha256=body.sha256,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    _, versions, object_links, work_bindings = await documents.details(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document.id,
    )
    return _document_snapshot(
        document,
        current=version,
        versions=versions,
        business_object_ids=[value.business_object_id for value in object_links],
        business_work_keys=[value.business_work_key for value in work_bindings],
    )


@router.get(
    "/projects/{project_id}/documents",
    response_model=DocumentListResponse,
)
async def list_documents(
    scope: Scope,
    session: Session,
    search: str | None = Query(default=None, max_length=256),
    category: str | None = Query(default=None, max_length=128),
    status: str | None = Query(default=None, max_length=32),
) -> DocumentListResponse:
    values = await documents.list_documents(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        search=search,
        category=category,
        status=status,
    )
    items: list[DocumentSnapshot] = []
    for document, version in values:
        _, _, object_links, work_bindings = await documents.details(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            document_id=document.id,
        )
        items.append(
            _document_snapshot(
                document,
                current=version,
                business_object_ids=[value.business_object_id for value in object_links],
                business_work_keys=[value.business_work_key for value in work_bindings],
            )
        )
    return DocumentListResponse(items=items)


@router.get(
    "/projects/{project_id}/documents/{document_id}",
    response_model=DocumentSnapshot,
)
async def get_document(
    document_id: UUID,
    scope: Scope,
    session: Session,
) -> DocumentSnapshot:
    document, versions, object_links, work_bindings = await documents.details(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
    )
    current = next(
        (value for value in versions if value.version == document.current_version),
        None,
    )
    return _document_snapshot(
        document,
        current=current,
        versions=versions,
        business_object_ids=[value.business_object_id for value in object_links],
        business_work_keys=[value.business_work_key for value in work_bindings],
    )


@router.post(
    "/projects/{project_id}/documents/{document_id}/versions/{version}:download",
)
async def download_document_version(
    document_id: UUID,
    version: int,
    scope: Scope,
    session: Session,
    request: Request,
) -> dict[str, Any]:
    document, versions, _, _ = await documents.details(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
    )
    selected = next((value for value in versions if value.version == version), None)
    if selected is None:
        raise LookupError("DOCUMENT_VERSION_NOT_FOUND")
    token = BlobCapabilityIssuer(
        request.app.state.settings.artifact_capability_secret.encode()
    ).issue(
        action="blob.read",
        tenant_id=str(scope.tenant_id),
        project_id=str(scope.project_id),
        blob_id=str(selected.blob_id),
        subject_id=scope.actor_id,
    )
    return {
        "documentId": document.id,
        "documentVersionId": selected.id,
        "filename": selected.filename,
        "mediaType": selected.media_type,
        "downloadRef": f"/internal/v1/blobs/{selected.blob_id}/content",
        "capabilityToken": token,
    }


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
async def get_evaluation(evaluation_id: UUID, scope: Scope, session: Session) -> EvaluationSnapshot:
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
async def list_findings(work_item_id: UUID, scope: Scope, session: Session) -> FindingListResponse:
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
async def list_reports(evaluation_id: UUID, scope: Scope, session: Session) -> ReportListResponse:
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
    normalized = value.strip().strip("W/").strip('"')
    try:
        return int(normalized)
    except ValueError as exc:
        raise ValueError("If-Match must contain the current numeric revision") from exc


def _business_object_snapshot(value: Any, version: Any) -> dict[str, Any]:
    return {
        "businessObjectId": value.id,
        "objectType": value.object_type,
        "canonicalKey": value.canonical_key,
        "lifecycle": value.lifecycle,
        "currentVersion": value.current_version,
        "versionId": version.id,
        "version": version.version,
        "schemaRef": version.schema_ref,
        "data": version.data,
        "dataHash": version.data_hash,
        "provenance": version.provenance,
        "effectiveAt": version.effective_at,
        "recordedAt": version.recorded_at,
    }


def _case_snapshot(
    item: WorkItem, revision: WorkItemRevision, subjects: list[Any]
) -> dict[str, Any]:
    return {
        "caseId": item.id,
        "scenarioType": item.work_item_type,
        "caseRevisionId": revision.id,
        "revision": revision.revision,
        "payload": revision.payload,
        "payloadHash": revision.payload_hash,
        "status": item.status,
        "owner": item.owner,
        "subjects": [
            {
                "businessObjectId": value.business_object_id,
                "businessObjectVersionId": value.business_object_version_id,
                "role": value.role,
                "subjectKey": value.subject_key,
            }
            for value in subjects
        ],
        "createdAt": item.created_at,
        "updatedAt": item.updated_at,
    }


@router.post("/projects/{project_id}/business-objects", status_code=201)
async def create_business_object(
    body: CreateBusinessObjectRequest,
    scope: Scope,
    session: Session,
) -> dict[str, Any]:
    value, version, _ = await business_objects.upsert(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        object_type=body.object_type,
        canonical_key=body.canonical_key,
        schema_ref=body.schema_ref,
        data=body.data,
        provenance=body.provenance,
        effective_at=body.effective_at,
        actor=scope.actor_id,
    )
    return _business_object_snapshot(value, version)


@router.get("/projects/{project_id}/business-objects")
async def list_business_objects(
    scope: Scope,
    session: Session,
    object_type: Annotated[str | None, Query(alias="objectType")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    values = await business_objects.list_objects(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        object_type=object_type,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [
            {
                "businessObjectId": value.id,
                "objectType": value.object_type,
                "canonicalKey": value.canonical_key,
                "lifecycle": value.lifecycle,
                "currentVersion": value.current_version,
                "updatedAt": value.updated_at,
            }
            for value in values
        ]
    }


@router.get("/projects/{project_id}/business-objects/{object_id}")
async def get_business_object(object_id: UUID, scope: Scope, session: Session) -> dict[str, Any]:
    value, version = await business_objects.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        object_id=object_id,
    )
    return _business_object_snapshot(value, version)


@router.post("/projects/{project_id}/business-objects/{object_id}/versions", status_code=201)
async def create_business_object_version(
    object_id: UUID,
    body: CreateBusinessObjectVersionRequest,
    scope: Scope,
    session: Session,
) -> dict[str, Any]:
    version, created = await business_objects.add_version(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        object_id=object_id,
        schema_ref=body.schema_ref,
        data=body.data,
        provenance=body.provenance,
        effective_at=body.effective_at,
        actor=scope.actor_id,
    )
    return {
        "businessObjectId": object_id,
        "versionId": version.id,
        "version": version.version,
        "dataHash": version.data_hash,
        "created": created,
    }


@router.post("/projects/{project_id}/business-object-relations", status_code=201)
async def create_business_object_relation(
    body: CreateBusinessObjectRelationRequest,
    scope: Scope,
    session: Session,
) -> dict[str, Any]:
    value = await business_objects.assert_relation(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        source_object_id=body.source_object_id,
        source_version_id=body.source_version_id,
        target_object_id=body.target_object_id,
        target_version_id=body.target_version_id,
        relation_type=body.relation_type,
        assertion_state=body.assertion_state,
        evidence=body.evidence,
        supersedes_relation_id=body.supersedes_relation_id,
        actor=scope.actor_id,
    )
    return {"relationId": value.id, "contentHash": value.content_hash}


@router.get("/projects/{project_id}/business-objects/{object_id}/relations")
async def list_business_object_relations(
    object_id: UUID, scope: Scope, session: Session
) -> dict[str, Any]:
    values = await business_objects.list_relations(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        object_id=object_id,
    )
    return {
        "items": [
            {
                "relationId": value.id,
                "sourceObjectId": value.source_object_id,
                "sourceVersionId": value.source_version_id,
                "targetObjectId": value.target_object_id,
                "targetVersionId": value.target_version_id,
                "relationType": value.relation_type,
                "assertionState": value.assertion_state,
                "evidence": value.evidence,
                "contentHash": value.content_hash,
            }
            for value in values
        ]
    }


@router.post("/projects/{project_id}/cases", status_code=201)
async def create_case(
    body: CreateCaseRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> dict[str, Any]:
    item, revision, subjects = await cases.create(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        scenario_type=body.scenario_type,
        payload=body.payload,
        subjects=[
            CaseSubjectInput(
                business_object_id=value.business_object_id,
                business_object_version_id=value.business_object_version_id,
                role=value.role,
                subject_key=value.subject_key,
            )
            for value in body.subjects
        ],
        owner=body.owner,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return _case_snapshot(item, revision, subjects)


@router.get("/projects/{project_id}/cases")
async def list_cases(
    scope: Scope,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    values, total = await cases.list_cases(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [
            {
                "caseId": value.id,
                "scenarioType": value.work_item_type,
                "status": value.status,
                "revision": value.revision_number,
                "owner": value.owner,
                "updatedAt": value.updated_at,
            }
            for value in values
        ],
        "total": total,
    }


@router.get("/projects/{project_id}/cases/{case_id}")
async def get_case(case_id: UUID, scope: Scope, session: Session) -> dict[str, Any]:
    item, revision, subjects = await cases.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
    )
    return _case_snapshot(item, revision, subjects)


@router.patch("/projects/{project_id}/cases/{case_id}")
async def update_case(
    case_id: UUID,
    body: UpdateCaseRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
    if_match: Annotated[str, Header(alias="If-Match")],
) -> dict[str, Any]:
    item, revision, subjects = await cases.revise(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
        payload=body.payload,
        subjects=(
            [
                CaseSubjectInput(
                    business_object_id=value.business_object_id,
                    business_object_version_id=value.business_object_version_id,
                    role=value.role,
                    subject_key=value.subject_key,
                )
                for value in body.subjects
            ]
            if body.subjects is not None
            else None
        ),
        owner=body.owner,
        expected_revision=_etag_revision(if_match),
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return _case_snapshot(item, revision, subjects)


@router.post("/projects/{project_id}/cases/{case_id}:assess", status_code=202)
async def assess_case(
    case_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> EvaluationSnapshot:
    evaluation = await cases.assess(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
        submitted_scopes=scope.scopes,
        auth_context_hash=scope.auth_context_hash,
    )
    return _evaluation_snapshot(evaluation)


@router.get("/projects/{project_id}/cases/{case_id}/assessments")
async def list_case_assessments(case_id: UUID, scope: Scope, session: Session) -> dict[str, Any]:
    values = list(
        await session.scalars(
            select(Evaluation)
            .where(
                Evaluation.tenant_id == scope.tenant_id,
                Evaluation.project_id == scope.project_id,
                Evaluation.work_item_id == case_id,
            )
            .order_by(Evaluation.created_at.desc())
        )
    )
    return {"items": [_evaluation_snapshot(value) for value in values]}


@router.get("/projects/{project_id}/cases/{case_id}/findings")
async def list_case_findings(case_id: UUID, scope: Scope, session: Session) -> FindingListResponse:
    values = await workbench.list_findings(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_item_id=case_id,
    )
    return FindingListResponse(items=[_finding_snapshot(value) for value in values])


@router.post("/projects/{project_id}/decision-assets", status_code=201)
async def create_decision_asset(
    body: CreateDecisionAssetRequest, scope: Scope, session: Session
) -> dict[str, Any]:
    asset, draft = await decision_assets.create(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        name=body.name,
        purpose=body.purpose,
        definition=body.definition,
        actor=scope.actor_id,
    )
    return {
        "decisionAssetId": asset.id,
        "draftId": draft.id,
        "revision": draft.revision,
        "definition": draft.rules,
    }


@router.patch("/projects/{project_id}/decision-assets/{asset_id}/draft")
async def update_decision_asset_draft(
    asset_id: UUID,
    body: UpdateDecisionDraftRequest,
    scope: Scope,
    session: Session,
) -> dict[str, Any]:
    envelope = decision_assets.validate(body.definition)
    draft = await session.scalar(
        select(RuleSetDraft)
        .where(
            RuleSetDraft.rule_set_id == asset_id,
            RuleSetDraft.tenant_id == scope.tenant_id,
            RuleSetDraft.project_id == scope.project_id,
        )
        .with_for_update()
    )
    if draft is None:
        raise LookupError("DECISION_ASSET_NOT_FOUND")
    if draft.revision != body.expected_revision:
        raise ValueError("CASE_REVISION_CONFLICT")
    draft.rules = envelope.model_dump(mode="json", by_alias=True)
    draft.revision += 1
    draft.updated_by = scope.actor_id
    await session.flush()
    return {"decisionAssetId": asset_id, "draftId": draft.id, "revision": draft.revision}


@router.post("/projects/{project_id}/decision-assets/{asset_id}/draft:validate")
async def validate_decision_asset_draft(
    asset_id: UUID, scope: Scope, session: Session
) -> dict[str, Any]:
    draft = await session.scalar(
        select(RuleSetDraft).where(
            RuleSetDraft.rule_set_id == asset_id,
            RuleSetDraft.tenant_id == scope.tenant_id,
            RuleSetDraft.project_id == scope.project_id,
        )
    )
    if draft is None:
        raise LookupError("DECISION_ASSET_NOT_FOUND")
    envelope = decision_assets.validate(draft.rules)
    return {"valid": True, "normalizedDefinition": envelope.model_dump(mode="json", by_alias=True)}


@router.post("/projects/{project_id}/decision-assets/{asset_id}/draft:publish", status_code=201)
async def publish_decision_asset_draft(
    asset_id: UUID, scope: Scope, session: Session
) -> dict[str, Any]:
    draft = await session.scalar(
        select(RuleSetDraft).where(
            RuleSetDraft.rule_set_id == asset_id,
            RuleSetDraft.tenant_id == scope.tenant_id,
            RuleSetDraft.project_id == scope.project_id,
        )
    )
    if draft is None:
        raise LookupError("DECISION_ASSET_NOT_FOUND")
    version = await decision_assets.publish(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        draft_id=draft.id,
        actor=scope.actor_id,
    )
    return {
        "decisionAssetId": asset_id,
        "decisionVersionId": version.id,
        "version": version.version,
        "contentHash": version.content_hash,
    }


@router.get("/projects/{project_id}/decision-assets/{asset_id}/versions")
async def list_decision_asset_versions(
    asset_id: UUID, scope: Scope, session: Session
) -> dict[str, Any]:
    values = list(
        await session.scalars(
            select(RuleSetVersion)
            .where(
                RuleSetVersion.rule_set_id == asset_id,
                RuleSetVersion.tenant_id == scope.tenant_id,
                RuleSetVersion.project_id == scope.project_id,
            )
            .order_by(RuleSetVersion.version.desc())
        )
    )
    return {
        "items": [
            {
                "decisionVersionId": value.id,
                "version": value.version,
                "contentHash": value.content_hash,
                "definition": value.rules,
            }
            for value in values
        ]
    }


@router.post("/projects/{project_id}/connections", status_code=201)
async def create_connection(
    body: CreateConnectionRequest, scope: Scope, session: Session
) -> dict[str, Any]:
    connection, version = await connections.create(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        name=body.name,
        connector_ref=body.connector_ref,
        configuration=body.configuration,
        credential_ref=body.credential_ref,
        policy_ref=body.policy_ref,
        actor=scope.actor_id,
    )
    return _connection_snapshot(connection, version)


def _connection_snapshot(connection: Connection, version: ConnectionVersion) -> dict[str, Any]:
    return {
        "connectionId": connection.id,
        "name": connection.name,
        "connectorRef": connection.connector_ref,
        "lifecycle": connection.lifecycle,
        "currentVersion": connection.current_version,
        "connectionVersionId": version.id,
        "configuration": version.configuration,
        "credentialConfigured": bool(version.credential_ref),
        "policyRef": version.policy_ref,
        "configurationHash": version.configuration_hash,
    }


@router.get("/projects/{project_id}/connections")
async def list_connections(scope: Scope, session: Session) -> dict[str, Any]:
    values = await connections.list(session, tenant_id=scope.tenant_id, project_id=scope.project_id)
    return {
        "items": [
            {
                "connectionId": value.id,
                "name": value.name,
                "connectorRef": value.connector_ref,
                "lifecycle": value.lifecycle,
                "currentVersion": value.current_version,
            }
            for value in values
        ]
    }


@router.get("/projects/{project_id}/connections/{connection_id}")
async def get_connection(connection_id: UUID, scope: Scope, session: Session) -> dict[str, Any]:
    connection, version = await connections.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        connection_id=connection_id,
    )
    return _connection_snapshot(connection, version)


@router.post("/projects/{project_id}/connections/{connection_id}/versions", status_code=201)
async def create_connection_version(
    connection_id: UUID,
    body: CreateConnectionVersionRequest,
    scope: Scope,
    session: Session,
) -> dict[str, Any]:
    version, created = await connections.add_version(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        connection_id=connection_id,
        configuration=body.configuration,
        credential_ref=body.credential_ref,
        policy_ref=body.policy_ref,
        actor=scope.actor_id,
    )
    return {
        "connectionVersionId": version.id,
        "version": version.version,
        "configurationHash": version.configuration_hash,
        "created": created,
    }


@router.post("/projects/{project_id}/connections/{connection_id}:test", status_code=202)
async def test_connection(
    connection_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> dict[str, Any]:
    command_id, version = await connections.queue_health_check(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        connection_id=connection_id,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return {
        "status": "ACCEPTED",
        "commandId": command_id,
        "connectionVersionId": version.id,
        "command": "connection.health-check",
    }


@router.post("/projects/{project_id}/resources", status_code=201)
async def create_resource(
    body: CreateResourceRequest, scope: Scope, session: Session
) -> dict[str, Any]:
    value = await resources.create(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        connection_id=body.connection_id,
        resource_kind=body.resource_kind,
        name=body.name,
        locator=body.locator,
        schema_ref=body.schema_ref,
        media_type=body.media_type,
        sensitivity=body.sensitivity,
        actor=scope.actor_id,
    )
    return _resource_snapshot(value)


def _resource_snapshot(value: ResourceDefinition) -> dict[str, Any]:
    return {
        "resourceId": value.id,
        "connectionId": value.connection_id,
        "resourceKind": value.resource_kind,
        "name": value.name,
        "locator": value.locator,
        "schemaRef": value.schema_ref,
        "mediaType": value.media_type,
        "sensitivity": value.sensitivity,
        "lifecycle": value.lifecycle,
    }


@router.get("/projects/{project_id}/resources")
async def list_resources(scope: Scope, session: Session) -> dict[str, Any]:
    values = await resources.list(session, tenant_id=scope.tenant_id, project_id=scope.project_id)
    return {"items": [_resource_snapshot(value) for value in values]}


@router.get("/projects/{project_id}/resources/{resource_id}")
async def get_resource(resource_id: UUID, scope: Scope, session: Session) -> dict[str, Any]:
    value = await session.scalar(
        select(ResourceDefinition).where(
            ResourceDefinition.id == resource_id,
            ResourceDefinition.tenant_id == scope.tenant_id,
            ResourceDefinition.project_id == scope.project_id,
        )
    )
    if value is None:
        raise LookupError("RESOURCE_NOT_FOUND")
    return _resource_snapshot(value)


async def _project_pack_binding(
    session: AsyncSession, scope: RequestScope, version_id: UUID
) -> ProjectCapabilityBinding:
    version = await session.scalar(
        select(CapabilityPackVersion).where(
            CapabilityPackVersion.id == version_id,
            CapabilityPackVersion.tenant_id == scope.tenant_id,
        )
    )
    if version is None:
        raise LookupError("CAPABILITY_PACK_NOT_FOUND")
    value = await session.scalar(
        select(ProjectCapabilityBinding).where(
            ProjectCapabilityBinding.pack_id == version.pack_id,
            ProjectCapabilityBinding.tenant_id == scope.tenant_id,
            ProjectCapabilityBinding.project_id == scope.project_id,
        )
    )
    if value is None:
        value = ProjectCapabilityBinding(
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            pack_id=version.pack_id,
            pack_version_id=version.id,
            status="DISABLED",
            configuration={},
            enabled_by=scope.actor_id,
        )
        session.add(value)
        await session.flush()
    return value


@router.put("/projects/{project_id}/capability-packs/{version_id}/decision-bindings/{slot}")
async def bind_decision(
    version_id: UUID, slot: str, body: BindDecisionRequest, scope: Scope, session: Session
) -> dict[str, Any]:
    pack_binding = await _project_pack_binding(session, scope, version_id)
    value = await decision_executions.bind(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        project_capability_binding_id=pack_binding.id,
        slot=slot,
        rule_set_version_id=body.rule_set_version_id,
        actor=scope.actor_id,
    )
    return {
        "bindingId": value.id,
        "slot": value.slot,
        "decisionVersionId": value.rule_set_version_id,
        "contentHash": value.content_hash,
    }


@router.put("/projects/{project_id}/capability-packs/{version_id}/resource-bindings/{slot}")
async def bind_resource(
    version_id: UUID, slot: str, body: BindResourceRequest, scope: Scope, session: Session
) -> dict[str, Any]:
    pack_binding = await _project_pack_binding(session, scope, version_id)
    value = await bindings.bind_resource(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        project_capability_binding_id=pack_binding.id,
        slot=slot,
        resource_definition_id=body.resource_definition_id,
        access_mode=body.access_mode,
        mapping_configuration=body.mapping_configuration,
        capability_pack_version_id=version_id,
        actor=scope.actor_id,
    )
    return {
        "bindingId": value.id,
        "slot": value.slot,
        "resourceId": value.resource_definition_id,
        "accessMode": value.access_mode,
    }


@router.get("/projects/{project_id}/capability-packs/{version_id}/bindings")
async def get_pack_bindings(version_id: UUID, scope: Scope, session: Session) -> dict[str, Any]:
    pack_binding = await _project_pack_binding(session, scope, version_id)
    decisions = list(
        await session.scalars(
            select(ProjectCapabilityDecisionBinding).where(
                ProjectCapabilityDecisionBinding.project_capability_binding_id == pack_binding.id
            )
        )
    )
    resource_values = list(
        await session.scalars(
            select(CapabilityResourceBinding).where(
                CapabilityResourceBinding.project_capability_binding_id == pack_binding.id
            )
        )
    )
    return {
        "decisions": [
            {
                "slot": value.slot,
                "decisionVersionId": value.rule_set_version_id,
                "contentHash": value.content_hash,
            }
            for value in decisions
        ],
        "resources": [
            {
                "slot": value.slot,
                "resourceId": value.resource_definition_id,
                "accessMode": value.access_mode,
            }
            for value in resource_values
        ],
    }


@router.get("/projects/{project_id}/assessments/{assessment_id}/resource-snapshots")
async def list_resource_snapshots(
    assessment_id: UUID, scope: Scope, session: Session
) -> dict[str, Any]:
    values = list(
        await session.scalars(
            select(ResourceSnapshot)
            .where(
                ResourceSnapshot.evaluation_id == assessment_id,
                ResourceSnapshot.tenant_id == scope.tenant_id,
                ResourceSnapshot.project_id == scope.project_id,
            )
            .order_by(ResourceSnapshot.retrieved_at)
        )
    )
    return {
        "items": [
            {
                "resourceSnapshotId": value.id,
                "slot": value.slot,
                "resourceId": value.resource_definition_id,
                "connectionVersionId": value.connection_version_id,
                "snapshotKey": value.snapshot_key,
                "direction": value.direction,
                "observedVersion": value.observed_version,
                "etag": value.etag,
                "contentHash": value.content_hash,
                "replayability": value.replayability,
                "retrievedAt": value.retrieved_at,
            }
            for value in values
        ]
    }


@router.get("/projects/{project_id}/assessments/{assessment_id}/document-snapshots")
async def list_document_snapshots(
    assessment_id: UUID, scope: Scope, session: Session
) -> dict[str, Any]:
    values = list(
        await session.scalars(
            select(DocumentUsageSnapshot)
            .where(
                DocumentUsageSnapshot.evaluation_id == assessment_id,
                DocumentUsageSnapshot.tenant_id == scope.tenant_id,
                DocumentUsageSnapshot.project_id == scope.project_id,
            )
            .order_by(DocumentUsageSnapshot.created_at)
        )
    )
    return {
        "items": [
            {
                "documentSnapshotId": value.id,
                "documentId": value.business_document_id,
                "documentVersionId": value.business_document_version_id,
                "blobId": value.blob_id,
                "businessWorkKey": value.business_work_key,
                "version": value.document_version,
                "sha256": value.sha256,
                "sizeBytes": value.size_bytes,
                "mediaType": value.media_type,
                "evidence": value.evidence,
                "createdAt": value.created_at,
            }
            for value in values
        ]
    }


@router.get("/projects/{project_id}/assessments/{assessment_id}/decision-executions")
async def list_decision_executions(
    assessment_id: UUID, scope: Scope, session: Session
) -> dict[str, Any]:
    values = list(
        (
            await session.execute(
                select(DecisionExecution, EvaluationDecision)
            .join(
                EvaluationDecision,
                EvaluationDecision.id == DecisionExecution.evaluation_decision_id,
            )
            .where(
                EvaluationDecision.evaluation_id == assessment_id,
                DecisionExecution.tenant_id == scope.tenant_id,
                DecisionExecution.project_id == scope.project_id,
            )
            .order_by(DecisionExecution.executed_at)
            )
        ).all()
    )
    return {
        "items": [
            {
                "decisionExecutionId": value.id,
                "decisionVersionId": frozen.rule_set_version_id,
                "decisionContentHash": frozen.decision_content_hash,
                "executionKey": value.execution_key,
                "attempt": value.attempt,
                "status": value.status,
                "inputHash": value.input_hash,
                "outputHash": value.output_hash,
                "matchedRuleIds": value.matched_rule_ids,
                "durationMs": value.duration_ms,
                "executedAt": value.executed_at,
            }
            for value, frozen in values
        ]
    }
