import asyncio

import pytest
from swarmcore_worker_agent import activities
from swarmcore_worker_agent.activities import AgentActivities


@pytest.mark.asyncio
async def test_agent_activity_heartbeats_while_model_is_running(monkeypatch) -> None:
    heartbeats: list[dict[str, str]] = []
    sleeps = 0

    async def fake_sleep(_seconds: float) -> None:
        nonlocal sleeps
        sleeps += 1
        if sleeps > 1:
            raise asyncio.CancelledError

    monkeypatch.setattr(activities.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(activities.activity, "heartbeat", heartbeats.append)

    with pytest.raises(asyncio.CancelledError):
        await AgentActivities._heartbeat_while_running("analyze")

    assert heartbeats == [{"stage": "running", "nodeKey": "analyze"}]
