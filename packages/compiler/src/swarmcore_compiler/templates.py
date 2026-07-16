from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from swarmcore_spec import SwarmStrategy

_OBJECT_SCHEMA = {"type": "object"}


def _base(name: str, agents: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "apiVersion": "swarmcore.io/v1",
        "kind": "SwarmStrategy",
        "metadata": {"name": name},
        "spec": {
            "inputSchema": deepcopy(_OBJECT_SCHEMA),
            "outputSchema": deepcopy(_OBJECT_SCHEMA),
            "agents": deepcopy(dict(agents)),
        },
    }


def sequential(name: str, agents: Mapping[str, Mapping[str, Any]]) -> SwarmStrategy:
    if not agents:
        raise ValueError("sequential requires at least one agent")
    document = _base(name, agents)
    nodes: dict[str, Any] = {}
    previous: str | None = None
    for key in agents:
        node: dict[str, Any] = {"type": "agent", "agent": key}
        if previous:
            node["dependsOn"] = [previous]
            node["input"] = {"previous": f"{{{{ tasks.{previous}.output }}}}"}
        nodes[key] = node
        previous = key
    document["spec"]["graph"] = {
        "entrypoint": next(iter(agents)),
        "nodes": nodes,
        "output": {"result": f"{{{{ tasks.{previous}.output }}}}"},
    }
    return SwarmStrategy.model_validate(document)


def parallel(name: str, agents: Mapping[str, Mapping[str, Any]]) -> SwarmStrategy:
    if not agents:
        raise ValueError("parallel requires at least one agent")
    document = _base(name, agents)
    branch_keys = list(agents)
    nodes: dict[str, Any] = {
        "fanout": {"type": "parallel", "branches": branch_keys},
        **{key: {"type": "agent", "agent": key, "dependsOn": ["fanout"]} for key in branch_keys},
        "results": {
            "type": "reducer",
            "reducer": "merge_object",
            "dependsOn": branch_keys,
        },
    }
    document["spec"]["graph"] = {
        "entrypoint": "fanout",
        "nodes": nodes,
        "output": {"result": "{{ tasks.results.output }}"},
    }
    return SwarmStrategy.model_validate(document)


def dag(
    name: str,
    agents: Mapping[str, Mapping[str, Any]],
    dependencies: Mapping[str, Sequence[str]],
) -> SwarmStrategy:
    if not agents:
        raise ValueError("dag requires at least one agent")
    roots = [key for key in agents if not dependencies.get(key)]
    if len(roots) != 1:
        raise ValueError("dag template requires exactly one entrypoint")
    document = _base(name, agents)
    nodes = {
        key: {
            "type": "agent",
            "agent": key,
            **({"dependsOn": list(dependencies[key])} if dependencies.get(key) else {}),
        }
        for key in agents
    }
    leaves = [key for key in agents if not any(key in values for values in dependencies.values())]
    output_key = leaves[0] if len(leaves) == 1 else "results"
    if len(leaves) > 1:
        nodes["results"] = {"type": "reducer", "reducer": "merge_object", "dependsOn": leaves}
    document["spec"]["graph"] = {
        "entrypoint": roots[0],
        "nodes": nodes,
        "output": {"result": f"{{{{ tasks.{output_key}.output }}}}"},
    }
    return SwarmStrategy.model_validate(document)


def supervisor(
    name: str,
    supervisor_agent: Mapping[str, Any],
    workers: Mapping[str, Mapping[str, Any]],
) -> SwarmStrategy:
    if not workers:
        raise ValueError("supervisor requires at least one worker")
    agents = {"supervisor": supervisor_agent, **workers}
    document = _base(name, agents)
    worker_keys = list(workers)
    nodes: dict[str, Any] = {
        "supervisor": {"type": "agent", "agent": "supervisor"},
        "dispatch": {"type": "parallel", "dependsOn": ["supervisor"], "branches": worker_keys},
        **{
            key: {
                "type": "agent",
                "agent": key,
                "dependsOn": ["dispatch"],
                "input": {"assignment": "{{ tasks.supervisor.output }}"},
            }
            for key in worker_keys
        },
        "synthesize": {
            "type": "agent",
            "agent": "supervisor",
            "dependsOn": worker_keys,
            "input": {
                "workerResults": {key: f"{{{{ tasks.{key}.output }}}}" for key in worker_keys}
            },
        },
    }
    document["spec"]["graph"] = {
        "entrypoint": "supervisor",
        "nodes": nodes,
        "output": {"result": "{{ tasks.synthesize.output }}"},
    }
    return SwarmStrategy.model_validate(document)
