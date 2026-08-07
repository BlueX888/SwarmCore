from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence.models import Run, RunEvent, RunTask, Strategy, StrategyVersion

_TERMINAL_RUN_STATUSES = {"REJECTED", "CANCELLED", "SUCCEEDED", "TIMED_OUT"}
ACTIVE_RUN_STATUSES = (
    "ACCEPTED",
    "QUEUED",
    "RUNNING",
    "PENDING",
    "WAITING_INPUT",
    "WAITING_APPROVAL",
    "PAUSING",
    "CANCELLING",
)


@dataclass(frozen=True, slots=True)
class RunSummary:
    run_id: UUID
    status: str
    strategy_version_id: UUID
    snapshot_seq: int
    event_count: int
    task_count: int
    operator_name: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None
    cancel_reason: str | None


@dataclass(frozen=True, slots=True)
class RunSummaryPage:
    items: tuple[RunSummary, ...]
    total: int


class RunQueryService:
    async def get_snapshot(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        run_id: UUID,
    ) -> dict[str, Any]:
        run = await session.scalar(
            select(Run).where(
                Run.id == run_id,
                Run.tenant_id == tenant_id,
                Run.project_id == project_id,
            )
        )
        if run is None:
            raise LookupError("run not found")
        strategy_spec = await session.scalar(
            select(StrategyVersion.raw_spec)
            .join(Strategy, Strategy.id == StrategyVersion.strategy_id)
            .where(
                StrategyVersion.id == run.strategy_version_id,
                StrategyVersion.tenant_id == tenant_id,
                Strategy.tenant_id == tenant_id,
                Strategy.project_id == project_id,
            )
        )
        tasks = list(
            await session.scalars(
                select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.task_instance_key)
            )
        )
        task_events = list(
            await session.scalars(
                select(RunEvent).where(
                    RunEvent.run_id == run_id,
                    RunEvent.task_id.is_not(None),
                    RunEvent.type.in_(("task.failed", "task.completed")),
                )
            )
        )
        failure = await session.scalar(
            select(RunEvent)
            .where(RunEvent.run_id == run_id, RunEvent.type == "run.failed")
            .order_by(RunEvent.event_seq.desc())
            .limit(1)
        )
        errors = {
            item.task_id: item.payload.get("error")
            for item in task_events
            if item.type == "task.failed" and isinstance(item.payload.get("error"), dict)
        }
        outputs = {
            item.task_id: item.payload.get("output")
            for item in task_events
            if item.type == "task.completed" and isinstance(item.payload.get("output"), dict)
        }
        return render_run_snapshot(
            run,
            tasks,
            errors=errors,
            outputs=outputs,
            retryable=is_retryable_run_failure(failure),
            strategy_node_order=strategy_node_order_from_spec(strategy_spec),
        )

    async def list_summaries(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        strategy_version_ids: tuple[UUID, ...] | None = None,
        limit: int = 5,
        include_active: bool = True,
    ) -> RunSummaryPage:
        filters: list[Any] = [
            Run.tenant_id == tenant_id,
            Run.project_id == project_id,
        ]
        if strategy_version_ids is not None:
            if not strategy_version_ids:
                return RunSummaryPage(items=(), total=0)
            filters.append(Run.strategy_version_id.in_(strategy_version_ids))
        recent = list(
            await session.scalars(
                select(Run)
                .where(*filters)
                .order_by(Run.created_at.desc())
                .limit(limit)
            )
        )
        runs_by_id = {run.id: run for run in recent}
        if include_active:
            active = list(
                await session.scalars(
                    select(Run)
                    .where(*filters, Run.status.in_(ACTIVE_RUN_STATUSES))
                    .order_by(Run.created_at.desc())
                )
            )
            runs_by_id.update({run.id: run for run in active})
        selected = sorted(runs_by_id.values(), key=lambda run: run.created_at, reverse=True)
        items = await self._summaries_for_runs(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            runs=selected,
        )
        total = await session.scalar(select(func.count()).select_from(Run).where(*filters))
        return RunSummaryPage(items=tuple(items), total=int(total or 0))

    async def latest_summaries_by_strategy(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        strategy_version_ids: tuple[UUID, ...],
    ) -> dict[UUID, RunSummary]:
        if not strategy_version_ids:
            return {}
        ranked = (
            select(
                Run.id.label("run_id"),
                func.row_number()
                .over(
                    partition_by=Run.strategy_version_id,
                    order_by=Run.created_at.desc(),
                )
                .label("rank"),
            )
            .where(
                Run.tenant_id == tenant_id,
                Run.project_id == project_id,
                Run.strategy_version_id.in_(strategy_version_ids),
            )
            .subquery()
        )
        runs = list(
            await session.scalars(
                select(Run)
                .join(ranked, ranked.c.run_id == Run.id)
                .where(ranked.c.rank == 1)
                .order_by(Run.created_at.desc())
            )
        )
        summaries = await self._summaries_for_runs(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            runs=runs,
        )
        return {item.strategy_version_id: item for item in summaries}

    async def _summaries_for_runs(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        runs: list[Run],
    ) -> list[RunSummary]:
        if not runs:
            return []
        run_ids = tuple(run.id for run in runs)
        task_rows = await session.execute(
            select(RunTask.run_id, func.count(RunTask.id))
            .where(RunTask.tenant_id == tenant_id, RunTask.run_id.in_(run_ids))
            .group_by(RunTask.run_id)
        )
        task_counts = {run_id: int(count) for run_id, count in task_rows}
        reason_by_run: dict[UUID, tuple[str, str]] = {}
        reason_ids = tuple(run.id for run in runs if run.status in {"FAILED", "CANCELLED"})
        if reason_ids:
            reason_rows = await session.execute(
                select(RunEvent.run_id, RunEvent.type, RunEvent.payload)
                .where(
                    RunEvent.tenant_id == tenant_id,
                    RunEvent.project_id == project_id,
                    RunEvent.run_id.in_(reason_ids),
                    RunEvent.type.in_(("run.failed", "run.cancelled")),
                )
                .order_by(RunEvent.event_seq.desc())
            )
            for run_id, event_type, payload in reason_rows:
                if run_id in reason_by_run or not isinstance(payload, dict):
                    continue
                reason = payload.get("message") or payload.get("reason") or payload.get("code")
                if isinstance(reason, str) and reason:
                    reason_by_run[run_id] = (event_type, reason)

        items: list[RunSummary] = []
        for run in runs:
            input_data = run.input if isinstance(run.input, dict) else {}
            provenance = input_data.get("provenance")
            operator_name = None
            if isinstance(provenance, dict) and isinstance(
                provenance.get("operatorName"), str
            ):
                operator_name = provenance["operatorName"]
            for key in ("operatorName", "owner"):
                if not operator_name and isinstance(input_data.get(key), str):
                    operator_name = input_data[key]
            operator_name = operator_name or run.initiated_by or "当前用户"
            output = run.output if isinstance(run.output, dict) else {}
            event_reason = reason_by_run.get(run.id)
            failure_reason = output.get("failureReason") or output.get("error")
            if event_reason is not None and event_reason[0] == "run.failed":
                failure_reason = event_reason[1]
            if not isinstance(failure_reason, str):
                failure_reason = "运行执行失败,请查看运行详情" if run.status == "FAILED" else None
            cancel_reason = input_data.get("cancelReason")
            if event_reason is not None and event_reason[0] == "run.cancelled":
                cancel_reason = event_reason[1]
            if not isinstance(cancel_reason, str):
                cancel_reason = "运行已取消" if run.status == "CANCELLED" else None
            items.append(
                RunSummary(
                    run_id=run.id,
                    status=run.status,
                    strategy_version_id=run.strategy_version_id,
                    snapshot_seq=run.next_event_seq - 1,
                    event_count=run.next_event_seq - 1,
                    task_count=task_counts.get(run.id, 0),
                    operator_name=operator_name,
                    created_at=run.created_at,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    failure_reason=failure_reason,
                    cancel_reason=cancel_reason,
                )
            )
        return items


def render_run_snapshot(
    run: Run,
    tasks: list[RunTask] | None = None,
    *,
    errors: dict[UUID | None, Any] | None = None,
    outputs: dict[UUID | None, Any] | None = None,
    retryable: bool = False,
    strategy_node_order: list[str] | None = None,
) -> dict[str, Any]:
    task_items = tasks or []
    task_counts: dict[str, int] = {}
    for task in task_items:
        task_counts[task.status] = task_counts.get(task.status, 0) + 1
    actions: list[str] = []
    if run.status in {"QUEUED", "RUNNING", "WAITING_APPROVAL", "WAITING_INPUT"}:
        actions.append("pause")
    if run.status in {"PAUSING", "PAUSED"}:
        actions.append("resume")
    if run.status not in _TERMINAL_RUN_STATUSES | {"FAILED"}:
        actions.append("cancel")
    can_retry = (
        retryable
        and run.status == "FAILED"
        and any(task.status == "FAILED" for task in task_items)
    )
    if can_retry:
        actions.append("retry_task")
    return {
        "runId": str(run.id),
        "status": run.status,
        "input": run.input,
        "output": run.output,
        "outputRef": run.output_ref,
        "snapshotSeq": run.next_event_seq - 1,
        "earliestAvailableSeq": run.earliest_available_seq,
        "strategyVersionId": str(run.strategy_version_id),
        "strategyNodeOrder": strategy_node_order or [],
        "planHash": run.plan_hash,
        "usage": run.usage,
        "taskCounts": task_counts,
        "allowedActions": actions,
        "startedAt": _utc_text(run.started_at),
        "completedAt": _utc_text(run.completed_at),
        "tasks": [
            {
                "taskId": str(task.id),
                "nodeKey": task.node_key,
                "nodeType": task.node_type,
                "status": task.status,
                "dependencies": task.dependencies,
                "error": (errors or {}).get(task.id) if task.status == "FAILED" else None,
                "output": (outputs or {}).get(task.id),
                "retryGeneration": task.retry_generation,
                "allowedActions": ["retry_task"] if can_retry and task.status == "FAILED" else [],
            }
            for task in task_items
        ],
    }


def strategy_node_order_from_spec(raw_spec: Any) -> list[str]:
    if not isinstance(raw_spec, dict):
        return []
    spec = raw_spec.get("spec")
    if not isinstance(spec, dict):
        return []
    graph = spec.get("graph")
    if not isinstance(graph, dict):
        return []
    nodes = graph.get("nodes")
    if not isinstance(nodes, dict):
        return []
    return [key for key in nodes if isinstance(key, str)]


def is_retryable_run_failure(failure: RunEvent | None) -> bool:
    if failure is None or not isinstance(failure.payload, dict):
        return False
    return failure.payload.get("retryable") is True


def _utc_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value.isoformat()).replace("+00:00", "Z")
