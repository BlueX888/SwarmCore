from __future__ import annotations

from datetime import datetime
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
    business_work_keys: list[str] = Field(
        default_factory=list, alias="businessWorkKeys"
    )
    retention_days: int = Field(default=365, alias="retentionDays", ge=1, le=3650)
    document_id: UUID | None = Field(default=None, alias="documentId")


class CompleteDocumentUploadRequest(BusinessModel):
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")


class DocumentUploadHandle(BusinessModel):
    document_id: UUID = Field(alias="documentId")
    upload_id: UUID = Field(alias="uploadId")
    blob_id: UUID = Field(alias="blobId")
    version: int
    upload_ref: str = Field(alias="uploadRef")
    capability_token: str | None = Field(alias="capabilityToken")
    status: str


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
    business_object_ids: list[UUID] = Field(
        default_factory=list, alias="businessObjectIds"
    )
    business_work_keys: list[str] = Field(
        default_factory=list, alias="businessWorkKeys"
    )
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
    payload: dict[str, Any]
    subjects: list[CaseSubjectRequest] = Field(default_factory=list)
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
