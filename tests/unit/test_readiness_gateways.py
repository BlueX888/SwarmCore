import json
from io import BytesIO
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from swarmcore_governance import InMemorySecretProvider
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
    assert probes == [("https://gateway.example", 300, "provider-test-key")]
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


def test_direct_provider_sse_preserves_streamed_tool_calls() -> None:
    raw = b"\n\n".join(
        (
            b'data: {"id":"answer-2","model":"test-model","choices":['
            b'{"index":0,"delta":{"role":"assistant","tool_calls":[{"index":0,'
            b'"id":"call-1","type":"function","function":{"name":"evidence_",'
            b'"arguments":"{\\"domain\\":"}}]}}]}',
            b'data: {"id":"answer-2","model":"test-model","choices":['
            b'{"index":0,"delta":{"tool_calls":[{"index":0,"function":'
            b'{"name":"search","arguments":"\\"contract\\"}"}}]},'
            b'"finish_reason":"tool_calls"}]}',
            b"data: [DONE]",
        )
    )

    result = model_gateway._decode_openai_response(raw)

    assert result["choices"] == [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "evidence_search",
                            "arguments": '{"domain":"contract"}',
                        },
                    }
                ],
            },
            "finish_reason": "tool_calls",
        }
    ]


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


def test_litellm_includes_provider_error_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def urlopen(request: Request, *, timeout: float) -> Any:
        del timeout
        raise HTTPError(
            request.full_url,
            400,
            "Bad Request",
            {},
            BytesIO(b'{"error":{"message":"unsupported response_format"}}'),
        )

    monkeypatch.setattr(model_gateway, "urlopen", urlopen)

    with pytest.raises(
        RuntimeError,
        match="provider HTTP 400: unsupported response_format",
    ):
        model_gateway._litellm(
            "https://models.example",
            "test-key",
            "provider/model",
            model_gateway.InvokeBody(
                capabilityToken="unused",
                messages=[{"role": "user", "content": "hi"}],
                maxTokens=16,
            ),
            30,
        )


def test_litellm_retries_without_structured_output_for_legacy_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads: list[dict[str, Any]] = []

    def urlopen(request: Request, *, timeout: float) -> Any:
        del timeout
        payloads.append(json.loads(cast(bytes, request.data)))
        if len(payloads) == 1:
            raise HTTPError(
                request.full_url,
                400,
                "Bad Request",
                {},
                BytesIO(b'{"error":{"message":"json_object is not supported"}}'),
            )
        return BytesIO(
            json.dumps(
                {
                    "id": "completion-1",
                    "model": "legacy-model",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": '{"answer":"ok"}'},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 4},
                }
            ).encode()
        )

    monkeypatch.setattr(model_gateway, "urlopen", urlopen)

    result = model_gateway._litellm(
        "https://models.example",
        "test-key",
        "legacy-model",
        model_gateway.InvokeBody(
            capabilityToken="unused",
            messages=[{"role": "user", "content": "return json"}],
            maxTokens=32,
            parameters={"response_format": {"type": "json_object"}},
        ),
        30,
    )

    assert result["choices"][0]["message"]["content"] == '{"answer":"ok"}'
    assert payloads[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in payloads[1]


@pytest.mark.asyncio
async def test_runtime_provider_falls_back_when_vault_lease_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenSecrets:
        def lease(self, _secret_ref: str) -> Any:
            raise model_gateway.SecretError("Vault read failed: HTTPError")

    async def saved(*_args: Any, **_kwargs: Any) -> tuple[str, str, str, str]:
        return (
            "https://gateway.example/v1",
            "kimi-k2.5",
            "secret://projects/demo/models/general",
            "kimi-k2.5",
        )

    monkeypatch.setattr(model_gateway, "_saved_runtime_provider", saved)
    result = await model_gateway._runtime_provider_configuration(
        object(),  # type: ignore[arg-type]
        BrokenSecrets(),  # type: ignore[arg-type]
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        project_id=UUID("00000000-0000-0000-0000-000000000002"),
        logical_model="model://general",
    )
    assert result is None


@pytest.mark.asyncio
async def test_model_api_key_is_configured_only_when_vault_value_is_readable() -> None:
    secret_ref = "secret://projects/demo/models/general"
    configured = InMemorySecretProvider({secret_ref: {"apiKey": "stored-key"}})
    empty = InMemorySecretProvider({secret_ref: {"apiKey": ""}})
    missing = InMemorySecretProvider({})

    assert await model_gateway._api_key_configured(configured, secret_ref) is True
    assert await model_gateway._read_api_key(configured, secret_ref) == "stored-key"
    assert await model_gateway._api_key_configured(empty, secret_ref) is False
    assert await model_gateway._read_api_key(empty, secret_ref) is None
    assert await model_gateway._api_key_configured(missing, secret_ref) is False
    assert await model_gateway._api_key_configured(None, secret_ref) is False


def test_provider_soft_failure_banner_is_rejected() -> None:
    with pytest.raises(ValueError, match="model provider soft failure"):
        model_gateway._assert_usable_completion(
            {
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "⚠️ 上游通道不可用"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        )


def test_provider_structured_sse_error_is_rejected() -> None:
    raw = (
        b'data: {"id":"err-1","model":"DeepSeek-V4-Flash","choices":[{"index":0,'
        b'"delta":{"role":"assistant","content":"banner"}}],'
        b'"error":{"code":"UPSTREAM_UNAVAILABLE","message":"upstream unavailable",'
        b'"hint":"linked API key disabled"}}\n\n'
        b"data: [DONE]\n\n"
    )

    with pytest.raises(ValueError, match="linked API key disabled"):
        model_gateway._decode_openai_response(raw)


def test_provider_reasoning_only_completion_is_accepted() -> None:
    model_gateway._assert_usable_completion(
        {
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "reasoning_content": "User asked for OK; prepare reply.",
                    },
                    "finish_reason": "length",
                }
            ]
        }
    )


def test_provider_empty_content_without_tools_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty content"):
        model_gateway._assert_usable_completion(
            {
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "   "},
                        "finish_reason": "stop",
                    }
                ]
            }
        )


def test_provider_tool_calls_without_content_are_accepted() -> None:
    model_gateway._assert_usable_completion(
        {
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {"name": "lookup", "arguments": "{}"},
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }
    )
