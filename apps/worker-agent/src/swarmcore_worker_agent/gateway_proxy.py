from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

import httpx
from swarmcore_registry import RegistrySnapshot

from agno.tools.function import Function


class HttpGatewayProxyFactory:
    def __init__(
        self,
        endpoint: str,
        registry: RegistrySnapshot,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._registry = registry
        self._client = client or httpx.AsyncClient(timeout=30)

    def create(self, tool_ref: str, capability_token: str, context: Mapping[str, Any]) -> Function:
        del context
        registration = self._registry.resolve_tool(tool_ref)
        if registration is None:
            raise ValueError(f"unknown gateway tool: {tool_ref}")

        async def invoke(**arguments: Any) -> Any:
            effect_id = str(uuid4())
            response = await self._client.post(
                f"{self._endpoint}/internal/v1/tools/invoke",
                json={
                    "token": capability_token,
                    "effectId": effect_id,
                    "input": arguments,
                },
            )
            response.raise_for_status()
            return response.json()["content"]

        name = re.sub(r"[^a-zA-Z0-9_]", "_", registration.operation)
        return Function(
            name=name,
            description=registration.description,
            parameters=registration.input_schema,
            entrypoint=invoke,
            skip_entrypoint_processing=True,
        )
