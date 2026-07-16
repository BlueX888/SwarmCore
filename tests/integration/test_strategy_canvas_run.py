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
from swarmcore_persistence import Database
from swarmcore_runtime_temporal import ControlActivities, SwarmRunWorkflow
from swarmcore_worker_agent import AgentActivities
from swarmcore_worker_agent.fake import DeterministicFakeAgentAdapter
from swarmcore_worker_control import PostgresPlanStore, PostgresTransitionProjector
from temporalio.worker import Worker


@pytest.mark.asyncio
async def test_canvas_strategy_completes_real_api_run_with_approval_and_parallelism(
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
            {"tenant": tenant_id, "name": f"canvas-tenant-{tenant_id}"},
        )
        await connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"),
            {"tenant": str(tenant_id)},
        )
        await connection.execute(
            text(
                "INSERT INTO projects "
                "(id, tenant_id, name, settings, created_at, updated_at) "
                "VALUES (:project, :tenant, 'canvas-project', '{}', now(), now())"
            ),
            {"project": project_id, "tenant": tenant_id},
        )
    await engine.dispose()

    database = Database(database_url)
    control_activities = ControlActivities(
        PostgresPlanStore(database.sessions),
        PostgresTransitionProjector(database.sessions),
    )
    agent_activities = AgentActivities(DeterministicFakeAgentAdapter())
    temporal = temporal_environment.client
    control_worker = Worker(
        temporal,
        task_queue="swarm-control",
        workflows=[SwarmRunWorkflow],
        activities=[
            control_activities.load_execution_plan,
            control_activities.project_transition,
            control_activities.execute_control_node,
        ],
    )
    agent_worker = Worker(
        temporal,
        task_queue="agent-general",
        activities=[agent_activities.execute_agent, agent_activities.execute_team],
    )
    dispatcher = CommandDispatcher(
        database.sessions,
        temporal,
        worker_id=f"canvas-integration-{uuid4()}",
    )
    headers = {"X-Tenant-ID": str(tenant_id)}
    strategies_url = f"/v1/projects/{project_id}/strategies"
    runs_url = f"/v1/projects/{project_id}/runs"
    editor_state = {
        "positions": {
            "planner": {"x": 0, "y": 0},
            "approval": {"x": 220, "y": 0},
            "fanout": {"x": 440, "y": 0},
            "research-a": {"x": 660, "y": -100},
            "research-b": {"x": 660, "y": 100},
            "result": {"x": 880, "y": 0},
        },
        "viewport": {"x": 20, "y": 30, "zoom": 0.9},
    }

    try:
        with TestClient(
            create_app(Settings(database_url=database_url, telemetry_enabled=False))
        ) as api:
            created = api.post(
                strategies_url,
                headers=headers,
                json={
                    "name": "canvas-approval-parallel",
                    "spec": _canvas_acceptance_spec(),
                    "editorState": editor_state,
                },
            )
            assert created.status_code == 201
            strategy = created.json()
            saved_draft = api.get(
                f"{strategies_url}/{strategy['strategyId']}/drafts/{strategy['draftId']}",
                headers=headers,
            )
            assert saved_draft.json()["editorState"] == editor_state
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
                    "input": {"topic": "M2C acceptance"},
                },
            )
            assert accepted.status_code == 202
            run_id = accepted.json()["runId"]

            async with control_worker, agent_worker:
                assert await dispatcher.run_once() == 1
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
                    json={"value": {"approved": True}},
                )
                assert decision.status_code == 202
                assert await dispatcher.run_once() == 1
                handle = temporal.get_workflow_handle(f"swarm:{tenant_id}:{run_id}")
                workflow_result = await asyncio.wait_for(handle.result(), timeout=30)

            assert workflow_result["status"] == "SUCCEEDED"
            snapshot = api.get(f"{runs_url}/{run_id}", headers=headers).json()
            assert snapshot["status"] == "SUCCEEDED"
            assert snapshot["planHash"] == published.json()["planHash"]
            assert {task["nodeKey"] for task in snapshot["tasks"]} == {
                "planner",
                "approval",
                "fanout",
                "research-a",
                "research-b",
                "result",
            }
            assert all(task["status"] == "SUCCEEDED" for task in snapshot["tasks"])
            run_result = api.get(f"{runs_url}/{run_id}/result", headers=headers)
            assert run_result.status_code == 200
            assert run_result.json()["completionQuality"] == "COMPLETE"
            assert run_result.json()["output"] == workflow_result["result"]
    finally:
        await database.dispose()


def _canvas_acceptance_spec() -> dict[str, Any]:
    agent = {"role": "Researcher", "instructions": "Return a concise result."}
    return {
        "apiVersion": "swarmcore.io/v1",
        "kind": "SwarmStrategy",
        "metadata": {"name": "canvas-approval-parallel"},
        "spec": {
            "inputSchema": {"type": "object"},
            "outputSchema": {"type": "object"},
            "defaults": {"model": "model://fake-deterministic"},
            "budget": {"maxAgents": 8, "maxParallelism": 4},
            "agents": {
                "planner-agent": {"role": "Planner", "instructions": "Plan the work."},
                "research-a-agent": agent,
                "research-b-agent": agent,
            },
            "graph": {
                "entrypoint": "planner",
                "nodes": {
                    "planner": {"type": "agent", "agent": "planner-agent"},
                    "approval": {
                        "type": "approval",
                        "prompt": "Approve the research plan?",
                        "inputSchema": {"type": "object"},
                        "dependsOn": ["planner"],
                    },
                    "fanout": {
                        "type": "parallel",
                        "branches": ["research-a", "research-b"],
                        "dependsOn": ["approval"],
                    },
                    "research-a": {
                        "type": "agent",
                        "agent": "research-a-agent",
                        "dependsOn": ["fanout"],
                    },
                    "research-b": {
                        "type": "agent",
                        "agent": "research-b-agent",
                        "dependsOn": ["fanout"],
                    },
                    "result": {
                        "type": "reducer",
                        "reducer": "merge_object",
                        "dependsOn": ["research-a", "research-b"],
                    },
                },
                "output": {"result": "{{ tasks.result.output }}"},
            },
        },
    }
