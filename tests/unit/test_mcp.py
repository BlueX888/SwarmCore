from fastapi.testclient import TestClient
from swarmcore_api import create_app
from swarmcore_api.settings import Settings
from swarmcore_application import (
    AgentRuntimeStatus,
    CapabilityCenterService,
    CapabilityReadinessService,
    ModelRuntimeStatus,
    ToolRuntimeStatus,
)
from swarmcore_registry import builtin_registry

from .test_spec import VALID_SPEC

HEADERS = {
    "X-Tenant-ID": "00000000-0000-0000-0000-000000000001",
    "Authorization": "Bearer test",
}


class ReadyCapabilityRuntime:
    async def inspect_tool(self, **_: object) -> ToolRuntimeStatus:
        return ToolRuntimeStatus(True, True)

    async def inspect_model(self, **_: object) -> ModelRuntimeStatus:
        return ModelRuntimeStatus(True, True, True)

    async def inspect_agent(self, **_: object) -> AgentRuntimeStatus:
        return AgentRuntimeStatus(True)


def _ready_capability_center() -> CapabilityCenterService:
    runtime = ReadyCapabilityRuntime()
    registry = builtin_registry()
    return CapabilityCenterService(
        registry,
        CapabilityReadinessService(tools=runtime, models=runtime, agents=runtime),
    )


def test_mcp_initialize_negotiates_stable_protocol() -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.post(
            "/mcp",
            headers=HEADERS,
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
    assert response.status_code == 200
    assert response.json()["result"]["protocolVersion"] == "2025-11-25"


def test_mcp_lists_default_tools() -> None:
    with TestClient(create_app(Settings())) as client:
        response = client.post(
            "/mcp",
            headers={**HEADERS, "Mcp-Protocol-Version": "2025-11-25"},
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
    names = {item["name"] for item in response.json()["result"]["tools"]}
    assert names == {
        "swarm.capabilities.get",
        "swarm.capability-center.list",
        "swarm.capability.run",
        "swarm.strategy.validate",
        "swarm.strategy.compile",
        "swarm.run.create",
        "swarm.run.status",
        "swarm.run.result",
        "swarm.run.control",
        "list_capability_packs",
        "create_work_item",
        "execute_work_item",
        "get_evaluation",
        "list_findings",
        "act_on_finding",
        "get_report",
    }


def test_rest_and_mcp_return_the_same_capability_catalog() -> None:
    project_id = "00000000-0000-0000-0000-000000000002"
    with TestClient(create_app(Settings())) as client:
        rest = client.get(
            f"/v1/projects/{project_id}/capabilities",
            headers={"X-Tenant-ID": HEADERS["X-Tenant-ID"]},
        )
        mcp = client.post(
            "/mcp",
            headers={**HEADERS, "Mcp-Protocol-Version": "2025-11-25"},
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "swarm.capabilities.get",
                    "arguments": {"projectId": project_id},
                },
            },
        )
    assert rest.status_code == 200
    assert mcp.status_code == 200
    catalog = rest.json()
    assert mcp.json()["result"]["structuredContent"] == catalog
    assert {item["type"] for item in catalog["nodeTypes"]} == {
        "agent",
        "approval",
        "input",
        "join",
        "loop",
        "parallel",
        "reducer",
        "router",
        "tool",
    }
    assert {item["ref"] for item in catalog["tools"]} == {
        "tool://contract/cross-file-consistency@1",
        "tool://document/read@1",
        "tool://publish-report@1",
        "tool://report/render@1",
        "tool://rules/evaluate@1",
        "tool://search@1",
        "tool://workbench/record-evaluation@1",
    }


def test_rest_and_mcp_share_capability_center_readiness_projection() -> None:
    project_id = "00000000-0000-0000-0000-000000000002"
    settings = Settings(capability_center_v2=True)
    with TestClient(create_app(settings)) as client:
        client.app.state.capability_center = _ready_capability_center()
        rest = client.get(
            f"/v1/projects/{project_id}/capability-center",
            headers={"X-Tenant-ID": HEADERS["X-Tenant-ID"]},
        )
        mcp = client.post(
            "/mcp",
            headers={**HEADERS, "Mcp-Protocol-Version": "2025-11-25"},
            json={
                "jsonrpc": "2.0",
                "id": 30,
                "method": "tools/call",
                "params": {
                    "name": "swarm.capability-center.list",
                    "arguments": {"projectId": project_id},
                },
            },
        )
    assert rest.status_code == 200
    assert mcp.status_code == 200
    assert mcp.json()["result"]["structuredContent"] == rest.json()


def test_capability_center_routes_and_mcp_tools_are_hidden_when_disabled() -> None:
    project_id = "00000000-0000-0000-0000-000000000002"
    with TestClient(create_app(Settings(capability_center_v2=False))) as client:
        rest = client.get(
            f"/v1/projects/{project_id}/capability-center",
            headers={"X-Tenant-ID": HEADERS["X-Tenant-ID"]},
        )
        listed = client.post(
            "/mcp",
            headers={**HEADERS, "Mcp-Protocol-Version": "2025-11-25"},
            json={"jsonrpc": "2.0", "id": 31, "method": "tools/list", "params": {}},
        )
    assert rest.status_code == 404
    names = {item["name"] for item in listed.json()["result"]["tools"]}
    assert "swarm.capability-center.list" not in names
    assert "swarm.capability.run" not in names


def test_rest_and_mcp_compile_have_identical_plan_and_diagnostics() -> None:
    import yaml

    project_id = "00000000-0000-0000-0000-000000000002"
    spec = yaml.safe_load(VALID_SPEC)
    with TestClient(create_app(Settings())) as client:
        rest = client.post(
            f"/v1/projects/{project_id}/strategies/compile",
            headers={"X-Tenant-ID": HEADERS["X-Tenant-ID"]},
            json={"spec": spec},
        ).json()
        mcp = client.post(
            "/mcp",
            headers={**HEADERS, "Mcp-Protocol-Version": "2025-11-25"},
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "swarm.strategy.compile",
                    "arguments": {"projectId": project_id, "spec": spec},
                },
            },
        ).json()["result"]["structuredContent"]
    assert mcp["plan"] == rest["plan"]
    assert mcp["diagnostics"] == rest["diagnostics"]
    assert mcp["planHash"] == rest["plan"]["plan_hash"]
