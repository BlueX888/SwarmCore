from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from swarmcore_domain import uuid7


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[Any, Any]] = {dict[str, Any]: JSONB}


class IdMixin:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid7)


class TenantMixin:
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class Tenant(Base, IdMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    policy_ref: Mapped[str | None] = mapped_column(String(512))


class Project(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_projects_tenant_name"),
        UniqueConstraint("tenant_id", "id", name="uq_projects_tenant_id"),
        ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class Strategy(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "strategies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_strategies_tenant_id"),
        UniqueConstraint("project_id", "name", name="uq_strategies_project_name"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"], ["projects.tenant_id", "projects.id"], ondelete="RESTRICT"
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)


class StrategyDraft(Base, IdMixin, TenantMixin):
    __tablename__ = "strategy_drafts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_strategy_drafts_tenant_id"),
        UniqueConstraint("strategy_id", "id", name="uq_strategy_drafts_strategy_id"),
        ForeignKeyConstraint(
            ["tenant_id", "strategy_id"],
            ["strategies.tenant_id", "strategies.id"],
            ondelete="CASCADE",
        ),
    )

    strategy_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    base_version_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    raw_spec: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    editor_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    diagnostics: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    updated_by: Mapped[str] = mapped_column(String(256), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class StrategyVersion(Base, IdMixin, TenantMixin):
    __tablename__ = "strategy_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_strategy_versions_tenant_id"),
        UniqueConstraint("strategy_id", "version", name="uq_strategy_versions_strategy_version"),
        ForeignKeyConstraint(
            ["tenant_id", "strategy_id"],
            ["strategies.tenant_id", "strategies.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_strategy_versions_plan_hash", "plan_hash"),
    )

    strategy_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(32), default="PUBLISHED", nullable=False)
    raw_spec: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    normalized_spec: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    plan: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    plan_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class Run(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_runs_tenant_id"),
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_runs_scope_id"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"], ["projects.tenant_id", "projects.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "strategy_version_id"],
            ["strategy_versions.tenant_id", "strategy_versions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "parent_run_id"], ["runs.tenant_id", "runs.id"], ondelete="RESTRICT"
        ),
        Index("ix_runs_tenant_created", "tenant_id", "created_at"),
        Index("ix_runs_project_status", "project_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    strategy_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACCEPTED", nullable=False)
    input: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    output_ref: Mapped[str | None] = mapped_column(String(1024))
    budgets: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    usage: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    plan_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_version: Mapped[str] = mapped_column(String(64), nullable=False)
    temporal_workflow_id: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    temporal_run_id: Mapped[str | None] = mapped_column(String(512))
    next_event_seq: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    earliest_available_seq: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    projection_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    parent_run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    initiated_by: Mapped[str] = mapped_column(String(256), default="system", nullable=False)
    submitted_scopes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    auth_context_hash: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    policy_revision: Mapped[str] = mapped_column(String(128), default="unknown", nullable=False)


class RunTask(Base, IdMixin, TenantMixin):
    __tablename__ = "run_tasks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_run_tasks_tenant_id"),
        UniqueConstraint("run_id", "task_instance_key", name="uq_run_tasks_instance_key"),
        ForeignKeyConstraint(
            ["tenant_id", "run_id"], ["runs.tenant_id", "runs.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "parent_task_id"],
            ["run_tasks.tenant_id", "run_tasks.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_run_tasks_run_status", "run_id", "status"),
    )

    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    task_instance_key: Mapped[str] = mapped_column(String(512), nullable=False)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    parent_task_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    iteration_no: Mapped[int | None] = mapped_column(Integer)
    fanout_key: Mapped[str | None] = mapped_column(String(256))
    subflow_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spawn_command_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    dependencies: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    output_ref: Mapped[str | None] = mapped_column(String(1024))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    retry_generation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_retry_command_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))


class TaskExecution(Base, IdMixin, TenantMixin):
    __tablename__ = "task_executions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_task_executions_tenant_id"),
        UniqueConstraint("task_id", "generation", name="uq_task_executions_generation"),
        UniqueConstraint("effect_id", name="uq_task_executions_effect_id"),
        ForeignKeyConstraint(
            ["tenant_id", "task_id"], ["run_tasks.tenant_id", "run_tasks.id"], ondelete="CASCADE"
        ),
    )

    task_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    effect_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    result_ref: Mapped[str | None] = mapped_column(String(1024))
    journal_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class Attempt(Base, IdMixin, TenantMixin):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_attempts_tenant_id"),
        UniqueConstraint(
            "task_execution_id",
            "temporal_activity_id",
            "temporal_attempt",
            name="uq_attempts_temporal_attempt",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "task_execution_id"],
            ["task_executions.tenant_id", "task_executions.id"],
            ondelete="CASCADE",
        ),
    )

    task_execution_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    temporal_activity_id: Mapped[str] = mapped_column(String(512), nullable=False)
    temporal_attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="CREATED", nullable=False)
    worker: Mapped[str | None] = mapped_column(String(512))
    lease_token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    producer_seq: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    effect_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    result_ref: Mapped[str | None] = mapped_column(String(1024))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_category: Mapped[str | None] = mapped_column(String(128))
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class RunEvent(Base, IdMixin, TenantMixin):
    __tablename__ = "run_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_run_events_tenant_id"),
        UniqueConstraint("run_id", "event_seq", name="uq_run_events_sequence"),
        UniqueConstraint("run_id", "transition_id", name="uq_run_events_transition"),
        UniqueConstraint("attempt_id", "producer_seq", name="uq_run_events_producer"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"], ["projects.tenant_id", "projects.id"], ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "run_id"], ["runs.tenant_id", "runs.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "task_id"], ["run_tasks.tenant_id", "run_tasks.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "attempt_id"], ["attempts.tenant_id", "attempts.id"], ondelete="CASCADE"
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    task_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    attempt_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    event_seq: Mapped[int] = mapped_column(BigInteger, nullable=False)
    transition_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), default="run-event.v1", nullable=False)
    producer_seq: Mapped[int | None] = mapped_column(BigInteger)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(64))
    causation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    correlation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    redacted: Mapped[bool] = mapped_column(default=False, nullable=False)


class OutboxEvent(Base, IdMixin, TenantMixin):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("ix_outbox_claim", "destination", "status", "available_at"),
        UniqueConstraint("destination", "source_id", name="uq_outbox_destination_source"),
    )

    aggregate_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    destination: Mapped[str] = mapped_column(String(32), nullable=False)
    partition_key: Mapped[str] = mapped_column(String(512), nullable=False)
    source_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    locked_by: Mapped[str | None] = mapped_column(String(512))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class RunCommand(Base, IdMixin, TenantMixin):
    __tablename__ = "run_commands"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_run_commands_tenant_id"),
        UniqueConstraint("run_id", "request_id", name="uq_run_commands_request"),
        UniqueConstraint("run_id", "command_seq", name="uq_run_commands_sequence"),
        ForeignKeyConstraint(
            ["tenant_id", "run_id"], ["runs.tenant_id", "runs.id"], ondelete="CASCADE"
        ),
        Index("ix_run_commands_status_created", "status", "created_at"),
    )

    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    command_seq: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    request_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    actor: Mapped[str] = mapped_column(String(256), default="system", nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACCEPTED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    delivering_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApprovalRequest(Base, IdMixin, TenantMixin):
    __tablename__ = "approval_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_approval_requests_tenant_id"),
        UniqueConstraint("run_id", "node_key", name="uq_approval_requests_run_node"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "run_id"],
            ["runs.tenant_id", "runs.project_id", "runs.id"],
            ondelete="CASCADE",
        ),
        Index("ix_approval_requests_pending", "project_id", "status", "created_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    input_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    requested_by: Mapped[str] = mapped_column(String(256), default="workflow", nullable=False)
    handled_by: Mapped[str | None] = mapped_column(String(256))
    decision: Mapped[str | None] = mapped_column(String(32))
    response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    handler_command_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    task_execution_id: Mapped[str | None] = mapped_column(String(128))
    tool_ref: Mapped[str | None] = mapped_column(String(512))
    tool_version: Mapped[str | None] = mapped_column(String(128))
    canonical_input_hash: Mapped[str | None] = mapped_column(String(64))
    policy_revision: Mapped[str | None] = mapped_column(String(128))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    requires_distinct_approver: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ExternalInputRequest(Base, IdMixin, TenantMixin):
    __tablename__ = "external_input_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_external_input_requests_tenant_id"),
        UniqueConstraint("run_id", "node_key", name="uq_external_input_requests_run_node"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "run_id"],
            ["runs.tenant_id", "runs.project_id", "runs.id"],
            ondelete="CASCADE",
        ),
        Index("ix_external_input_requests_pending", "project_id", "status", "created_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    input_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    requested_by: Mapped[str] = mapped_column(String(256), default="workflow", nullable=False)
    handled_by: Mapped[str | None] = mapped_column(String(256))
    value: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    handler_command_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "project_id"], ["projects.tenant_id", "projects.id"], ondelete="CASCADE"
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    operation: Mapped[str] = mapped_column(String(128), primary_key=True)
    key: Mapped[str] = mapped_column(String(256), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_ref: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ToolEffect(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "tool_effects"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "project_id", "tool_ref", "effect_id", name="uq_tool_effect_scope"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "run_id"],
            ["runs.tenant_id", "runs.project_id", "runs.id"],
            ondelete="CASCADE",
        ),
        Index("ix_tool_effects_run_status", "run_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    tool_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    effect_id: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    lease_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectConfiguration(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "project_configurations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_project_configurations_tenant_id"),
        UniqueConstraint(
            "tenant_id",
            "project_id",
            "kind",
            "name",
            name="uq_project_configurations_scope_name",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"],
            ["projects.tenant_id", "projects.id"],
            ondelete="CASCADE",
        ),
        Index("ix_project_configurations_project_kind", "project_id", "kind", "updated_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(256), nullable=False)


class Artifact(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_artifacts_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "run_id"],
            ["runs.tenant_id", "runs.project_id", "runs.id"],
            ondelete="CASCADE",
        ),
        Index("ix_artifacts_run_status", "run_id", "status"),
        Index("ix_artifacts_retention", "status", "retention_until"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    media_type: Mapped[str] = mapped_column(String(256), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    data_classification: Mapped[str] = mapped_column(
        String(32), default="internal", nullable=False
    )
    retention_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ArtifactDownloadGrant(Base, IdMixin, TenantMixin):
    __tablename__ = "artifact_download_grants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_artifact_download_grants_tenant_id"),
        UniqueConstraint("token_hash", name="uq_artifact_download_grants_token"),
        ForeignKeyConstraint(
            ["tenant_id", "artifact_id"],
            ["artifacts.tenant_id", "artifacts.id"],
            ondelete="CASCADE",
        ),
        Index("ix_artifact_download_grants_expiry", "expires_at"),
    )

    artifact_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    issued_to: Mapped[str] = mapped_column(String(256), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class AuditLog(Base, IdMixin, TenantMixin):
    __tablename__ = "audit_logs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_audit_logs_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"],
            ["projects.tenant_id", "projects.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_audit_logs_scope_time", "tenant_id", "project_id", "occurred_at"),
        Index("ix_audit_logs_run", "run_id", "occurred_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    actor_id: Mapped[str] = mapped_column(String(256), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(512), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_revision: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    trace_id: Mapped[str | None] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModelUsageRecord(Base, IdMixin, TenantMixin):
    __tablename__ = "model_usage_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_model_usage_records_tenant_id"),
        UniqueConstraint("run_id", "request_id", name="uq_model_usage_run_request"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "run_id"],
            ["runs.tenant_id", "runs.project_id", "runs.id"],
            ondelete="CASCADE",
        ),
        Index("ix_model_usage_run", "run_id", "occurred_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    logical_model: Mapped[str] = mapped_column(String(512), nullable=False)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_model: Mapped[str] = mapped_column(String(512), nullable=False)
    price_version: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd_micros: Mapped[int] = mapped_column(BigInteger, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WebhookEndpoint(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "webhook_endpoints"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_webhook_endpoints_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"],
            ["projects.tenant_id", "projects.id"],
            ondelete="CASCADE",
        ),
        Index("ix_webhook_endpoints_project_status", "project_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    event_types: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class WebhookDelivery(Base, IdMixin, TenantMixin):
    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_webhook_deliveries_tenant_id"),
        UniqueConstraint("endpoint_id", "event_id", name="uq_webhook_delivery_event"),
        ForeignKeyConstraint(
            ["tenant_id", "endpoint_id"],
            ["webhook_endpoints.tenant_id", "webhook_endpoints.id"],
            ondelete="CASCADE",
        ),
        Index("ix_webhook_delivery_retry", "status", "next_attempt_at"),
    )

    endpoint_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    delivery_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    response_status: Mapped[int | None] = mapped_column(Integer)
    last_error: Mapped[str | None] = mapped_column(Text)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SandboxExecution(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "sandbox_executions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_sandbox_executions_tenant_id"),
        UniqueConstraint("run_id", "task_execution_id", name="uq_sandbox_run_task_execution"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "run_id"],
            ["runs.tenant_id", "runs.project_id", "runs.id"],
            ondelete="CASCADE",
        ),
        Index("ix_sandbox_execution_run_status", "run_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    task_execution_id: Mapped[str] = mapped_column(String(128), nullable=False)
    image_digest: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_revision: Mapped[str] = mapped_column(String(128), nullable=False)
    result_ref: Mapped[str | None] = mapped_column(String(1024))
    cleanup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CompensationRecord(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "compensation_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_compensation_records_tenant_id"),
        UniqueConstraint("run_id", "effect_id", name="uq_compensation_run_effect"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "run_id"],
            ["runs.tenant_id", "runs.project_id", "runs.id"],
            ondelete="CASCADE",
        ),
        Index("ix_compensation_run_status", "run_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    effect_id: Mapped[str] = mapped_column(String(128), nullable=False)
    operation: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
