from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import OutboxEvent, Run, RunEvent


@dataclass(frozen=True)
class ReconcileReport:
    run_id: UUID
    projection_repaired: bool
    outbox_repaired: int


class ProjectionReconciler:
    STATUS_BY_EVENT: ClassVar[dict[str, str]] = {
        "run.accepted": "ACCEPTED",
        "run.validating": "VALIDATING",
        "run.queued": "QUEUED",
        "run.started": "RUNNING",
        "run.waiting_input": "WAITING_INPUT",
        "run.waiting_approval": "WAITING_APPROVAL",
        "run.pausing": "PAUSING",
        "run.paused": "PAUSED",
        "run.resumed": "RUNNING",
        "run.cancelling": "CANCELLING",
        "run.compensating": "COMPENSATING",
        "run.cancelled": "CANCELLED",
        "run.completed": "SUCCEEDED",
        "run.failed": "FAILED",
        "run.timed_out": "TIMED_OUT",
        "run.rejected": "REJECTED",
    }

    async def reconcile_run(self, session: AsyncSession, run_id: UUID) -> ReconcileReport:
        run = await session.scalar(select(Run).where(Run.id == run_id).with_for_update())
        if run is None:
            raise LookupError("run not found")
        events = list(
            await session.scalars(
                select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.event_seq)
            )
        )
        expected_status = next(
            (
                self.STATUS_BY_EVENT[event.type]
                for event in reversed(events)
                if event.type in self.STATUS_BY_EVENT
            ),
            run.status,
        )
        projection_repaired = expected_status != run.status
        if projection_repaired:
            run.status = expected_status
            run.version += 1
            run.projection_updated_at = events[-1].occurred_at if events else None

        existing_sources = set(
            await session.scalars(
                select(OutboxEvent.source_id).where(
                    OutboxEvent.destination == "nats",
                    OutboxEvent.source_id.in_([event.id for event in events]),
                )
            )
        )
        repaired = 0
        for event in events:
            if event.id in existing_sources:
                continue
            session.add(
                OutboxEvent(
                    tenant_id=event.tenant_id,
                    aggregate_id=event.run_id,
                    destination="nats",
                    partition_key=str(event.run_id),
                    source_id=event.id,
                    type=event.type,
                    payload=self._envelope(event),
                )
            )
            repaired += 1
        run.reconciled_at = datetime.now(UTC)
        return ReconcileReport(
            run_id=run_id,
            projection_repaired=projection_repaired,
            outbox_repaired=repaired,
        )

    @staticmethod
    def _envelope(event: RunEvent) -> dict[str, object]:
        return {
            "id": str(event.id),
            "seq": event.event_seq,
            "type": event.type,
            "schemaVersion": event.schema_version,
            "tenantId": str(event.tenant_id),
            "projectId": str(event.project_id),
            "runId": str(event.run_id),
            "taskId": str(event.task_id) if event.task_id else None,
            "attemptId": str(event.attempt_id) if event.attempt_id else None,
            "occurredAt": event.occurred_at.isoformat(),
            "traceId": event.trace_id,
            "causationId": str(event.causation_id) if event.causation_id else None,
            "correlationId": str(event.correlation_id) if event.correlation_id else None,
            "redacted": event.redacted,
            "data": event.payload,
        }
