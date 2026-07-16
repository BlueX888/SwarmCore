from __future__ import annotations

from typing import Any, Protocol

from temporalio import activity

from agno.models.base import Model


class StaticModelResolver:
    def __init__(self, models: dict[str, str]) -> None:
        self._models = models

    def resolve(self, reference: str) -> Model | str:
        try:
            return self._models[reference]
        except KeyError as exc:
            raise ValueError(f"model reference is not configured: {reference}") from exc


class AgentAdapter(Protocol):
    async def execute(self, request: dict[str, Any]) -> dict[str, Any]: ...


class AgentActivities:
    def __init__(self, adapter: AgentAdapter) -> None:
        self._adapter = adapter

    @activity.defn(name="execute_agent")
    async def execute_agent(self, request: dict[str, Any]) -> dict[str, Any]:
        activity.heartbeat({"stage": "starting", "nodeKey": request["node"]["key"]})
        result = await self._adapter.execute(request)
        activity.heartbeat({"stage": "completed", "nodeKey": request["node"]["key"]})
        return result

    @activity.defn(name="execute_team")
    async def execute_team(self, request: dict[str, Any]) -> dict[str, Any]:
        raise ValueError("opaque Agno Team definitions are not configured in Phase 1")
