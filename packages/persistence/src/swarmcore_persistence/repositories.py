from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from swarmcore_domain import RunStatus, can_transition_run, uuid7

from .errors import IdempotencyConflictError, TransitionConflictError
from .models import OutboxEvent, Run, RunCommand, RunEvent


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class RunCommandRepository:
    """Appends commands and their Temporal outbox messages in the caller's transaction."""

    async def append(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        run_id: UUID,
        command_type: str,
        request_id: UUID,
        payload: dict[str, Any],
        actor: str = "system",
    ) -> RunCommand:
        existing = await session.scalar(
            select(RunCommand).where(
                RunCommand.run_id == run_id,
                RunCommand.request_id == request_id,
            )
        )
        if existing is not None:
            if existing.type != command_type or canonical_hash(existing.payload) != canonical_hash(
                payload
            ):
                raise IdempotencyConflictError("request_id was reused with a different command")
            return existing

        run = await session.scalar(
            select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id).with_for_update()
        )
        if run is None:
            raise LookupError("run not found")
        last_seq = await session.scalar(
            select(func.max(RunCommand.command_seq)).where(RunCommand.run_id == run_id)
        )
        command = RunCommand(
            tenant_id=tenant_id,
            run_id=run_id,
            command_seq=(last_seq or 0) + 1,
            type=command_type,
            request_id=request_id,
            payload=payload,
            actor=actor,
        )
        session.add(command)
        await session.flush()
        session.add(
            OutboxEvent(
                tenant_id=tenant_id,
                aggregate_id=run_id,
                destination="temporal",
                partition_key=str(run_id),
                source_id=command.id,
                type=f"run.command.{command_type}",
                payload={
                    "commandId": str(command.id),
                    "requestId": str(request_id),
                    "runId": str(run_id),
                    "commandSeq": command.command_seq,
                    "type": command_type,
                    "data": payload,
                },
            )
        )
        return command


class EventRepository:
    _STATUS_BY_EVENT: ClassVar[dict[str, RunStatus]] = {
        "run.accepted": RunStatus.ACCEPTED,
        "run.validating": RunStatus.VALIDATING,
        "run.queued": RunStatus.QUEUED,
        "run.started": RunStatus.RUNNING,
        "run.waiting_input": RunStatus.WAITING_INPUT,
        "run.waiting_approval": RunStatus.WAITING_APPROVAL,
        "run.pausing": RunStatus.PAUSING,
        "run.paused": RunStatus.PAUSED,
        "run.resumed": RunStatus.RUNNING,
        "run.cancelling": RunStatus.CANCELLING,
        "run.compensating": RunStatus.COMPENSATING,
        "run.cancelled": RunStatus.CANCELLED,
        "run.completed": RunStatus.SUCCEEDED,
        "run.failed": RunStatus.FAILED,
        "run.timed_out": RunStatus.TIMED_OUT,
        "run.rejected": RunStatus.REJECTED,
    }

    async def append(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        run_id: UUID,
        transition_id: UUID,
        event_type: str,
        payload: dict[str, Any],
        occurred_at: datetime,
        task_id: UUID | None = None,
        attempt_id: UUID | None = None,
        producer_seq: int | None = None,
        trace_id: str | None = None,
        causation_id: UUID | None = None,
        correlation_id: UUID | None = None,
    ) -> RunEvent:
        payload_hash = canonical_hash(payload)
        existing = await session.scalar(
            select(RunEvent).where(
                RunEvent.run_id == run_id,
                RunEvent.transition_id == transition_id,
            )
        )
        if existing is not None:
            if existing.type != event_type or existing.payload_hash != payload_hash:
                raise TransitionConflictError(
                    "transition_id was replayed with different event content"
                )
            return existing

        run = await session.scalar(
            select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id).with_for_update()
        )
        if run is None or run.project_id != project_id:
            raise LookupError("run not found")
        target = self._STATUS_BY_EVENT.get(event_type)
        if target is not None and target != RunStatus(run.status):
            manual_retry = (
                RunStatus(run.status) == RunStatus.FAILED
                and target == RunStatus.RUNNING
                and event_type == "run.resumed"
                and payload.get("reason") == "task_retry"
            )
            if not manual_retry and not can_transition_run(RunStatus(run.status), target):
                raise TransitionConflictError(f"illegal run transition {run.status} -> {target}")
            run.status = target.value
            run.version += 1
            run.projection_updated_at = occurred_at
            if event_type == "run.started" and run.started_at is None:
                run.started_at = occurred_at
            if manual_retry:
                run.completed_at = None
            if target in {
                RunStatus.REJECTED,
                RunStatus.CANCELLED,
                RunStatus.SUCCEEDED,
                RunStatus.FAILED,
                RunStatus.TIMED_OUT,
            }:
                run.completed_at = occurred_at

        event = RunEvent(
            id=uuid7(),
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            task_id=task_id,
            attempt_id=attempt_id,
            event_seq=run.next_event_seq,
            transition_id=transition_id,
            type=event_type,
            producer_seq=producer_seq,
            payload=payload,
            payload_hash=payload_hash,
            occurred_at=occurred_at,
            trace_id=trace_id,
            causation_id=causation_id,
            correlation_id=correlation_id,
        )
        run.next_event_seq += 1
        session.add(event)
        await session.flush()
        session.add(
            OutboxEvent(
                tenant_id=tenant_id,
                aggregate_id=run_id,
                destination="nats",
                partition_key=str(run_id),
                source_id=event.id,
                type=event_type,
                payload={
                    "id": str(event.id),
                    "seq": event.event_seq,
                    "type": event.type,
                    "schemaVersion": event.schema_version,
                    "tenantId": str(tenant_id),
                    "projectId": str(project_id),
                    "runId": str(run_id),
                    "taskId": str(task_id) if task_id else None,
                    "attemptId": str(attempt_id) if attempt_id else None,
                    "occurredAt": occurred_at.isoformat(),
                    "traceId": trace_id,
                    "causationId": str(causation_id) if causation_id else None,
                    "correlationId": str(correlation_id) if correlation_id else None,
                    "redacted": False,
                    "data": payload,
                },
            )
        )
        return event


def pending_outbox_query(destination: str, *, limit: int) -> Select[tuple[OutboxEvent]]:
    """Claim candidates; caller updates lease fields before committing."""
    return (
        select(OutboxEvent)
        .where(
            OutboxEvent.destination == destination,
            OutboxEvent.status == "PENDING",
            OutboxEvent.available_at <= func.now(),
        )
        .order_by(OutboxEvent.available_at, OutboxEvent.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )


def pending_temporal_outbox_query(*, limit: int) -> Select[tuple[OutboxEvent]]:
    """Claim only the earliest unfinished command of each Run."""
    current = aliased(RunCommand)
    earlier = aliased(RunCommand)
    unfinished_earlier = (
        select(earlier.id)
        .where(
            earlier.run_id == current.run_id,
            earlier.command_seq < current.command_seq,
            earlier.status.not_in(("APPLIED", "REJECTED", "FAILED", "DEAD")),
        )
        .exists()
    )
    return (
        select(OutboxEvent)
        .join(current, current.id == OutboxEvent.source_id)
        .where(
            OutboxEvent.destination == "temporal",
            OutboxEvent.status == "PENDING",
            OutboxEvent.available_at <= func.now(),
            ~unfinished_earlier,
        )
        .order_by(OutboxEvent.available_at, OutboxEvent.id)
        .limit(limit)
        .with_for_update(skip_locked=True, of=OutboxEvent)
    )


def pending_nats_outbox_query(*, limit: int) -> Select[tuple[OutboxEvent]]:
    """Claim only the earliest unpublished durable event of each Run."""
    current_event = aliased(RunEvent)
    earlier_event = aliased(RunEvent)
    earlier_outbox = aliased(OutboxEvent)
    unpublished_earlier = (
        select(earlier_outbox.id)
        .join(earlier_event, earlier_event.id == earlier_outbox.source_id)
        .where(
            earlier_event.run_id == current_event.run_id,
            earlier_event.event_seq < current_event.event_seq,
            earlier_outbox.destination == "nats",
            earlier_outbox.delivered_at.is_(None),
        )
        .exists()
    )
    return (
        select(OutboxEvent)
        .join(current_event, current_event.id == OutboxEvent.source_id)
        .where(
            OutboxEvent.destination == "nats",
            OutboxEvent.status == "PENDING",
            OutboxEvent.available_at <= func.now(),
            ~unpublished_earlier,
        )
        .order_by(OutboxEvent.available_at, OutboxEvent.id)
        .limit(limit)
        .with_for_update(skip_locked=True, of=OutboxEvent)
    )
