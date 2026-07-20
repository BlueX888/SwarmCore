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
