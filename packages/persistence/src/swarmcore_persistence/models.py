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
    data_classification: Mapped[str] = mapped_column(String(32), default="internal", nullable=False)
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


class CapabilityPack(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "capability_packs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_capability_packs_tenant_id"),
        UniqueConstraint("tenant_id", "name", name="uq_capability_packs_tenant_name"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)


class CapabilityPackVersion(Base, IdMixin, TenantMixin):
    __tablename__ = "capability_pack_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_capability_pack_versions_tenant_id"),
        UniqueConstraint("pack_id", "version", name="uq_capability_pack_versions_version"),
        UniqueConstraint("pack_id", "content_hash", name="uq_capability_pack_versions_hash"),
        ForeignKeyConstraint(
            ["tenant_id", "pack_id"],
            ["capability_packs.tenant_id", "capability_packs.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_capability_pack_versions_hash", "content_hash"),
    )

    pack_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    dependency_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProjectCapabilityBinding(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "project_capability_bindings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_project_capability_bindings_tenant_id"),
        UniqueConstraint("project_id", "pack_id", name="uq_project_capability_bindings_pack"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"],
            ["projects.tenant_id", "projects.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "pack_id"],
            ["capability_packs.tenant_id", "capability_packs.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "pack_version_id"],
            ["capability_pack_versions.tenant_id", "capability_pack_versions.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_project_capability_bindings_status", "project_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    pack_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    pack_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ENABLED", nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    enabled_by: Mapped[str] = mapped_column(String(256), nullable=False)


class WorkItem(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "work_items"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_work_items_tenant_id"),
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_work_items_scope_id"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"],
            ["projects.tenant_id", "projects.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_work_items_project_status", "project_id", "status", "updated_at"),
        Index("ix_work_items_project_type", "project_id", "work_item_type"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    work_item_type: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(256), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)
    owner: Mapped[str | None] = mapped_column(String(256))
    revision_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class WorkItemRevision(Base, IdMixin, TenantMixin):
    __tablename__ = "work_item_revisions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_work_item_revisions_tenant_id"),
        UniqueConstraint("work_item_id", "revision", name="uq_work_item_revisions_number"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "work_item_id"],
            ["work_items.tenant_id", "work_items.project_id", "work_items.id"],
            ondelete="CASCADE",
        ),
        Index("ix_work_item_revisions_item", "work_item_id", "revision"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    work_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(256), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BlobObject(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "blob_objects"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_blob_objects_tenant_id"),
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_blob_objects_scope_id"),
        UniqueConstraint("object_key", name="uq_blob_objects_object_key"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"],
            ["projects.tenant_id", "projects.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_blob_objects_scope_status", "project_id", "status"),
        Index("ix_blob_objects_retention", "status", "retention_until"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    media_type: Mapped[str] = mapped_column(String(256), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    scan_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    retention_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )


class WorkItemAttachment(Base, IdMixin, TenantMixin):
    __tablename__ = "work_item_attachments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_work_item_attachments_tenant_id"),
        UniqueConstraint("revision_id", "blob_id", name="uq_work_item_attachments_blob"),
        ForeignKeyConstraint(
            ["tenant_id", "revision_id"],
            ["work_item_revisions.tenant_id", "work_item_revisions.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "blob_id"],
            ["blob_objects.tenant_id", "blob_objects.project_id", "blob_objects.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_work_item_attachments_revision", "revision_id"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    work_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    revision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    blob_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    document_type: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DocumentExtraction(Base, IdMixin, TenantMixin):
    __tablename__ = "document_extractions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_document_extractions_tenant_id"),
        UniqueConstraint(
            "project_id",
            "blob_id",
            "source_sha256",
            "pipeline_version",
            name="uq_document_extractions_pipeline",
        ),
        UniqueConstraint(
            "tenant_id",
            "project_id",
            "cache_key",
            name="uq_document_extractions_cache_key",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "blob_id"],
            ["blob_objects.tenant_id", "blob_objects.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_document_extractions_blob", "blob_id", "created_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    blob_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(512), nullable=False)
    cache_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BusinessDocument(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "business_documents"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "project_id", "id", name="uq_business_documents_scope_id"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"],
            ["projects.tenant_id", "projects.id"],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_business_documents_list",
            "project_id",
            "status",
            "category",
            "updated_at",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="UPLOADING", nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)


class BusinessDocumentVersion(Base, IdMixin, TenantMixin):
    __tablename__ = "business_document_versions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "project_id",
            "id",
            name="uq_business_document_versions_scope_id",
        ),
        UniqueConstraint(
            "business_document_id",
            "version",
            name="uq_business_document_versions_number",
        ),
        UniqueConstraint(
            "business_document_id",
            "blob_id",
            name="uq_business_document_versions_blob",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_document_id"],
            [
                "business_documents.tenant_id",
                "business_documents.project_id",
                "business_documents.id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "blob_id"],
            ["blob_objects.tenant_id", "blob_objects.project_id", "blob_objects.id"],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_business_document_versions_document",
            "business_document_id",
            "version",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    blob_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    media_type: Mapped[str] = mapped_column(String(256), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(32), default="UPLOADING", nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DocumentBusinessObjectLink(Base, IdMixin, TenantMixin):
    __tablename__ = "document_business_object_links"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "project_id",
            "id",
            name="uq_document_business_object_links_scope_id",
        ),
        UniqueConstraint(
            "business_document_id",
            "business_object_id",
            name="uq_document_business_object_links_object",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_document_id"],
            [
                "business_documents.tenant_id",
                "business_documents.project_id",
                "business_documents.id",
            ],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_object_id"],
            [
                "business_objects.tenant_id",
                "business_objects.project_id",
                "business_objects.id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_object_version_id"],
            [
                "business_object_versions.tenant_id",
                "business_object_versions.project_id",
                "business_object_versions.id",
            ],
            ondelete="RESTRICT",
        ),
        Index("ix_document_business_object_links_object", "business_object_id"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_object_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_object_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(64), default="RELATED", nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DocumentWorkBinding(Base, IdMixin, TenantMixin):
    __tablename__ = "document_work_bindings"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "project_id",
            "id",
            name="uq_document_work_bindings_scope_id",
        ),
        UniqueConstraint(
            "business_document_id",
            "business_work_key",
            name="uq_document_work_bindings_work",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_document_id"],
            [
                "business_documents.tenant_id",
                "business_documents.project_id",
                "business_documents.id",
            ],
            ondelete="CASCADE",
        ),
        Index("ix_document_work_bindings_work", "project_id", "business_work_key"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_work_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DocumentProcessingResult(Base, IdMixin, TenantMixin):
    __tablename__ = "document_processing_results"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "project_id",
            "id",
            name="uq_document_processing_results_scope_id",
        ),
        UniqueConstraint(
            "business_document_version_id",
            "result_type",
            "result_version",
            name="uq_document_processing_results_version",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_document_version_id"],
            [
                "business_document_versions.tenant_id",
                "business_document_versions.project_id",
                "business_document_versions.id",
            ],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_document_processing_results_document_version",
            "business_document_version_id",
            "result_type",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_document_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    result_type: Mapped[str] = mapped_column(String(64), nullable=False)
    result_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_ref: Mapped[str | None] = mapped_column(String(256))
    producer_ref: Mapped[str | None] = mapped_column(String(256))
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    confirmed_by: Mapped[str | None] = mapped_column(String(256))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UploadBatch(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "upload_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_upload_batches_scope_id"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"],
            ["projects.tenant_id", "projects.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_upload_batches_scope_status", "project_id", "status", "created_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="web", nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    file_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    succeeded_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentProcessingRun(Base, IdMixin, TenantMixin):
    __tablename__ = "document_processing_runs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "project_id",
            "id",
            name="uq_document_processing_runs_scope_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_document_version_id"],
            [
                "business_document_versions.tenant_id",
                "business_document_versions.project_id",
                "business_document_versions.id",
            ],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_document_processing_runs_version",
            "business_document_version_id",
            "attempt",
        ),
        Index("ix_document_processing_runs_status", "project_id", "status", "started_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_document_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    upload_batch_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    profile_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    current_stage: Mapped[str] = mapped_column(String(64), default="PENDING", nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parser_ref: Mapped[str | None] = mapped_column(String(256))
    classifier_ref: Mapped[str | None] = mapped_column(String(256))
    extractor_refs: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_detail: Mapped[str | None] = mapped_column(String(2048))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class RuleSet(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "rule_sets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_rule_sets_tenant_id"),
        UniqueConstraint("project_id", "name", name="uq_rule_sets_project_name"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"],
            ["projects.tenant_id", "projects.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_rule_sets_project", "project_id", "updated_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str] = mapped_column(String(512), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)


class RuleSetDraft(Base, IdMixin, TenantMixin):
    __tablename__ = "rule_set_drafts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_rule_set_drafts_tenant_id"),
        UniqueConstraint("rule_set_id", name="uq_rule_set_drafts_rule_set"),
        ForeignKeyConstraint(
            ["tenant_id", "rule_set_id"],
            ["rule_sets.tenant_id", "rule_sets.id"],
            ondelete="CASCADE",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    rule_set_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    updated_by: Mapped[str] = mapped_column(String(256), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RuleSetVersion(Base, IdMixin, TenantMixin):
    __tablename__ = "rule_set_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_rule_set_versions_tenant_id"),
        UniqueConstraint("rule_set_id", "version", name="uq_rule_set_versions_number"),
        UniqueConstraint("rule_set_id", "content_hash", name="uq_rule_set_versions_hash"),
        ForeignKeyConstraint(
            ["tenant_id", "rule_set_id"],
            ["rule_sets.tenant_id", "rule_sets.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_rule_set_versions_match", "project_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    rule_set_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(256), nullable=False)
    match_expression: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PUBLISHED", nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Evaluation(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_evaluations_tenant_id"),
        UniqueConstraint(
            "project_id",
            "work_item_revision_id",
            "capability_pack_version_id",
            "idempotency_key",
            name="uq_evaluations_idempotency",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "work_item_revision_id"],
            ["work_item_revisions.tenant_id", "work_item_revisions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "capability_pack_version_id"],
            ["capability_pack_versions.tenant_id", "capability_pack_versions.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "run_id"],
            ["runs.tenant_id", "runs.project_id", "runs.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_evaluations_item_status", "work_item_id", "status", "created_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    work_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    work_item_revision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    capability_pack_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    rule_set_version_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACCEPTED", nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    strategy_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    plan_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    registry_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    attachment_manifest_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    input_schema_version: Mapped[str] = mapped_column(String(256), nullable=False)
    output_schema_version: Mapped[str] = mapped_column(String(256), nullable=False)
    report_template_version: Mapped[str] = mapped_column(String(256), nullable=False)
    policy_revision: Mapped[str] = mapped_column(String(128), nullable=False)


class Finding(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_findings_tenant_id"),
        UniqueConstraint("work_item_id", "rule_key", name="uq_findings_rule_key"),
        ForeignKeyConstraint(
            ["tenant_id", "evaluation_id"],
            ["evaluations.tenant_id", "evaluations.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_findings_item_status", "work_item_id", "status", "severity"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    work_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evaluation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(256), nullable=False)
    code: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    resolved_by_evaluation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))


class FindingAction(Base, IdMixin, TenantMixin):
    __tablename__ = "finding_actions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_finding_actions_tenant_id"),
        ForeignKeyConstraint(
            ["tenant_id", "finding_id"],
            ["findings.tenant_id", "findings.id"],
            ondelete="CASCADE",
        ),
        Index("ix_finding_actions_history", "finding_id", "created_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    finding_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    assignee: Mapped[str | None] = mapped_column(String(256))
    actor_id: Mapped[str] = mapped_column(String(256), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Report(Base, IdMixin, TenantMixin):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_reports_tenant_id"),
        UniqueConstraint("evaluation_id", "format", name="uq_reports_evaluation_format"),
        ForeignKeyConstraint(
            ["tenant_id", "evaluation_id"],
            ["evaluations.tenant_id", "evaluations.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_reports_evaluation", "evaluation_id"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    work_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evaluation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    template_version: Mapped[str] = mapped_column(String(256), nullable=False)
    result_schema_version: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    artifact_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BusinessObject(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "business_objects"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_business_objects_scope_id"),
        UniqueConstraint(
            "project_id", "object_type", "canonical_key", name="uq_business_objects_key"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"], ["projects.tenant_id", "projects.id"], ondelete="RESTRICT"
        ),
        Index("ix_business_objects_list", "project_id", "object_type", "lifecycle", "updated_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    object_type: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_key: Mapped[str] = mapped_column(String(256), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class BusinessObjectVersion(Base, IdMixin, TenantMixin):
    __tablename__ = "business_object_versions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "project_id", "id", name="uq_business_object_versions_scope_id"
        ),
        UniqueConstraint(
            "business_object_id", "version", name="uq_business_object_versions_number"
        ),
        UniqueConstraint(
            "business_object_id", "data_hash", name="uq_business_object_versions_hash"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_object_id"],
            ["business_objects.tenant_id", "business_objects.project_id", "business_objects.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_business_object_versions_object", "business_object_id", "version"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_object_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    data_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[str] = mapped_column(String(256), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BusinessObjectRelation(Base, IdMixin, TenantMixin):
    __tablename__ = "business_object_relations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "project_id", "id", name="uq_business_object_relations_scope_id"
        ),
        UniqueConstraint("project_id", "content_hash", name="uq_business_object_relations_hash"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "source_object_id"],
            ["business_objects.tenant_id", "business_objects.project_id", "business_objects.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "target_object_id"],
            ["business_objects.tenant_id", "business_objects.project_id", "business_objects.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "source_version_id"],
            [
                "business_object_versions.tenant_id",
                "business_object_versions.project_id",
                "business_object_versions.id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "target_version_id"],
            [
                "business_object_versions.tenant_id",
                "business_object_versions.project_id",
                "business_object_versions.id",
            ],
            ondelete="RESTRICT",
        ),
        Index("ix_business_object_relations_source", "source_object_id", "relation_type"),
        Index("ix_business_object_relations_target", "target_object_id", "relation_type"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    source_object_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    target_object_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    source_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    target_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(128), nullable=False)
    assertion_state: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    supersedes_relation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkItemSubject(Base, IdMixin, TenantMixin):
    __tablename__ = "work_item_subjects"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_work_item_subjects_scope_id"),
        UniqueConstraint(
            "work_item_revision_id",
            "subject_key",
            "business_object_id",
            name="uq_work_item_subjects_binding",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "work_item_id"],
            ["work_items.tenant_id", "work_items.project_id", "work_items.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "work_item_revision_id"],
            ["work_item_revisions.tenant_id", "work_item_revisions.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_object_id"],
            ["business_objects.tenant_id", "business_objects.project_id", "business_objects.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_object_version_id"],
            [
                "business_object_versions.tenant_id",
                "business_object_versions.project_id",
                "business_object_versions.id",
            ],
            ondelete="RESTRICT",
        ),
        Index("ix_work_item_subjects_revision", "work_item_revision_id", "role"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    work_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    work_item_revision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_object_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_object_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProjectCapabilityDecisionBinding(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "project_capability_decision_bindings"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "project_id", "id", name="uq_capability_decision_bindings_scope_id"
        ),
        UniqueConstraint(
            "project_capability_binding_id", "slot", name="uq_capability_decision_bindings_slot"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_capability_binding_id"],
            ["project_capability_bindings.tenant_id", "project_capability_bindings.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "rule_set_version_id"],
            ["rule_set_versions.tenant_id", "rule_set_versions.id"],
            ondelete="RESTRICT",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    project_capability_binding_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    slot: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_set_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    bound_by: Mapped[str] = mapped_column(String(256), nullable=False)


class EvaluationDecision(Base, IdMixin, TenantMixin):
    __tablename__ = "evaluation_decisions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_evaluation_decisions_tenant_id"),
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_evaluation_decisions_scope_id"),
        UniqueConstraint("evaluation_id", "slot", name="uq_evaluation_decisions_slot"),
        ForeignKeyConstraint(
            ["tenant_id", "evaluation_id"],
            ["evaluations.tenant_id", "evaluations.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "rule_set_version_id"],
            ["rule_set_versions.tenant_id", "rule_set_versions.id"],
            ondelete="RESTRICT",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evaluation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    slot: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_set_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    decision_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    input_schema_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    output_schema_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    engine: Mapped[str] = mapped_column(String(128), nullable=False)


class DecisionExecution(Base, IdMixin, TenantMixin):
    __tablename__ = "decision_executions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_decision_executions_scope_id"),
        UniqueConstraint(
            "evaluation_decision_id",
            "execution_key",
            "attempt",
            name="uq_decision_executions_attempt",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "evaluation_decision_id"],
            ["evaluation_decisions.tenant_id", "evaluation_decisions.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_decision_executions_evaluation", "evaluation_decision_id", "executed_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evaluation_decision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    task_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    trace_id: Mapped[str | None] = mapped_column(String(128))
    execution_key: Mapped[str] = mapped_column(String(256), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    input_artifact_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    output_artifact_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    output_hash: Mapped[str | None] = mapped_column(String(64))
    matched_rule_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_summary: Mapped[str | None] = mapped_column(String(512))
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Connection(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "connections"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_connections_scope_id"),
        UniqueConstraint("project_id", "name", name="uq_connections_name"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id"], ["projects.tenant_id", "projects.id"], ondelete="RESTRICT"
        ),
        Index("ix_connections_list", "project_id", "lifecycle", "updated_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    connector_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ConnectionVersion(Base, IdMixin, TenantMixin):
    __tablename__ = "connection_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_connection_versions_scope_id"),
        UniqueConstraint("connection_id", "version", name="uq_connection_versions_number"),
        UniqueConstraint("connection_id", "configuration_hash", name="uq_connection_versions_hash"),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "connection_id"],
            ["connections.tenant_id", "connections.project_id", "connections.id"],
            ondelete="RESTRICT",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    connection_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    credential_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    policy_ref: Mapped[str | None] = mapped_column(String(256))
    configuration_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ResourceDefinition(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "resource_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_resource_definitions_scope_id"),
        UniqueConstraint(
            "project_id", "connection_id", "name", name="uq_resource_definitions_name"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "connection_id"],
            ["connections.tenant_id", "connections.project_id", "connections.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_resource_definitions_list", "project_id", "resource_kind", "lifecycle"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    connection_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    resource_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    locator: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    schema_ref: Mapped[str | None] = mapped_column(String(256))
    media_type: Mapped[str | None] = mapped_column(String(256))
    sensitivity: Mapped[str] = mapped_column(String(32), default="INTERNAL", nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)


class CapabilityResourceBinding(Base, IdMixin, TenantMixin, TimestampMixin):
    __tablename__ = "capability_resource_bindings"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "project_id", "id", name="uq_capability_resource_bindings_scope_id"
        ),
        UniqueConstraint(
            "project_capability_binding_id", "slot", name="uq_capability_resource_bindings_slot"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_capability_binding_id"],
            ["project_capability_bindings.tenant_id", "project_capability_bindings.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "resource_definition_id"],
            [
                "resource_definitions.tenant_id",
                "resource_definitions.project_id",
                "resource_definitions.id",
            ],
            ondelete="RESTRICT",
        ),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    project_capability_binding_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    slot: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_definition_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    access_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    mapping_configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    bound_by: Mapped[str] = mapped_column(String(256), nullable=False)


class ResourceSnapshot(Base, IdMixin, TenantMixin):
    __tablename__ = "resource_snapshots"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", "id", name="uq_resource_snapshots_scope_id"),
        UniqueConstraint("evaluation_id", "slot", "snapshot_key", name="uq_resource_snapshots_key"),
        ForeignKeyConstraint(
            ["tenant_id", "evaluation_id"],
            ["evaluations.tenant_id", "evaluations.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "resource_definition_id"],
            [
                "resource_definitions.tenant_id",
                "resource_definitions.project_id",
                "resource_definitions.id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "connection_version_id"],
            [
                "connection_versions.tenant_id",
                "connection_versions.project_id",
                "connection_versions.id",
            ],
            ondelete="RESTRICT",
        ),
        Index("ix_resource_snapshots_evaluation", "evaluation_id", "retrieved_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evaluation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    slot: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_definition_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    snapshot_key: Mapped[str] = mapped_column(String(256), nullable=False)
    connection_version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    observed_version: Mapped[str | None] = mapped_column(String(256))
    etag: Mapped[str | None] = mapped_column(String(512))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    artifact_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    blob_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    replayability: Mapped[str] = mapped_column(String(32), nullable=False)
    non_replayable_reason: Mapped[str | None] = mapped_column(String(512))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )


class DocumentUsageSnapshot(Base, IdMixin, TenantMixin):
    __tablename__ = "document_usage_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "project_id",
            "id",
            name="uq_document_usage_snapshots_scope_id",
        ),
        UniqueConstraint(
            "evaluation_id",
            "business_document_version_id",
            "business_work_key",
            name="uq_document_usage_snapshots_version",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "evaluation_id"],
            ["evaluations.tenant_id", "evaluations.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "run_id"],
            ["runs.tenant_id", "runs.project_id", "runs.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_document_id"],
            [
                "business_documents.tenant_id",
                "business_documents.project_id",
                "business_documents.id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "business_document_version_id"],
            [
                "business_document_versions.tenant_id",
                "business_document_versions.project_id",
                "business_document_versions.id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "project_id", "blob_id"],
            ["blob_objects.tenant_id", "blob_objects.project_id", "blob_objects.id"],
            ondelete="RESTRICT",
        ),
        Index("ix_document_usage_snapshots_evaluation", "evaluation_id", "created_at"),
        Index("ix_document_usage_snapshots_run", "run_id", "created_at"),
    )

    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    evaluation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_work_key: Mapped[str] = mapped_column(String(128), nullable=False)
    business_document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    business_document_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    blob_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    document_version: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    media_type: Mapped[str] = mapped_column(String(256), nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
