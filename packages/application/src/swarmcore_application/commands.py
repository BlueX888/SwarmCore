from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import Run, RunCommand
from swarmcore_persistence.repositories import RunCommandRepository


class RunCommandConflictError(RuntimeError):
    """The requested command is incompatible with the current Run state."""


class CommandHandle(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    command_id: UUID = Field(alias="commandId")
    request_id: UUID = Field(alias="requestId")
    command_seq: int = Field(alias="commandSeq")
    status: str
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    created_at: datetime | None = Field(default=None, alias="createdAt")
    applied_at: datetime | None = Field(default=None, alias="appliedAt")
    rejected_at: datetime | None = Field(default=None, alias="rejectedAt")

    @classmethod
    def from_command(cls, command: RunCommand) -> CommandHandle:
        return cls(
            commandId=command.id,
            requestId=command.request_id,
            commandSeq=command.command_seq,
            status=command.status,
            result=command.result,
            error=command.error,
            createdAt=command.created_at,
            appliedAt=command.applied_at,
            rejectedAt=command.rejected_at,
        )


def command_request_id(
    *, tenant_id: UUID, run_id: UUID, command_type: str, idempotency_key: str
) -> UUID:
    return uuid5(
        NAMESPACE_URL,
        f"{tenant_id}:{run_id}:{command_type}:{idempotency_key}",
    )


class RunCommandService:
    _ALLOWED_TYPES: ClassVar[frozenset[str]] = frozenset(
        {
            "approve",
            "cancel",
            "pause",
            "provide_input",
            "reject",
            "resume",
            "retry_task",
        }
    )
    _TERMINAL_STATUSES: ClassVar[frozenset[str]] = frozenset(
        {"REJECTED", "CANCELLED", "SUCCEEDED", "TIMED_OUT"}
    )
    _PAUSABLE_STATUSES: ClassVar[frozenset[str]] = frozenset(
        {"QUEUED", "RUNNING", "WAITING_APPROVAL", "WAITING_INPUT"}
    )
    _RESUMABLE_STATUSES: ClassVar[frozenset[str]] = frozenset({"PAUSING", "PAUSED"})

    def __init__(self, repository: RunCommandRepository | None = None) -> None:
        self._repository = repository or RunCommandRepository()
        self._audit = AuditRepository()

    async def append(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        run_id: UUID,
        command_type: str,
        idempotency_key: str,
        payload: dict[str, Any],
        actor: str = "system",
    ) -> CommandHandle:
        if command_type not in self._ALLOWED_TYPES:
            raise ValueError(f"unsupported control action: {command_type}")
        request_id = command_request_id(
            tenant_id=tenant_id,
            run_id=run_id,
            command_type=command_type,
            idempotency_key=idempotency_key,
        )
        run = await session.scalar(
            select(Run).where(
                Run.id == run_id,
                Run.tenant_id == tenant_id,
                Run.project_id == project_id,
            ).with_for_update()
        )
        if run is None:
            raise LookupError("run not found")

        existing = await session.scalar(
            select(RunCommand).where(
                RunCommand.run_id == run_id,
                RunCommand.request_id == request_id,
            )
        )
        if existing is None:
            self._validate_state(run.status, command_type)

        command = await self._repository.append(
            session,
            tenant_id=tenant_id,
            run_id=run_id,
            command_type=command_type,
            request_id=request_id,
            payload=payload,
            actor=actor,
        )
        if existing is None:
            audit_action = (
                "approval.decide"
                if command_type in {"approve", "reject"}
                else f"run.{command_type}"
            )
            await self._audit.append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=actor,
                action=audit_action,
                resource_type=("approval" if command_type in {"approve", "reject"} else "run"),
                resource_id=str(payload.get("requestId", run_id)),
                run_id=run_id,
                policy_revision=run.policy_revision,
                metadata={"commandId": str(command.id), "decision": command_type},
            )
        return CommandHandle.from_command(command)

    async def get(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        command_id: UUID,
    ) -> CommandHandle:
        command = await session.scalar(
            select(RunCommand)
            .join(Run, Run.id == RunCommand.run_id)
            .where(
                RunCommand.id == command_id,
                RunCommand.tenant_id == tenant_id,
                Run.project_id == project_id,
            )
        )
        if command is None:
            raise LookupError("command not found")
        return CommandHandle.from_command(command)

    @classmethod
    def _validate_state(cls, status: str, command_type: str) -> None:
        if command_type == "cancel" and status in cls._TERMINAL_STATUSES:
            raise RunCommandConflictError("run is already terminal")
        if command_type == "pause" and status not in cls._PAUSABLE_STATUSES:
            raise RunCommandConflictError(f"run cannot be paused from {status}")
        if command_type == "resume" and status not in cls._RESUMABLE_STATUSES:
            raise RunCommandConflictError(f"run cannot be resumed from {status}")
