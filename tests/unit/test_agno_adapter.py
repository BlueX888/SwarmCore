from typing import Any

import pytest
from swarmcore_adapter_agno import AgnoAdapter


class Resolver:
    def resolve(self, reference: str) -> str:
        assert reference == "model://general"
        return "openai:gpt-4o-mini"


def test_adapter_never_builds_input_from_tool_definitions() -> None:
    request: dict[str, Any] = {
        "run": {"input": {"topic": "test"}},
        "node": {"config": {"input": {"x": 1}}},
        "dependencyOutputs": {"research": {"facts": []}},
        "untrustedTools": [{"callable": "must-not-be-used"}],
    }
    assert AgnoAdapter._build_input(request) == {
        "input": {"topic": "test"},
        "nodeInput": {"x": 1},
        "dependencyOutputs": {"research": {"facts": []}},
    }


def test_missing_model_is_rejected_before_calling_agno() -> None:
    request = {
        "agent": {"role": "worker", "instructions": "work"},
        "run": {"runId": "run"},
        "node": {"key": "node"},
    }
    with pytest.raises(ValueError, match="model reference"):
        import asyncio

        asyncio.run(AgnoAdapter(Resolver()).execute(request))
