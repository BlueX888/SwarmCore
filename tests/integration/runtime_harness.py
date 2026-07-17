from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_api import create_app
from swarmcore_api.settings import Settings
from swarmcore_command_dispatcher import CommandDispatcher
from swarmcore_persistence import Database
from swarmcore_runtime_temporal import ControlActivities, SwarmRunWorkflow
from swarmcore_worker_agent import AgentActivities
from swarmcore_worker_agent.fake import DeterministicFakeAgentAdapter
from swarmcore_worker_control import PostgresPlanStore, PostgresTransitionProjector
from temporalio.client import Client
from temporalio.worker import Worker


class RuntimeHarness:
    """Owns the shared API, PostgreSQL, dispatcher, and Temporal test runtime."""

    def __init__(self, database_url: str, temporal: Client) -> None:
        self.database_url = database_url
        self.temporal = temporal
        self.tenant_id = uuid4()
        self.project_id = uuid4()
        self.database = Database(database_url)
        self.dispatcher = CommandDispatcher(
            self.database.sessions,
            temporal,
            worker_id=f"runtime-integration-{uuid4()}",
        )
        self._control_activities = ControlActivities(
            PostgresPlanStore(self.database.sessions),
            PostgresTransitionProjector(self.database.sessions),
        )
        self._agent_activities = AgentActivities(DeterministicFakeAgentAdapter())
        self._api_context = TestClient(
            create_app(Settings(database_url=database_url, telemetry_enabled=False))
        )
        self.api: TestClient

    @property
    def headers(self) -> dict[str, str]:
        return {"X-Tenant-ID": str(self.tenant_id)}

    def project_url(self, resource: str) -> str:
        return f"/v1/projects/{self.project_id}/{resource}"

    async def start(self) -> None:
        await self._seed_scope()
        self.api = self._api_context.__enter__()

    async def close(self) -> None:
        self._api_context.__exit__(None, None, None)
        await self.database.dispose()

    def control_worker(self) -> Worker:
        return Worker(
            self.temporal,
            task_queue="swarm-control",
            workflows=[SwarmRunWorkflow],
            activities=[
                self._control_activities.load_execution_plan,
                self._control_activities.project_transition,
                self._control_activities.execute_control_node,
            ],
        )

    def agent_worker(self) -> Worker:
        return Worker(
            self.temporal,
            task_queue="agent-general",
            activities=[
                self._agent_activities.execute_agent,
                self._agent_activities.execute_team,
            ],
        )

    @asynccontextmanager
    async def workers(self) -> AsyncIterator[None]:
        async with self.control_worker(), self.agent_worker():
            yield

    async def _seed_scope(self) -> None:
        engine = create_async_engine(self.database_url)
        try:
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        "INSERT INTO tenants (id, name, status, created_at, updated_at) "
                        "VALUES (:tenant, :name, 'ACTIVE', now(), now())"
                    ),
                    {
                        "tenant": self.tenant_id,
                        "name": f"runtime-tenant-{self.tenant_id}",
                    },
                )
                await connection.execute(
                    text("SELECT set_config('app.tenant_id', :tenant, true)"),
                    {"tenant": str(self.tenant_id)},
                )
                await connection.execute(
                    text(
                        "INSERT INTO projects "
                        "(id, tenant_id, name, settings, created_at, updated_at) "
                        "VALUES (:project, :tenant, 'runtime-project', '{}', now(), now())"
                    ),
                    {"project": self.project_id, "tenant": self.tenant_id},
                )
        finally:
            await engine.dispose()


def workflow_id(tenant_id: UUID, run_id: str) -> str:
    return f"swarm:{tenant_id}:{run_id}"
