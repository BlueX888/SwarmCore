from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from swarmcore_observability import SwarmMetrics
from swarmcore_persistence import (
    OutboxClaim,
    OutboxLeaseKeeper,
    claim_outbox,
    owns_outbox_claim,
)
from swarmcore_persistence.models import (
    DocumentProcessingRun,
    OutboxEvent,
    Run,
    RunCommand,
)
from swarmcore_persistence.repositories import EventRepository, pending_temporal_outbox_query
from swarmcore_runtime_temporal import DocumentProcessingWorkflow, SwarmRunWorkflow
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
        task_queue: str = "swarm-control",
        agent_task_queue: str = "agent-general",
        tool_task_queue: str = "tool-trusted",
        batch_size: int = 50,
        metrics: SwarmMetrics | None = None,
    ) -> None:
        self._sessions = sessions
        self._temporal = temporal
        self._worker_id = worker_id
        self._task_queue = task_queue
        self._agent_task_queue = agent_task_queue
        self._tool_task_queue = tool_task_queue
        self._batch_size = batch_size
        self._events = EventRepository()
        self._metrics = metrics
        self._last_pending = 0

    async def run_once(self) -> int:
        claimed = await self._claim()
        for claim in claimed:
            try:
                async with OutboxLeaseKeeper(
                    self._sessions, claim, worker_id=self._worker_id
                ):
                    await self._deliver(claim)
            except Exception as exc:
                await self._retry(claim, str(exc))
        return len(claimed)

    async def _claim(self) -> list[OutboxClaim]:
        now = datetime.now(UTC)
        claimed: list[OutboxClaim] = []
        partitions: set[str] = set()
        async with self._sessions() as session, session.begin():
            pending = int(
                await session.scalar(
                    select(func.count(OutboxEvent.id)).where(
                        OutboxEvent.destination.in_(("temporal", "document-temporal")),
                        OutboxEvent.status == "PENDING",
                    )
                )
                or 0
            )
            candidates = list(
                await session.scalars(pending_temporal_outbox_query(limit=self._batch_size * 2))
            )
            for event in candidates:
                if event.partition_key in partitions:
                    continue
                partitions.add(event.partition_key)
                claimed.append(claim_outbox(event, worker_id=self._worker_id, now=now))
                if self._metrics is not None:
                    self._metrics.queue_schedule_latency.record(
                        max(0.0, (now - event.available_at).total_seconds()),
                        {"queue": "temporal"},
                    )
                if len(claimed) >= self._batch_size:
                    break
        if self._metrics is not None:
            self._metrics.outbox_pending.add(
                pending - self._last_pending, {"destination": "temporal"}
            )
            self._last_pending = pending
        return claimed

    async def _deliver(self, claim: OutboxClaim) -> None:
        async with self._sessions() as session:
            outbox = await session.get(OutboxEvent, claim.id)
            if outbox is None or not owns_outbox_claim(
                outbox, claim, worker_id=self._worker_id
            ):
                return
            if outbox.type in {
                "document.processing.requested",
                "document.processing.cancel.requested",
            }:
                await self._deliver_document_processing(claim, outbox)
                return
            command = await session.get(RunCommand, outbox.source_id)
            if command is None:
                await self._dead(claim, "source RunCommand does not exist")
                return
            run = await session.get(Run, command.run_id)
            if run is None:
                await self._dead(claim, "Run does not exist")
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
                    "strategyVersionId": str(run.strategy_version_id),
                    "planHash": run.plan_hash,
                    "input": run.input,
                    "initiatedBy": run.initiated_by,
                    "submittedScopes": run.submitted_scopes,
                    "authContextHash": run.auth_context_hash,
                    "policyRevision": run.policy_revision,
                    "controlTaskQueue": self._task_queue,
                    "agentTaskQueue": self._agent_task_queue,
                    "toolTaskQueue": self._tool_task_queue,
                    "startCommand": command_payload,
                }
                try:
                    handle = await self._temporal.start_workflow(
                        SwarmRunWorkflow.run,
                        run_input,
                        id=run.temporal_workflow_id,
                        task_queue=self._task_queue,
                        id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
                    )
                    temporal_run_id = handle.first_execution_run_id
                except WorkflowAlreadyStartedError:
                    temporal_run_id = None
                result: dict[str, Any] = {"status": "APPLIED"}
            elif command.type in {
                "pause",
                "resume",
                "cancel",
                "approve",
                "reject",
                "provide_input",
                "retry_task",
            }:
                handle = self._temporal.get_workflow_handle(run.temporal_workflow_id)
                result = await handle.execute_update(
                    "apply_command",
                    command_payload,
                    id=str(command.request_id),
                    result_type=dict[str, Any],
                    rpc_timeout=timedelta(seconds=20),
                )
                temporal_run_id = None
            else:
                await self._dead(claim, f"unknown command type: {command.type}")
                return
        await self._complete(claim, result, temporal_run_id=temporal_run_id)

    async def _deliver_document_processing(
        self, claim: OutboxClaim, outbox: OutboxEvent
    ) -> None:
        payload = dict(outbox.payload)
        workflow_id = f"document-processing/{payload['processingRunId']}"
        temporal_run_id: str | None = None
        if outbox.type == "document.processing.requested":
            try:
                handle = await self._temporal.start_workflow(
                    DocumentProcessingWorkflow.run,
                    payload,
                    id=workflow_id,
                    task_queue=self._task_queue,
                    id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
                )
                temporal_run_id = handle.first_execution_run_id
            except WorkflowAlreadyStartedError:
                pass
        else:
            handle = self._temporal.get_workflow_handle(workflow_id)
            await handle.cancel()
        now = datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            current = await session.get(OutboxEvent, claim.id, with_for_update=True)
            if current is None or not owns_outbox_claim(
                current, claim, worker_id=self._worker_id
            ):
                return
            current.status = "DELIVERED"
            current.delivered_at = now
            current.locked_by = None
            current.locked_until = None
            processing = await session.get(
                DocumentProcessingRun,
                UUID(str(payload["processingRunId"])),
                with_for_update=True,
            )
            if processing is not None:
                processing.provenance = {
                    **processing.provenance,
                    "temporalWorkflowId": workflow_id,
                    **(
                        {
                            "temporalRunId": temporal_run_id,
                            "dispatchedAt": now.isoformat(),
                        }
                        if outbox.type == "document.processing.requested"
                        else {"cancelDispatchedAt": now.isoformat()}
                    ),
                }

    async def _complete(
        self, claim: OutboxClaim, result: dict[str, Any], *, temporal_run_id: str | None
    ) -> None:
        now = datetime.now(UTC)
        async with self._sessions() as session, session.begin():
            outbox = await session.get(OutboxEvent, claim.id, with_for_update=True)
            if outbox is None or not owns_outbox_claim(
                outbox, claim, worker_id=self._worker_id
            ):
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
            run = await session.get(Run, command.run_id, with_for_update=True)
            if run is not None:
                await self._events.append(
                    session,
                    tenant_id=run.tenant_id,
                    project_id=run.project_id,
                    run_id=run.id,
                    transition_id=command.id,
                    event_type=(
                        "command.applied"
                        if result.get("status") == "APPLIED"
                        else "command.rejected"
                    ),
                    payload={
                        "commandId": str(command.id),
                        "requestId": str(command.request_id),
                        "commandSeq": command.command_seq,
                        "type": command.type,
                        "status": command.status,
                        "result": result,
                    },
                    occurred_at=now,
                    causation_id=command.id,
                )
            if temporal_run_id and run is not None:
                run.temporal_run_id = temporal_run_id

    async def _retry(self, claim: OutboxClaim, error: str) -> None:
        if self._metrics is not None:
            self._metrics.activity_retries.add(1, {"category": "command_dispatch"})
        async with self._sessions() as session, session.begin():
            outbox = await session.get(OutboxEvent, claim.id, with_for_update=True)
            if outbox is None or not owns_outbox_claim(
                outbox, claim, worker_id=self._worker_id
            ):
                return
            outbox.attempts += 1
            outbox.status = "PENDING"
            outbox.available_at = datetime.now(UTC) + retry_delay(outbox.attempts)
            outbox.last_error = error[:4000]
            outbox.locked_by = None
            outbox.locked_until = None

    async def _dead(self, claim: OutboxClaim, error: str) -> None:
        async with self._sessions() as session, session.begin():
            outbox = await session.get(OutboxEvent, claim.id, with_for_update=True)
            if outbox is None or not owns_outbox_claim(
                outbox, claim, worker_id=self._worker_id
            ):
                return
            outbox.status = "DEAD"
            outbox.last_error = error
            outbox.locked_by = None
            outbox.locked_until = None
            command = await session.get(RunCommand, outbox.source_id, with_for_update=True)
            if command is not None:
                command.status = "FAILED"
                command.error = {"code": "PERMANENT_DELIVERY_ERROR", "detail": error}
