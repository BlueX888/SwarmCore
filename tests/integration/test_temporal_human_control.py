from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest
from swarmcore_runtime_temporal import SwarmRunWorkflow
from temporalio import activity
from temporalio.exceptions import ApplicationError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

PROJECTED: list[str] = []
FAILURES = 0


def _plan(node_type: str) -> dict[str, Any]:
    config: dict[str, Any] = {"agent": "worker"} if node_type == "agent" else {}
    if node_type in {"approval", "input"}:
        config = {
            "prompt": "Human response required",
            "inputSchema": {
                "type": "object",
                "required": ["reason"],
                "properties": {"reason": {"type": "string"}},
            },
        }
    return {
        "nodes": [{"key": "one", "type": node_type, "dependencies": [], "config": config}],
        "budget": {"maxParallelism": 1},
        "resolved_agents": {"worker": {"role": "worker", "instructions": "work"}},
        "defaults": {},
        "result_reducer": {},
    }


@activity.defn(name="load_execution_plan")
async def load_human_plan(request: dict[str, Any]) -> dict[str, Any]:
    return _plan(str(request["fixture"]))


@activity.defn(name="project_transition")
async def project_human_transition(value: dict[str, Any]) -> None:
    PROJECTED.append(str(value["type"]))


@activity.defn(name="execute_agent")
async def controlled_agent(value: dict[str, Any]) -> dict[str, Any]:
    global FAILURES
    if value["run"].get("slow"):
        await asyncio.sleep(0.15)
    if value["run"].get("failUntilManualRetry") and FAILURES < 3:
        FAILURES += 1
        raise ApplicationError("temporary", type="TEMPORARY")
    return {"ok": True}


async def _wait_for(
    handle: Any, predicate: Any, *, attempts: int = 100
) -> dict[str, Any]:
    for _ in range(attempts):
        state = await handle.query("engine_state", result_type=dict[str, Any])
        if predicate(state):
            return state
        await asyncio.sleep(0.01)
    raise AssertionError("workflow state was not reached")


@pytest.mark.asyncio
async def test_pause_resume_approval_input_retry_and_recovery() -> None:
    global FAILURES
    FAILURES = 0
    PROJECTED.clear()
    environment = await WorkflowEnvironment.start_time_skipping()
    control = Worker(
        environment.client,
        task_queue="swarm-control",
        workflows=[SwarmRunWorkflow],
        activities=[load_human_plan, project_human_transition],
    )
    agent = Worker(
        environment.client,
        task_queue="agent-general",
        activities=[controlled_agent],
    )
    async with control, agent:
        pause_handle = await environment.client.start_workflow(
            SwarmRunWorkflow.run,
            _input("agent", slow=True),
            id=f"phase2a:pause:{uuid4()}",
            task_queue="swarm-control",
        )
        await _wait_for(pause_handle, lambda state: state["inFlightCount"] == 1)
        assert await pause_handle.execute_update(
            "apply_command", _command(2, "pause"), id=str(uuid4()), result_type=dict[str, Any]
        ) == {"status": "APPLIED"}
        await _wait_for(pause_handle, lambda state: state["paused"] is True)
        assert await pause_handle.execute_update(
            "apply_command", _command(3, "resume"), id=str(uuid4()), result_type=dict[str, Any]
        ) == {"status": "APPLIED"}
        assert (await pause_handle.result())["status"] == "SUCCEEDED"

        for fixture, command_type in (("approval", "approve"), ("input", "provide_input")):
            handle = await environment.client.start_workflow(
                SwarmRunWorkflow.run,
                _input(fixture),
                id=f"phase2a:{fixture}:{uuid4()}",
                task_queue="swarm-control",
            )
            state = await _wait_for(handle, lambda value: value["pendingHumanRequests"] == 1)
            request_id = next(iter(state["humanRequests"]))
            applied = await handle.execute_update(
                "apply_command",
                _command(2, command_type, {"requestId": request_id, "value": {"reason": "ok"}}),
                id=str(uuid4()),
                result_type=dict[str, Any],
            )
            assert applied["status"] == "APPLIED"
            assert (await handle.result())["status"] == "SUCCEEDED"

        retry_handle = await environment.client.start_workflow(
            SwarmRunWorkflow.run,
            _input("agent", failUntilManualRetry=True),
            id=f"phase2a:retry:{uuid4()}",
            task_queue="swarm-control",
        )
        await _wait_for(
            retry_handle,
            lambda state: state["states"].get("one") == "FAILED",
        )
        retried = await retry_handle.execute_update(
            "apply_command",
            _command(2, "retry_task", {"nodeKey": "one"}),
            id=str(uuid4()),
            result_type=dict[str, Any],
        )
        assert retried["status"] == "APPLIED"
        assert (await retry_handle.result())["status"] == "SUCCEEDED"
    await environment.shutdown()

    assert "run.paused" in PROJECTED
    assert "approval.approved" in PROJECTED
    assert "input.received" in PROJECTED
    assert "task.retry_started" in PROJECTED


def _input(fixture: str, **extra: Any) -> dict[str, Any]:
    return {
        "tenantId": str(uuid4()),
        "projectId": str(uuid4()),
        "runId": str(uuid4()),
        "planHash": "a" * 64,
        "fixture": fixture,
        "input": {},
        "startCommand": {"commandSeq": 1, "requestId": str(uuid4())},
        **extra,
    }


def _command(
    sequence: int, command_type: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "commandSeq": sequence,
        "requestId": str(uuid4()),
        "type": command_type,
        "data": data or {},
    }
