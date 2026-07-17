from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest
from deeptalk_harness import DeepTalkContractHarness
from runtime_harness import RuntimeHarness, workflow_id
from swarmcore_compiler import parallel, sequential


@pytest.mark.asyncio
async def test_run_closes_api_postgres_temporal_worker_loop(
    runtime_harness: RuntimeHarness,
) -> None:
    tenant_id = runtime_harness.tenant_id
    project_id = runtime_harness.project_id
    temporal = runtime_harness.temporal

    agent = {"role": "worker", "instructions": "Return a deterministic result."}
    spec = sequential("run-loop", {"one": agent}).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    deeptalk_spec = parallel(
        "deeptalk-contract",
        {"analysis_a": agent, "analysis_b": agent},
    ).model_dump(mode="json", by_alias=True, exclude_none=True)
    headers = runtime_harness.headers
    strategies_url = runtime_harness.project_url("strategies")
    runs_url = runtime_harness.project_url("runs")

    api = runtime_harness.api
    contract = DeepTalkContractHarness(
        api,
        tenant_id=str(tenant_id),
        project_id=str(project_id),
    )
    rest_catalog = contract.rest_capabilities()
    mcp_catalog = contract.mcp("swarm.capabilities.get", {"projectId": str(project_id)})
    assert mcp_catalog == rest_catalog
    rest_compiled = contract.rest_compile(deeptalk_spec)
    mcp_compiled = contract.mcp(
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

    mcp_handle = contract.mcp(
        "swarm.run.create",
        {
            "projectId": str(project_id),
            "spec": deeptalk_spec,
            "input": {"question": "mcp-inline", "_delaySeconds": 2},
            "idempotencyKey": str(uuid4()),
        },
    )
    assert mcp_handle["planHash"] == inline_handle["planHash"]

    async with runtime_harness.control_worker():
        async with runtime_harness.agent_worker():
            assert await runtime_harness.dispatcher.run_once() == 3
            mcp_workflow = temporal.get_workflow_handle(workflow_id(tenant_id, mcp_handle["runId"]))
            for _ in range(100):
                state = await mcp_workflow.query("engine_state", result_type=dict[str, Any])
                if state["inFlightCount"]:
                    break
                await asyncio.sleep(0.05)
            else:
                raise AssertionError("MCP Run did not start before Worker restart")

        async with runtime_harness.agent_worker():
            handle = temporal.get_workflow_handle(workflow_id(tenant_id, run_id))
            inline_workflow = temporal.get_workflow_handle(
                workflow_id(tenant_id, inline_handle["runId"])
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

    inline_snapshot = api.get(f"{runs_url}/{inline_handle['runId']}", headers=headers).json()
    assert inline_snapshot["status"] == "SUCCEEDED"
    assert inline_snapshot["output"] == inline_result["result"]

    mcp_status = contract.mcp(
        "swarm.run.status",
        {"projectId": str(project_id), "runId": mcp_handle["runId"]},
    )
    rest_status = api.get(f"{runs_url}/{mcp_handle['runId']}", headers=headers).json()
    assert mcp_status == rest_status
    mcp_result = contract.mcp(
        "swarm.run.result",
        {"projectId": str(project_id), "runId": mcp_handle["runId"]},
    )
    rest_result = api.get(f"{runs_url}/{mcp_handle['runId']}/result", headers=headers).json()
    assert mcp_result == rest_result

    history = api.get(f"{runs_url}/{run_id}/event-history", headers=headers)
    assert history.status_code == 200
    event_types = [item["type"] for item in history.json()["items"]]
    assert event_types[0] == "run.accepted"
    assert event_types[-1] == "run.completed"
