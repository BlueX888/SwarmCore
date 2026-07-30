from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from temporalio import activity


class PlanStore(Protocol):
    async def load(
        self, *, tenant_id: str, project_id: str, run_id: str, plan_hash: str
    ) -> dict[str, Any]: ...


class TransitionProjector(Protocol):
    async def project(self, transition: Mapping[str, Any]) -> None: ...


class ToolCapabilityIssuer(Protocol):
    def issue(self, request: Mapping[str, Any]) -> str: ...


class ControlActivities:
    def __init__(
        self,
        plans: PlanStore,
        projector: TransitionProjector,
        capability_issuer: ToolCapabilityIssuer | None = None,
    ) -> None:
        self._plans = plans
        self._projector = projector
        self._capability_issuer = capability_issuer

    @activity.defn(name="load_execution_plan")
    async def load_execution_plan(self, run_input: dict[str, Any]) -> dict[str, Any]:
        return await self._plans.load(
            tenant_id=str(run_input["tenantId"]),
            project_id=str(run_input["projectId"]),
            run_id=str(run_input["runId"]),
            plan_hash=str(run_input["planHash"]),
        )

    @activity.defn(name="project_transition")
    async def project_transition(self, transition: dict[str, Any]) -> None:
        await self._projector.project(transition)

    @activity.defn(name="issue_tool_capability")
    async def issue_tool_capability(self, request: dict[str, Any]) -> str:
        if self._capability_issuer is None:
            raise RuntimeError("Tool Gateway capability issuer is not configured")
        return self._capability_issuer.issue(request)

    @activity.defn(name="execute_control_node")
    async def execute_control_node(self, request: dict[str, Any]) -> dict[str, Any]:
        node = request["node"]
        node_type = node["type"]
        dependencies = request.get("dependencyOutputs", {})
        if node_type in {"parallel", "join"}:
            return {"outputs": dependencies}
        if node_type == "reducer":
            return self._reduce(str(node["config"]["reducer"]), dependencies)
        if node_type == "transform":
            transform = node["config"].get("transform")
            if transform == "identity":
                return {"value": dependencies}
            raise ValueError("CEL transforms require the policy runtime")
        raise ValueError(f"unsupported control node type: {node_type}")

    @staticmethod
    def _reduce(strategy: str, values: dict[str, Any]) -> dict[str, Any]:
        ordered = [values[key] for key in sorted(values)]
        if strategy == "merge_object":
            result: dict[str, Any] = {}
            for value in ordered:
                content = value.get("content", value) if isinstance(value, dict) else value
                if isinstance(content, dict):
                    result.update(content)
            return result
        if strategy == "concat":
            return {"items": ordered}
        if strategy == "first_success":
            for value in ordered:
                if isinstance(value, dict):
                    if value:
                        return value
                    continue
                if value is not None:
                    return {"value": value}
            return {}
        if strategy == "vote":
            counts: dict[str, int] = {}
            for value in ordered:
                key = str(value)
                counts[key] = counts.get(key, 0) + 1
            winner = min(counts, key=lambda key: (-counts[key], key))
            return {"winner": winner, "counts": counts}
        raise ValueError(f"unknown reducer: {strategy}")
