from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest
from conftest import TemporalTestEnvironment
from swarmcore_compiler import Compiler, dag, parallel, sequential, supervisor
from swarmcore_registry import builtin_registry
from swarmcore_runtime_temporal import SwarmRunWorkflow
from temporalio import activity
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker

PROJECTED: list[dict[str, Any]] = []
REGISTRY = builtin_registry().snapshot_id
AGENT = {"role": "worker", "instructions": "Do the assigned work."}
PLANS = {
    "sequential": Compiler()
    .compile(
        sequential("sequential", {"one": AGENT, "two": AGENT}),
        registry_snapshot=REGISTRY,
        policy_revision="p1",
    )
    .model_dump(mode="json"),
    "parallel": Compiler()
    .compile(
        parallel("parallel", {"one": AGENT, "two": AGENT}),
        registry_snapshot=REGISTRY,
        policy_revision="p1",
    )
    .model_dump(mode="json"),
    "dag": Compiler()
    .compile(
        dag("dag", {"one": AGENT, "two": AGENT}, {"two": ["one"]}),
        registry_snapshot=REGISTRY,
        policy_revision="p1",
    )
    .model_dump(mode="json"),
    "supervisor": Compiler()
    .compile(
        supervisor("supervisor", AGENT, {"one": AGENT, "two": AGENT}),
        registry_snapshot=REGISTRY,
        policy_revision="p1",
    )
    .model_dump(mode="json"),
}


@activity.defn(name="load_execution_plan")
async def load_execution_plan(request: dict[str, Any]) -> dict[str, Any]:
    return PLANS[str(request["fixture"])]


@activity.defn(name="project_transition")
async def project_transition(value: dict[str, Any]) -> None:
    PROJECTED.append(value)


@activity.defn(name="execute_agent")
async def execute_agent(value: dict[str, Any]) -> dict[str, Any]:
    if value["run"].get("recoverOnce") and activity.info().attempt == 1:
        raise ApplicationError("simulated worker loss", type="WORKER_LOST")
    key = str(value["node"]["key"])
    return {key: True}


@activity.defn(name="execute_control_node")
async def execute_control_node(value: dict[str, Any]) -> dict[str, Any]:
    if value["node"]["type"] == "reducer":
        merged: dict[str, Any] = {}
        for output in value["dependencyOutputs"].values():
            merged.update(output)
        return merged
    return {}


@activity.defn(name="execute_agent")
async def slow_execute_agent(_: dict[str, Any]) -> dict[str, Any]:
    while True:
        activity.heartbeat("waiting")
        await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_phase_one_workflow_acceptance(
    temporal_environment: TemporalTestEnvironment,
) -> None:
    PROJECTED.clear()
    client = temporal_environment.client
    control_worker = Worker(
        client,
        task_queue="swarm-control",
        workflows=[SwarmRunWorkflow],
        activities=[load_execution_plan, project_transition, execute_control_node],
    )
    async with control_worker:
        agent_worker = Worker(
            client,
            task_queue="agent-general",
            activities=[execute_agent],
        )
        async with agent_worker:
            for fixture, expected in [
                ("sequential", {"two": True}),
                ("parallel", {"one": True, "two": True}),
                ("dag", {"two": True}),
                ("supervisor", {"synthesize": True}),
            ]:
                result = await client.execute_workflow(
                    SwarmRunWorkflow.run,
                    {
                        "tenantId": str(uuid4()),
                        "projectId": str(uuid4()),
                        "runId": str(uuid4()),
                        "planHash": "c" * 64,
                        "input": {},
                        "fixture": fixture,
                        "recoverOnce": True,
                        "startCommand": {"commandSeq": 1},
                    },
                    id=f"swarm:{fixture}:{uuid4()}",
                    task_queue="swarm-control",
                )
                assert result["status"] == "SUCCEEDED"
                assert result["result"] == expected

        slow_worker = Worker(
            client,
            task_queue="agent-general",
            activities=[slow_execute_agent],
        )
        async with slow_worker:
            handle = await client.start_workflow(
                SwarmRunWorkflow.run,
                {
                    "tenantId": str(uuid4()),
                    "projectId": str(uuid4()),
                    "runId": str(uuid4()),
                    "planHash": "b" * 64,
                    "input": {},
                    "fixture": "sequential",
                    "startCommand": {"commandSeq": 1},
                },
                id=f"swarm:cancel:{uuid4()}",
                task_queue="swarm-control",
            )
            for _ in range(50):
                state = await asyncio.wait_for(
                    handle.query("engine_state", result_type=dict[str, Any]), timeout=2
                )
                if state["inFlightCount"]:
                    break
                await asyncio.sleep(0.01)
            update = await asyncio.wait_for(
                handle.execute_update(
                    "apply_command",
                    {"commandSeq": 2, "type": "cancel"},
                    id=str(uuid4()),
                    result_type=dict[str, Any],
                ),
                timeout=5,
            )
            try:
                result = await asyncio.wait_for(handle.result(), timeout=30)
            except TimeoutError as exc:
                state = await asyncio.wait_for(
                    handle.query("engine_state", result_type=dict[str, Any]), timeout=5
                )
                raise AssertionError(f"cancelled workflow did not finish: {state}") from exc
    assert update == {"status": "APPLIED"}
    assert result["status"] == "CANCELLED"
    assert [event["type"] for event in PROJECTED[-2:]] == [
        "run.cancelling",
        "run.cancelled",
    ]
    for event_type in ("run.validating", "run.queued", "run.started"):
        payloads = [event["data"] for event in PROJECTED if event["type"] == event_type]
        assert payloads
        assert all(payload for payload in payloads)
