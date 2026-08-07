from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BusinessModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class CapabilityPackSnapshot(BusinessModel):
    pack_id: UUID = Field(alias="packId")
    name: str
    version_id: UUID = Field(alias="versionId")
    version: str
    content_hash: str = Field(alias="contentHash")
    manifest: dict[str, Any]
    enabled: bool
    binding_status: str | None = Field(default=None, alias="bindingStatus")
    configuration: dict[str, Any] = Field(default_factory=dict)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    delete_blocked_reason: str | None = Field(default=None, alias="deleteBlockedReason")


class CapabilityPackListResponse(BusinessModel):
    items: list[CapabilityPackSnapshot]


class EnableCapabilityPackRequest(BusinessModel):
    configuration: dict[str, Any] = Field(default_factory=dict)


class CreateCapabilityPackRequest(BusinessModel):
    manifest: dict[str, Any]
    strategy_version_id: UUID = Field(alias="strategyVersionId")


class CreateWorkItemRequest(BusinessModel):
    work_item_type: str = Field(alias="workItemType", min_length=1, max_length=128)
    payload: dict[str, Any]
    owner: str | None = Field(default=None, max_length=256)


class UpdateWorkItemRequest(BusinessModel):
    payload: dict[str, Any]
    owner: str | None = Field(default=None, max_length=256)


class WorkItemSnapshot(BusinessModel):
    work_item_id: UUID = Field(alias="workItemId")
    work_item_type: str = Field(alias="workItemType")
    schema_version: str = Field(alias="schemaVersion")
    payload: dict[str, Any]
    status: str
    owner: str | None
    revision_id: UUID = Field(alias="revisionId")
    revision: int
    payload_hash: str = Field(alias="payloadHash")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class WorkItemListResponse(BusinessModel):
    items: list[WorkItemSnapshot]
    total: int


class InitiateAttachmentRequest(BusinessModel):
    document_type: str = Field(alias="documentType", min_length=1, max_length=128)
    filename: str = Field(min_length=1, max_length=512)
    media_type: str = Field(alias="mediaType", min_length=1, max_length=256)
    size_bytes: int = Field(alias="sizeBytes", gt=0)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    retention_days: int = Field(default=30, alias="retentionDays", ge=1, le=3650)


class AttachmentUploadHandle(BusinessModel):
    attachment_id: UUID = Field(alias="attachmentId")
    blob_id: UUID = Field(alias="blobId")
    upload_ref: str = Field(alias="uploadRef")
    capability_token: str | None = Field(alias="capabilityToken")
    object_key: str = Field(alias="objectKey")
    status: str


class CompleteAttachmentRequest(BusinessModel):
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    scan_status: Literal["CLEAN", "INFECTED", "ERROR"] = Field(alias="scanStatus")


class InitiateDocumentRequest(BusinessModel):
    name: str = Field(min_length=1, max_length=512)
    category: str = Field(min_length=1, max_length=128)
    tags: list[str] = Field(default_factory=list)
    filename: str = Field(min_length=1, max_length=512)
    media_type: str = Field(alias="mediaType", min_length=1, max_length=256)
    size_bytes: int = Field(alias="sizeBytes", gt=0)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    business_object_ids: list[UUID] = Field(default_factory=list, alias="businessObjectIds")
    business_work_keys: list[str] = Field(default_factory=list, alias="businessWorkKeys")
    retention_days: int = Field(default=365, alias="retentionDays", ge=1, le=3650)
    document_id: UUID | None = Field(default=None, alias="documentId")


class CompleteDocumentUploadRequest(BusinessModel):
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    upload_batch_id: UUID | None = Field(default=None, alias="uploadBatchId")
    profile_ref: str | None = Field(default=None, alias="profileRef", max_length=256)
    extraction_schema_ref: str | None = Field(
        default=None, alias="extractionSchemaRef", max_length=256
    )
    classification_labels: list[dict[str, str]] = Field(
        default_factory=list, alias="classificationLabels"
    )


class CreateUploadBatchRequest(BusinessModel):
    source: str = Field(default="web", min_length=1, max_length=64)
    context: dict[str, Any] = Field(default_factory=dict)


class UploadBatchSnapshot(BusinessModel):
    batch_id: UUID = Field(alias="batchId")
    source: str
    context: dict[str, Any]
    status: str
    file_count: int = Field(alias="fileCount")
    succeeded_count: int = Field(alias="succeededCount")
    failed_count: int = Field(alias="failedCount")
    created_by: str = Field(alias="createdBy")
    created_at: datetime = Field(alias="createdAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")


class DocumentProcessingRunSnapshot(BusinessModel):
    processing_run_id: UUID = Field(alias="processingRunId")
    business_document_version_id: UUID = Field(alias="businessDocumentVersionId")
    profile_ref: str = Field(alias="profileRef")
    status: str
    current_stage: str = Field(alias="currentStage")
    stage_label: str = Field(alias="stageLabel")
    attempt: int
    parser_ref: str | None = Field(default=None, alias="parserRef")
    classifier_ref: str | None = Field(default=None, alias="classifierRef")
    extractor_refs: list[str] = Field(default_factory=list, alias="extractorRefs")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_detail: str | None = Field(default=None, alias="errorDetail")
    started_at: datetime = Field(alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    provenance: dict[str, Any] = Field(default_factory=dict)


class DocumentProcessingEventSnapshot(BusinessModel):
    event_id: UUID = Field(alias="eventId")
    event_seq: int = Field(alias="eventSeq")
    processing_run_id: UUID = Field(alias="processingRunId")
    business_document_version_id: UUID = Field(alias="businessDocumentVersionId")
    type: str
    stage: str
    payload: dict[str, Any]
    input_hash: str | None = Field(default=None, alias="inputHash")
    output_hash: str | None = Field(default=None, alias="outputHash")
    tool_ref: str | None = Field(default=None, alias="toolRef")
    actor_id: str = Field(alias="actorId")
    trace_id: str | None = Field(default=None, alias="traceId")
    occurred_at: datetime = Field(alias="occurredAt")


class DocumentProcessingEventListResponse(BusinessModel):
    items: list[DocumentProcessingEventSnapshot]
    next_after: int = Field(alias="nextAfter")


class DocumentProcessingResultSnapshot(BusinessModel):
    result_id: UUID = Field(alias="resultId")
    result_type: str = Field(alias="resultType")
    result_version: int = Field(alias="resultVersion")
    status: str
    schema_ref: str | None = Field(default=None, alias="schemaRef")
    producer_ref: str | None = Field(default=None, alias="producerRef")
    result: dict[str, Any]
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confirmed_by: str | None = Field(default=None, alias="confirmedBy")
    confirmed_at: datetime | None = Field(default=None, alias="confirmedAt")
    created_at: datetime = Field(alias="createdAt")


class ConfirmClassificationRequest(BusinessModel):
    label: str = Field(min_length=1, max_length=128)
    display_name: str | None = Field(default=None, alias="displayName", max_length=256)
    expected_result_version: int | None = Field(default=None, alias="expectedResultVersion")


class ConfirmFieldsRequest(BusinessModel):
    fields: list[dict[str, Any]] = Field(default_factory=list)
    accept_high_confidence: bool = Field(default=False, alias="acceptHighConfidence")
    expected_result_version: int | None = Field(default=None, alias="expectedResultVersion")


class ReprocessDocumentRequest(BusinessModel):
    profile_ref: str | None = Field(default=None, alias="profileRef")
    extraction_schema_ref: str | None = Field(default=None, alias="extractionSchemaRef")
    classification_labels: list[dict[str, str]] = Field(
        default_factory=list, alias="classificationLabels"
    )


class ResumeDocumentUploadRequest(BusinessModel):
    profile_ref: str | None = Field(default=None, alias="profileRef", max_length=256)
    extraction_schema_ref: str | None = Field(
        default=None, alias="extractionSchemaRef", max_length=256
    )
    classification_labels: list[dict[str, str]] = Field(
        default_factory=list, alias="classificationLabels"
    )


class UpdateDocumentBindingsRequest(BusinessModel):
    business_object_ids: list[UUID] = Field(default_factory=list, alias="businessObjectIds")
    business_work_keys: list[str] = Field(default_factory=list, alias="businessWorkKeys")


class DocumentRequirementSnapshot(BusinessModel):
    key: str
    display_name: str = Field(alias="displayName")
    description: str = ""
    required: bool = True
    min_count: int = Field(default=1, alias="minCount")
    max_count: int | None = Field(default=None, alias="maxCount")
    accepted_media_types: list[str] = Field(default_factory=list, alias="acceptedMediaTypes")
    classification_labels: list[str] = Field(default_factory=list, alias="classificationLabels")
    processing_profile_ref: str | None = Field(default=None, alias="processingProfileRef")
    extraction_schema_ref: str | None = Field(default=None, alias="extractionSchemaRef")
    category: str | None = None
    satisfied_count: int = Field(default=0, alias="satisfiedCount")
    satisfied: bool = False


class DocumentRequirementListResponse(BusinessModel):
    processing_profile_ref: str | None = Field(default=None, alias="processingProfileRef")
    items: list[DocumentRequirementSnapshot]


class DocumentUploadHandle(BusinessModel):
    document_id: UUID = Field(alias="documentId")
    upload_id: UUID = Field(alias="uploadId")
    blob_id: UUID = Field(alias="blobId")
    version: int
    upload_ref: str = Field(alias="uploadRef")
    capability_token: str | None = Field(alias="capabilityToken")
    status: str
    upload_batch_id: UUID | None = Field(default=None, alias="uploadBatchId")


class DocumentVersionSnapshot(BusinessModel):
    document_version_id: UUID = Field(alias="documentVersionId")
    blob_id: UUID = Field(alias="blobId")
    version: int
    filename: str
    media_type: str = Field(alias="mediaType")
    size_bytes: int = Field(alias="sizeBytes")
    sha256: str
    processing_status: str = Field(alias="processingStatus")
    created_at: datetime = Field(alias="createdAt")


class DocumentSnapshot(BusinessModel):
    document_id: UUID = Field(alias="documentId")
    name: str
    category: str
    tags: list[str]
    status: str
    current_version: int = Field(alias="currentVersion")
    updated_at: datetime = Field(alias="updatedAt")
    current: DocumentVersionSnapshot | None = None
    business_object_ids: list[UUID] = Field(default_factory=list, alias="businessObjectIds")
    business_work_keys: list[str] = Field(default_factory=list, alias="businessWorkKeys")
    versions: list[DocumentVersionSnapshot] = Field(default_factory=list)


class DocumentListResponse(BusinessModel):
    items: list[DocumentSnapshot]


class EvaluationSnapshot(BusinessModel):
    evaluation_id: UUID = Field(alias="evaluationId")
    work_item_id: UUID = Field(alias="workItemId")
    work_item_revision_id: UUID = Field(alias="workItemRevisionId")
    run_id: UUID = Field(alias="runId")
    status: str
    result: dict[str, Any] | None
    capability_pack_version_id: UUID = Field(alias="capabilityPackVersionId")
    rule_set_version_id: UUID | None = Field(alias="ruleSetVersionId")
    plan_hash: str = Field(alias="planHash")
    attachment_manifest_hash: str = Field(alias="attachmentManifestHash")
    registry_snapshot: dict[str, Any] = Field(alias="registrySnapshot")
    created_at: datetime = Field(alias="createdAt")


class FindingSnapshot(BusinessModel):
    finding_id: UUID = Field(alias="findingId")
    work_item_id: UUID = Field(alias="workItemId")
    evaluation_id: UUID = Field(alias="evaluationId")
    rule_key: str = Field(alias="ruleKey")
    code: str
    category: str
    severity: str
    status: str
    title: str
    detail: str
    evidence: dict[str, Any]


class FindingListResponse(BusinessModel):
    items: list[FindingSnapshot]


class FindingActionRequest(BusinessModel):
    action: Literal["ACKNOWLEDGE", "ASSIGN", "WAIVE", "RESOLVE", "REOPEN"]
    reason: str | None = None
    assignee: str | None = None
    expires_at: datetime | None = Field(default=None, alias="expiresAt")


class ReportSnapshot(BusinessModel):
    report_id: UUID = Field(alias="reportId")
    evaluation_id: UUID = Field(alias="evaluationId")
    format: str
    template_version: str = Field(alias="templateVersion")
    result_schema_version: str = Field(alias="resultSchemaVersion")
    content: dict[str, Any] | None
    content_hash: str = Field(alias="contentHash")
    created_at: datetime = Field(alias="createdAt")


class ReportListResponse(BusinessModel):
    items: list[ReportSnapshot]


class CreateRuleSetRequest(BusinessModel):
    name: str = Field(min_length=1, max_length=128)
    purpose: str = Field(min_length=1, max_length=512)
    rules: dict[str, Any]


class UpdateRuleSetDraftRequest(BusinessModel):
    rules: dict[str, Any]


class ValidateRuleSetRequest(BusinessModel):
    attachments: list[dict[str, Any]] | None = None


class RuleSetDraftSnapshot(BusinessModel):
    rule_set_id: UUID = Field(alias="ruleSetId")
    draft_id: UUID = Field(alias="draftId")
    revision: int
    rules: dict[str, Any]


class RuleSetValidationResponse(BusinessModel):
    valid: bool
    normalized_rules: dict[str, Any] = Field(alias="normalizedRules")
    preview: dict[str, Any] | None = None


class RuleSetVersionSnapshot(BusinessModel):
    rule_set_id: UUID = Field(alias="ruleSetId")
    rule_set_version_id: UUID = Field(alias="ruleSetVersionId")
    version: int
    schema_version: str = Field(alias="schemaVersion")
    content_hash: str = Field(alias="contentHash")
    rules: dict[str, Any]


class CreateBusinessObjectRequest(BusinessModel):
    object_type: str = Field(alias="objectType", pattern=r"^[a-z][a-z0-9-]{0,127}$")
    canonical_key: str = Field(alias="canonicalKey", min_length=1, max_length=256)
    schema_ref: str = Field(alias="schemaRef", min_length=1, max_length=256)
    data: dict[str, Any]
    provenance: dict[str, Any] = Field(default_factory=dict)
    effective_at: datetime | None = Field(default=None, alias="effectiveAt")


class CreateBusinessObjectVersionRequest(BusinessModel):
    schema_ref: str = Field(alias="schemaRef", min_length=1, max_length=256)
    data: dict[str, Any]
    provenance: dict[str, Any] = Field(default_factory=dict)
    effective_at: datetime | None = Field(default=None, alias="effectiveAt")


class CreateBusinessObjectRelationRequest(BusinessModel):
    source_object_id: UUID = Field(alias="sourceObjectId")
    source_version_id: UUID = Field(alias="sourceVersionId")
    target_object_id: UUID = Field(alias="targetObjectId")
    target_version_id: UUID = Field(alias="targetVersionId")
    relation_type: str = Field(alias="relationType", min_length=1, max_length=128)
    assertion_state: Literal["ACTIVE", "RETRACTED"] = Field(
        default="ACTIVE", alias="assertionState"
    )
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    supersedes_relation_id: UUID | None = Field(default=None, alias="supersedesRelationId")


class CaseSubjectRequest(BusinessModel):
    business_object_id: UUID = Field(alias="businessObjectId")
    business_object_version_id: UUID = Field(alias="businessObjectVersionId")
    role: Literal["PRIMARY", "COMPARISON", "EVIDENCE", "RELATED"]
    subject_key: str = Field(alias="subjectKey", min_length=1, max_length=128)


class CreateCaseRequest(BusinessModel):
    scenario_type: str = Field(alias="scenarioType", min_length=1, max_length=128)
    business_work_key: str | None = Field(
        default=None, alias="businessWorkKey", min_length=1, max_length=128
    )
    payload: dict[str, Any]
    subjects: list[CaseSubjectRequest] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list, alias="documentIds")
    owner: str | None = Field(default=None, max_length=256)


class UpdateCaseRequest(BusinessModel):
    payload: dict[str, Any]
    subjects: list[CaseSubjectRequest] | None = None
    owner: str | None = Field(default=None, max_length=256)


class CreateDecisionAssetRequest(BusinessModel):
    name: str = Field(min_length=1, max_length=128)
    purpose: str = Field(min_length=1, max_length=512)
    definition: dict[str, Any]


class UpdateDecisionDraftRequest(BusinessModel):
    definition: dict[str, Any]
    expected_revision: int = Field(alias="expectedRevision", ge=1)


class CreateConnectionRequest(BusinessModel):
    name: str = Field(min_length=1, max_length=128)
    connector_ref: str = Field(alias="connectorRef", min_length=1, max_length=256)
    configuration: dict[str, Any] = Field(default_factory=dict)
    credential_ref: str = Field(alias="credentialRef", min_length=1, max_length=512)
    policy_ref: str | None = Field(default=None, alias="policyRef", max_length=256)


class CreateConnectionVersionRequest(BusinessModel):
    configuration: dict[str, Any] = Field(default_factory=dict)
    credential_ref: str = Field(alias="credentialRef", min_length=1, max_length=512)
    policy_ref: str | None = Field(default=None, alias="policyRef", max_length=256)


class CreateResourceRequest(BusinessModel):
    connection_id: UUID = Field(alias="connectionId")
    resource_kind: str = Field(alias="resourceKind")
    name: str = Field(min_length=1, max_length=128)
    locator: dict[str, Any]
    schema_ref: str | None = Field(default=None, alias="schemaRef")
    media_type: str | None = Field(default=None, alias="mediaType")
    sensitivity: str = "INTERNAL"


class BindDecisionRequest(BusinessModel):
    rule_set_version_id: UUID = Field(alias="ruleSetVersionId")


class BindResourceRequest(BusinessModel):
    resource_definition_id: UUID = Field(alias="resourceDefinitionId")
    access_mode: Literal["READ", "WRITE", "SUBSCRIBE"] = Field(alias="accessMode")
    mapping_configuration: dict[str, Any] = Field(
        default_factory=dict, alias="mappingConfiguration"
    )


class BusinessWorkBlockerSnapshot(BusinessModel):
    code: str
    message: str
    ref: str | None = None


class BusinessWorkFunctionSnapshot(BusinessModel):
    name: str
    description: str


class BusinessCaseDefinitionSnapshot(BusinessModel):
    type: str
    schema_ref: str = Field(alias="schema")
    subjects_required: bool = Field(default=True, alias="subjectsRequired")
    subject_roles: list[dict[str, Any]] = Field(default_factory=list, alias="subjectRoles")


class BusinessWorkSnapshot(BusinessModel):
    work_key: str = Field(alias="workKey")
    name: str
    short_name: str = Field(alias="shortName")
    category: str
    summary: str
    status: Literal["planned", "not_configured", "incomplete", "runnable", "unavailable"]
    status_label: str = Field(alias="statusLabel")
    qualification_status: Literal[
        "planned", "unverified", "local_verified", "production_verified"
    ] = Field(
        alias="qualificationStatus"
    )
    qualification_label: str = Field(alias="qualificationLabel")
    pack_name: str | None = Field(default=None, alias="packName")
    pack_version_id: UUID | None = Field(default=None, alias="packVersionId")
    pack_version: str | None = Field(default=None, alias="packVersion")
    enabled: bool
    binding_status: str | None = Field(default=None, alias="bindingStatus")
    blockers: list[BusinessWorkBlockerSnapshot] = Field(default_factory=list)
    agents: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    document_requirements: list[dict[str, Any]] = Field(
        default_factory=list, alias="documentRequirements"
    )
    document_binding_keys: list[str] = Field(default_factory=list, alias="documentBindingKeys")
    decision_slots: list[dict[str, Any]] = Field(default_factory=list, alias="decisionSlots")
    functions: list[BusinessWorkFunctionSnapshot] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    work_item_type: str | None = Field(default=None, alias="workItemType")
    case_based: bool = Field(default=False, alias="caseBased")
    bound_strategy_version_id: UUID | None = Field(default=None, alias="boundStrategyVersionId")
    bound_strategy_name: str | None = Field(default=None, alias="boundStrategyName")
    bound_strategy_version: int | None = Field(default=None, alias="boundStrategyVersion")
    case_definition: BusinessCaseDefinitionSnapshot | None = Field(
        default=None, alias="caseDefinition"
    )


class BusinessWorkListResponse(BusinessModel):
    items: list[BusinessWorkSnapshot]


class ProjectOverviewCountsSnapshot(BusinessModel):
    pending_approvals: int = Field(alias="pendingApprovals")
    pending_inputs: int = Field(alias="pendingInputs")
    documents_available: int = Field(alias="documentsAvailable")
    documents_review_required: int = Field(alias="documentsReviewRequired")
    documents_failed: int = Field(alias="documentsFailed")
    active_runs: int = Field(alias="activeRuns")
    waiting_runs: int = Field(alias="waitingRuns")


class ProjectOverviewReadinessSnapshot(BusinessModel):
    required_documents: int = Field(alias="requiredDocuments")
    satisfied_documents: int = Field(alias="satisfiedDocuments")
    documents_ready: bool = Field(alias="documentsReady")
    ready_to_start: bool = Field(alias="readyToStart")


class ProjectOverviewRunSnapshot(BusinessModel):
    run_id: UUID = Field(alias="runId")
    business_work_key: str | None = Field(default=None, alias="businessWorkKey")
    business_work_name: str = Field(alias="businessWorkName")
    status: str
    strategy_version_id: UUID = Field(alias="strategyVersionId")
    event_count: int = Field(alias="eventCount")
    task_count: int = Field(alias="taskCount")
    operator_name: str = Field(alias="operatorName")
    created_at: datetime = Field(alias="createdAt")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    failure_reason: str | None = Field(default=None, alias="failureReason")
    cancel_reason: str | None = Field(default=None, alias="cancelReason")


class ProjectOverviewWorkSnapshot(BusinessModel):
    work_key: str = Field(alias="workKey")
    name: str
    short_name: str = Field(alias="shortName")
    category: Literal["foundation", "business", "governance"]
    status: Literal["planned", "not_configured", "incomplete", "runnable", "unavailable"]
    status_label: str = Field(alias="statusLabel")
    qualification_status: Literal[
        "planned", "unverified", "local_verified", "production_verified"
    ] = Field(
        alias="qualificationStatus"
    )
    qualification_label: str = Field(alias="qualificationLabel")
    blockers: list[BusinessWorkBlockerSnapshot] = Field(default_factory=list)
    readiness: ProjectOverviewReadinessSnapshot
    active_run_id: UUID | None = Field(default=None, alias="activeRunId")
    latest_run: ProjectOverviewRunSnapshot | None = Field(default=None, alias="latestRun")


class ProjectOverviewSnapshot(BusinessModel):
    generated_at: datetime = Field(alias="generatedAt")
    counts: ProjectOverviewCountsSnapshot
    business_works: list[ProjectOverviewWorkSnapshot] = Field(alias="businessWorks")
    recent_runs: list[ProjectOverviewRunSnapshot] = Field(alias="recentRuns")


class BindBusinessWorkStrategyRequest(BusinessModel):
    strategy_version_id: UUID = Field(alias="strategyVersionId")


class AssessmentDetailSnapshot(BusinessModel):
    assessment_id: UUID = Field(alias="assessmentId")
    evaluation_id: UUID = Field(alias="evaluationId")
    case_id: UUID = Field(alias="caseId")
    work_item_id: UUID = Field(alias="workItemId")
    work_item_revision_id: UUID = Field(alias="workItemRevisionId")
    run_id: UUID = Field(alias="runId")
    status: str
    result: dict[str, Any] | None
    capability_pack_version_id: UUID = Field(alias="capabilityPackVersionId")
    plan_hash: str = Field(alias="planHash")
    attachment_manifest_hash: str = Field(alias="attachmentManifestHash")
    registry_snapshot: dict[str, Any] = Field(alias="registrySnapshot")
    created_at: datetime = Field(alias="createdAt")
    case_payload: dict[str, Any] | None = Field(default=None, alias="casePayload")
    case_status: str | None = Field(default=None, alias="caseStatus")
    scenario_type: str | None = Field(default=None, alias="scenarioType")
    owner: str | None = None


class InvoiceAssuranceBatchItemRequest(BusinessModel):
    payload: dict[str, Any]
    subjects: list[CaseSubjectRequest] = Field(min_length=1)
    owner: str | None = Field(default=None, max_length=256)


class CreateInvoiceAssuranceBatchRequest(BusinessModel):
    items: list[InvoiceAssuranceBatchItemRequest] = Field(min_length=1, max_length=100)
    max_parallelism: int = Field(default=3, ge=1, le=10, alias="maxParallelism")


class InvoiceAssuranceBatchItemSnapshot(BusinessModel):
    ordinal: int
    case_id: UUID = Field(alias="caseId")
    evaluation_id: UUID = Field(alias="evaluationId")
    status: str
    outcome: str | None = None


class InvoiceAssuranceBatchSnapshot(BusinessModel):
    batch_id: UUID = Field(alias="batchId")
    status: str
    total_items: int = Field(alias="totalItems")
    max_parallelism: int = Field(alias="maxParallelism")
    requested_by: str = Field(alias="requestedBy")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    items: list[InvoiceAssuranceBatchItemSnapshot]


class InvoiceRuleTrendBucket(BusinessModel):
    period: str
    assessments: int
    rule_hits: int = Field(alias="ruleHits")
    outcomes: dict[str, int]


class InvoiceRuleTrendItem(BusinessModel):
    rule_id: str = Field(alias="ruleId")
    status: str
    count: int


class InvoiceRuleTrendSnapshot(BusinessModel):
    bucket: Literal["day", "week", "month"]
    total_assessments: int = Field(alias="totalAssessments")
    outcomes: dict[str, int]
    buckets: list[InvoiceRuleTrendBucket]
    top_rules: list[InvoiceRuleTrendItem] = Field(alias="topRules")


class CreateContractPerformanceCaseRequest(BusinessModel):
    contract_object_id: UUID = Field(alias="contractObjectId")
    timezone: str = Field(default="Asia/Shanghai", min_length=1, max_length=128)
    currency: str = Field(default="CNY", pattern=r"^[A-Z]{3}$")


class ContractPerformanceCaseSnapshot(BusinessModel):
    case_id: UUID = Field(alias="caseId")
    contract_object_id: UUID = Field(alias="contractObjectId")
    status: str
    timezone: str
    currency: str
    active_plan_version_id: UUID | None = Field(default=None, alias="activePlanVersionId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class InitializeContractPerformanceRequest(BusinessModel):
    as_of: date = Field(alias="asOf")
    candidates: dict[str, Any]
    coverage: dict[str, Any] = Field(default_factory=dict)
    selection_manifest_hash: str | None = Field(default=None, alias="selectionManifestHash")
    configuration_hash: str | None = Field(default=None, alias="configurationHash")


class PublishContractPerformancePlanRequest(BusinessModel):
    approval_id: UUID = Field(alias="approvalId")
    confirmations: list[dict[str, Any]] = Field(default_factory=list)


class ContractPerformancePlanSnapshot(BusinessModel):
    plan_version_id: UUID = Field(alias="planVersionId")
    case_id: UUID = Field(alias="caseId")
    version: int
    status: str
    original_baseline: dict[str, Any] = Field(alias="originalBaseline")
    current_baseline: dict[str, Any] = Field(alias="currentBaseline")
    coverage: dict[str, Any]
    change_history: dict[str, Any] = Field(alias="changeHistory")
    review_decisions: list[dict[str, Any]] = Field(alias="reviewDecisions")
    plan_hash: str = Field(alias="planHash")
    effective_at: datetime | None = Field(default=None, alias="effectiveAt")
    published_by: str | None = Field(default=None, alias="publishedBy")


class CollectContractPerformanceRequest(BusinessModel):
    as_of: date = Field(alias="asOf")
    evidence: list[dict[str, Any]] = Field(default_factory=list, max_length=1000)
    candidate_links: list[dict[str, Any]] = Field(default_factory=list, alias="candidateLinks")
    sources: list[dict[str, Any]] = Field(default_factory=list, max_length=5)
    manual_documents: list[UUID] = Field(default_factory=list, alias="manualDocuments")
    collection_status: Literal["COMPLETE", "PARTIAL", "FAILED"] = Field(
        default="COMPLETE", alias="collectionStatus"
    )
    approved_exceptions: list[str] = Field(default_factory=list, alias="approvedExceptions")


class ContractPerformanceSnapshotResponse(BusinessModel):
    snapshot_id: UUID = Field(alias="snapshotId")
    case_id: UUID = Field(alias="caseId")
    plan_version_id: UUID = Field(alias="planVersionId")
    as_of: datetime = Field(alias="asOf")
    status: str
    collection_status: str = Field(alias="collectionStatus")
    result: dict[str, Any]
    result_hash: str = Field(alias="resultHash")
    gantt_hash: str = Field(alias="ganttHash")
    created_at: datetime = Field(alias="createdAt")


class ContractPerformanceEvidenceListResponse(BusinessModel):
    items: list[dict[str, Any]]
    total: int


class SwarmCalibrationSandboxRequest(BusinessModel):
    enabled: bool = True
    test_command: list[str] = Field(alias="testCommand", min_length=1, max_length=32)


class RunSwarmCalibrationRequest(BusinessModel):
    calibration_mode: Literal["GITHUB_ENGINEERING_ISSUE"] = Field(
        default="GITHUB_ENGINEERING_ISSUE", alias="calibrationMode"
    )
    title: str = Field(min_length=1, max_length=256)
    issue_url: str = Field(
        alias="issueUrl",
        pattern=r"^https://(?:www\.)?github\.com/[^/]+/[^/]+/issues/[1-9][0-9]*/?$",
    )
    objective: str = Field(min_length=1, max_length=4000)
    acceptance_criteria: list[str] = Field(
        alias="acceptanceCriteria",
        min_length=1,
        max_length=20,
    )
    sandbox: SwarmCalibrationSandboxRequest
    budget: dict[str, Any] = Field(default_factory=dict)
    owner: str | None = Field(default=None, max_length=256)


class CreateSupplierRiskMonitorRequest(BusinessModel):
    case_id: UUID = Field(alias="caseId")
    supplier_name: str = Field(alias="supplierName", min_length=1, max_length=512)
    supplier_credit_code: str = Field(
        alias="supplierCreditCode", min_length=1, max_length=64
    )
    cadence: Literal["HOURLY", "DAILY", "WEEKLY"] = "DAILY"
    sources: list[dict[str, Any]] = Field(min_length=1, max_length=10)


class SupplierRiskMonitorSnapshot(BusinessModel):
    monitor_id: UUID = Field(alias="monitorId")
    case_id: UUID = Field(alias="caseId")
    supplier_name: str = Field(alias="supplierName")
    supplier_credit_code: str = Field(alias="supplierCreditCode")
    status: str
    cadence: str
    sources: list[dict[str, Any]]
    next_check_at: datetime | None = Field(default=None, alias="nextCheckAt")
    last_checked_at: datetime | None = Field(default=None, alias="lastCheckedAt")
    last_snapshot_id: UUID | None = Field(default=None, alias="lastSnapshotId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class SupplierRiskHistoryItem(BusinessModel):
    snapshot_id: UUID = Field(alias="snapshotId")
    evaluation_id: UUID = Field(alias="evaluationId")
    as_of: datetime = Field(alias="asOf")
    decision: str
    risk_level: str = Field(alias="riskLevel")
    risk_score: int = Field(alias="riskScore")
    source_coverage: dict[str, Any] = Field(alias="sourceCoverage")
    change_summary: dict[str, Any] = Field(alias="changeSummary")
    result_hash: str = Field(alias="resultHash")
    result: dict[str, Any]


class SupplierRiskHistoryResponse(BusinessModel):
    items: list[SupplierRiskHistoryItem]


class SupplierRiskAlertSnapshot(BusinessModel):
    alert_id: UUID = Field(alias="alertId")
    monitor_id: UUID = Field(alias="monitorId")
    snapshot_id: UUID = Field(alias="snapshotId")
    alert_type: str = Field(alias="alertType")
    severity: str
    status: str
    title: str
    details: dict[str, Any]
    evidence: list[dict[str, Any]]
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class SupplierRiskAlertListResponse(BusinessModel):
    items: list[SupplierRiskAlertSnapshot]


class CreateSupplierRiskWorkOrderRequest(BusinessModel):
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"
    assignee: str | None = Field(default=None, max_length=256)
    due_at: datetime | None = Field(default=None, alias="dueAt")


class UpdateSupplierRiskWorkOrderRequest(BusinessModel):
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED", "REJECTED", "CLOSED"]
    assignee: str | None = Field(default=None, max_length=256)
    resolution: dict[str, Any] | None = None
    comment: str | None = Field(default=None, max_length=2048)


class SupplierRiskWorkOrderSnapshot(BusinessModel):
    work_order_id: UUID = Field(alias="workOrderId")
    alert_id: UUID = Field(alias="alertId")
    status: str
    priority: str
    assignee: str | None = None
    due_at: datetime | None = Field(default=None, alias="dueAt")
    resolution: dict[str, Any] | None = None
    created_by: str = Field(alias="createdBy")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    actions: list[dict[str, Any]] = Field(default_factory=list)


class SupplierRiskWorkOrderListResponse(BusinessModel):
    items: list[SupplierRiskWorkOrderSnapshot]
