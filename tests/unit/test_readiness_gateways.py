import json
from typing import cast
from urllib.error import URLError
from urllib.request import Request

import pytest
from fastapi.testclient import TestClient
from swarmcore_model_gateway import main as model_gateway
from swarmcore_tool_gateway_api.main import Settings as ToolGatewaySettings
from swarmcore_tool_gateway_api.main import create_app as create_tool_gateway


def test_tool_gateway_readiness_reports_registered_executors() -> None:
    app = create_tool_gateway(ToolGatewaySettings(telemetry_enabled=False))
    with TestClient(app) as client:
        response = client.get("/internal/v1/readiness")
    assert response.status_code == 200
    tools = {item["ref"]: item for item in response.json()["tools"]}
    assert tools["tool://search@1"]["executorRegistered"] is True
    assert tools["tool://contract/cross-file-consistency@1"]["executorRegistered"] is True
    assert all(item["executorRegistered"] for item in tools.values())


def test_model_gateway_readiness_reports_routes_without_exposing_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(model_gateway, "_probe_litellm", lambda *_: True)
    app = model_gateway.create_app(
        model_gateway.Settings(_env_file=None, telemetry_enabled=False)
    )
    with TestClient(app) as client:
        response = client.get("/internal/v1/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["models"]
    assert all(item["routeRegistered"] for item in payload["models"])
    assert all(item["secretAvailable"] for item in payload["models"])
    assert "apiKey" not in response.text
    assert "capability-secret" not in response.text


def test_model_gateway_readiness_skips_probes_when_no_routes_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probes: list[object] = []

    def probe(*args: object) -> bool:
        probes.append(args)
        return True

    monkeypatch.setattr(model_gateway, "_probe_litellm", probe)
    app = model_gateway.create_app(
        model_gateway.Settings(
            _env_file=None,
            telemetry_enabled=False,
            model_routes={},
        )
    )
    with TestClient(app) as client:
        response = client.get("/internal/v1/readiness")
    assert response.status_code == 200
    assert response.json() == {"models": []}
    assert probes == []


def test_model_gateway_readiness_supports_openai_compatible_model_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[Request] = []

    class Response:
        status = 200

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

    def urlopen(request: Request, *, timeout: float) -> Response:
        del timeout
        requests.append(request)
        if len(requests) == 1:
            raise URLError("LiteLLM health endpoint is unavailable")
        return Response()

    monkeypatch.setattr(model_gateway, "urlopen", urlopen)

    assert model_gateway._probe_litellm("https://models.example", 2, "test-key") is True
    assert requests[1].full_url == "https://models.example/v1/models"
    assert requests[1].headers["Authorization"] == "Bearer test-key"


def test_model_gateway_readiness_uses_direct_provider_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probes: list[tuple[str, float, str]] = []

    def probe(url: str, timeout: float, api_key: str) -> bool:
        probes.append((url, timeout, api_key))
        return True

    monkeypatch.setattr(model_gateway, "_probe_litellm", probe)
    app = model_gateway.create_app(
        model_gateway.Settings(
            _env_file=None,
            telemetry_enabled=False,
            model_provider_url="https://gateway.example/v1/",
            model_provider_api_key="provider-test-key",
        )
    )

    with TestClient(app) as client:
        response = client.get("/internal/v1/readiness")

    assert response.status_code == 200
    assert probes == [("https://gateway.example", 120, "provider-test-key")]
    assert "provider-test-key" not in response.text


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://gateway.example/v1", "https://gateway.example"),
        ("https://gateway.example/v1/", "https://gateway.example"),
        ("https://gateway.example/openai", "https://gateway.example/openai"),
    ],
)
def test_provider_root_normalizes_openai_compatible_base_url(
    url: str, expected: str
) -> None:
    assert model_gateway._provider_root(url) == expected


def test_direct_provider_sse_is_normalized_to_openai_completion() -> None:
    raw = b"\n\n".join(
        (
            b'data: {"id":"answer-1","model":"test-model","choices":['
            b'{"index":0,"delta":{"role":"assistant","reasoning_content":"think "}}]}',
            b'data: {"id":"answer-1","model":"test-model","choices":['
            b'{"index":0,"delta":{"content":"{\\"answer\\":\\"ok\\"}"}}]}',
            b"data: [DONE]",
            b'data: {"id":"answer-1","model":"test-model","choices":['
            b'{"index":0,"delta":{"content":""},"finish_reason":"stop"}],'
            b'"usage":{"prompt_tokens":5,"completion_tokens":7,"total_tokens":12}}',
        )
    )

    result = model_gateway._decode_openai_response(raw)

    assert result["id"] == "answer-1"
    assert result["choices"] == [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": '{"answer":"ok"}',
                "reasoning_content": "think ",
            },
            "finish_reason": "stop",
        }
    ]
    assert result["usage"] == {
        "prompt_tokens": 5,
        "completion_tokens": 7,
        "total_tokens": 12,
    }


def test_direct_provider_maps_developer_messages_to_legacy_system_role() -> None:
    messages = [
        {"role": "developer", "content": "Follow the schema."},
        {"role": "user", "content": "Evaluate this contract."},
    ]

    assert model_gateway._provider_compatible_messages(messages) == [
        {"role": "system", "content": "Follow the schema."},
        {"role": "user", "content": "Evaluate this contract."},
    ]
    assert messages[0]["role"] == "developer"


def test_direct_provider_wraps_bare_output_schema_as_response_format() -> None:
    schema = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"type": "string"}},
    }

    result = model_gateway._provider_compatible_parameters(
        {"response_format": schema, "temperature": 0}
    )

    assert result == {
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_output",
                "strict": True,
                "schema": schema,
            },
        },
        "temperature": 0,
    }


def test_portal_capability_invoke_url_is_detected() -> None:
    url = (
        "http://192.168.10.20:8787/api/v1/openapi/capabilities/"
        "model.5wqnbx75.multimodal/invoke"
    )
    assert model_gateway._is_portal_capability_invoke_url(url) is True
    assert model_gateway._provider_root(url) == url.rstrip("/")
    assert (
        model_gateway._portal_health_url(url)
        == "http://192.168.10.20:8787/api/v1/health"
    )
    assert model_gateway._is_portal_capability_invoke_url("https://gateway.example/v1") is False


def test_portal_capability_probe_uses_api_health(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[Request] = []

    class Response:
        status = 200

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

    def urlopen(request: Request, *, timeout: float) -> Response:
        del timeout
        requests.append(request)
        return Response()

    monkeypatch.setattr(model_gateway, "urlopen", urlopen)
    url = (
        "http://192.168.10.20:8787/api/v1/openapi/capabilities/"
        "model.example.multimodal/invoke"
    )
    assert model_gateway._probe_litellm(url, 2, "portal-key") is True
    assert requests[0].full_url == "http://192.168.10.20:8787/api/v1/health"
    assert requests[0].headers["Authorization"] == "Bearer portal-key"


def test_portal_capability_response_is_normalized_to_openai_completion() -> None:
    raw = (
        b'{"code":200,"msg":"success","data":{"output":{"message":{"role":"assistant",'
        b'"content":"Hello!","reasoning_content":"greet"},"model":"kimi-k2.5",'
        b'"finishReason":"stop"},"usage":{"inputTokens":8,"outputTokens":3,"cost":0.0001},'
        b'"trace":{"requestId":"req_demo"}}}'
    )
    result = model_gateway._decode_portal_response(raw, fallback_model="kimi-k2.5")
    assert result["id"] == "req_demo"
    assert result["choices"] == [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello!",
                "reasoning_content": "greet",
            },
            "finish_reason": "stop",
        }
    ]
    assert result["usage"] == {
        "prompt_tokens": 8,
        "completion_tokens": 3,
        "total_tokens": 11,
    }
    assert result["response_cost"] == 0.0001


def test_portal_capability_invoke_posts_input_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self, _size: int) -> bytes:
            return (
                b'{"code":200,"msg":"success","data":{"output":{"message":'
                b'{"role":"assistant","content":"ok"},"model":"kimi-k2.5",'
                b'"finishReason":"stop"},"usage":{"inputTokens":1,"outputTokens":1,'
                b'"cost":0},"trace":{"requestId":"req_1"}}}'
            )

    def urlopen(request: Request, *, timeout: float) -> Response:
        del timeout
        captured["url"] = request.full_url
        captured["headers"] = dict(request.headers)
        captured["body"] = request.data
        return Response()

    monkeypatch.setattr(model_gateway, "urlopen", urlopen)
    url = (
        "http://192.168.10.20:8787/api/v1/openapi/capabilities/"
        "model.example.multimodal/invoke"
    )
    result = model_gateway._litellm(
        url,
        "portal-key",
        "kimi-k2.5",
        model_gateway.InvokeBody(
            capabilityToken="unused",
            messages=[{"role": "user", "content": "hi"}],
            maxTokens=16,
        ),
        30,
    )
    assert captured["url"] == url
    assert captured["headers"]["Authorization"] == "Bearer portal-key"
    assert json.loads(cast(bytes, captured["body"])) == {
        "input": {"messages": [{"role": "user", "content": "hi"}]},
        "stream": False,
    }
    assert result["choices"][0]["message"]["content"] == "ok"
