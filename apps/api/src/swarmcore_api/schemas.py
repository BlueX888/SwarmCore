from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from swarmcore_domain import CapabilityReadiness, CapabilitySummary
from swarmcore_registry import builtin_registry

_REGISTRY_SNAPSHOT = builtin_registry().snapshot_id


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class CompileRequest(ApiModel):
    spec: dict[str, Any]
    registry_snapshot: str = Field(default=_REGISTRY_SNAPSHOT, alias="registrySnapshot")
    policy_revision: str = Field(default="m3", alias="policyRevision")


class CompileResponse(ApiModel):
    valid: bool
    plan: dict[str, Any] | None = None
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)


class EditorPosition(ApiModel):
    x: float
    y: float


class EditorViewport(ApiModel):
    x: float = 0
    y: float = 0
    zoom: float = Field(default=1, gt=0)


class EditorState(ApiModel):
    positions: dict[str, EditorPosition] = Field(default_factory=dict)
    viewport: EditorViewport = Field(default_factory=EditorViewport)


class CreateStrategyRequest(ApiModel):
    name: str = Field(min_length=1, max_length=128)
    spec: dict[str, Any]
    editor_state: EditorState = Field(default_factory=EditorState, alias="editorState")


class StrategyHandle(ApiModel):
    strategy_id: UUID = Field(alias="strategyId")
    draft_id: UUID = Field(alias="draftId")
    revision: int


class StrategySummary(ApiModel):
    strategy_id: UUID = Field(alias="strategyId")
    name: str
    lifecycle: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    draft_id: UUID | None = Field(default=None, alias="draftId")
    draft_revision: int | None = Field(default=None, alias="draftRevision")
    latest_version: int | None = Field(default=None, alias="latestVersion")


class StrategyListResponse(ApiModel):
    items: list[StrategySummary]
    total: int


class StrategyDetail(StrategySummary):
    project_id: UUID = Field(alias="projectId")


class StrategyDeleteBlockerSnapshot(ApiModel):
    code: str
    count: int
    message: str


class StrategyDeleteImpactResponse(ApiModel):
    strategy_id: UUID = Field(alias="strategyId")
    deletable: bool
    blockers: list[StrategyDeleteBlockerSnapshot] = Field(default_factory=list)


class DraftSnapshot(ApiModel):
    draft_id: UUID = Field(alias="draftId")
    strategy_id: UUID = Field(alias="strategyId")
    revision: int
    spec: dict[str, Any]
    editor_state: EditorState = Field(alias="editorState")
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)
    updated_by: str = Field(alias="updatedBy")
    updated_at: datetime = Field(alias="updatedAt")


class StrategyVersionSummary(ApiModel):
    strategy_version_id: UUID = Field(alias="strategyVersionId")
    strategy_id: UUID = Field(alias="strategyId")
    version: int
    lifecycle: str
    plan_hash: str = Field(alias="planHash")
    schema_version: str = Field(alias="schemaVersion")
    runtime_version: str = Field(alias="runtimeVersion")
    created_at: datetime = Field(alias="createdAt")


class StrategyVersionListResponse(ApiModel):
    items: list[StrategyVersionSummary]
    total: int


class StrategyVersionDetail(StrategyVersionSummary):
    spec: dict[str, Any]
    normalized_spec: dict[str, Any] = Field(alias="normalizedSpec")
    plan: dict[str, Any]


class UpdateDraftRequest(ApiModel):
    spec: dict[str, Any]
    editor_state: EditorState | None = Field(default=None, alias="editorState")


class PublishRequest(ApiModel):
    draft_id: UUID = Field(alias="draftId")
    registry_snapshot: str = Field(default=_REGISTRY_SNAPSHOT, alias="registrySnapshot")
    policy_revision: str = Field(default="m3", alias="policyRevision")


class StrategyVersionHandle(ApiModel):
    strategy_id: UUID = Field(alias="strategyId")
    strategy_version_id: UUID = Field(alias="strategyVersionId")
    version: int
    plan_hash: str = Field(alias="planHash")


class CreateProjectConfigurationRequest(ApiModel):
    name: str = Field(min_length=1, max_length=128)
    source_ref: str = Field(alias="sourceRef", min_length=1, max_length=512)
    configuration: dict[str, Any]


class ProjectConfigurationSnapshot(ApiModel):
    configuration_id: UUID = Field(alias="configurationId")
    kind: Literal["agent", "tool", "model"]
    name: str
    source_ref: str = Field(alias="sourceRef")
    configuration: dict[str, Any]
    revision: int
    created_by: str = Field(alias="createdBy")
    updated_by: str = Field(alias="updatedBy")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class ProjectConfigurationListResponse(ApiModel):
    items: list[ProjectConfigurationSnapshot]
    total: int


class CreateRunRequest(ApiModel):
    strategy_version_id: UUID | None = Field(default=None, alias="strategyVersionId")
    spec: dict[str, Any] | None = None
    input: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def has_one_strategy_source(self) -> CreateRunRequest:
        if (self.strategy_version_id is None) == (self.spec is None):
            raise ValueError("exactly one of strategyVersionId or spec is required")
        return self


class CapabilityCenterResponse(ApiModel):
    registry_snapshot: str = Field(alias="registrySnapshot")
    items: tuple[CapabilitySummary, ...]


class CapabilityRunRequest(ApiModel):
    capability_ref: str = Field(alias="capabilityRef", min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    preset_id: UUID | None = Field(default=None, alias="presetId")


class ModelProviderConfigurationRequest(ApiModel):
    logical_model: str = Field(alias="logicalModel", min_length=1, max_length=512)
    provider_url: str = Field(alias="providerUrl", min_length=1, max_length=2048)
    model_name: str = Field(alias="modelName", min_length=1, max_length=256)
    api_key: str | None = Field(default=None, alias="apiKey", max_length=8192)
    display_name: str | None = Field(default=None, alias="displayName", max_length=128)


class ModelProviderConfigurationSnapshot(ApiModel):
    logical_model: str = Field(alias="logicalModel")
    provider_url: str = Field(alias="providerUrl")
    model_name: str = Field(alias="modelName")
    api_key_configured: bool = Field(alias="apiKeyConfigured")
    display_name: str = Field(default="", alias="displayName")


class ModelProviderTestResult(ApiModel):
    connected: bool
    model_name: str = Field(alias="modelName")
    latency_ms: int = Field(alias="latencyMs")


class CapabilityPresetRequest(ApiModel):
    name: str = Field(min_length=1, max_length=128)
    capability_ref: str = Field(alias="capabilityRef", min_length=1)
    parameters: dict[str, Any]


class CapabilityPresetCopyRequest(ApiModel):
    name: str = Field(min_length=1, max_length=128)


class CapabilityPresetSnapshot(ApiModel):
    preset_id: UUID = Field(alias="presetId")
    kind: Literal["agent", "tool", "model"]
    name: str
    capability_ref: str = Field(alias="capabilityRef")
    parameters: dict[str, Any]
    revision: int
    readiness: CapabilityReadiness | None = None
    created_by: str = Field(alias="createdBy")
    updated_by: str = Field(alias="updatedBy")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class CapabilityPresetListResponse(ApiModel):
    items: list[CapabilityPresetSnapshot]
    total: int


class RunHandle(ApiModel):
    run_id: UUID = Field(alias="runId")
    status: str
    command_id: UUID = Field(alias="commandId")
    command_status: str = Field(alias="commandStatus")
    plan_hash: str = Field(alias="planHash")


class HumanResponseRequest(ApiModel):
    value: dict[str, Any] = Field(default_factory=dict)


class ApprovalSnapshot(ApiModel):
    approval_id: UUID = Field(alias="approvalId")
    run_id: UUID = Field(alias="runId")
    node_key: str = Field(alias="nodeKey")
    prompt: str
    input_schema: dict[str, Any] = Field(alias="inputSchema")
    status: str
    allowed_actions: list[str] = Field(default_factory=list, alias="allowedActions")
    requested_by: str = Field(alias="requestedBy")
    handled_by: str | None = Field(default=None, alias="handledBy")
    created_at: datetime = Field(alias="createdAt")
    handled_at: datetime | None = Field(default=None, alias="handledAt")


class ApprovalListResponse(ApiModel):
    items: list[ApprovalSnapshot]
    total: int


class ExternalInputSnapshot(ApiModel):
    input_request_id: UUID = Field(alias="inputRequestId")
    run_id: UUID = Field(alias="runId")
    node_key: str = Field(alias="nodeKey")
    prompt: str
    input_schema: dict[str, Any] = Field(alias="inputSchema")
    status: str
    allowed_actions: list[str] = Field(default_factory=list, alias="allowedActions")
    requested_by: str = Field(alias="requestedBy")
    handled_by: str | None = Field(default=None, alias="handledBy")
    created_at: datetime = Field(alias="createdAt")
    handled_at: datetime | None = Field(default=None, alias="handledAt")


class ExternalInputListResponse(ApiModel):
    items: list[ExternalInputSnapshot]
    total: int


class RunSnapshot(ApiModel):
    run_id: UUID = Field(alias="runId")
    status: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    output_ref: str | None = Field(alias="outputRef")
    snapshot_seq: int = Field(alias="snapshotSeq")
    earliest_available_seq: int = Field(alias="earliestAvailableSeq")
    plan_hash: str = Field(alias="planHash")
    usage: dict[str, Any] = Field(default_factory=dict)
    task_counts: dict[str, int] = Field(default_factory=dict, alias="taskCounts")
    allowed_actions: list[str] = Field(default_factory=list, alias="allowedActions")
    tasks: list[TaskSnapshot] = Field(default_factory=list)
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")


class TaskSnapshot(ApiModel):
    task_id: UUID = Field(alias="taskId")
    node_key: str = Field(alias="nodeKey")
    node_type: str = Field(alias="nodeType")
    status: str
    dependencies: list[str]
    error: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    retry_generation: int = Field(default=0, alias="retryGeneration")
    allowed_actions: list[str] = Field(default_factory=list, alias="allowedActions")


class RunListResponse(ApiModel):
    items: list[RunSnapshot]
    total: int


class Problem(ApiModel):
    type: str = "about:blank"
    title: str
    status: int
    code: str
    detail: str
    trace_id: str | None = Field(default=None, alias="traceId")
    blockers: list[StrategyDeleteBlockerSnapshot] | None = None


class JsonRpcRequest(ApiModel):
    jsonrpc: Literal["2.0"]
    id: str | int | None = None
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


class ArtifactSnapshot(ApiModel):
    artifact_id: UUID = Field(alias="artifactId")
    run_id: UUID = Field(alias="runId")
    kind: str
    filename: str
    media_type: str = Field(alias="mediaType")
    size_bytes: int = Field(alias="sizeBytes")
    sha256: str
    status: str
    version: int
    retention_until: datetime = Field(alias="retentionUntil")


class ArtifactListResponse(ApiModel):
    items: list[ArtifactSnapshot]
    total: int


class ArtifactDownloadGrantResponse(ApiModel):
    artifact_id: UUID = Field(alias="artifactId")
    download_ref: str = Field(alias="downloadRef")
    expires_at: datetime = Field(alias="expiresAt")


class AuditSnapshot(ApiModel):
    audit_id: UUID = Field(alias="auditId")
    actor_id: str = Field(alias="actorId")
    action: str
    resource_type: str = Field(alias="resourceType")
    resource_id: str = Field(alias="resourceId")
    outcome: str
    policy_revision: str | None = Field(default=None, alias="policyRevision")
    run_id: UUID | None = Field(default=None, alias="runId")
    metadata: dict[str, Any]
    occurred_at: datetime = Field(alias="occurredAt")


class AuditListResponse(ApiModel):
    items: list[AuditSnapshot]
    total: int


class CreateWebhookRequest(ApiModel):
    url: str = Field(min_length=1, max_length=2048)
    secret_ref: str = Field(alias="secretRef", min_length=1, max_length=512)
    event_types: list[str] = Field(default_factory=list, alias="eventTypes")


class WebhookSnapshot(ApiModel):
    endpoint_id: UUID = Field(alias="endpointId")
    url: str
    secret_ref: str = Field(alias="secretRef")
    event_types: list[str] = Field(alias="eventTypes")
    status: str
    failure_count: int = Field(alias="failureCount")
    created_at: datetime = Field(alias="createdAt")


class WebhookListResponse(ApiModel):
    items: list[WebhookSnapshot]
    total: int
