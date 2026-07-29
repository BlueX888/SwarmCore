from __future__ import annotations

import asyncio
import json
import time
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from swarmcore_application import (
    AgentRuntimeStatus,
    CapabilityCenterService,
    CapabilityReadinessService,
    ModelRuntimeStatus,
    ToolRuntimeStatus,
)
from swarmcore_registry import (
    AgentRegistration,
    ModelRegistration,
    ToolRegistration,
    builtin_registry,
)

from .settings import Settings


class ReadinessHttpClient:
    _stale_if_error_seconds = 30.0

    def __init__(self, url: str, timeout_seconds: float) -> None:
        self._url = url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._cached_at = 0.0
        self._cached: dict[str, Any] | None = None
        self._has_cached = False
        self._last_success_at = 0.0
        self._lock = asyncio.Lock()

    async def get(self) -> dict[str, Any] | None:
        now = time.monotonic()
        if self._has_cached and now - self._cached_at < 1.0:
            return self._cached
        if not self._url:
            return None
        async with self._lock:
            now = time.monotonic()
            if self._has_cached and now - self._cached_at < 1.0:
                return self._cached
            inspected = await asyncio.to_thread(self._get)
            inspected_at = time.monotonic()
            if inspected is not None:
                self._cached = inspected
                self._last_success_at = inspected_at
            elif (
                self._cached is None
                or inspected_at - self._last_success_at >= self._stale_if_error_seconds
            ):
                self._cached = None
            self._cached_at = inspected_at
            self._has_cached = True
            return self._cached

    def _get(self) -> dict[str, Any] | None:
        try:
            request = Request(f"{self._url}/internal/v1/readiness", method="GET")
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return cast(dict[str, Any], json.loads(response.read(1024 * 1024)))
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
            return None


class HttpToolReadinessPort:
    def __init__(self, client: ReadinessHttpClient) -> None:
        self._client = client

    async def inspect_tool(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registration: ToolRegistration,
    ) -> ToolRuntimeStatus:
        del tenant_id, project_id, environment
        payload = await self._client.get()
        rows = payload.get("tools", []) if payload is not None else []
        row = next(
            (
                item
                for item in rows
                if isinstance(item, dict) and item.get("ref") == registration.ref
            ),
            None,
        )
        return ToolRuntimeStatus(
            executor_registered=bool(row and row.get("executorRegistered")),
            healthy=bool(row and row.get("healthy")),
        )


class HttpModelReadinessPort:
    def __init__(self, client: ReadinessHttpClient) -> None:
        self._client = client

    async def inspect_model(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registration: ModelRegistration,
    ) -> ModelRuntimeStatus:
        del tenant_id, project_id, environment
        payload = await self._client.get()
        if payload is None:
            return ModelRuntimeStatus(
                route_registered=False,
                secret_available=False,
                endpoint_healthy=False,
                inspected=False,
            )
        rows = payload.get("models", [])
        logical_model = registration.ref.rsplit("@", 1)[0]
        row = next(
            (
                item
                for item in rows
                if isinstance(item, dict) and item.get("logicalModel") == logical_model
            ),
            None,
        )
        return ModelRuntimeStatus(
            route_registered=bool(row and row.get("routeRegistered")),
            secret_available=bool(row and row.get("secretAvailable")),
            endpoint_healthy=bool(row and row.get("endpointHealthy")),
            inspected=True,
        )


class HttpAgentReadinessPort:
    def __init__(self, client: ReadinessHttpClient) -> None:
        self._client = client

    async def inspect_agent(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registration: AgentRegistration,
    ) -> AgentRuntimeStatus:
        del tenant_id, project_id, registration
        payload = await self._client.get()
        rows = payload.get("adapters", []) if payload is not None else []
        allowed_runtimes = (
            {"agno", "fake-deterministic"}
            if environment in {"development", "test"}
            else {"agno"}
        )
        row = next(
            (
                item
                for item in rows
                if isinstance(item, dict) and item.get("runtime") in allowed_runtimes
            ),
            None,
        )
        return AgentRuntimeStatus(adapter_available=bool(row and row.get("healthy")))


def create_capability_center(settings: Settings) -> CapabilityCenterService:
    tools = HttpToolReadinessPort(
        ReadinessHttpClient(settings.tool_gateway_url, settings.readiness_timeout_seconds)
    )
    models = HttpModelReadinessPort(
        ReadinessHttpClient(settings.model_gateway_url, settings.readiness_timeout_seconds)
    )
    agents = HttpAgentReadinessPort(
        ReadinessHttpClient(settings.agent_readiness_url, settings.readiness_timeout_seconds)
    )
    return CapabilityCenterService(
        builtin_registry(),
        CapabilityReadinessService(tools=tools, models=models, agents=agents),
    )
