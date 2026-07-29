from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from swarmcore_domain import uuid7
from swarmcore_observability import SwarmMetrics
from swarmcore_persistence import EventRepository, tenant_transaction
from swarmcore_persistence.models import (
    ApprovalRequest,
    CompensationRecord,
    ExternalInputRequest,
    Run,
    RunEvent,
    RunTask,
    StrategyVersion,
)
from swarmcore_tool_gateway import CapabilityTokenIssuer


class GatewayCapabilityIssuer:
    def __init__(self, tokens: CapabilityTokenIssuer) -> None:
        self._tokens = tokens

    def issue(self, request: Mapping[str, Any]) -> str:
        run = request["run"]
        return self._tokens.issue(
            tenant_id=str(run["tenantId"]),
            project_id=str(run["projectId"]),
            run_id=str(run["runId"]),
            node_key=str(request["nodeKey"]),
            tool_ref=str(request["toolRef"]),
            execution_id=str(request["executionId"]),
            effect_id=(str(request["effectId"]) if request.get("effectId") else None),
            approved=bool(request.get("approved", False)),
            canonical_input_hash=(
                str(request["canonicalInputHash"]) if request.get("canonicalInputHash") else None
            ),
            policy_revision=(
                str(request["policyRevision"]) if request.get("policyRevision") else None
            ),
            action=str(request.get("action", "tool.execute")),
        )


class PostgresPlanStore:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def load(
        self, *, tenant_id: str, project_id: str, run_id: str, plan_hash: str
    ) -> dict[str, Any]:
        tenant_uuid = UUID(tenant_id)
        project_uuid = UUID(project_id)
        run_uuid = UUID(run_id)
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_uuid, project_id=project_uuid
        ) as session:
            run = await session.scalar(
                select(Run).where(Run.id == run_uuid, Run.tenant_id == tenant_uuid)
            )
            if run is None:
                raise LookupError("run not found")
            version = await session.scalar(
                select(StrategyVersion).where(
                    StrategyVersion.id == run.strategy_version_id,
                    StrategyVersion.tenant_id == tenant_uuid,
                )
            )
            if version is None or version.plan_hash != plan_hash or run.plan_hash != plan_hash:
                raise RuntimeError("execution plan hash mismatch")
            return dict(version.plan)


class PostgresTransitionProjector:
    _TASK_STATUS: ClassVar[dict[str, str]] = {
        "task.started": "RUNNING",
        "task.completed": "SUCCEEDED",
        "task.failed": "FAILED",
        "task.skipped": "SKIPPED",
        "task.cancelled": "CANCELLED",
        "task.retry_requested": "RETRYING",
        "task.retry_started": "RUNNING",
    }

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        metrics: SwarmMetrics | None = None,
    ) -> None:
        self._sessions = sessions
        self._events = EventRepository()
        self._metrics = metrics

    async def project(self, transition: Mapping[str, Any]) -> None:
        run_data = transition["run"]
        tenant_id = UUID(str(run_data["tenantId"]))
        project_id = UUID(str(run_data["projectId"]))
        run_id = UUID(str(run_data["runId"]))
        event_type = str(transition["type"])
        data = dict(transition.get("data", {}))
        occurred_at = datetime.now(UTC)
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            task_id = await self._project_task(
                session,
                tenant_id=tenant_id,
                run_id=run_id,
                event_type=event_type,
                data=data,
            )
            await self._events.append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                task_id=task_id,
                transition_id=UUID(str(transition["transitionId"])),
                event_type=event_type,
                payload=data,
                occurred_at=occurred_at,
            )
            await self._project_human_request(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                event_type=event_type,
                data=data,
                occurred_at=occurred_at,
            )
            if event_type.startswith("compensation."):
                await self._project_compensation(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    run_id=run_id,
                    event_type=event_type,
                    data=data,
                )
            if event_type == "run.completed":
                run = await session.get(Run, run_id, with_for_update=True)
                if run is not None:
                    result = data.get("result")
                    run.output = result if isinstance(result, dict) else {"result": result}
            elif event_type == "task.completed":
                run = await session.get(Run, run_id, with_for_update=True)
                output = data.get("output")
                metrics = output.get("metrics") if isinstance(output, dict) else None
                if run is not None and isinstance(metrics, dict):
                    usage = dict(run.usage)
                    for key, value in metrics.items():
                        if isinstance(value, int | float):
                            usage[key] = float(usage.get(key, 0)) + value
                    run.usage = usage
            if self._metrics is not None:
                if event_type == "run.started":
                    self._metrics.active_runs.add(1)
                if event_type in {
                    "run.completed",
                    "run.failed",
                    "run.cancelled",
                    "run.timed_out",
                    "run.rejected",
                }:
                    status = event_type.removeprefix("run.")
                    run = await session.get(Run, run_id)
                    strategy = (
                        str(run.strategy_version_id) if run is not None else "unknown"
                    )
                    self._metrics.runs_total.add(
                        1, {"status": status, "strategy": strategy}
                    )
                    self._metrics.active_runs.add(-1)
                    if run is not None and run.started_at is not None:
                        self._metrics.run_duration.record(
                            max(0.0, (occurred_at - run.started_at).total_seconds()),
                            {"status": status},
                        )
                if event_type in {"task.completed", "task.failed", "task.cancelled"}:
                    task = await session.get(RunTask, task_id) if task_id is not None else None
                    if task is not None:
                        started_at = await session.scalar(
                            select(RunEvent.occurred_at)
                            .where(
                                RunEvent.run_id == run_id,
                                RunEvent.task_id == task.id,
                                RunEvent.type == "task.started",
                            )
                            .order_by(RunEvent.occurred_at.desc())
                            .limit(1)
                        )
                        if started_at is not None:
                            self._metrics.task_duration.record(
                                max(0.0, (occurred_at - started_at).total_seconds()),
                                {"node_type": task.node_type},
                            )

    async def _project_compensation(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        run_id: UUID,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        effect_id = str(data["effectId"])
        record = await session.scalar(
            select(CompensationRecord).where(
                CompensationRecord.run_id == run_id,
                CompensationRecord.effect_id == effect_id,
            )
        )
        status = {
            "compensation.completed": "COMPENSATED",
            "compensation.failed": "FAILED",
            "compensation.manual_required": "MANUAL_RECOVERY_REQUIRED",
        }.get(event_type, "PENDING")
        if record is None:
            record = CompensationRecord(
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                effect_id=effect_id,
                operation=str(data.get("toolRef", "unknown")),
                status=status,
                input=dict(data.get("input", {})),
            )
            session.add(record)
        else:
            record.status = status
        if data.get("error") is not None:
            record.error = str(data["error"])[:2000]

    async def _project_task(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        run_id: UUID,
        event_type: str,
        data: dict[str, Any],
    ) -> UUID | None:
        if not event_type.startswith("task."):
            return None
        node_key = str(data["nodeKey"])
        task_instance_key = str(data.get("taskInstanceKey", node_key))
        task = await session.scalar(
            select(RunTask).where(
                RunTask.run_id == run_id,
                RunTask.task_instance_key == task_instance_key,
            )
        )
        if task is None:
            task = RunTask(
                id=uuid7(),
                tenant_id=tenant_id,
                run_id=run_id,
                node_key=node_key,
                task_instance_key=task_instance_key,
                node_type=str(data.get("nodeType", "unknown")),
                iteration_no=(
                    int(data["iterationNo"]) if data.get("iterationNo") is not None else None
                ),
                dependencies=list(data.get("dependencies", [])),
            )
            session.add(task)
            await session.flush()
        target = self._TASK_STATUS.get(event_type)
        if target:
            task.status = target
            task.version += 1
            if event_type == "task.retry_requested":
                task.retry_generation += 1
            if event_type == "task.completed":
                task.output_ref = f"inline:event:{data.get('nodeKey')}"
        return task.id

    async def _project_human_request(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        run_id: UUID,
        event_type: str,
        data: dict[str, Any],
        occurred_at: datetime,
    ) -> None:
        request_id_text = data.get("requestId")
        if not isinstance(request_id_text, str):
            return
        request_id = UUID(request_id_text)
        if event_type == "approval.requested":
            existing = await session.get(ApprovalRequest, request_id)
            if existing is None:
                existing = await session.scalar(
                    select(ApprovalRequest)
                    .where(
                        ApprovalRequest.run_id == run_id,
                        ApprovalRequest.node_key == str(data["nodeKey"]),
                    )
                    .with_for_update()
                )
            if existing is None:
                session.add(
                    ApprovalRequest(
                        id=request_id,
                        tenant_id=tenant_id,
                        project_id=project_id,
                        run_id=run_id,
                        node_key=str(data["nodeKey"]),
                        prompt=str(data["prompt"]),
                        input_schema=dict(data.get("inputSchema", {"type": "object"})),
                        requested_by=str(data.get("requestedBy", "workflow")),
                        task_execution_id=data.get("taskExecutionId"),
                        tool_ref=data.get("toolRef"),
                        tool_version=data.get("toolVersion"),
                        canonical_input_hash=data.get("canonicalInputHash"),
                        policy_revision=data.get("policyRevision"),
                        expires_at=(
                            datetime.fromisoformat(str(data["expiresAt"]))
                            if data.get("expiresAt")
                            else None
                        ),
                        requires_distinct_approver=bool(
                            data.get("requiresDistinctApprover", False)
                        ),
                    )
                )
            else:
                existing.id = request_id
                existing.prompt = str(data["prompt"])
                existing.input_schema = dict(
                    data.get("inputSchema", {"type": "object"})
                )
                existing.status = "PENDING"
                existing.requested_by = str(data.get("requestedBy", "workflow"))
                existing.handled_by = None
                existing.decision = None
                existing.response = None
                existing.handler_command_id = None
                existing.created_at = occurred_at
                existing.handled_at = None
                existing.task_execution_id = data.get("taskExecutionId")
                existing.tool_ref = data.get("toolRef")
                existing.tool_version = data.get("toolVersion")
                existing.canonical_input_hash = data.get("canonicalInputHash")
                existing.policy_revision = data.get("policyRevision")
                existing.expires_at = (
                    datetime.fromisoformat(str(data["expiresAt"]))
                    if data.get("expiresAt")
                    else None
                )
                existing.requires_distinct_approver = bool(
                    data.get("requiresDistinctApprover", False)
                )
            return
        if event_type == "input.requested":
            if await session.get(ExternalInputRequest, request_id) is None:
                session.add(
                    ExternalInputRequest(
                        id=request_id,
                        tenant_id=tenant_id,
                        project_id=project_id,
                        run_id=run_id,
                        node_key=str(data["nodeKey"]),
                        prompt=str(data["prompt"]),
                        input_schema=dict(data.get("inputSchema", {"type": "object"})),
                    )
                )
            return
        if event_type in {"approval.approved", "approval.rejected"}:
            approval_request = await session.get(ApprovalRequest, request_id, with_for_update=True)
            if approval_request is not None and approval_request.status == "PENDING":
                approval_request.status = (
                    "APPROVED" if event_type.endswith("approved") else "REJECTED"
                )
                approval_request.decision = approval_request.status
                approval_request.response = dict(data.get("value", {}))
                approval_request.handled_at = occurred_at
                if self._metrics is not None:
                    self._metrics.approval_wait.record(
                        max(
                            0.0,
                            (occurred_at - approval_request.created_at).total_seconds(),
                        )
                    )
        elif event_type == "input.received":
            input_request = await session.get(
                ExternalInputRequest, request_id, with_for_update=True
            )
            if input_request is not None and input_request.status == "PENDING":
                input_request.status = "RECEIVED"
                input_request.value = dict(data.get("value", {}))
                input_request.handled_at = occurred_at
