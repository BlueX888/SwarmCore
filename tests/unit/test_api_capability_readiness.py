from uuid import UUID

import pytest
from swarmcore_api.capability_readiness import HttpAgentReadinessPort, ReadinessHttpClient
from swarmcore_registry import builtin_registry


@pytest.mark.asyncio
async def test_readiness_client_tolerates_one_transient_probe_failure(monkeypatch) -> None:
    client = ReadinessHttpClient("http://agent-worker", 2)
    responses = iter([{"adapters": [{"runtime": "agno", "healthy": True}]}, None, None])
    monkeypatch.setattr(client, "_get", lambda: next(responses))

    ready = await client.get()
    client._cached_at -= 2
    transient = await client.get()
    client._cached_at -= 2
    client._last_success_at -= 31
    unavailable = await client.get()

    assert transient == ready
    assert unavailable is None


@pytest.mark.asyncio
async def test_fake_agent_adapter_is_ready_only_outside_production(monkeypatch) -> None:
    client = ReadinessHttpClient("http://agent-worker", 2)

    async def fake_get() -> dict[str, object]:
        return {"adapters": [{"runtime": "fake-deterministic", "healthy": True}]}

    monkeypatch.setattr(client, "get", fake_get)
    port = HttpAgentReadinessPort(client)
    registration = builtin_registry().agents[0]
    development = await port.inspect_agent(
        tenant_id=UUID(int=1),
        project_id=UUID(int=2),
        environment="development",
        registration=registration,
    )
    production = await port.inspect_agent(
        tenant_id=UUID(int=1),
        project_id=UUID(int=2),
        environment="production",
        registration=registration,
    )

    assert development.adapter_available is True
    assert production.adapter_available is False
