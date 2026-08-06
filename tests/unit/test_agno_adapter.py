import asyncio
from collections.abc import Mapping
from typing import Any

import pytest
from swarmcore_adapter_agno import AgnoAdapter
from swarmcore_adapter_agno import adapter as adapter_module

from agno.models.message import Message
from agno.models.metrics import Metrics
from agno.run.agent import RunOutput, RunStatus


class Resolver:
    def resolve(self, reference: str, context: Mapping[str, Any]) -> str:
        del context
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


def test_adapter_node_only_context_omits_bulk_run_and_dependency_inputs() -> None:
    request: dict[str, Any] = {
        "run": {"input": {"documents": [{"text": "bulk"}]}},
        "node": {
            "config": {
                "input": {
                    "_contextMode": "node_only",
                    "evidence": {"hits": [{"excerpt": "selected"}]},
                }
            }
        },
        "dependencyOutputs": {"search-other-domain": {"content": "bulk"}},
    }

    assert AgnoAdapter._build_input(request) == {
        "input": {},
        "nodeInput": {"evidence": {"hits": [{"excerpt": "selected"}]}},
        "dependencyOutputs": {},
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


def test_error_status_is_not_treated_as_structured_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeAgent:
        def __init__(self, **_: Any) -> None:
            pass

        async def arun(self, *_: Any, **__: Any) -> RunOutput:
            return RunOutput(
                run_id="agno-run",
                status=RunStatus.error,
                content="Internal Server Error",
            )

    monkeypatch.setattr(adapter_module, "Agent", FakeAgent)
    request = {
        "agent": {
            "role": "worker",
            "instructions": "work",
            "model": "model://general",
            "outputSchema": {"type": "object"},
        },
        "run": {"runId": "run", "input": {}},
        "node": {"key": "node", "config": {}},
        "taskExecutionId": "task",
        "agentInstanceId": "agent",
    }

    with pytest.raises(ValueError, match="model invocation failed: Internal Server Error"):
        asyncio.run(AgnoAdapter(Resolver()).execute(request))


def test_provider_soft_failure_banner_is_not_schema_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeAgent:
        def __init__(self, **_: Any) -> None:
            pass

        async def arun(self, *_: Any, **__: Any) -> RunOutput:
            return RunOutput(
                run_id="agno-run",
                status=RunStatus.completed,
                content="⚠️ 上游通道不可用",
            )

    monkeypatch.setattr(adapter_module, "Agent", FakeAgent)
    request = {
        "agent": {
            "role": "worker",
            "instructions": "work",
            "model": "model://general",
            "outputSchema": {
                "type": "object",
                "required": ["recommendedRoute"],
                "properties": {"recommendedRoute": {"type": "string"}},
            },
        },
        "run": {"runId": "run", "input": {}},
        "node": {"key": "schedule-calibration", "config": {}},
        "taskExecutionId": "task",
        "agentInstanceId": "agent",
    }

    with pytest.raises(ValueError, match="model invocation failed: ⚠️ 上游通道不可用"):
        asyncio.run(AgnoAdapter(Resolver()).execute(request))


def test_json_string_content_is_parsed_before_schema_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeAgent:
        def __init__(self, **_: Any) -> None:
            pass

        async def arun(self, *_: Any, **__: Any) -> RunOutput:
            return RunOutput(
                run_id="agno-run",
                content='{"recommendedRoute":"PRIMARY","reasonCodes":[],'
                '"budgetAllocation":{},"risks":[]}',
            )

    monkeypatch.setattr(adapter_module, "Agent", FakeAgent)
    request = {
        "agent": {
            "role": "worker",
            "instructions": "work",
            "model": "model://general",
            "outputSchema": {
                "type": "object",
                "required": ["recommendedRoute", "reasonCodes", "budgetAllocation", "risks"],
                "properties": {
                    "recommendedRoute": {"type": "string"},
                    "reasonCodes": {"type": "array"},
                    "budgetAllocation": {"type": "object"},
                    "risks": {"type": "array"},
                },
            },
        },
        "run": {"runId": "run", "input": {}},
        "node": {"key": "node", "config": {}},
        "taskExecutionId": "task",
        "agentInstanceId": "agent",
    }

    result = asyncio.run(AgnoAdapter(Resolver()).execute(request))

    assert result["content"]["recommendedRoute"] == "PRIMARY"

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


def test_structured_agent_uses_prompt_backed_json_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeAgent:
        def __init__(self, **values: Any) -> None:
            captured.update(values)

        async def arun(self, *_: Any, **__: Any) -> RunOutput:
            return RunOutput(run_id="run", content={"facts": []})

    monkeypatch.setattr(adapter_module, "Agent", FakeAgent)
    request = {
        "agent": {
            "role": "worker",
            "instructions": "work",
            "model": "model://general",
            "outputSchema": {
                "type": "object",
                "required": ["facts"],
                "properties": {"facts": {"type": "array"}},
            },
        },
        "run": {"runId": "run", "input": {}},
        "node": {"key": "node", "config": {}},
        "taskExecutionId": "task",
        "agentInstanceId": "agent",
    }

    asyncio.run(AgnoAdapter(Resolver()).execute(request))

    assert captured["use_json_mode"] is True


def test_structured_agent_uses_validated_safe_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeAgent:
        def __init__(self, **_: Any) -> None:
            pass

        async def arun(self, *_: Any, **__: Any) -> RunOutput:
            return RunOutput(run_id="run", content={"unexpected": True})

    monkeypatch.setattr(adapter_module, "Agent", FakeAgent)
    request = {
        "agent": {
            "role": "worker",
            "instructions": "work",
            "model": "model://general",
            "outputSchema": {
                "type": "object",
                "required": ["reviewRequired"],
                "properties": {"reviewRequired": {"type": "boolean"}},
                "additionalProperties": False,
            },
            "outputSchemaFallback": {"reviewRequired": True},
        },
        "run": {"runId": "run", "input": {}},
        "node": {"key": "node", "config": {}},
        "taskExecutionId": "task",
        "agentInstanceId": "agent",
    }

    result = asyncio.run(AgnoAdapter(Resolver()).execute(request))

    assert result["content"] == {"reviewRequired": True}
