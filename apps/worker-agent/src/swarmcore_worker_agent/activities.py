from __future__ import annotations

import json
import logging
from typing import Any, Protocol

from temporalio import activity

from agno.models.base import Model

logger = logging.getLogger(__name__)


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
        node_key = str(request["node"]["key"])
        model_ref = request["agent"].get("model") or request.get("defaultModel")
        activity.heartbeat({"stage": "starting", "nodeKey": node_key})
        logger.info(
            "agent_execution_started %s",
            json.dumps({"nodeKey": node_key, "modelRef": model_ref}, sort_keys=True),
        )
        try:
            result = await self._adapter.execute(request)
        except Exception as exc:
            logger.exception(
                "agent_execution_failed %s",
                json.dumps(
                    {
                        "nodeKey": node_key,
                        "modelRef": model_ref,
                        "errorType": type(exc).__name__,
                    },
                    sort_keys=True,
                ),
            )
            raise
        activity.heartbeat({"stage": "completed", "nodeKey": node_key})
        logger.info(
            "agent_execution_completed %s",
            json.dumps(
                {
                    "nodeKey": node_key,
                    "model": result.get("model"),
                    "status": result.get("status"),
                    "metrics": result.get("metrics", {}),
                },
                sort_keys=True,
            ),
        )
        return result

    @activity.defn(name="execute_team")
    async def execute_team(self, request: dict[str, Any]) -> dict[str, Any]:
        raise ValueError("opaque Agno Team definitions are not configured in Phase 1")
