from fastapi.testclient import TestClient
from swarmcore_api import create_app
from swarmcore_api.settings import Settings

from .test_spec import VALID_SPEC


def test_compile_endpoint_returns_immutable_plan() -> None:
    import yaml

    app = create_app(Settings())
    with TestClient(app) as client:
        response = client.post(
            "/v1/projects/00000000-0000-0000-0000-000000000002/strategies/compile",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
            json={"spec": yaml.safe_load(VALID_SPEC)},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert len(payload["plan"]["plan_hash"]) == 64


def test_compile_endpoint_returns_structured_diagnostics() -> None:
    import yaml

    spec = yaml.safe_load(VALID_SPEC)
    spec["spec"]["graph"]["nodes"]["final"] = {
        "type": "emit",
        "event": "not-supported",
    }
    with TestClient(create_app(Settings())) as client:
        response = client.post(
            "/v1/projects/00000000-0000-0000-0000-000000000002/strategies/compile",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
            json={"spec": spec},
        )
    assert response.status_code == 200
    assert response.json()["diagnostics"] == [
        {
            "severity": "error",
            "code": "UNSUPPORTED_NODE_TYPE",
            "path": "$.spec.graph.nodes.final.type",
            "message": "node type 'emit' is not supported by the Phase 1 runtime",
        }
    ]
