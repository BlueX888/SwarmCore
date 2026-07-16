import asyncio

from swarmcore_worker_agent.fake import DeterministicFakeAgentAdapter


def test_fake_agent_is_deterministic_and_structured() -> None:
    request = {
        "run": {"input": {"topic": "retries", "_failOnce": False}},
        "node": {"key": "worker", "config": {"input": {}}},
        "taskExecutionId": "task-1",
        "dependencyOutputs": {},
    }
    adapter = DeterministicFakeAgentAdapter()
    first = asyncio.run(adapter.execute(request))
    second = asyncio.run(adapter.execute(request))
    assert first == second
    assert first["status"] == "COMPLETED"
    assert first["metrics"]["costUsd"] == 0.0
