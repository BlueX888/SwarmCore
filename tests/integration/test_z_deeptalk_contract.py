from __future__ import annotations

import asyncio
import os
from typing import Any
from uuid import uuid4

import pytest
from conftest import TemporalTestEnvironment
from deeptalk_harness import DeepTalkContractHarness
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_api import create_app
from swarmcore_api.settings import Settings
from swarmcore_command_dispatcher import CommandDispatcher
from swarmcore_compiler import parallel, sequential
from swarmcore_persistence import Database
from swarmcore_runtime_temporal import ControlActivities, SwarmRunWorkflow
from swarmcore_worker_agent import AgentActivities
from swarmcore_worker_agent.fake import DeterministicFakeAgentAdapter
from swarmcore_worker_control import PostgresPlanStore, PostgresTransitionProjector
from temporalio.worker import Worker


@pytest.mark.asyncio
async def test_run_closes_api_postgres_temporal_worker_loop(
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
            {"tenant": tenant_id, "name": f"run-tenant-{tenant_id}"},
        )
        await connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"),
            {"tenant": str(tenant_id)},
        )
        await connection.execute(
            text(
                "INSERT INTO projects "
                "(id, tenant_id, name, settings, created_at, updated_at) "
                "VALUES (:project, :tenant, 'run-project', '{}', now(), now())"
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
        worker_id=f"integration-{uuid4()}",
    )

    agent = {"role": "worker", "instructions": "Return a deterministic result."}
    spec = sequential("run-loop", {"one": agent}).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    deeptalk_spec = parallel(
        "deeptalk-contract",
        {"analysis_a": agent, "analysis_b": agent},
    ).model_dump(mode="json", by_alias=True, exclude_none=True)
    headers = {"X-Tenant-ID": str(tenant_id)}
    strategies_url = f"/v1/projects/{project_id}/strategies"
    runs_url = f"/v1/projects/{project_id}/runs"

    try:
        with TestClient(
            create_app(Settings(database_url=database_url, telemetry_enabled=False))
        ) as api:
            harness = DeepTalkContractHarness(
                api,
                tenant_id=str(tenant_id),
                project_id=str(project_id),
            )
            rest_catalog = harness.rest_capabilities()
            mcp_catalog = harness.mcp(
                "swarm.capabilities.get", {"projectId": str(project_id)}
            )
            assert mcp_catalog == rest_catalog
            rest_compiled = harness.rest_compile(deeptalk_spec)
            mcp_compiled = harness.mcp(
                "swarm.strategy.compile",
                {"projectId": str(project_id), "spec": deeptalk_spec},
            )
            assert mcp_compiled["plan"] == rest_compiled["plan"]

            created = api.post(
                strategies_url,
                headers=headers,
                json={"name": "run-loop", "spec": spec},
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
                    "input": {"question": "integration"},
                },
            )
            assert accepted.status_code == 202
            run_id = accepted.json()["runId"]
            not_terminal = api.get(f"{runs_url}/{run_id}/result", headers=headers)
            assert not_terminal.status_code == 409
            assert not_terminal.json()["code"] == "RUN_NOT_TERMINAL"

            inline_key = str(uuid4())
            inline_accepted = api.post(
                runs_url,
                headers={**headers, "Idempotency-Key": inline_key},
                json={"spec": deeptalk_spec, "input": {"question": "inline"}},
            )
            assert inline_accepted.status_code == 202
            inline_handle = inline_accepted.json()
            assert len(inline_handle["planHash"]) == 64
            replayed = api.post(
                runs_url,
                headers={**headers, "Idempotency-Key": inline_key},
                json={"spec": deeptalk_spec, "input": {"question": "inline"}},
            )
            assert replayed.json()["runId"] == inline_handle["runId"]

            mcp_handle = harness.mcp(
                "swarm.run.create",
                {
                    "projectId": str(project_id),
                    "spec": deeptalk_spec,
                    "input": {"question": "mcp-inline", "_delaySeconds": 2},
                    "idempotencyKey": str(uuid4()),
                },
            )
            assert mcp_handle["planHash"] == inline_handle["planHash"]

            async with control_worker:
                async with agent_worker:
                    assert await dispatcher.run_once() == 3
                    mcp_workflow = temporal.get_workflow_handle(
                        f"swarm:{tenant_id}:{mcp_handle['runId']}"
                    )
                    for _ in range(100):
                        state = await mcp_workflow.query(
                            "engine_state", result_type=dict[str, Any]
                        )
                        if state["inFlightCount"]:
                            break
                        await asyncio.sleep(0.05)
                    else:
                        raise AssertionError("MCP Run did not start before Worker restart")

                restarted_agent = Worker(
                    temporal,
                    task_queue="agent-general",
                    activities=[
                        agent_activities.execute_agent,
                        agent_activities.execute_team,
                    ],
                )
                async with restarted_agent:
                    handle = temporal.get_workflow_handle(f"swarm:{tenant_id}:{run_id}")
                    inline_workflow = temporal.get_workflow_handle(
                        f"swarm:{tenant_id}:{inline_handle['runId']}"
                    )
                    workflow_result, inline_result, _ = await asyncio.gather(
                        asyncio.wait_for(handle.result(), timeout=30),
                        asyncio.wait_for(inline_workflow.result(), timeout=30),
                        asyncio.wait_for(mcp_workflow.result(), timeout=30),
                    )

            snapshot = api.get(f"{runs_url}/{run_id}", headers=headers)
            assert snapshot.status_code == 200
            body = snapshot.json()
            assert body["status"] == "SUCCEEDED"
            assert body["planHash"] == published.json()["planHash"]
            assert body["output"] == workflow_result["result"]
            assert body["tasks"][0]["status"] == "SUCCEEDED"

            result_response = api.get(f"{runs_url}/{run_id}/result", headers=headers)
            assert result_response.status_code == 200
            run_result = result_response.json()
            assert run_result["completionQuality"] == "COMPLETE"
            assert run_result["output"] == workflow_result["result"]
            assert run_result["tasksSummary"] == {
                "total": 1,
                "succeeded": 1,
                "failed": 0,
                "skipped": 0,
                "cancelled": 0,
            }
            assert run_result["error"] is None
            assert run_result["provenance"]["planHash"] == published.json()["planHash"]

            inline_snapshot = api.get(
                f"{runs_url}/{inline_handle['runId']}", headers=headers
            ).json()
            assert inline_snapshot["status"] == "SUCCEEDED"
            assert inline_snapshot["output"] == inline_result["result"]

            mcp_status = harness.mcp(
                "swarm.run.status",
                {"projectId": str(project_id), "runId": mcp_handle["runId"]},
            )
            rest_status = api.get(f"{runs_url}/{mcp_handle['runId']}", headers=headers).json()
            assert mcp_status == rest_status
            mcp_result = harness.mcp(
                "swarm.run.result",
                {"projectId": str(project_id), "runId": mcp_handle["runId"]},
            )
            rest_result = api.get(
                f"{runs_url}/{mcp_handle['runId']}/result", headers=headers
            ).json()
            assert mcp_result == rest_result

            history = api.get(f"{runs_url}/{run_id}/event-history", headers=headers)
            assert history.status_code == 200
            event_types = [item["type"] for item in history.json()["items"]]
            assert event_types[0] == "run.accepted"
            assert event_types[-1] == "run.completed"
    finally:
        await database.dispose()
