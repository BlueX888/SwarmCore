from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence.models import Run, RunEvent, RunTask, Strategy, StrategyVersion

_TERMINAL_RUN_STATUSES = {"REJECTED", "CANCELLED", "SUCCEEDED", "TIMED_OUT"}


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
