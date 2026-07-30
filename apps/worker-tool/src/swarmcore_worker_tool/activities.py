from __future__ import annotations

import asyncio
from contextlib import suppress
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
        node_key = str(request["node"]["key"])
        activity.heartbeat({"stage": "gateway", "nodeKey": node_key})
        heartbeat_task = asyncio.create_task(
            self._heartbeat_while_running({"stage": "gateway", "nodeKey": node_key})
        )
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
        finally:
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task

    @activity.defn(name="compensate_tool")
    async def compensate_tool(self, request: dict[str, Any]) -> dict[str, Any]:
        details = {"stage": "compensating", "effectId": request["effectId"]}
        activity.heartbeat(details)
        heartbeat_task = asyncio.create_task(self._heartbeat_while_running(details))
        try:
            return await self._gateway.compensate(
                CompensationInvocation(
                    token=str(request["capabilityToken"]),
                    effectId=str(request["effectId"]),
                    input=dict(request.get("input", {})),
                )
            )
        finally:
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task

    @staticmethod
    async def _heartbeat_while_running(details: dict[str, Any]) -> None:
        while True:
            await asyncio.sleep(10)
            activity.heartbeat(details)
