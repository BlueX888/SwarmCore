from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest
from runtime_harness import RuntimeHarness, workflow_id


@pytest.mark.asyncio
async def test_canvas_strategy_completes_real_api_run_with_approval_and_parallelism(
    runtime_harness: RuntimeHarness,
) -> None:
    tenant_id = runtime_harness.tenant_id
    project_id = runtime_harness.project_id
    api = runtime_harness.api
    headers = runtime_harness.headers
    strategies_url = runtime_harness.project_url("strategies")
    runs_url = runtime_harness.project_url("runs")
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
        "agentBindings": {},
    }

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

    async with runtime_harness.workers():
        assert await runtime_harness.dispatcher.run_once() == 1
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
        assert await runtime_harness.dispatcher.run_once() == 1
        handle = runtime_harness.temporal.get_workflow_handle(workflow_id(tenant_id, run_id))
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
