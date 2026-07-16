from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from swarmcore_domain import uuid7
from swarmcore_persistence import EventRepository, tenant_transaction
from swarmcore_persistence.models import Run, RunTask, StrategyVersion


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
    }

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions
        self._events = EventRepository()

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
        task = await session.scalar(
            select(RunTask).where(
                RunTask.run_id == run_id,
                RunTask.task_instance_key == node_key,
            )
        )
        if task is None:
            task = RunTask(
                id=uuid7(),
                tenant_id=tenant_id,
                run_id=run_id,
                node_key=node_key,
                task_instance_key=node_key,
                node_type=str(data.get("nodeType", "unknown")),
                dependencies=list(data.get("dependencies", [])),
            )
            session.add(task)
            await session.flush()
        target = self._TASK_STATUS.get(event_type)
        if target:
            task.status = target
            task.version += 1
            if event_type == "task.completed":
                task.output_ref = f"inline:event:{data.get('nodeKey')}"
        return task.id
