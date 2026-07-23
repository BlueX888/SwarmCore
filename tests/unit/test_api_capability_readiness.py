import pytest
from swarmcore_api.capability_readiness import ReadinessHttpClient


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
