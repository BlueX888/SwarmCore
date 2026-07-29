from __future__ import annotations

import hashlib
import json
import re
from collections import deque
from typing import Any, Literal

from jsonschema import Draft202012Validator, SchemaError
from pydantic import BaseModel, ConfigDict, Field
from swarmcore_registry import (
    RegistrySnapshot,
    builtin_registry,
    synthesize_project_model_registration,
)
from swarmcore_spec import ExpressionError, validate_condition
from swarmcore_spec.models import (
    AgentNode,
    LoopNode,
    ParallelNode,
    RouterNode,
    SwarmStrategy,
    ToolNode,
)

COMPILER_VERSION = "1.1.0"
RUNTIME_VERSION = "1.1.0"
PLAN_VERSION = "swarmcore.io/plan/v1"
_TASK_TEMPLATE = re.compile(r"tasks\.([a-z][a-z0-9_-]{0,62})\b")
_SUPPORTED_NODE_TYPES = {
    "agent",
    "tool",
    "router",
    "loop",
    "parallel",
    "join",
    "reducer",
    "approval",
    "input",
}


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
    resolved_models: dict[str, dict[str, Any]]
    resolved_tools: dict[str, dict[str, Any]]
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

    def __init__(self, registry: RegistrySnapshot | None = None) -> None:
        self._registry = registry or builtin_registry()

    def compile(
        self,
        strategy: SwarmStrategy,
        *,
        registry_snapshot: str,
        policy_revision: str,
    ) -> ExecutionPlan:
        if registry_snapshot != self._registry.snapshot_id:
            raise CompileError(
                [
                    Diagnostic(
                        severity="error",
                        code="REGISTRY_SNAPSHOT_MISMATCH",
                        path="$.registrySnapshot",
                        message=(
                            f"requested {registry_snapshot!r}, available "
                            f"{self._registry.snapshot_id!r}"
                        ),
                    )
                ]
            )
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
            "resolved_models": self._resolved_models(strategy),
            "resolved_tools": self._resolved_tools(strategy),
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
        diagnostics = [
            *self._validate_strategy_schemas(strategy),
            *self._validate_graph(strategy),
            *self._validate_agents(strategy),
        ]
        return sorted(diagnostics, key=lambda item: (item.path, item.code, item.message))

    @staticmethod
    def _validate_strategy_schemas(strategy: SwarmStrategy) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        spec = strategy.spec
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
        return diagnostics

    def _validate_graph(self, strategy: SwarmStrategy) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        spec = strategy.spec
        nodes = spec.graph.nodes.root

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
            diagnostics.extend(self._validate_node(strategy, key, node, nodes))

        diagnostics.extend(self._validate_templates("output", spec.graph.output, nodes))
        diagnostics.extend(self._validate_loop_ownership(nodes))
        if not any(item.code in {"UNKNOWN_DEPENDENCY", "SELF_DEPENDENCY"} for item in diagnostics):
            try:
                self._topological_order(strategy)
            except CompileError as exc:
                diagnostics.extend(exc.diagnostics)
        return diagnostics

    def _validate_node(
        self,
        strategy: SwarmStrategy,
        key: str,
        node: Any,
        nodes: dict[str, Any],
    ) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
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
        for dependency in sorted(set(node.depends_on) - nodes.keys()):
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="UNKNOWN_DEPENDENCY",
                    path=f"{path}.dependsOn",
                    message=f"node {dependency!r} does not exist",
                )
            )
        if isinstance(node, AgentNode) and node.agent not in strategy.spec.agents:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="UNKNOWN_AGENT",
                    path=f"{path}.agent",
                    message=f"agent {node.agent!r} is not declared",
                )
            )
        if isinstance(node, AgentNode) and node.fallback_agent is not None:
            if node.fallback_agent not in strategy.spec.agents:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="UNKNOWN_FALLBACK_AGENT",
                        path=f"{path}.fallbackAgent",
                        message=f"agent {node.fallback_agent!r} is not declared",
                    )
                )
            elif node.fallback_agent == node.agent:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="FALLBACK_AGENT_REUSES_PRIMARY",
                        path=f"{path}.fallbackAgent",
                        message="fallbackAgent must differ from the primary agent",
                    )
                )
        if isinstance(node, ToolNode) and self._registry.resolve_tool(node.tool) is None:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="UNKNOWN_TOOL",
                    path=f"{path}.tool",
                    message=f"tool {node.tool!r} is not present in the registry snapshot",
                )
            )
        if isinstance(node, RouterNode):
            diagnostics.extend(self._validate_router_node(key, node, nodes))
        if isinstance(node, LoopNode):
            diagnostics.extend(self._validate_loop_node(key, node, nodes))
        diagnostics.extend(self._validate_control_references(key, node, nodes))
        diagnostics.extend(self._validate_templates(key, node.input, nodes))
        return diagnostics

    def _validate_router_node(
        self, key: str, node: RouterNode, nodes: dict[str, Any]
    ) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        path = f"$.spec.graph.nodes.{key}"
        for index, route in enumerate(node.routes):
            try:
                validate_condition(route.when)
            except ExpressionError as exc:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="INVALID_CONDITION",
                        path=f"{path}.routes.{index}.when",
                        message=str(exc),
                    )
                )
        targets = [route.target for route in node.routes]
        if node.default:
            targets.append(node.default)
        for target in targets:
            if target in nodes and key not in nodes[target].depends_on:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="ROUTE_TARGET_NOT_GATED",
                        path=f"{path}.routes",
                        message=f"route target {target!r} must depend on router {key!r}",
                    )
                )
        diagnostics.extend(self._validate_router_shape(key, targets, nodes))
        return diagnostics

    def _validate_loop_node(
        self, key: str, node: LoopNode, nodes: dict[str, Any]
    ) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        try:
            validate_condition(node.until)
        except ExpressionError as exc:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="INVALID_CONDITION",
                    path=f"$.spec.graph.nodes.{key}.until",
                    message=str(exc),
                )
            )
        diagnostics.extend(self._validate_loop(key, node, nodes))
        return diagnostics

    @staticmethod
    def _validate_loop_ownership(nodes: dict[str, Any]) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        body_owners: dict[str, list[str]] = {}
        for loop_key, candidate in nodes.items():
            if isinstance(candidate, LoopNode):
                for body_key in candidate.body:
                    body_owners.setdefault(body_key, []).append(loop_key)
        for body_key, owners in body_owners.items():
            if len(owners) > 1:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="LOOP_BODY_SHARED",
                        path=f"$.spec.graph.nodes.{body_key}",
                        message=f"loop body node is shared by: {', '.join(sorted(owners))}",
                    )
                )
        return diagnostics

    def _validate_agents(self, strategy: SwarmStrategy) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        spec = strategy.spec
        if len(spec.agents) > spec.budget.max_agents:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="AGENT_BUDGET_EXCEEDED",
                    path="$.spec.agents",
                    message="declared agents exceed budget.maxAgents",
                )
            )
        if spec.defaults.model and self._resolve_model(spec.defaults.model) is None:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="UNKNOWN_MODEL",
                    path="$.spec.defaults.model",
                    message=(
                        f"model {spec.defaults.model!r} is not present in the registry snapshot"
                    ),
                )
            )
        for key, agent in sorted(spec.agents.items()):
            if agent.ref and self._registry.resolve_agent(agent.ref) is None:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="UNKNOWN_REGISTERED_AGENT",
                        path=f"$.spec.agents.{key}.ref",
                        message=f"agent {agent.ref!r} is not present in the registry snapshot",
                    )
                )
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
            resolved = self._agent_values(strategy, key)
            model_ref = resolved.get("model") or spec.defaults.model
            if isinstance(model_ref, str) and self._resolve_model(model_ref) is None:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="UNKNOWN_MODEL",
                        path=f"$.spec.agents.{key}.model",
                        message=f"model {model_ref!r} is not present in the registry snapshot",
                    )
                )
            for tool_ref in resolved.get("tools", []):
                registration = self._registry.resolve_tool(str(tool_ref))
                if registration is None:
                    diagnostics.append(
                        Diagnostic(
                            severity="error",
                            code="UNKNOWN_TOOL",
                            path=f"$.spec.agents.{key}.tools",
                            message=f"tool {tool_ref!r} is not present in the registry snapshot",
                        )
                    )
                elif registration.side_effecting:
                    diagnostics.append(
                        Diagnostic(
                            severity="error",
                            code="AGENT_SIDE_EFFECT_TOOL_REQUIRES_NODE",
                            path=f"$.spec.agents.{key}.tools",
                            message=(
                                f"side-effecting tool {tool_ref!r} must be an explicit tool node"
                            ),
                        )
                    )
        return diagnostics

    @staticmethod
    def _validate_router_shape(
        key: str, targets: list[str], nodes: dict[str, Any]
    ) -> list[Diagnostic]:
        target_set = set(targets)
        diagnostics: list[Diagnostic] = []
        for other_key, other in nodes.items():
            dependencies = set(other.depends_on)
            if (
                other_key not in target_set
                and dependencies.intersection(target_set)
                and not (target_set.issubset(dependencies))
            ):
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="ROUTER_BRANCH_MUST_CONVERGE",
                        path=f"$.spec.graph.nodes.{other_key}.dependsOn",
                        message=(
                            f"router {key!r} v1 branches must converge at a node depending "
                            "on every route target"
                        ),
                    )
                )
        return diagnostics

    @staticmethod
    def _validate_loop(key: str, node: LoopNode, nodes: dict[str, Any]) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        body = set(node.body)
        position = {body_key: index for index, body_key in enumerate(node.body)}
        allowed_types = {"agent", "tool", "reducer"}
        for body_key in node.body:
            if body_key not in nodes:
                continue
            body_node = nodes[body_key]
            if body_node.type not in allowed_types:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="UNSUPPORTED_LOOP_BODY",
                        path=f"$.spec.graph.nodes.{key}.body",
                        message=(
                            f"loop body node {body_key!r} has unsupported type {body_node.type!r}"
                        ),
                    )
                )
            external = set(body_node.depends_on) - body
            if not external.issubset(node.depends_on):
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="LOOP_DEPENDENCY_NOT_GATED",
                        path=f"$.spec.graph.nodes.{body_key}.dependsOn",
                        message="loop body external dependencies must also be loop dependencies",
                    )
                )
            out_of_order = [
                dependency
                for dependency in body_node.depends_on
                if dependency in position and position[dependency] >= position[body_key]
            ]
            if out_of_order:
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="LOOP_BODY_ORDER_INVALID",
                        path=f"$.spec.graph.nodes.{body_key}.dependsOn",
                        message="loop body dependencies must precede the dependent body node",
                    )
                )
        for other_key, other in nodes.items():
            if other_key not in body and other_key != key and body.intersection(other.depends_on):
                diagnostics.append(
                    Diagnostic(
                        severity="error",
                        code="LOOP_BODY_EXPOSED",
                        path=f"$.spec.graph.nodes.{other_key}.dependsOn",
                        message="nodes outside a loop must depend on the loop, not its body",
                    )
                )
        return diagnostics

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
        for key in strategy.spec.agents:
            agent = self._agent_values(strategy, key)
            if agent.get("model"):
                resources.add(str(agent["model"]))
            resources.update(str(item) for item in agent.get("tools", []))
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
        resolved = self._agent_values(strategy, key)
        if agent.output_schema_ref:
            schema = self._resolve_local_schema(strategy, agent.output_schema_ref)
            if schema is not None:
                resolved["outputSchema"] = schema
        return resolved

    def _agent_values(self, strategy: SwarmStrategy, key: str) -> dict[str, Any]:
        agent = strategy.spec.agents[key]
        values: dict[str, Any] = {}
        if agent.ref:
            registered = self._registry.resolve_agent(agent.ref)
            if registered is not None:
                values = registered.model_dump(mode="json", by_alias=True, exclude_none=True)
                values["registryRef"] = values.pop("ref")
        inline = agent.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude={"ref", "output_schema_ref"},
        )
        values.update(inline)
        return values

    def _resolved_models(self, strategy: SwarmStrategy) -> dict[str, dict[str, Any]]:
        references: set[str] = set()
        if strategy.spec.defaults.model:
            references.add(strategy.spec.defaults.model)
        for key in strategy.spec.agents:
            model = self._agent_values(strategy, key).get("model")
            if isinstance(model, str):
                references.add(model)
        return {
            reference: registration.model_dump(mode="json", by_alias=True)
            for reference in sorted(references)
            if (registration := self._resolve_model(reference)) is not None
        }

    def _resolved_tools(self, strategy: SwarmStrategy) -> dict[str, dict[str, Any]]:
        references = {
            reference
            for values in (self._agent_values(strategy, key) for key in strategy.spec.agents)
            for reference in values.get("tools", [])
        }
        references.update(
            node.tool
            for node in strategy.spec.graph.nodes.root.values()
            if isinstance(node, ToolNode)
        )
        return {
            reference: registration.model_dump(mode="json", by_alias=True)
            for reference in sorted(references)
            if (registration := self._registry.resolve_tool(reference)) is not None
        }

    def _resolve_model(self, reference: str):
        return self._registry.resolve_model(reference) or synthesize_project_model_registration(
            reference
        )

    @staticmethod
    def _resolve_local_schema(strategy: SwarmStrategy, reference: str) -> dict[str, Any] | None:
        prefix = "#/$defs/"
        if not reference.startswith(prefix):
            return None
        value = strategy.spec.definitions.get(reference.removeprefix(prefix))
        return value if isinstance(value, dict) else None
