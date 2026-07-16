from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

import pytest
from conftest import TemporalTestEnvironment
from swarmcore_compiler import Compiler
from swarmcore_registry import RegistrySnapshot, ToolRegistration, ToolRisk, builtin_registry
from swarmcore_runtime_temporal import SwarmRunWorkflow
from swarmcore_spec import SwarmStrategy
from swarmcore_tool_gateway import (
    CapabilityTokenIssuer,
    InMemoryEffectJournal,
    ToolGateway,
    builtin_executors,
)
from swarmcore_worker_tool import ToolActivities
from temporalio import activity
from temporalio.worker import Worker

SECRET = "integration-capability-secret-at-least-32-bytes"
ISSUER = CapabilityTokenIssuer(SECRET)
BASE_REGISTRY = builtin_registry()
REGISTRY = RegistrySnapshot.create(
    agents=BASE_REGISTRY.agents,
    models=BASE_REGISTRY.models,
    tools=(
        *BASE_REGISTRY.tools,
        ToolRegistration(
            ref="tool://counter@1",
            version="1",
            operation="test.counter",
            description="Return whether the bounded loop has converged.",
            risk=ToolRisk.LOW,
            inputSchema={
                "type": "object",
                "required": ["iteration"],
                "properties": {"iteration": {"type": "integer"}},
            },
            outputSchema={
                "type": "object",
                "required": ["done", "iteration"],
                "properties": {
                    "done": {"type": "boolean"},
                    "iteration": {"type": "integer"},
                },
            },
            idempotent=True,
            sideEffecting=False,
        ),
    ),
)


def compile_plan(nodes: dict[str, Any], *, input_schema: dict[str, Any]) -> dict[str, Any]:
    raw = {
        "apiVersion": "swarmcore.io/v1",
        "kind": "SwarmStrategy",
        "metadata": {"name": "m3-acceptance"},
        "spec": {
            "inputSchema": input_schema,
            "outputSchema": {"type": "object"},
            "defaults": {"model": "model://fake-deterministic"},
            "agents": {
                "worker": {"role": "worker", "instructions": "Produce one report."}
            },
            "graph": {
                "entrypoint": next(iter(nodes)),
                "nodes": nodes,
                "output": {},
            },
        },
    }
    return (
        Compiler(REGISTRY)
        .compile(
            SwarmStrategy.model_validate(raw),
            registry_snapshot=REGISTRY.snapshot_id,
            policy_revision="m3",
        )
        .model_dump(mode="json")
    )


PLANS = {
    "business": compile_plan(
        {
            "fan": {"type": "parallel", "branches": ["one", "two"]},
            "one": {"type": "agent", "agent": "worker", "dependsOn": ["fan"]},
            "two": {"type": "agent", "agent": "worker", "dependsOn": ["fan"]},
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
        input_schema={"type": "object"},
    ),
    "router": compile_plan(
        {
            "route": {
                "type": "router",
                "routes": [{"when": 'input.route == "left"', "target": "left"}],
                "default": "right",
            },
            "left": {
                "type": "tool",
                "tool": "tool://search",
                "dependsOn": ["route"],
                "input": {"query": "left"},
            },
            "right": {
                "type": "tool",
                "tool": "tool://search",
                "dependsOn": ["route"],
                "input": {"query": "right"},
            },
            "final": {
                "type": "reducer",
                "reducer": "merge_object",
                "dependsOn": ["left", "right"],
            },
        },
        input_schema={"type": "object"},
    ),
    "loop": compile_plan(
        {
            "count": {
                "type": "tool",
                "tool": "tool://counter@1",
                "input": {"iteration": "{{ iteration }}"},
            },
            "loop": {
                "type": "loop",
                "body": ["count"],
                "until": "output.content.done == true",
                "maxIterations": 3,
            },
            "final": {
                "type": "reducer",
                "reducer": "merge_object",
                "dependsOn": ["loop"],
            },
        },
        input_schema={"type": "object"},
    ),
}


@activity.defn(name="load_execution_plan")
async def load_execution_plan(request: dict[str, Any]) -> dict[str, Any]:
    return PLANS[str(request["fixture"])]


@activity.defn(name="project_transition")
async def project_transition(_: dict[str, Any]) -> None:
    return None


@activity.defn(name="issue_tool_capability")
async def issue_tool_capability(request: dict[str, Any]) -> str:
    run = request["run"]
    return ISSUER.issue(
        tenant_id=str(run["tenantId"]),
        project_id=str(run["projectId"]),
        run_id=str(run["runId"]),
        node_key=str(request["nodeKey"]),
        tool_ref=str(request["toolRef"]),
        execution_id=str(request["executionId"]),
        effect_id=str(request["effectId"]) if request.get("effectId") else None,
        approved=bool(request["approved"]),
    )


@activity.defn(name="execute_control_node")
async def execute_control_node(request: dict[str, Any]) -> dict[str, Any]:
    node_type = request["node"]["type"]
    dependencies = request["dependencyOutputs"]
    if node_type in {"parallel", "join"}:
        return {"outputs": dependencies}
    if node_type == "reducer":
        merged: dict[str, Any] = {}
        for key in sorted(dependencies):
            value = dependencies[key]
            content = value.get("content", value)
            if isinstance(content, dict):
                merged.update(content)
        return merged
    raise ValueError(node_type)


@activity.defn(name="execute_agent")
async def execute_agent(request: dict[str, Any]) -> dict[str, Any]:
    return {"content": {"node": request["node"]["key"], "approved": True}}


async def counter(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    iteration = int(input_value["iteration"])
    return {"iteration": iteration, "done": iteration >= 2}


@pytest.mark.asyncio
async def test_m3_tool_router_loop_acceptance(
    temporal_environment: TemporalTestEnvironment,
) -> None:
    client = temporal_environment.client
    gateway = ToolGateway(
        REGISTRY,
        ISSUER,
        InMemoryEffectJournal(),
        {**builtin_executors(), "test.counter": counter},
    )
    tool_activities = ToolActivities(gateway)
    control_worker = Worker(
        client,
        task_queue="swarm-control",
        workflows=[SwarmRunWorkflow],
        activities=[
            load_execution_plan,
            project_transition,
            issue_tool_capability,
            execute_control_node,
        ],
    )
    async with control_worker:
        agent_worker = Worker(
            client, task_queue="agent-general", activities=[execute_agent]
        )
        tool_worker = Worker(
            client, task_queue="tool-trusted", activities=[tool_activities.execute_tool]
        )
        async with agent_worker, tool_worker:
            handle = await client.start_workflow(
                SwarmRunWorkflow.run,
                run_input("business"),
                id=f"swarm:m3-business:{uuid4()}",
                task_queue="swarm-control",
            )
            request_id = ""
            for _ in range(100):
                state = await handle.query("engine_state", result_type=dict[str, Any])
                pending = [
                    key
                    for key, value in state["humanRequests"].items()
                    if value["status"] == "PENDING"
                ]
                if pending:
                    request_id = pending[0]
                    break
                await asyncio.sleep(0.01)
            assert request_id
            decision = await handle.execute_update(
                "apply_command",
                {
                    "commandSeq": 2,
                    "type": "approve",
                    "data": {"requestId": request_id, "value": {}},
                },
                id=str(uuid4()),
                result_type=dict[str, Any],
            )
            business = await handle.result()
            router = await client.execute_workflow(
                SwarmRunWorkflow.run,
                run_input("router", {"route": "left"}),
                id=f"swarm:m3-router:{uuid4()}",
                task_queue="swarm-control",
            )
            loop = await client.execute_workflow(
                SwarmRunWorkflow.run,
                run_input("loop"),
                id=f"swarm:m3-loop:{uuid4()}",
                task_queue="swarm-control",
            )

    assert decision == {"status": "APPLIED", "requestId": request_id}
    assert business["result"]["publicationId"]
    assert business["result"]["reports"].keys() == {"one", "two"}
    assert router["result"]["items"][0]["title"] == "left"
    assert len(loop["result"]["iterations"]) == 2
    assert loop["result"]["last"]["content"]["done"] is True


def run_input(fixture: str, input_value: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "tenantId": str(uuid4()),
        "projectId": str(uuid4()),
        "runId": str(uuid4()),
        "planHash": "d" * 64,
        "input": input_value or {},
        "fixture": fixture,
        "startCommand": {"commandSeq": 1},
    }
