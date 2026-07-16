import asyncio
from typing import Any

import pytest
from swarmcore_adapter_agno import AgnoAdapter
from swarmcore_adapter_agno import adapter as adapter_module

from agno.models.message import Message
from agno.models.metrics import Metrics
from agno.run.agent import RunOutput


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
        asyncio.run(AgnoAdapter(Resolver()).execute(request))


def test_normal_text_response_uses_content() -> None:
    output = RunOutput(run_id="run", content="final answer", reasoning_content="private")

    assert AgnoAdapter._extract_final_content(output) == ("final answer", "content")


def test_reasoning_is_not_used_as_final_answer() -> None:
    output = RunOutput(
        run_id="run",
        content="",
        reasoning_content="private chain of thought",
        messages=[
            Message(
                role="assistant",
                content="private chain of thought",
                reasoning_content="private",
            )
        ],
    )

    assert AgnoAdapter._extract_final_content(output) == (None, None)


def test_final_assistant_message_is_used_when_run_content_is_empty() -> None:
    output = RunOutput(
        run_id="run",
        content="",
        reasoning_content="private",
        messages=[Message(role="assistant", content="visible answer")],
    )

    assert AgnoAdapter._extract_final_content(output) == (
        "visible answer",
        "assistant_message.content",
    )


def test_empty_response_fails_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeAgent:
        def __init__(self, **_: Any) -> None:
            pass

        async def arun(self, *_: Any, **__: Any) -> RunOutput:
            return RunOutput(run_id="agno-run", content="", reasoning_content="private")

    monkeypatch.setattr(adapter_module, "Agent", FakeAgent)
    request = {
        "agent": {
            "role": "worker",
            "instructions": "work",
            "model": "model://general",
        },
        "run": {"runId": "run", "input": {"prompt": "sensitive"}},
        "node": {"key": "node", "config": {}},
        "taskExecutionId": "task",
        "agentInstanceId": "agent",
    }

    with pytest.raises(ValueError, match="no final answer"):
        asyncio.run(AgnoAdapter(Resolver()).execute(request))


def test_token_metrics_are_converted_and_cost_is_optional() -> None:
    without_cost = RunOutput(
        run_id="run",
        metrics=Metrics(input_tokens=12, output_tokens=7),
    )
    with_cost = RunOutput(
        run_id="run",
        metrics=Metrics(input_tokens=3, output_tokens=2, cost=0.004),
    )

    assert AgnoAdapter._extract_metrics(without_cost) == {
        "input_tokens": 12,
        "output_tokens": 7,
    }
    assert AgnoAdapter._extract_metrics(with_cost) == {
        "input_tokens": 3,
        "output_tokens": 2,
        "cost_usd": 0.004,
    }


def test_agent_receives_only_gateway_proxy_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class FakeAgent:
        def __init__(self, **values: Any) -> None:
            captured.update(values)

        async def arun(self, *_: Any, **__: Any) -> RunOutput:
            return RunOutput(run_id="run", content="done")

    class ProxyFactory:
        def create(self, tool_ref: str, capability_token: str, context: Any) -> str:
            assert context["run"]["runId"] == "run"
            return f"gateway:{tool_ref}:{capability_token}"

    monkeypatch.setattr(adapter_module, "Agent", FakeAgent)
    request = {
        "agent": {
            "role": "worker",
            "instructions": "work",
            "model": "model://general",
            "tools": ["tool://search"],
        },
        "run": {"runId": "run", "input": {}},
        "node": {"key": "node", "config": {}},
        "taskExecutionId": "task",
        "agentInstanceId": "agent",
        "toolCapabilities": {"tool://search": "signed-token"},
        "untrustedTools": ["must-not-be-used"],
    }

    asyncio.run(AgnoAdapter(Resolver(), ProxyFactory()).execute(request))

    assert captured["tools"] == ["gateway:tool://search:signed-token"]
