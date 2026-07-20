from __future__ import annotations

import asyncio
import os
from typing import Any
from uuid import uuid4

import pytest
from conftest import TemporalTestEnvironment
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_api import create_app
from swarmcore_api.settings import Settings
from swarmcore_command_dispatcher import CommandDispatcher
from swarmcore_persistence import Database, PostgresEffectJournal
from swarmcore_registry import builtin_registry
from swarmcore_runtime_temporal import ControlActivities, SwarmRunWorkflow
from swarmcore_tool_gateway import CapabilityTokenIssuer, ToolGateway, builtin_executors
from swarmcore_worker_agent import AgentActivities
from swarmcore_worker_agent.fake import DeterministicFakeAgentAdapter
from swarmcore_worker_control import (
    GatewayCapabilityIssuer,
    PostgresPlanStore,
    PostgresTransitionProjector,
)
from swarmcore_worker_tool import ToolActivities
from temporalio.worker import Worker

SECRET = "integration-capability-secret-at-least-32-bytes"


@pytest.mark.asyncio
async def test_parallel_agents_publish_through_approved_gateway_and_reduce(
    temporal_environment: TemporalTestEnvironment,
) -> None:
    database_url = os.getenv("SWARMCORE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("SWARMCORE_TEST_DATABASE_URL is not configured")

    tenant_id, project_id = uuid4(), uuid4()
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO tenants (id, name, status, created_at, updated_at) "
                "VALUES (:tenant, :name, 'ACTIVE', now(), now())"
            ),
            {"tenant": tenant_id, "name": f"m3-tenant-{tenant_id}"},
        )
        await connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"),
            {"tenant": str(tenant_id)},
        )
        await connection.execute(
            text(
                "INSERT INTO projects "
                "(id, tenant_id, name, settings, created_at, updated_at) "
                "VALUES (:project, :tenant, 'm3-project', '{}', now(), now())"
            ),
            {"project": project_id, "tenant": tenant_id},
        )
    await engine.dispose()

    database = Database(database_url)
    tokens = CapabilityTokenIssuer(SECRET)
    control = ControlActivities(
        PostgresPlanStore(database.sessions),
        PostgresTransitionProjector(database.sessions),
        GatewayCapabilityIssuer(tokens),
    )
    agents = AgentActivities(DeterministicFakeAgentAdapter())
    tools = ToolActivities(
        ToolGateway(
            builtin_registry(),
            tokens,
            PostgresEffectJournal(database.sessions),
            builtin_executors(),
        )
    )
    temporal = temporal_environment.client
    control_worker = Worker(
        temporal,
        task_queue="swarm-control",
        workflows=[SwarmRunWorkflow],
        activities=[
            control.load_execution_plan,
            control.project_transition,
            control.issue_tool_capability,
            control.execute_control_node,
        ],
    )
    agent_worker = Worker(
        temporal,
        task_queue="agent-general",
        activities=[agents.execute_agent, agents.execute_team],
    )
    tool_worker = Worker(
        temporal, task_queue="tool-trusted", activities=[tools.execute_tool]
    )
    dispatcher = CommandDispatcher(
        database.sessions, temporal, worker_id=f"m3-integration-{uuid4()}"
    )
    headers = {"X-Tenant-ID": str(tenant_id)}
    strategies_url = f"/v1/projects/{project_id}/strategies"
    runs_url = f"/v1/projects/{project_id}/runs"

    try:
        with TestClient(
            create_app(Settings(database_url=database_url, telemetry_enabled=False))
        ) as api:
            created = api.post(
                strategies_url,
                headers=headers,
                json={"name": "m3-business", "spec": acceptance_spec()},
            )
            assert created.status_code == 201
            strategy = created.json()
            published = api.post(
                f"{strategies_url}/{strategy['strategyId']}/publish",
                headers=headers,
                json={"draftId": strategy["draftId"]},
            )
            assert published.status_code == 200
            accepted = api.post(
                runs_url,
                headers={**headers, "Idempotency-Key": str(uuid4())},
                json={
                    "strategyVersionId": published.json()["strategyVersionId"],
                    "input": {"topic": "M3 controlled publication"},
                },
            )
            assert accepted.status_code == 202
            run_id = accepted.json()["runId"]

            async with control_worker, agent_worker, tool_worker:
                assert await dispatcher.run_once() >= 1
                approval: dict[str, Any] | None = None
                for _ in range(200):
                    response = api.get(
                        f"/v1/projects/{project_id}/approvals?runId={run_id}",
                        headers=headers,
                    )
                    if response.json()["items"]:
                        approval = response.json()["items"][0]
                        break
                    await asyncio.sleep(0.05)
                assert approval is not None
                decision = api.post(
                    f"/v1/projects/{project_id}/approvals/{approval['approvalId']}:approve",
                    headers={**headers, "Idempotency-Key": str(uuid4())},
                    json={"value": {}},
                )
                assert decision.status_code == 202
                assert await dispatcher.run_once() == 1
                handle = temporal.get_workflow_handle(f"swarm:{tenant_id}:{run_id}")
                workflow_result = await asyncio.wait_for(handle.result(), timeout=30)

            assert workflow_result["status"] == "SUCCEEDED"
            result = api.get(f"{runs_url}/{run_id}/result", headers=headers)
            assert result.status_code == 200
            output = result.json()["output"]
            assert output["publicationId"]
            assert output["reports"].keys() == {"one", "two"}

        engine = create_async_engine(database_url)
        async with engine.connect() as connection:
            transaction = await connection.begin()
            await connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": str(tenant_id)},
            )
            effects = await connection.scalar(
                text("SELECT count(*) FROM tool_effects WHERE run_id = :run"),
                {"run": run_id},
            )
            completed_events = await connection.scalar(
                text(
                    "SELECT count(*) FROM run_events "
                    "WHERE run_id = :run AND type = 'tool.completed'"
                ),
                {"run": run_id},
            )
            await transaction.rollback()
        await engine.dispose()
        assert effects == 1
        assert completed_events == 1
    finally:
        await database.dispose()


def acceptance_spec() -> dict[str, Any]:
    agent = {"role": "Analyst", "instructions": "Return a structured analysis."}
    return {
        "apiVersion": "swarmcore.io/v1",
        "kind": "SwarmStrategy",
        "metadata": {"name": "m3-business"},
        "spec": {
            "inputSchema": {"type": "object"},
            "outputSchema": {"type": "object"},
            "defaults": {"model": "model://fake-deterministic"},
            "agents": {"one-agent": agent, "two-agent": agent},
            "graph": {
                "entrypoint": "fan",
                "nodes": {
                    "fan": {"type": "parallel", "branches": ["one", "two"]},
                    "one": {
                        "type": "agent",
                        "agent": "one-agent",
                        "dependsOn": ["fan"],
                    },
                    "two": {
                        "type": "agent",
                        "agent": "two-agent",
                        "dependsOn": ["fan"],
                    },
                    "publish": {
                        "type": "tool",
                        "tool": "tool://publish-report",
                        "dependsOn": ["one", "two"],
                        "input": {
                            "reports": {
                                "one": "{{ tasks.one.output.content }}",
                                "two": "{{ tasks.two.output.content }}",
                            }
                        },
                    },
                    "final": {
                        "type": "reducer",
                        "reducer": "merge_object",
                        "dependsOn": ["publish"],
                    },
                },
                "output": {"result": "{{ tasks.final.output }}"},
            },
        },
    }
