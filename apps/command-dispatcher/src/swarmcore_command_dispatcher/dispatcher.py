from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from swarmcore_persistence.models import OutboxEvent, Run, RunCommand
from swarmcore_persistence.repositories import pending_temporal_outbox_query
from swarmcore_runtime_temporal import SwarmRunWorkflow
from temporalio.client import Client
from temporalio.common import WorkflowIDConflictPolicy
from temporalio.exceptions import WorkflowAlreadyStartedError


def retry_delay(attempt: int) -> timedelta:
    return timedelta(seconds=min(300, 2 ** min(max(attempt, 0), 9)))


class CommandDispatcher:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        temporal: Client,
        *,
        worker_id: str,
        batch_size: int = 50,
    ) -> None:
        self._sessions = sessions
        self._temporal = temporal
        self._worker_id = worker_id
        self._batch_size = batch_size

    async def run_once(self) -> int:
        claimed = await self._claim()
        for outbox_id in claimed:
            try:
                await self._deliver(outbox_id)
            except Exception as exc:
                await self._retry(outbox_id, str(exc))
        return len(claimed)

    async def _claim(self) -> list[UUID]:
        now = datetime.now(UTC)
        claimed: list[UUID] = []
        partitions: set[str] = set()
        async with self._sessions() as session, session.begin():
            candidates = list(
                await session.scalars(pending_temporal_outbox_query(limit=self._batch_size * 2))
            )
            for event in candidates:
                if event.partition_key in partitions:
                    continue
                event.status = "DELIVERING"
                event.locked_by = self._worker_id
                event.locked_until = now + timedelta(seconds=30)
                partitions.add(event.partition_key)
                claimed.append(event.id)
                if len(claimed) >= self._batch_size:
                    break
        return claimed

    async def _deliver(self, outbox_id: UUID) -> None:
        async with self._sessions() as session:
            outbox = await session.get(OutboxEvent, outbox_id)
            if outbox is None or outbox.status != "DELIVERING":
                return
            command = await session.get(RunCommand, outbox.source_id)
            if command is None:
                await self._dead(outbox_id, "source RunCommand does not exist")
                return
            run = await session.get(Run, command.run_id)
            if run is None:
                await self._dead(outbox_id, "Run does not exist")
                return
            command_payload = {
                "commandId": str(command.id),
                "commandSeq": command.command_seq,
                "requestId": str(command.request_id),
                "type": command.type,
                "data": command.payload,
            }
            if command.type == "start":
                run_input = {
                    "tenantId": str(run.tenant_id),
                    "projectId": str(run.project_id),
                    "runId": str(run.id),
                    "planHash": run.plan_hash,
                    "input": run.input,
                    "startCommand": command_payload,
                }
                try:
                    handle = await self._temporal.start_workflow(
                        SwarmRunWorkflow.run,
                        run_input,
                        id=run.temporal_workflow_id,
                        task_queue="swarm-control",
                        id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
                    )
                    temporal_run_id = handle.first_execution_run_id
                except WorkflowAlreadyStartedError:
                    temporal_run_id = None
                result: dict[str, Any] = {"status": "APPLIED"}
            elif command.type == "cancel":
                handle = self._temporal.get_workflow_handle(run.temporal_workflow_id)
                result = await handle.execute_update(
                    "apply_command",
                    command_payload,
                    id=str(command.request_id),
                    result_type=dict[str, Any],
                )
                temporal_run_id = None
            else:
                await self._dead(outbox_id, f"unknown command type: {command.type}")
                return
        await self._complete(outbox_id, result, temporal_run_id=temporal_run_id)

    async def _complete(
        self, outbox_id: UUID, result: dict[str, Any], *, temporal_run_id: str | None
    ) -> None:
        now = datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            outbox = await session.get(OutboxEvent, outbox_id, with_for_update=True)
            if outbox is None:
                return
            command = await session.get(RunCommand, outbox.source_id, with_for_update=True)
            if command is None:
                return
            outbox.status = "DELIVERED"
            outbox.delivered_at = now
            outbox.locked_by = None
            outbox.locked_until = None
            command.result = result
            if result.get("status") == "APPLIED":
                command.status = "APPLIED"
                command.applied_at = now
            else:
                command.status = "REJECTED"
                command.rejected_at = now
            if temporal_run_id:
                run = await session.get(Run, command.run_id, with_for_update=True)
                if run is not None:
                    run.temporal_run_id = temporal_run_id

    async def _retry(self, outbox_id: UUID, error: str) -> None:
        async with self._sessions() as session, session.begin():
            outbox = await session.get(OutboxEvent, outbox_id, with_for_update=True)
            if outbox is None or outbox.status == "DEAD":
                return
            outbox.attempts += 1
            outbox.status = "PENDING"
            outbox.available_at = datetime.now(UTC) + retry_delay(outbox.attempts)
            outbox.last_error = error[:4000]
            outbox.locked_by = None
            outbox.locked_until = None

    async def _dead(self, outbox_id: UUID, error: str) -> None:
        async with self._sessions() as session, session.begin():
            outbox = await session.get(OutboxEvent, outbox_id, with_for_update=True)
            if outbox is None:
                return
            outbox.status = "DEAD"
            outbox.last_error = error
            outbox.locked_by = None
            outbox.locked_until = None
            command = await session.get(RunCommand, outbox.source_id, with_for_update=True)
            if command is not None:
                command.status = "DEAD"
                command.error = {"code": "PERMANENT_DELIVERY_ERROR", "detail": error}
