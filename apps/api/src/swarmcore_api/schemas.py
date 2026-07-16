from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class CompileRequest(ApiModel):
    spec: dict[str, Any]
    registry_snapshot: str = Field(default="inline", alias="registrySnapshot")
    policy_revision: str = Field(default="phase1", alias="policyRevision")


class CompileResponse(ApiModel):
    valid: bool
    plan: dict[str, Any] | None = None
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)


class CreateStrategyRequest(ApiModel):
    name: str = Field(min_length=1, max_length=128)
    spec: dict[str, Any]


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


class DraftSnapshot(ApiModel):
    draft_id: UUID = Field(alias="draftId")
    strategy_id: UUID = Field(alias="strategyId")
    revision: int
    spec: dict[str, Any]
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


class PublishRequest(ApiModel):
    draft_id: UUID = Field(alias="draftId")
    registry_snapshot: str = Field(default="phase1", alias="registrySnapshot")
    policy_revision: str = Field(default="phase1", alias="policyRevision")


class StrategyVersionHandle(ApiModel):
    strategy_id: UUID = Field(alias="strategyId")
    strategy_version_id: UUID = Field(alias="strategyVersionId")
    version: int
    plan_hash: str = Field(alias="planHash")


class CreateRunRequest(ApiModel):
    strategy_version_id: UUID = Field(alias="strategyVersionId")
    input: dict[str, Any] = Field(default_factory=dict)


class RunHandle(ApiModel):
    run_id: UUID = Field(alias="runId")
    status: str
    command_id: UUID = Field(alias="commandId")
    command_status: str = Field(alias="commandStatus")


class CommandHandle(ApiModel):
    command_id: UUID = Field(alias="commandId")
    request_id: UUID = Field(alias="requestId")
    command_seq: int = Field(alias="commandSeq")
    status: str


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


class JsonRpcRequest(ApiModel):
    jsonrpc: Literal["2.0"]
    id: str | int | None = None
    method: str
    params: dict[str, Any] = Field(default_factory=dict)
