from fastapi.testclient import TestClient
from swarmcore_worker_agent.fake import DeterministicFakeAgentAdapter
from swarmcore_worker_agent.main import create_readiness_app


def test_agent_readiness_reports_the_live_adapter_without_credentials() -> None:
    with TestClient(create_readiness_app(DeterministicFakeAgentAdapter())) as client:
        response = client.get("/internal/v1/readiness")
    assert response.status_code == 200
    assert response.json() == {
        "adapters": [{"runtime": "fake-deterministic", "healthy": True}]
    }
    assert "secret" not in response.text.lower()
