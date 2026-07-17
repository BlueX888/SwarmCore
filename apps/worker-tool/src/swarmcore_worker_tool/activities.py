from __future__ import annotations

from datetime import timedelta
from typing import Any

from swarmcore_tool_gateway import (
    CompensationInvocation,
    EffectInProgress,
    ToolGateway,
    ToolInvocation,
)
from temporalio import activity
from temporalio.exceptions import ApplicationError


class ToolActivities:
    def __init__(self, gateway: ToolGateway) -> None:
        self._gateway = gateway

    @activity.defn(name="execute_tool")
    async def execute_tool(self, request: dict[str, Any]) -> dict[str, Any]:
        activity.heartbeat({"stage": "gateway", "nodeKey": request["node"]["key"]})
        try:
            return await self._gateway.invoke(
                ToolInvocation(
                    token=str(request["capabilityToken"]),
                    effectId=str(request["effectId"]),
                    input=dict(request.get("input", {})),
                )
            )
        except EffectInProgress as exc:
            raise ApplicationError(
                str(exc),
                type="TOOL_EFFECT_IN_PROGRESS",
                next_retry_delay=timedelta(seconds=45),
            ) from exc

    @activity.defn(name="compensate_tool")
    async def compensate_tool(self, request: dict[str, Any]) -> dict[str, Any]:
        activity.heartbeat({"stage": "compensating", "effectId": request["effectId"]})
        return await self._gateway.compensate(
            CompensationInvocation(
                token=str(request["capabilityToken"]),
                effectId=str(request["effectId"]),
                input=dict(request.get("input", {})),
            )
        )
