from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_api import create_app
from swarmcore_api.settings import Settings
from swarmcore_application import (
    AgentRuntimeStatus,
    CapabilityCenterService,
    CapabilityPresetService,
    CapabilityReadinessService,
    ModelRuntimeStatus,
    ToolRuntimeStatus,
)
from swarmcore_registry import builtin_registry


class ReadyRuntime:
    async def inspect_tool(self, **_: object) -> ToolRuntimeStatus:
        return ToolRuntimeStatus(True, True)

    async def inspect_model(self, **_: object) -> ModelRuntimeStatus:
        return ModelRuntimeStatus(True, True, True)

    async def inspect_agent(self, **_: object) -> AgentRuntimeStatus:
        return AgentRuntimeStatus(True)


@pytest.mark.asyncio
async def test_rest_and_mcp_direct_capability_run_share_standard_run_service() -> None:
    database_url = os.getenv("SWARMCORE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("SWARMCORE_TEST_DATABASE_URL is not configured")
    tenant_id, project_id = uuid4(), uuid4()
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO tenants (id, name, status, created_at, updated_at) "
                "VALUES (:tenant, :name, 'ACTIVE', now(), now())"
            ),
            {"tenant": tenant_id, "name": f"capability-center-{tenant_id}"},
        )
        await connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"),
            {"tenant": str(tenant_id)},
        )
        await connection.execute(
            text(
                "INSERT INTO projects "
                "(id, tenant_id, name, settings, created_at, updated_at) "
                "VALUES (:project, :tenant, 'capability-center', '{}', now(), now())"
            ),
            {"project": project_id, "tenant": tenant_id},
        )
    await engine.dispose()

    runtime = ReadyRuntime()
    registry = builtin_registry()
    center = CapabilityCenterService(
        registry,
        CapabilityReadinessService(tools=runtime, models=runtime, agents=runtime),
    )
    presets = CapabilityPresetService(center)
    center.attach_preset_resolver(presets)
    settings = Settings(
        database_url=database_url,
        telemetry_enabled=False,
        capability_center_v2=True,
    )
    headers = {"X-Tenant-ID": str(tenant_id)}
    body = {
        "capabilityRef": "tool://search@1",
        "input": {"query": "swarm"},
    }
    with TestClient(create_app(settings)) as client:
        client.app.state.capability_center = center
        client.app.state.capability_presets = presets
        rest = client.post(
            f"/v1/projects/{project_id}/capability-runs",
            headers={**headers, "Idempotency-Key": "direct-search"},
            json=body,
        )
        mcp = client.post(
            "/mcp",
            headers={
                **headers,
                "Authorization": "Bearer test",
                "Mcp-Protocol-Version": "2025-11-25",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "swarm.capability.run",
                    "arguments": {
                        "projectId": str(project_id),
                        **body,
                        "idempotencyKey": "direct-search",
                    },
                },
            },
        )
        runs = client.get(f"/v1/projects/{project_id}/runs", headers=headers)

        created_preset = client.post(
            f"/v1/projects/{project_id}/presets",
            headers=headers,
            json={
                "name": "演示预设",
                "capabilityRef": "tool://search@1",
                "parameters": {"query": "from-preset"},
            },
        )
        preset_id = created_preset.json()["presetId"]
        legacy = client.get(
            f"/v1/projects/{project_id}/configurations/tool", headers=headers
        )
        preset_run = client.post(
            f"/v1/projects/{project_id}/capability-runs",
            headers={**headers, "Idempotency-Key": "preset-search"},
            json={
                "capabilityRef": "tool://search@1",
                "presetId": preset_id,
                "input": {},
            },
        )
        secret = client.post(
            f"/v1/projects/{project_id}/presets",
            headers=headers,
            json={
                "name": "非法预设",
                "capabilityRef": "tool://search@1",
                "parameters": {"apiKey": "plain-text-secret"},
            },
        )
        created_agent = client.post(
            f"/v1/projects/{project_id}/configurations/agent",
            headers=headers,
            json={
                "name": "项目研究员",
                "sourceRef": "inline/agno",
                "configuration": {
                    "spec": {
                        "agents": {
                            "researcher": {
                                "role": "project-researcher",
                                "instructions": "Research the supplied task.",
                                "model": "model://general@1",
                                "tools": ["tool://search@1"],
                            }
                        },
                        "graph": {
                            "entrypoint": "researcher",
                            "nodes": {
                                "researcher": {
                                    "type": "agent",
                                    "agent": "researcher",
                                    "dependsOn": [],
                                }
                            },
                        },
                    }
                },
            },
        )
        center_catalog = client.get(
            f"/v1/projects/{project_id}/capability-center", headers=headers
        )
        project_agent = next(
            item
            for item in center_catalog.json()["items"]
            if item["name"] == "项目研究员"
        )
        project_agent_run = client.post(
            f"/v1/projects/{project_id}/capability-runs",
            headers={**headers, "Idempotency-Key": "project-agent-run"},
            json={"capabilityRef": project_agent["ref"], "input": {"query": "swarm"}},
        )
        mcp_catalog = client.post(
            "/mcp",
            headers={
                **headers,
                "Authorization": "Bearer test",
                "Mcp-Protocol-Version": "2025-11-25",
            },
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "swarm.capability-center.list",
                    "arguments": {"projectId": str(project_id)},
                },
            },
        )

    assert rest.status_code == 202, rest.text
    assert mcp.status_code == 200, mcp.text
    mcp_handle = mcp.json()["result"]["structuredContent"]
    assert mcp.json()["result"]["isError"] is False
    assert mcp_handle == rest.json()
    assert runs.status_code == 200
    assert runs.json()["total"] == 1
    assert created_preset.status_code == 201, created_preset.text
    assert created_preset.json()["readiness"]["status"] == "READY"
    assert legacy.status_code == 200
    assert legacy.json()["items"][0]["configurationId"] == preset_id
    assert preset_run.status_code == 202, preset_run.text
    assert secret.status_code == 422
    assert "forbidden secret field" in secret.text
    assert created_agent.status_code == 201, created_agent.text
    assert center_catalog.status_code == 200, center_catalog.text
    assert project_agent["ref"].startswith("agent://project/")
    assert project_agent["source"] == "project"
    assert project_agent["readiness"]["status"] == "READY"
    assert project_agent_run.status_code == 202, project_agent_run.text
    assert mcp_catalog.status_code == 200, mcp_catalog.text
    mcp_items = mcp_catalog.json()["result"]["structuredContent"]["items"]
    assert any(item["ref"] == project_agent["ref"] for item in mcp_items)
