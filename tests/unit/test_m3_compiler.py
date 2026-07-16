from __future__ import annotations

from typing import Any

import pytest
from swarmcore_compiler import CompileError, Compiler
from swarmcore_registry import builtin_registry
from swarmcore_spec import SwarmStrategy


def strategy(nodes: dict[str, Any], *, agents: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "apiVersion": "swarmcore.io/v1",
        "kind": "SwarmStrategy",
        "metadata": {"name": "m3"},
        "spec": {
            "inputSchema": {"type": "object"},
            "outputSchema": {"type": "object"},
            "defaults": {"model": "model://fake-deterministic"},
            "agents": agents or {},
            "graph": {"entrypoint": next(iter(nodes)), "nodes": nodes, "output": {}},
        },
    }


def test_tool_router_loop_compile_to_pinned_registry_resources() -> None:
    raw = strategy(
        {
            "route": {
                "type": "router",
                "routes": [{"when": 'input.mode == "search"', "target": "search"}],
                "default": "finish",
            },
            "search": {
                "type": "tool",
                "tool": "tool://search",
                "dependsOn": ["route"],
                "input": {"query": "{{ input.query }}"},
            },
            "finish": {
                "type": "reducer",
                "reducer": "merge_object",
                "dependsOn": ["route"],
            },
        }
    )
    plan = Compiler().compile(
        SwarmStrategy.model_validate(raw),
        registry_snapshot=builtin_registry().snapshot_id,
        policy_revision="m3",
    )

    assert {node.type for node in plan.nodes} == {"router", "tool", "reducer"}
    assert plan.resolved_tools["tool://search"]["ref"] == "tool://search@1"
    assert plan.resolved_models["model://fake-deterministic"]["version"] == "1"


def test_unknown_tool_is_rejected_before_runtime() -> None:
    raw = strategy(
        {"call": {"type": "tool", "tool": "tool://missing@1", "input": {}}}
    )
    with pytest.raises(CompileError, match="UNKNOWN_TOOL"):
        Compiler().compile(
            SwarmStrategy.model_validate(raw),
            registry_snapshot=builtin_registry().snapshot_id,
            policy_revision="p",
        )


def test_router_target_must_be_dependency_gated() -> None:
    raw = strategy(
        {
            "route": {
                "type": "router",
                "routes": [{"when": "input.enabled", "target": "finish"}],
            },
            "finish": {"type": "reducer", "reducer": "merge_object"},
        }
    )
    with pytest.raises(CompileError, match="ROUTE_TARGET_NOT_GATED"):
        Compiler().compile(
            SwarmStrategy.model_validate(raw),
            registry_snapshot=builtin_registry().snapshot_id,
            policy_revision="p",
        )


def test_loop_body_is_bounded_and_not_exposed_as_a_dependency() -> None:
    raw = strategy(
        {
            "body": {"type": "tool", "tool": "tool://search", "input": {"query": "x"}},
            "loop": {
                "type": "loop",
                "body": ["body"],
                "until": "output.content.done == true",
                "maxIterations": 3,
            },
            "finish": {
                "type": "reducer",
                "reducer": "merge_object",
                "dependsOn": ["body"],
            },
        }
    )
    with pytest.raises(CompileError, match="LOOP_BODY_EXPOSED"):
        Compiler().compile(
            SwarmStrategy.model_validate(raw),
            registry_snapshot=builtin_registry().snapshot_id,
            policy_revision="p",
        )


def test_side_effecting_tool_cannot_run_inside_retryable_agent_activity() -> None:
    raw = strategy(
        {"work": {"type": "agent", "agent": "worker"}},
        agents={
            "worker": {
                "role": "worker",
                "instructions": "work",
                "tools": ["tool://publish-report"],
            }
        },
    )
    with pytest.raises(CompileError, match="AGENT_SIDE_EFFECT_TOOL_REQUIRES_NODE"):
        Compiler().compile(
            SwarmStrategy.model_validate(raw),
            registry_snapshot=builtin_registry().snapshot_id,
            policy_revision="p",
        )


def test_registered_agent_is_resolved_to_a_versioned_plan_definition() -> None:
    raw = strategy(
        {"work": {"type": "agent", "agent": "worker"}},
        agents={"worker": {"ref": "agent://builtin/researcher@1"}},
    )
    plan = Compiler().compile(
        SwarmStrategy.model_validate(raw),
        registry_snapshot=builtin_registry().snapshot_id,
        policy_revision="p",
    )

    assert plan.resolved_agents["worker"]["registryRef"] == (
        "agent://builtin/researcher@1"
    )
    assert plan.resolved_agents["worker"]["tools"] == ["tool://search@1"]
