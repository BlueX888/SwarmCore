from fastapi.testclient import TestClient
from swarmcore_api import create_app
from swarmcore_api.settings import Settings

HEADERS = {
    "X-Tenant-ID": "00000000-0000-0000-0000-000000000001",
    "Authorization": "Bearer test",
}


def test_mcp_initialize_negotiates_stable_protocol() -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.post(
            "/mcp",
            headers=HEADERS,
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
    assert response.status_code == 200
    assert response.json()["result"]["protocolVersion"] == "2025-11-25"


def test_mcp_lists_phase_one_run_tools() -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.post(
            "/mcp",
            headers={**HEADERS, "Mcp-Protocol-Version": "2025-11-25"},
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
    names = {item["name"] for item in response.json()["result"]["tools"]}
    assert {"swarm.run.start", "swarm.run.get", "swarm.run.cancel"} <= names
