from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_application import (
    BusinessObjectService,
    BusinessWorkService,
    BusinessWorkSummary,
    CapabilityBindingService,
    CapabilityPackReadinessError,
    CapabilityPackService,
    CaseService,
    CaseSubjectInput,
    ConnectionService,
    ContractPerformanceService,
    DecisionAssetService,
    DecisionExecutionService,
    DocumentLibraryService,
    DocumentProcessingService,
    DocumentRequirementService,
    DocumentReviewService,
    InvoiceAssuranceOperationsService,
    InvoiceBatchInput,
    ProcurementSupplierRiskService,
    ResourceCatalogService,
    RuleSetService,
    UploadBatchService,
    WorkbenchService,
    build_schedule,
)
from swarmcore_capability_contract_integrity import (
    MANIFEST,
    MANIFEST_V2,
    MANIFEST_V2_1,
    REFERENCES,
    SCHEMAS,
    STRATEGIES,
)
from swarmcore_capability_contract_performance import (
    MANIFEST as CONTRACT_PERFORMANCE_MANIFEST,
)
from swarmcore_capability_contract_performance import (
    REFERENCES as CONTRACT_PERFORMANCE_REFERENCES,
)
from swarmcore_capability_contract_performance import (
    SCHEMAS as CONTRACT_PERFORMANCE_SCHEMAS,
)
from swarmcore_capability_contract_performance import (
    STRATEGIES as CONTRACT_PERFORMANCE_STRATEGIES,
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
from swarmcore_capability_deviation_analysis import (
    MANIFEST as DEVIATION_ANALYSIS_MANIFEST,
)
from swarmcore_capability_deviation_analysis import (
    REFERENCES as DEVIATION_ANALYSIS_REFERENCES,
)
from swarmcore_capability_deviation_analysis import (
    SCHEMAS as DEVIATION_ANALYSIS_SCHEMAS,
)
from swarmcore_capability_deviation_analysis import (
    STRATEGIES as DEVIATION_ANALYSIS_STRATEGIES,
)
from swarmcore_capability_document_structuring import (
    MANIFEST as DOCUMENT_STRUCTURING_MANIFEST,
)
from swarmcore_capability_document_structuring import (
    REFERENCES as DOCUMENT_STRUCTURING_REFERENCES,
)
from swarmcore_capability_document_structuring import (
    SCHEMAS as DOCUMENT_STRUCTURING_SCHEMAS,
)
from swarmcore_capability_document_structuring import (
    STRATEGIES as DOCUMENT_STRUCTURING_STRATEGIES,
)
from swarmcore_capability_invoice_assurance import (
    MANIFEST as INVOICE_ASSURANCE_MANIFEST,
)
from swarmcore_capability_invoice_assurance import (
    REFERENCES as INVOICE_ASSURANCE_REFERENCES,
)
from swarmcore_capability_invoice_assurance import (
    SCHEMAS as INVOICE_ASSURANCE_SCHEMAS,
)
from swarmcore_capability_invoice_assurance import (
    STRATEGIES as INVOICE_ASSURANCE_STRATEGIES,
)
from swarmcore_capability_procurement_supplier_risk import (
    MANIFEST as PROCUREMENT_SUPPLIER_RISK_MANIFEST,
)
from swarmcore_capability_procurement_supplier_risk import (
    REFERENCES as PROCUREMENT_SUPPLIER_RISK_REFERENCES,
)
from swarmcore_capability_procurement_supplier_risk import (
    SCHEMAS as PROCUREMENT_SUPPLIER_RISK_SCHEMAS,
)
from swarmcore_capability_procurement_supplier_risk import (
    STRATEGIES as PROCUREMENT_SUPPLIER_RISK_STRATEGIES,
)
from swarmcore_capability_swarm_calibration import (
    MANIFEST as SWARM_CALIBRATION_MANIFEST,
)
from swarmcore_capability_swarm_calibration import (
    REFERENCES as SWARM_CALIBRATION_REFERENCES,
)
from swarmcore_capability_swarm_calibration import (
    SCHEMAS as SWARM_CALIBRATION_SCHEMAS,
)
from swarmcore_capability_swarm_calibration import (
    STRATEGIES as SWARM_CALIBRATION_STRATEGIES,
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
    AssessmentDetailSnapshot,
    AttachmentUploadHandle,
    BindBusinessWorkStrategyRequest,
    BindDecisionRequest,
    BindResourceRequest,
    BusinessWorkBlockerSnapshot,
    BusinessWorkFunctionSnapshot,
    BusinessWorkListResponse,
    BusinessWorkSnapshot,
    CapabilityPackListResponse,
    CapabilityPackSnapshot,
    CollectContractPerformanceRequest,
    CompleteAttachmentRequest,
    CompleteDocumentUploadRequest,
    ConfirmClassificationRequest,
    ConfirmFieldsRequest,
    ContractPerformanceCaseSnapshot,
    ContractPerformanceEvidenceListResponse,
    ContractPerformancePlanSnapshot,
    ContractPerformanceSnapshotResponse,
    CreateBusinessObjectRelationRequest,
    CreateBusinessObjectRequest,
    CreateBusinessObjectVersionRequest,
    CreateCapabilityPackRequest,
    CreateCaseRequest,
    CreateConnectionRequest,
    CreateConnectionVersionRequest,
    CreateContractPerformanceCaseRequest,
    CreateDecisionAssetRequest,
    CreateInvoiceAssuranceBatchRequest,
    CreateResourceRequest,
    CreateRuleSetRequest,
    CreateSupplierRiskMonitorRequest,
    CreateSupplierRiskWorkOrderRequest,
    CreateUploadBatchRequest,
    CreateWorkItemRequest,
    DocumentListResponse,
    DocumentProcessingEventListResponse,
    DocumentProcessingEventSnapshot,
    DocumentProcessingResultSnapshot,
    DocumentProcessingRunSnapshot,
    DocumentRequirementListResponse,
    DocumentRequirementSnapshot,
    DocumentSnapshot,
    DocumentUploadHandle,
    DocumentVersionSnapshot,
    EnableCapabilityPackRequest,
    EvaluationSnapshot,
    FindingActionRequest,
    FindingListResponse,
    FindingSnapshot,
    InitializeContractPerformanceRequest,
    InitiateAttachmentRequest,
    InitiateDocumentRequest,
    InvoiceAssuranceBatchItemSnapshot,
    InvoiceAssuranceBatchSnapshot,
    InvoiceRuleTrendSnapshot,
    PublishContractPerformancePlanRequest,
    ReportListResponse,
    ReportSnapshot,
    ReprocessDocumentRequest,
    ResumeDocumentUploadRequest,
    RuleSetDraftSnapshot,
    RuleSetValidationResponse,
    RuleSetVersionSnapshot,
    RunSwarmCalibrationRequest,
    SupplierRiskAlertListResponse,
    SupplierRiskAlertSnapshot,
    SupplierRiskHistoryItem,
    SupplierRiskHistoryResponse,
    SupplierRiskMonitorSnapshot,
    SupplierRiskWorkOrderListResponse,
    SupplierRiskWorkOrderSnapshot,
    UpdateCaseRequest,
    UpdateDecisionDraftRequest,
    UpdateDocumentBindingsRequest,
    UpdateRuleSetDraftRequest,
    UpdateSupplierRiskWorkOrderRequest,
    UpdateWorkItemRequest,
    UploadBatchSnapshot,
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
    CapabilityReferenceCatalog.from_iterable(
        (
            *REFERENCES,
            *POST_EVALUATION_REFERENCES,
            *CONTRACT_PERFORMANCE_REFERENCES,
            *DEVIATION_ANALYSIS_REFERENCES,
            *DOCUMENT_STRUCTURING_REFERENCES,
            *INVOICE_ASSURANCE_REFERENCES,
            *PROCUREMENT_SUPPLIER_RISK_REFERENCES,
            *SWARM_CALIBRATION_REFERENCES,
        )
    ),
    trusted_manifests=(
        MANIFEST,
        MANIFEST_V2,
        MANIFEST_V2_1,
        POST_EVALUATION_MANIFEST,
        CONTRACT_PERFORMANCE_MANIFEST,
        DEVIATION_ANALYSIS_MANIFEST,
        DOCUMENT_STRUCTURING_MANIFEST,
        INVOICE_ASSURANCE_MANIFEST,
        PROCUREMENT_SUPPLIER_RISK_MANIFEST,
        SWARM_CALIBRATION_MANIFEST,
    ),
    trusted_strategies={
        **STRATEGIES,
        **POST_EVALUATION_STRATEGIES,
        **CONTRACT_PERFORMANCE_STRATEGIES,
        **DEVIATION_ANALYSIS_STRATEGIES,
        **DOCUMENT_STRUCTURING_STRATEGIES,
        **INVOICE_ASSURANCE_STRATEGIES,
        **PROCUREMENT_SUPPLIER_RISK_STRATEGIES,
        **SWARM_CALIBRATION_STRATEGIES,
    },
)
rule_sets = RuleSetService()
workbench = WorkbenchService(
    capability_packs,
    schemas={
        **SCHEMAS,
        **POST_EVALUATION_SCHEMAS,
        **CONTRACT_PERFORMANCE_SCHEMAS,
        **DEVIATION_ANALYSIS_SCHEMAS,
        **DOCUMENT_STRUCTURING_SCHEMAS,
        **INVOICE_ASSURANCE_SCHEMAS,
        **PROCUREMENT_SUPPLIER_RISK_SCHEMAS,
        **SWARM_CALIBRATION_SCHEMAS,
    },
    rule_sets=rule_sets,
)
business_objects = BusinessObjectService()
cases = CaseService(workbench, capability_packs)
decision_assets = DecisionAssetService()
decision_executions = DecisionExecutionService()
connections = ConnectionService()
resources = ResourceCatalogService()
bindings = CapabilityBindingService()
document_processing = DocumentProcessingService()
documents = DocumentLibraryService(processing=document_processing)
document_review = DocumentReviewService(document_processing)
upload_batches = UploadBatchService()
document_requirements = DocumentRequirementService()
business_works = BusinessWorkService(capability_packs, workbench, cases, documents=documents)
invoice_assurance_operations = InvoiceAssuranceOperationsService(business_works)
contract_performance = ContractPerformanceService()
procurement_supplier_risk = ProcurementSupplierRiskService()

Scope = Annotated[RequestScope, Depends(request_scope)]
Session = Annotated[AsyncSession, Depends(db_session)]
IdempotencyKey = Annotated[str, Depends(require_idempotency_key)]


def _business_work_snapshot(summary: BusinessWorkSummary) -> BusinessWorkSnapshot:
    return BusinessWorkSnapshot(
        workKey=summary.work_key,
        name=summary.name,
        shortName=summary.short_name,
        category=summary.category,
        summary=summary.summary,
        status=summary.status,
        statusLabel=summary.status_label,
        packName=summary.pack_name,
        packVersionId=summary.pack_version_id,
        packVersion=summary.pack_version,
        enabled=summary.enabled,
        bindingStatus=summary.binding_status,
        blockers=[
            BusinessWorkBlockerSnapshot(code=item.code, message=item.message, ref=item.ref)
            for item in summary.blockers
        ],
        agents=list(summary.agents),
        tools=list(summary.tools),
        models=list(summary.models),
        documentRequirements=list(summary.document_requirements),
        decisionSlots=list(summary.decision_slots),
        functions=[
            BusinessWorkFunctionSnapshot(name=item.name, description=item.description)
            for item in summary.functions
        ],
        configuration=summary.configuration,
        workItemType=summary.work_item_type,
        caseBased=summary.case_based,
        boundStrategyVersionId=summary.bound_strategy_version_id,
        boundStrategyName=summary.bound_strategy_name,
        boundStrategyVersion=summary.bound_strategy_version,
    )


def _invoice_batch_snapshot(value: Any) -> InvoiceAssuranceBatchSnapshot:
    return InvoiceAssuranceBatchSnapshot(
        batchId=value.batch_id,
        status=value.status,
        totalItems=value.total_items,
        maxParallelism=value.max_parallelism,
        requestedBy=value.requested_by,
        createdAt=value.created_at,
        updatedAt=value.updated_at,
        items=[
            InvoiceAssuranceBatchItemSnapshot(
                ordinal=item.ordinal,
                caseId=item.case_id,
                evaluationId=item.evaluation_id,
                status=item.status,
                outcome=item.outcome,
            )
            for item in value.items
        ],
    )


def _contract_performance_case_snapshot(value: Any) -> ContractPerformanceCaseSnapshot:
    return ContractPerformanceCaseSnapshot(
        caseId=value.id,
        contractObjectId=value.contract_object_id,
        status=value.status,
        timezone=value.timezone,
        currency=value.currency,
        activePlanVersionId=value.active_plan_version_id,
        createdAt=value.created_at,
        updatedAt=value.updated_at,
    )


def _contract_performance_plan_snapshot(value: Any) -> ContractPerformancePlanSnapshot:
    return ContractPerformancePlanSnapshot(
        planVersionId=value.id,
        caseId=value.case_id,
        version=value.version,
        status=value.status,
        originalBaseline=value.original_baseline,
        currentBaseline=value.current_baseline,
        coverage=value.coverage,
        changeHistory=value.change_history,
        reviewDecisions=value.review_decisions,
        planHash=value.plan_hash,
        effectiveAt=value.effective_at,
        publishedBy=value.published_by,
    )


def _contract_performance_snapshot(value: Any) -> ContractPerformanceSnapshotResponse:
    return ContractPerformanceSnapshotResponse(
        snapshotId=value.id,
        caseId=value.case_id,
        planVersionId=value.plan_version_id,
        asOf=value.as_of,
        status=value.status,
        collectionStatus=value.collection_status,
        result=value.result,
        resultHash=value.result_hash,
        ganttHash=value.gantt_hash,
        createdAt=value.created_at,
    )


def _supplier_risk_monitor_snapshot(value: Any) -> SupplierRiskMonitorSnapshot:
    return SupplierRiskMonitorSnapshot(
        monitorId=value.id,
        caseId=value.case_id,
        supplierName=value.supplier_name,
        supplierCreditCode=value.supplier_credit_code,
        status=value.status,
        cadence=value.cadence,
        sources=list(value.source_configuration),
        nextCheckAt=value.next_check_at,
        lastCheckedAt=value.last_checked_at,
        lastSnapshotId=value.last_snapshot_id,
        createdAt=value.created_at,
        updatedAt=value.updated_at,
    )


def _supplier_risk_alert_snapshot(value: Any) -> SupplierRiskAlertSnapshot:
    return SupplierRiskAlertSnapshot(
        alertId=value.id,
        monitorId=value.monitor_id,
        snapshotId=value.snapshot_id,
        alertType=value.alert_type,
        severity=value.severity,
        status=value.status,
        title=value.title,
        details=value.details,
        evidence=list(value.evidence),
        createdAt=value.created_at,
        updatedAt=value.updated_at,
    )


async def _supplier_risk_work_order_snapshot(
    session: AsyncSession,
    *,
    scope: RequestScope,
    value: Any,
) -> SupplierRiskWorkOrderSnapshot:
    actions = await procurement_supplier_risk.list_work_order_actions(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_order_id=value.id,
    )
    return SupplierRiskWorkOrderSnapshot(
        workOrderId=value.id,
        alertId=value.alert_id,
        status=value.status,
        priority=value.priority,
        assignee=value.assignee,
        dueAt=value.due_at,
        resolution=value.resolution,
        createdBy=value.created_by,
        createdAt=value.created_at,
        updatedAt=value.updated_at,
        actions=[
            {
                "actionId": item.id,
                "action": item.action,
                "fromStatus": item.from_status,
                "toStatus": item.to_status,
                "comment": item.comment,
                "actor": item.actor,
                "metadata": item.metadata_,
                "createdAt": item.created_at,
            }
            for item in actions
        ],
    )


def _assessment_detail(
    evaluation: Evaluation,
    item: WorkItem | None,
    revision: WorkItemRevision | None,
) -> AssessmentDetailSnapshot:
    return AssessmentDetailSnapshot(
        assessmentId=evaluation.id,
        evaluationId=evaluation.id,
        caseId=evaluation.work_item_id,
        workItemId=evaluation.work_item_id,
        workItemRevisionId=evaluation.work_item_revision_id,
        runId=evaluation.run_id,
        status=evaluation.status,
        result=evaluation.result,
        capabilityPackVersionId=evaluation.capability_pack_version_id,
        planHash=evaluation.plan_hash,
        attachmentManifestHash=evaluation.attachment_manifest_hash,
        registrySnapshot=evaluation.registry_snapshot,
        createdAt=evaluation.created_at,
        casePayload=revision.payload if revision is not None else None,
        caseStatus=item.status if item is not None else None,
        scenarioType=item.work_item_type if item is not None else None,
        owner=item.owner if item is not None else None,
    )


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
    evaluated_version_ids = (
        set(
            await session.scalars(
                select(Evaluation.capability_pack_version_id).where(
                    Evaluation.tenant_id == scope.tenant_id,
                    Evaluation.capability_pack_version_id.in_(version_ids),
                )
            )
        )
        if version_ids
        else set()
    )
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
    "/projects/{project_id}/contract-performance/cases",
    response_model=ContractPerformanceCaseSnapshot,
    status_code=201,
)
async def create_contract_performance_case(
    body: CreateContractPerformanceCaseRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> ContractPerformanceCaseSnapshot:
    value = await contract_performance.create_case(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        contract_object_id=body.contract_object_id,
        timezone=body.timezone,
        currency=body.currency,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return _contract_performance_case_snapshot(value)


@router.post(
    "/projects/{project_id}/contract-performance/cases/{case_id}:initialize",
    response_model=ContractPerformancePlanSnapshot,
    status_code=202,
)
async def initialize_contract_performance_case(
    case_id: UUID,
    body: InitializeContractPerformanceRequest,
    scope: Scope,
    session: Session,
) -> ContractPerformancePlanSnapshot:
    value = await contract_performance.initialize(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
        candidates=body.candidates,
        as_of=body.as_of,
        coverage=body.coverage,
        actor=scope.actor_id,
    )
    return _contract_performance_plan_snapshot(value)


@router.post(
    "/projects/{project_id}/contract-performance/cases/{case_id}/plans/{version}:publish",
    response_model=ContractPerformancePlanSnapshot,
)
async def publish_contract_performance_plan(
    case_id: UUID,
    version: int,
    body: PublishContractPerformancePlanRequest,
    scope: Scope,
    session: Session,
) -> ContractPerformancePlanSnapshot:
    if set(scope.roles) <= {"supplier", "supplier_collaborator"}:
        raise HTTPException(status_code=403, detail="supplier cannot publish a buyer plan")
    value = await contract_performance.publish_plan(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
        version=version,
        approval_id=body.approval_id,
        actor=scope.actor_id,
        confirmations=body.confirmations,
    )
    return _contract_performance_plan_snapshot(value)


@router.post(
    "/projects/{project_id}/contract-performance/cases/{case_id}:collect",
    response_model=ContractPerformanceSnapshotResponse,
    status_code=202,
)
async def collect_contract_performance_evidence(
    case_id: UUID,
    body: CollectContractPerformanceRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> ContractPerformanceSnapshotResponse:
    value = await contract_performance.collect(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
        as_of=body.as_of,
        evidence=body.evidence,
        candidate_links=body.candidate_links,
        sources=body.sources,
        collection_status=body.collection_status,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
        approved_exceptions=body.approved_exceptions,
    )
    return _contract_performance_snapshot(value)


@router.get(
    "/projects/{project_id}/contract-performance/cases/{case_id}/plan",
    response_model=ContractPerformancePlanSnapshot,
)
async def get_contract_performance_plan(
    case_id: UUID,
    scope: Scope,
    session: Session,
    version: Annotated[int | None, Query(ge=1)] = None,
) -> ContractPerformancePlanSnapshot:
    value = await contract_performance.get_plan(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
        version=version,
    )
    return _contract_performance_plan_snapshot(value)


@router.get("/projects/{project_id}/contract-performance/cases/{case_id}/gantt")
async def get_contract_performance_gantt(
    case_id: UUID,
    scope: Scope,
    session: Session,
    as_of: Annotated[date, Query(alias="asOf")],
) -> dict[str, Any]:
    value = await contract_performance.get_plan(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
    )
    snapshot = await contract_performance.get_latest_snapshot(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
        as_of=as_of,
    )
    actuals = {
        str(item["milestoneId"]): {
            "status": item["status"],
            "evidenceStatus": (
                "COMPLETE" if not item.get("missingEvidenceTypes") else "PENDING"
            ),
            "actualStartDate": item.get("actualStartDate"),
            "actualFinishDate": item.get("actualFinishDate"),
        }
        for item in (
            snapshot.result.get("performance", {}).get("milestones", [])
            if snapshot is not None
            else []
        )
    }
    return build_schedule(
        value.current_baseline,
        original_plan=value.original_baseline,
        actuals=actuals,
        as_of=as_of,
    )


@router.get(
    "/projects/{project_id}/contract-performance/cases/{case_id}/evidence",
    response_model=ContractPerformanceEvidenceListResponse,
)
async def list_contract_performance_evidence(
    case_id: UUID,
    scope: Scope,
    session: Session,
    evidence_type: Annotated[str | None, Query(alias="type")] = None,
) -> ContractPerformanceEvidenceListResponse:
    values = await contract_performance.list_evidence(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
        evidence_type=evidence_type,
    )
    items = [
        {
            **value.snapshot,
            "id": str(value.id),
            "type": value.evidence_type,
            "sourceRef": value.source_ref,
            "sourceRecordId": value.source_record_id,
            "contentHash": value.content_hash,
            "capturedAt": value.captured_at.isoformat(),
        }
        for value in values
    ]
    return ContractPerformanceEvidenceListResponse(items=items, total=len(items))


@router.get(
    "/projects/{project_id}/contract-performance/cases/{case_id}/snapshots/{snapshot_id}",
    response_model=ContractPerformanceSnapshotResponse,
)
async def get_contract_performance_snapshot(
    case_id: UUID,
    snapshot_id: UUID,
    scope: Scope,
    session: Session,
) -> ContractPerformanceSnapshotResponse:
    value = await contract_performance.get_snapshot(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=case_id,
        snapshot_id=snapshot_id,
    )
    return _contract_performance_snapshot(value)


@router.post(
    "/projects/{project_id}/swarm-calibration:run",
    response_model=EvaluationSnapshot,
    status_code=202,
)
async def run_swarm_calibration(
    body: RunSwarmCalibrationRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> EvaluationSnapshot:
    payload = body.model_dump(
        by_alias=True,
        mode="json",
        exclude={"owner"},
        exclude_none=True,
    )
    item, _ = await business_works.create_work_item(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_key="swarm-calibration",
        payload=payload,
        owner=body.owner,
        idempotency_key=f"{idempotency_key}:case",
        actor=scope.actor_id,
    )
    evaluation = await business_works.execute_work_item(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_key="swarm-calibration",
        work_item_id=item.id,
        idempotency_key=f"{idempotency_key}:assessment",
        actor=scope.actor_id,
        submitted_scopes=scope.scopes,
        auth_context_hash=scope.auth_context_hash,
    )
    return _evaluation_snapshot(evaluation)


@router.post(
    "/projects/{project_id}/procurement-supplier-risk/monitors",
    response_model=SupplierRiskMonitorSnapshot,
    status_code=201,
)
async def create_supplier_risk_monitor(
    body: CreateSupplierRiskMonitorRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> SupplierRiskMonitorSnapshot:
    value = await procurement_supplier_risk.create_monitor(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=body.case_id,
        supplier_name=body.supplier_name,
        supplier_credit_code=body.supplier_credit_code,
        cadence=body.cadence,
        source_configuration=body.sources,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return _supplier_risk_monitor_snapshot(value)


@router.get(
    "/projects/{project_id}/procurement-supplier-risk/monitors/{monitor_id}",
    response_model=SupplierRiskMonitorSnapshot,
)
async def get_supplier_risk_monitor(
    monitor_id: UUID,
    scope: Scope,
    session: Session,
) -> SupplierRiskMonitorSnapshot:
    value = await procurement_supplier_risk.get_monitor(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        monitor_id=monitor_id,
    )
    return _supplier_risk_monitor_snapshot(value)


@router.post(
    "/projects/{project_id}/procurement-supplier-risk/monitors/{monitor_id}:refresh",
    response_model=EvaluationSnapshot,
    status_code=202,
)
async def refresh_supplier_risk_monitor(
    monitor_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> EvaluationSnapshot:
    monitor = await procurement_supplier_risk.get_monitor(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        monitor_id=monitor_id,
    )
    item, revision, _ = await cases.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=monitor.case_id,
    )
    prior_snapshots = await procurement_supplier_risk.list_snapshots(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        monitor_id=monitor.id,
        limit=1,
    )
    payload = {
        **revision.payload,
        "monitorId": str(monitor.id),
        "supplier": {
            **dict(revision.payload.get("supplier") or {}),
            "name": monitor.supplier_name,
            "creditCode": monitor.supplier_credit_code,
        },
        "riskSources": list(monitor.source_configuration),
        "previousSnapshot": (
            dict(prior_snapshots[0].result.get("risk") or {})
            if prior_snapshots
            else None
        ),
    }
    refresh_key = idempotency_key[:220]
    if payload != revision.payload:
        await cases.revise(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            case_id=monitor.case_id,
            payload=payload,
            subjects=None,
            owner=item.owner,
            expected_revision=item.revision_number,
            idempotency_key=f"{refresh_key}:monitor-context",
            actor=scope.actor_id,
        )
    evaluation = await cases.assess(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        case_id=monitor.case_id,
        idempotency_key=f"{refresh_key}:assessment",
        actor=scope.actor_id,
        submitted_scopes=scope.scopes,
        auth_context_hash=scope.auth_context_hash,
    )
    return _evaluation_snapshot(evaluation)


@router.get(
    "/projects/{project_id}/procurement-supplier-risk/monitors/{monitor_id}/history",
    response_model=SupplierRiskHistoryResponse,
)
async def list_supplier_risk_history(
    monitor_id: UUID,
    scope: Scope,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> SupplierRiskHistoryResponse:
    values = await procurement_supplier_risk.list_snapshots(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        monitor_id=monitor_id,
        limit=limit,
    )
    return SupplierRiskHistoryResponse(
        items=[
            SupplierRiskHistoryItem(
                snapshotId=value.id,
                evaluationId=value.evaluation_id,
                asOf=value.as_of,
                decision=value.decision,
                riskLevel=value.risk_level,
                riskScore=value.risk_score,
                sourceCoverage=value.source_coverage,
                changeSummary=value.change_summary,
                resultHash=value.result_hash,
                result=value.result,
            )
            for value in values
        ]
    )


@router.get(
    "/projects/{project_id}/procurement-supplier-risk/alerts",
    response_model=SupplierRiskAlertListResponse,
)
async def list_supplier_risk_alerts(
    scope: Scope,
    session: Session,
    monitor_id: Annotated[UUID | None, Query(alias="monitorId")] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> SupplierRiskAlertListResponse:
    values = await procurement_supplier_risk.list_alerts(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        monitor_id=monitor_id,
        status=status,
        limit=limit,
    )
    return SupplierRiskAlertListResponse(
        items=[_supplier_risk_alert_snapshot(value) for value in values]
    )


@router.post(
    "/projects/{project_id}/procurement-supplier-risk/alerts/{alert_id}/work-orders",
    response_model=SupplierRiskWorkOrderSnapshot,
    status_code=201,
)
async def create_supplier_risk_work_order(
    alert_id: UUID,
    body: CreateSupplierRiskWorkOrderRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> SupplierRiskWorkOrderSnapshot:
    value = await procurement_supplier_risk.create_work_order(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        alert_id=alert_id,
        priority=body.priority,
        assignee=body.assignee,
        due_at=body.due_at,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
    )
    return await _supplier_risk_work_order_snapshot(session, scope=scope, value=value)


@router.get(
    "/projects/{project_id}/procurement-supplier-risk/work-orders",
    response_model=SupplierRiskWorkOrderListResponse,
)
async def list_supplier_risk_work_orders(
    scope: Scope,
    session: Session,
    monitor_id: Annotated[UUID | None, Query(alias="monitorId")] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> SupplierRiskWorkOrderListResponse:
    values = await procurement_supplier_risk.list_work_orders(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        monitor_id=monitor_id,
        status=status,
        limit=limit,
    )
    return SupplierRiskWorkOrderListResponse(
        items=[
            await _supplier_risk_work_order_snapshot(session, scope=scope, value=value)
            for value in values
        ]
    )


@router.patch(
    "/projects/{project_id}/procurement-supplier-risk/work-orders/{work_order_id}",
    response_model=SupplierRiskWorkOrderSnapshot,
)
async def update_supplier_risk_work_order(
    work_order_id: UUID,
    body: UpdateSupplierRiskWorkOrderRequest,
    scope: Scope,
    session: Session,
) -> SupplierRiskWorkOrderSnapshot:
    value = await procurement_supplier_risk.update_work_order(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_order_id=work_order_id,
        status=body.status,
        assignee=body.assignee,
        resolution=body.resolution,
        comment=body.comment,
        actor=scope.actor_id,
    )
    return await _supplier_risk_work_order_snapshot(session, scope=scope, value=value)


@router.get(
    "/projects/{project_id}/business-works",
    response_model=BusinessWorkListResponse,
)
async def list_business_works(scope: Scope, session: Session) -> BusinessWorkListResponse:
    items = await business_works.list_works(
        session, tenant_id=scope.tenant_id, project_id=scope.project_id
    )
    return BusinessWorkListResponse(items=[_business_work_snapshot(item) for item in items])


@router.post(
    "/projects/{project_id}/business-works/invoice-assurance/batches",
    response_model=InvoiceAssuranceBatchSnapshot,
    status_code=202,
)
async def create_invoice_assurance_batch(
    body: CreateInvoiceAssuranceBatchRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> InvoiceAssuranceBatchSnapshot:
    batch = await invoice_assurance_operations.create_batch(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        inputs=tuple(
            InvoiceBatchInput(
                payload=item.payload,
                subjects=tuple(
                    CaseSubjectInput(
                        business_object_id=subject.business_object_id,
                        business_object_version_id=subject.business_object_version_id,
                        role=subject.role,
                        subject_key=subject.subject_key,
                    )
                    for subject in item.subjects
                ),
                owner=item.owner,
            )
            for item in body.items
        ),
        max_parallelism=body.max_parallelism,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
        submitted_scopes=scope.scopes,
        auth_context_hash=scope.auth_context_hash,
    )
    return _invoice_batch_snapshot(batch)


@router.get(
    "/projects/{project_id}/business-works/invoice-assurance/batches/{batch_id}",
    response_model=InvoiceAssuranceBatchSnapshot,
)
async def get_invoice_assurance_batch(
    batch_id: UUID,
    scope: Scope,
    session: Session,
) -> InvoiceAssuranceBatchSnapshot:
    batch = await invoice_assurance_operations.get_batch(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        batch_id=batch_id,
    )
    return _invoice_batch_snapshot(batch)


@router.get(
    "/projects/{project_id}/business-works/invoice-assurance/rule-trends",
    response_model=InvoiceRuleTrendSnapshot,
)
async def get_invoice_assurance_rule_trends(
    scope: Scope,
    session: Session,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    bucket: Annotated[Literal["day", "week", "month"], Query()] = "day",
) -> InvoiceRuleTrendSnapshot:
    trend = await invoice_assurance_operations.rule_trends(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        date_from=date_from,
        date_to=date_to,
        bucket=bucket,
    )
    return InvoiceRuleTrendSnapshot.model_validate(trend)


# Register before GET {work_key}: path params swallow `:suffix` if ordered later.
@router.post(
    "/projects/{project_id}/business-works/{work_key}:bind-strategy",
    response_model=BusinessWorkSnapshot,
)
async def bind_business_work_strategy(
    work_key: str,
    body: BindBusinessWorkStrategyRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> BusinessWorkSnapshot | JSONResponse:
    try:
        summary = await business_works.bind_strategy(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            work_key=work_key,
            strategy_version_id=body.strategy_version_id,
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
    return _business_work_snapshot(summary)


@router.get(
    "/projects/{project_id}/business-works/{work_key}",
    response_model=BusinessWorkSnapshot,
)
async def get_business_work(work_key: str, scope: Scope, session: Session) -> BusinessWorkSnapshot:
    summary = await business_works.get_work(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_key=work_key,
    )
    return _business_work_snapshot(summary)


@router.get(
    "/projects/{project_id}/assessments/{assessment_id}",
    response_model=AssessmentDetailSnapshot,
)
async def get_assessment(
    assessment_id: UUID, scope: Scope, session: Session
) -> AssessmentDetailSnapshot:
    evaluation, item, revision = await business_works.get_assessment(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        assessment_id=assessment_id,
    )
    return _assessment_detail(evaluation, item, revision)


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
    request: Request,
) -> DocumentSnapshot:
    blob_content: bytes | None = None
    # Prefer local artifact store used by Artifact Gateway when available.
    from pathlib import Path

    from swarmcore_persistence.models import BlobObject

    blob = await session.scalar(
        select(BlobObject).where(
            BlobObject.tenant_id == scope.tenant_id,
            BlobObject.project_id == scope.project_id,
            BlobObject.metadata_json["documentUploadId"].astext == str(upload_id),
        )
    )
    if blob is not None:
        candidate = Path(request.app.state.settings.artifact_root) / blob.object_key
        if candidate.is_file():
            blob_content = candidate.read_bytes()
    document, version = await documents.complete(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        upload_id=upload_id,
        sha256=body.sha256,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
        profile_ref=body.profile_ref,
        candidate_labels=body.classification_labels or None,
        extraction_schema_ref=body.extraction_schema_ref,
        upload_batch_id=body.upload_batch_id,
        blob_content=blob_content,
    )
    if body.upload_batch_id is not None:
        batch = await upload_batches.get(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            batch_id=body.upload_batch_id,
        )
        await upload_batches.mark_file_result(
            session, batch=batch, succeeded=document.status != "FAILED"
        )
        await upload_batches.complete_if_idle(session, batch=batch)
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
    "/projects/{project_id}/upload-batches",
    response_model=UploadBatchSnapshot,
    status_code=201,
)
async def create_upload_batch(
    body: CreateUploadBatchRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> UploadBatchSnapshot:
    batch = await upload_batches.create(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        source=body.source,
        context=body.context,
        actor=scope.actor_id,
        idempotency_key=idempotency_key,
    )
    return UploadBatchSnapshot(
        batchId=batch.id,
        source=batch.source,
        context=batch.context,
        status=batch.status,
        fileCount=batch.file_count,
        succeededCount=batch.succeeded_count,
        failedCount=batch.failed_count,
        createdBy=batch.created_by,
        createdAt=batch.created_at,
        completedAt=batch.completed_at,
    )


@router.get(
    "/projects/{project_id}/upload-batches/{batch_id}",
    response_model=UploadBatchSnapshot,
)
async def get_upload_batch(
    batch_id: UUID,
    scope: Scope,
    session: Session,
) -> UploadBatchSnapshot:
    batch = await upload_batches.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        batch_id=batch_id,
    )
    return UploadBatchSnapshot(
        batchId=batch.id,
        source=batch.source,
        context=batch.context,
        status=batch.status,
        fileCount=batch.file_count,
        succeededCount=batch.succeeded_count,
        failedCount=batch.failed_count,
        createdBy=batch.created_by,
        createdAt=batch.created_at,
        completedAt=batch.completed_at,
    )


@router.get(
    "/projects/{project_id}/documents/{document_id}/processing",
    response_model=DocumentProcessingRunSnapshot,
)
async def get_document_processing(
    document_id: UUID,
    scope: Scope,
    session: Session,
) -> DocumentProcessingRunSnapshot:
    from swarmcore_application.document_processing import STAGE_LABELS_ZH

    document = await documents.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
    )
    version = await session.scalar(
        select(BusinessDocumentVersion).where(
            BusinessDocumentVersion.business_document_id == document.id,
            BusinessDocumentVersion.version == document.current_version,
        )
    )
    if version is None:
        raise LookupError("DOCUMENT_VERSION_NOT_FOUND")
    run = await document_processing.latest_run_for_version(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        version_id=version.id,
    )
    if run is None:
        raise LookupError("PROCESSING_RUN_NOT_FOUND")
    return DocumentProcessingRunSnapshot(
        processingRunId=run.id,
        businessDocumentVersionId=run.business_document_version_id,
        profileRef=run.profile_ref,
        status=run.status,
        currentStage=run.current_stage,
        stageLabel=STAGE_LABELS_ZH.get(run.current_stage, run.current_stage),
        attempt=run.attempt,
        parserRef=run.parser_ref,
        classifierRef=run.classifier_ref,
        extractorRefs=list(run.extractor_refs or []),
        errorCode=run.error_code,
        errorDetail=run.error_detail,
        startedAt=run.started_at,
        completedAt=run.completed_at,
        provenance=dict(run.provenance or {}),
    )


@router.get(
    "/projects/{project_id}/documents/{document_id}/processing/events",
    response_model=DocumentProcessingEventListResponse,
)
async def get_document_processing_events(
    document_id: UUID,
    scope: Scope,
    session: Session,
    after: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
) -> DocumentProcessingEventListResponse:
    document = await documents.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
    )
    version = await session.scalar(
        select(BusinessDocumentVersion).where(
            BusinessDocumentVersion.business_document_id == document.id,
            BusinessDocumentVersion.version == document.current_version,
            BusinessDocumentVersion.tenant_id == scope.tenant_id,
            BusinessDocumentVersion.project_id == scope.project_id,
        )
    )
    if version is None:
        raise LookupError("DOCUMENT_VERSION_NOT_FOUND")
    values = await document_processing.list_events(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        version_id=version.id,
        after=after,
        limit=limit,
    )
    items = [
        DocumentProcessingEventSnapshot(
            eventId=value.id,
            eventSeq=value.event_seq,
            processingRunId=value.processing_run_id,
            businessDocumentVersionId=value.business_document_version_id,
            type=value.type,
            stage=value.stage,
            payload=dict(value.payload or {}),
            inputHash=value.input_hash,
            outputHash=value.output_hash,
            toolRef=value.tool_ref,
            actorId=value.actor_id,
            traceId=value.trace_id,
            occurredAt=value.occurred_at,
        )
        for value in values
    ]
    return DocumentProcessingEventListResponse(
        items=items,
        nextAfter=items[-1].event_seq if items else after,
    )


@router.get(
    "/projects/{project_id}/documents/{document_id}/processing-result",
    response_model=DocumentProcessingResultSnapshot,
)
async def get_document_processing_result(
    document_id: UUID,
    scope: Scope,
    session: Session,
) -> DocumentProcessingResultSnapshot:
    document = await documents.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
    )
    version = await session.scalar(
        select(BusinessDocumentVersion).where(
            BusinessDocumentVersion.business_document_id == document.id,
            BusinessDocumentVersion.version == document.current_version,
        )
    )
    if version is None:
        raise LookupError("DOCUMENT_VERSION_NOT_FOUND")
    result = await document_processing.latest_result(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        version_id=version.id,
    )
    if result is None:
        raise LookupError("PROCESSING_RESULT_NOT_FOUND")
    return DocumentProcessingResultSnapshot(
        resultId=result.id,
        resultType=result.result_type,
        resultVersion=result.result_version,
        status=result.status,
        schemaRef=result.schema_ref,
        producerRef=result.producer_ref,
        result=result.result,
        evidence=list(result.evidence or []),
        confirmedBy=result.confirmed_by,
        confirmedAt=result.confirmed_at,
        createdAt=result.created_at,
    )


@router.get(
    "/projects/{project_id}/documents/{document_id}/structured-package",
    response_model=DocumentProcessingResultSnapshot,
)
async def get_document_structured_package(
    document_id: UUID,
    scope: Scope,
    session: Session,
) -> DocumentProcessingResultSnapshot:
    document = await documents.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
    )
    version = await session.scalar(
        select(BusinessDocumentVersion).where(
            BusinessDocumentVersion.business_document_id == document.id,
            BusinessDocumentVersion.version == document.current_version,
            BusinessDocumentVersion.tenant_id == scope.tenant_id,
            BusinessDocumentVersion.project_id == scope.project_id,
        )
    )
    if version is None:
        raise LookupError("DOCUMENT_VERSION_NOT_FOUND")
    result = await document_processing.latest_result(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        version_id=version.id,
        result_type="STRUCTURED_PACKAGE",
    )
    if result is None:
        raise LookupError("STRUCTURED_PACKAGE_NOT_FOUND")
    return DocumentProcessingResultSnapshot(
        resultId=result.id,
        resultType=result.result_type,
        resultVersion=result.result_version,
        status=result.status,
        schemaRef=result.schema_ref,
        producerRef=result.producer_ref,
        result=result.result,
        evidence=list(result.evidence or []),
        confirmedBy=result.confirmed_by,
        confirmedAt=result.confirmed_at,
        createdAt=result.created_at,
    )


@router.post(
    "/projects/{project_id}/documents/{document_id}:publish",
    response_model=DocumentProcessingResultSnapshot,
)
async def publish_document_structured_package(
    document_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> DocumentProcessingResultSnapshot:
    result = await document_review.publish(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
        actor=scope.actor_id,
        idempotency_key=idempotency_key,
    )
    return DocumentProcessingResultSnapshot(
        resultId=result.id,
        resultType=result.result_type,
        resultVersion=result.result_version,
        status=result.status,
        schemaRef=result.schema_ref,
        producerRef=result.producer_ref,
        result=result.result,
        evidence=list(result.evidence or []),
        confirmedBy=result.confirmed_by,
        confirmedAt=result.confirmed_at,
        createdAt=result.created_at,
    )


@router.post(
    "/projects/{project_id}/documents/{document_id}:confirm-classification",
    response_model=DocumentProcessingResultSnapshot,
)
async def confirm_document_classification(
    document_id: UUID,
    body: ConfirmClassificationRequest,
    scope: Scope,
    session: Session,
) -> DocumentProcessingResultSnapshot:
    result = await document_review.confirm_classification(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
        label=body.label,
        display_name=body.display_name,
        actor=scope.actor_id,
        expected_result_version=body.expected_result_version,
    )
    return DocumentProcessingResultSnapshot(
        resultId=result.id,
        resultType=result.result_type,
        resultVersion=result.result_version,
        status=result.status,
        schemaRef=result.schema_ref,
        producerRef=result.producer_ref,
        result=result.result,
        evidence=list(result.evidence or []),
        confirmedBy=result.confirmed_by,
        confirmedAt=result.confirmed_at,
        createdAt=result.created_at,
    )


@router.post(
    "/projects/{project_id}/documents/{document_id}:confirm-fields",
    response_model=DocumentProcessingResultSnapshot,
)
async def confirm_document_fields(
    document_id: UUID,
    body: ConfirmFieldsRequest,
    scope: Scope,
    session: Session,
) -> DocumentProcessingResultSnapshot:
    result = await document_review.confirm_fields(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
        fields=body.fields,
        actor=scope.actor_id,
        expected_result_version=body.expected_result_version,
        accept_high_confidence=body.accept_high_confidence,
    )
    return DocumentProcessingResultSnapshot(
        resultId=result.id,
        resultType=result.result_type,
        resultVersion=result.result_version,
        status=result.status,
        schemaRef=result.schema_ref,
        producerRef=result.producer_ref,
        result=result.result,
        evidence=list(result.evidence or []),
        confirmedBy=result.confirmed_by,
        confirmedAt=result.confirmed_at,
        createdAt=result.created_at,
    )


@router.post(
    "/projects/{project_id}/documents/{document_id}:resume-upload",
    response_model=DocumentSnapshot,
)
async def resume_document_upload(
    document_id: UUID,
    body: ResumeDocumentUploadRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
    request: Request,
) -> DocumentSnapshot:
    from pathlib import Path

    from swarmcore_persistence.models import BlobObject

    pending_blob = await session.scalar(
        select(BlobObject)
        .where(
            BlobObject.tenant_id == scope.tenant_id,
            BlobObject.project_id == scope.project_id,
            BlobObject.metadata_json["documentId"].astext == str(document_id),
            BlobObject.status == "AVAILABLE",
            BlobObject.scan_status == "CLEAN",
        )
        .order_by(BlobObject.created_at.desc())
        .limit(1)
    )
    blob_content: bytes | None = None
    if pending_blob is not None:
        candidate = Path(request.app.state.settings.artifact_root) / pending_blob.object_key
        if candidate.is_file():
            blob_content = candidate.read_bytes()
    document, version = await documents.resume_pending_upload(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
        idempotency_key=idempotency_key,
        actor=scope.actor_id,
        profile_ref=body.profile_ref,
        candidate_labels=body.classification_labels or None,
        extraction_schema_ref=body.extraction_schema_ref,
        blob_content=blob_content,
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


@router.post(
    "/projects/{project_id}/documents/{document_id}:reprocess",
    response_model=DocumentProcessingRunSnapshot,
)
async def reprocess_document(
    document_id: UUID,
    body: ReprocessDocumentRequest,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> DocumentProcessingRunSnapshot:
    from swarmcore_application.document_processing import STAGE_LABELS_ZH

    run = await document_processing.reprocess(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
        actor=scope.actor_id,
        idempotency_key=idempotency_key,
        profile_ref=body.profile_ref,
        candidate_labels=body.classification_labels or None,
        extraction_schema_ref=body.extraction_schema_ref,
    )
    return DocumentProcessingRunSnapshot(
        processingRunId=run.id,
        businessDocumentVersionId=run.business_document_version_id,
        profileRef=run.profile_ref,
        status=run.status,
        currentStage=run.current_stage,
        stageLabel=STAGE_LABELS_ZH.get(run.current_stage, run.current_stage),
        attempt=run.attempt,
        parserRef=run.parser_ref,
        classifierRef=run.classifier_ref,
        extractorRefs=list(run.extractor_refs or []),
        errorCode=run.error_code,
        errorDetail=run.error_detail,
        startedAt=run.started_at,
        completedAt=run.completed_at,
    )


@router.post(
    "/projects/{project_id}/documents/{document_id}:cancel-processing",
    response_model=DocumentProcessingRunSnapshot,
)
async def cancel_document_processing(
    document_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: IdempotencyKey,
) -> DocumentProcessingRunSnapshot:
    from swarmcore_application.document_processing import STAGE_LABELS_ZH

    run = await document_processing.cancel(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
        actor=scope.actor_id,
        idempotency_key=idempotency_key,
    )
    return DocumentProcessingRunSnapshot(
        processingRunId=run.id,
        businessDocumentVersionId=run.business_document_version_id,
        profileRef=run.profile_ref,
        status=run.status,
        currentStage=run.current_stage,
        stageLabel=STAGE_LABELS_ZH.get(run.current_stage, run.current_stage),
        attempt=run.attempt,
        parserRef=run.parser_ref,
        classifierRef=run.classifier_ref,
        extractorRefs=list(run.extractor_refs or []),
        errorCode=run.error_code,
        errorDetail=run.error_detail,
        provenance=dict(run.provenance or {}),
        startedAt=run.started_at,
        completedAt=run.completed_at,
    )


@router.put(
    "/projects/{project_id}/documents/{document_id}/bindings",
    response_model=DocumentSnapshot,
)
async def update_document_bindings(
    document_id: UUID,
    body: UpdateDocumentBindingsRequest,
    scope: Scope,
    session: Session,
) -> DocumentSnapshot:
    await documents.update_bindings(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        document_id=document_id,
        business_object_ids=body.business_object_ids,
        business_work_keys=body.business_work_keys,
        actor=scope.actor_id,
    )
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


@router.get(
    "/projects/{project_id}/business-works/{work_key}/document-requirements",
    response_model=DocumentRequirementListResponse,
)
async def list_work_document_requirements(
    work_key: str,
    scope: Scope,
    session: Session,
) -> DocumentRequirementListResponse:
    summary = await business_works.get_work(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        work_key=work_key,
    )
    profile_ref, requirements = document_requirements.from_pack_documents(
        list(summary.document_requirements)
    )
    bound = await documents.current_versions_for_work(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        business_work_keys=(work_key, summary.pack_name or work_key),
    )
    counts: dict[str, int] = {}
    for document, _, _ in bound:
        counts[document.category] = counts.get(document.category, 0) + 1
    items = []
    for item in requirements:
        category = item.category or item.key
        satisfied_count = counts.get(category, 0)
        items.append(
            DocumentRequirementSnapshot(
                key=item.key,
                displayName=item.display_name,
                description=item.description,
                required=item.required,
                minCount=item.min_count,
                maxCount=item.max_count,
                acceptedMediaTypes=list(item.accepted_media_types),
                classificationLabels=list(item.classification_labels),
                processingProfileRef=item.processing_profile_ref,
                extractionSchemaRef=item.extraction_schema_ref,
                category=item.category,
                satisfiedCount=satisfied_count,
                satisfied=satisfied_count >= item.min_count,
            )
        )
    return DocumentRequirementListResponse(
        processingProfileRef=profile_ref,
        items=items,
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
    document_ids = {value.business_document_id for value in values}
    documents_by_id: dict[UUID, BusinessDocument] = {}
    if document_ids:
        documents_by_id = {
            document.id: document
            for document in await session.scalars(
                select(BusinessDocument).where(
                    BusinessDocument.id.in_(document_ids),
                    BusinessDocument.tenant_id == scope.tenant_id,
                    BusinessDocument.project_id == scope.project_id,
                )
            )
        }
    return {
        "items": [
            {
                "documentSnapshotId": value.id,
                "documentId": value.business_document_id,
                "documentVersionId": value.business_document_version_id,
                "blobId": value.blob_id,
                "businessWorkKey": value.business_work_key,
                "documentName": (
                    documents_by_id[value.business_document_id].name
                    if value.business_document_id in documents_by_id
                    else None
                ),
                "documentCategory": (
                    documents_by_id[value.business_document_id].category
                    if value.business_document_id in documents_by_id
                    else None
                ),
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
