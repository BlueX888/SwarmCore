from __future__ import annotations

import hashlib
import json
import re
from collections import deque
from typing import Any, Literal

from jsonschema import Draft202012Validator, SchemaError
from pydantic import BaseModel, ConfigDict, Field
from swarmcore_spec.models import (
    AgentNode,
    LoopNode,
    ParallelNode,
    RouterNode,
    SwarmStrategy,
)

COMPILER_VERSION = "1.0.0"
RUNTIME_VERSION = "1.0.0"
PLAN_VERSION = "swarmcore.io/plan/v1"
_TASK_TEMPLATE = re.compile(r"tasks\.([a-z][a-z0-9_-]{0,62})\b")
_SUPPORTED_NODE_TYPES = {"agent", "parallel", "join", "reducer", "approval", "input"}


class Diagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    severity: Literal["error", "warning"]
    code: str
    path: str
    message: str


class PlanNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    type: str
    dependencies: tuple[str, ...]
    config: dict[str, Any]


class PlanEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: str
    target: str
    kind: Literal["dependency", "route", "branch", "loop"]


class ExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_version: str
    compiler_version: str
    runtime_version: str
    spec_hash: str
    registry_snapshot: str
    policy_revision: str
    entrypoint: str
    nodes: tuple[PlanNode, ...]
    edges: tuple[PlanEdge, ...]
    resolved_resources: tuple[str, ...]
    resolved_agents: dict[str, dict[str, Any]]
    defaults: dict[str, Any]
    budget: dict[str, Any]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    result_reducer: dict[str, Any]
    diagnostics: tuple[Diagnostic, ...]
    plan_hash: str = Field(min_length=64, max_length=64)

    def canonical_json(self) -> str:
        return _canonical_json(self.model_dump(mode="json", by_alias=True))


class CompileError(ValueError):
    def __init__(self, diagnostics: list[Diagnostic]):
        self.diagnostics = tuple(diagnostics)
        summary = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in diagnostics)
        super().__init__(summary)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class Compiler:
    """Pure deterministic compiler from a validated SwarmSpec to an immutable plan."""

    def compile(
        self,
        strategy: SwarmStrategy,
        *,
        registry_snapshot: str,
        policy_revision: str,
    ) -> ExecutionPlan:
        diagnostics = self.validate(strategy)
        errors = [item for item in diagnostics if item.severity == "error"]
        if errors:
            raise CompileError(errors)

        spec = strategy.spec
        node_map = spec.graph.nodes.root
        order = self._topological_order(strategy)
        nodes = tuple(
            PlanNode(
                key=key,
                type=node_map[key].type,
                dependencies=tuple(sorted(node_map[key].depends_on)),
                config=node_map[key].model_dump(
                    mode="json", by_alias=True, exclude={"type", "depends_on"}, exclude_none=True
                ),
            )
            for key in order
        )
        edges = self._edges(strategy)
        resources = self._resources(strategy)
        normalized_spec = strategy.model_dump(mode="json", by_alias=True, exclude_none=True)
        spec_hash = _sha256(_canonical_json(normalized_spec))
        reducer = {
            key: node.model_dump(mode="json", by_alias=True, exclude_none=True)
            for key, node in sorted(node_map.items())
            if node.type == "reducer"
        }
        payload: dict[str, Any] = {
            "plan_version": PLAN_VERSION,
            "compiler_version": COMPILER_VERSION,
            "runtime_version": RUNTIME_VERSION,
            "spec_hash": spec_hash,
            "registry_snapshot": registry_snapshot,
            "policy_revision": policy_revision,
            "entrypoint": spec.graph.entrypoint,
            "nodes": [node.model_dump(mode="json") for node in nodes],
            "edges": [edge.model_dump(mode="json") for edge in edges],
            "resolved_resources": list(resources),
            "resolved_agents": {
                key: self._resolved_agent(strategy, key) for key in sorted(spec.agents)
            },
            "defaults": spec.defaults.model_dump(mode="json", by_alias=True, exclude_none=True),
            "budget": spec.budget.model_dump(mode="json", by_alias=True),
            "input_schema": spec.input_schema,
            "output_schema": spec.output_schema,
            "result_reducer": reducer,
            "diagnostics": [item.model_dump(mode="json") for item in diagnostics],
        }
        plan_hash = _sha256(_canonical_json(payload))
        encoded_size = len(_canonical_json({**payload, "plan_hash": plan_hash}).encode("utf-8"))
        if encoded_size > 512 * 1024:
            raise CompileError(
                [
                    Diagnostic(
                        severity="error",
                        code="PLAN_TOO_LARGE",
                        path="$",
                        message="compiled ExecutionPlan exceeds 512 KiB",
                    )
                ]
            )
        return ExecutionPlan(**payload, plan_hash=plan_hash)

    def validate(self, strategy: SwarmStrategy) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        spec = strategy.spec
        nodes = spec.graph.nodes.root

        for name, schema in (
            ("inputSchema", spec.input_schema),
            ("outputSchema", spec.output_schema),
        ):
            try:
                Draft202012Validator.check_schema(schema)
            except SchemaError as exc:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="INVALID_JSON_SCHEMA",
                        path=f"$.spec.{name}",
                        message=exc.message,
                    )
                )

        if spec.graph.entrypoint not in nodes:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="UNKNOWN_ENTRYPOINT",
                    path="$.spec.graph.entrypoint",
                    message=f"node {spec.graph.entrypoint!r} does not exist",
                )
            )

        for key, node in sorted(nodes.items()):
            path = f"$.spec.graph.nodes.{key}"
            if node.type not in _SUPPORTED_NODE_TYPES:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="UNSUPPORTED_NODE_TYPE",
                        path=f"{path}.type",
                        message=f"node type {node.type!r} is not supported by the Phase 1 runtime",
                    )
                )
            if key in node.depends_on:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="SELF_DEPENDENCY",
                        path=f"{path}.dependsOn",
                        message="a node cannot depend on itself",
                    )
                )
            unknown = sorted(set(node.depends_on) - nodes.keys())
            for dependency in unknown:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="UNKNOWN_DEPENDENCY",
                        path=f"{path}.dependsOn",
                        message=f"node {dependency!r} does not exist",
                    )
                )
            if isinstance(node, AgentNode) and node.agent not in spec.agents:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="UNKNOWN_AGENT",
                        path=f"{path}.agent",
                        message=f"agent {node.agent!r} is not declared",
                    )
                )
            diagnostics.extend(self._validate_control_references(key, node, nodes))
            diagnostics.extend(self._validate_templates(key, node.input, nodes))

        diagnostics.extend(self._validate_templates("output", spec.graph.output, nodes))
        if not any(item.code in {"UNKNOWN_DEPENDENCY", "SELF_DEPENDENCY"} for item in diagnostics):
            try:
                self._topological_order(strategy)
            except CompileError as exc:
                diagnostics.extend(exc.diagnostics)
        if len(spec.agents) > spec.budget.max_agents:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="AGENT_BUDGET_EXCEEDED",
                    path="$.spec.agents",
                    message="declared agents exceed budget.maxAgents",
                )
            )
        for key, agent in sorted(spec.agents.items()):
            if (
                agent.output_schema_ref
                and self._resolve_local_schema(strategy, agent.output_schema_ref) is None
            ):
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="UNKNOWN_SCHEMA_REFERENCE",
                        path=f"$.spec.agents.{key}.outputSchemaRef",
                        message=f"schema {agent.output_schema_ref!r} does not exist",
                    )
                )
        return sorted(diagnostics, key=lambda item: (item.path, item.code, item.message))

    def _validate_control_references(
        self, key: str, node: Any, nodes: dict[str, Any]
    ) -> list[Diagnostic]:
        refs: list[tuple[str, str]] = []
        if isinstance(node, RouterNode):
            refs.extend(("routes", route.target) for route in node.routes)
            if node.default:
                refs.append(("default", node.default))
        elif isinstance(node, ParallelNode):
            refs.extend(("branches", target) for target in node.branches)
        elif isinstance(node, LoopNode):
            refs.extend(("body", target) for target in node.body)
        return [
            Diagnostic(
                severity="error",
                code="UNKNOWN_NODE_REFERENCE",
                path=f"$.spec.graph.nodes.{key}.{field}",
                message=f"node {target!r} does not exist",
            )
            for field, target in refs
            if target not in nodes
        ]

    def _validate_templates(self, key: str, value: Any, nodes: dict[str, Any]) -> list[Diagnostic]:
        unknown: set[str] = set()

        def walk(current: Any) -> None:
            if isinstance(current, str):
                unknown.update(
                    match for match in _TASK_TEMPLATE.findall(current) if match not in nodes
                )
            elif isinstance(current, dict):
                for child in current.values():
                    walk(child)
            elif isinstance(current, list):
                for child in current:
                    walk(child)

        walk(value)
        return [
            Diagnostic(
                severity="error",
                code="UNKNOWN_TEMPLATE_TASK",
                path=f"$.spec.graph.{key}",
                message=f"template references unknown task {item!r}",
            )
            for item in sorted(unknown)
        ]

    def _topological_order(self, strategy: SwarmStrategy) -> tuple[str, ...]:
        nodes = strategy.spec.graph.nodes.root
        indegree = {key: len(node.depends_on) for key, node in nodes.items()}
        dependents: dict[str, list[str]] = {key: [] for key in nodes}
        for key, node in nodes.items():
            for dependency in node.depends_on:
                if dependency in dependents:
                    dependents[dependency].append(key)
        ready = deque(sorted(key for key, count in indegree.items() if count == 0))
        ordered: list[str] = []
        while ready:
            key = ready.popleft()
            ordered.append(key)
            for dependent in sorted(dependents[key]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)
            ready = deque(sorted(ready))
        if len(ordered) != len(nodes):
            cyclic = sorted(key for key, count in indegree.items() if count > 0)
            raise CompileError(
                [
                    Diagnostic(
                        severity="error",
                        code="CYCLIC_DEPENDENCY",
                        path="$.spec.graph.nodes",
                        message=f"dependency cycle includes: {', '.join(cyclic)}",
                    )
                ]
            )
        return tuple(ordered)

    def _edges(self, strategy: SwarmStrategy) -> tuple[PlanEdge, ...]:
        edges: set[tuple[str, str, str]] = set()
        for key, node in strategy.spec.graph.nodes.root.items():
            edges.update((dependency, key, "dependency") for dependency in node.depends_on)
            if isinstance(node, RouterNode):
                edges.update((key, route.target, "route") for route in node.routes)
                if node.default:
                    edges.add((key, node.default, "route"))
            elif isinstance(node, ParallelNode):
                edges.update((key, target, "branch") for target in node.branches)
            elif isinstance(node, LoopNode):
                edges.update((key, target, "loop") for target in node.body)
        return tuple(PlanEdge(source=a, target=b, kind=c) for a, b, c in sorted(edges))  # type: ignore[arg-type]

    def _resources(self, strategy: SwarmStrategy) -> tuple[str, ...]:
        resources: set[str] = set()
        if strategy.spec.defaults.model:
            resources.add(strategy.spec.defaults.model)
        for agent in strategy.spec.agents.values():
            if agent.model:
                resources.add(agent.model)
            resources.update(agent.tools)
        for node in strategy.spec.graph.nodes.root.values():
            if node.type == "tool":
                resources.add(node.tool)
            elif node.type == "team":
                resources.add(node.team)
            elif node.type == "subflow":
                resources.add(node.strategy)
        return tuple(sorted(resources))

    def _resolved_agent(self, strategy: SwarmStrategy, key: str) -> dict[str, Any]:
        agent = strategy.spec.agents[key]
        resolved = agent.model_dump(mode="json", by_alias=True, exclude_none=True)
        if agent.output_schema_ref:
            schema = self._resolve_local_schema(strategy, agent.output_schema_ref)
            if schema is not None:
                resolved["outputSchema"] = schema
        return resolved

    @staticmethod
    def _resolve_local_schema(strategy: SwarmStrategy, reference: str) -> dict[str, Any] | None:
        prefix = "#/$defs/"
        if not reference.startswith(prefix):
            return None
        value = strategy.spec.definitions.get(reference.removeprefix(prefix))
        return value if isinstance(value, dict) else None
