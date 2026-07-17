from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_api import create_app
from swarmcore_api.settings import Settings


@pytest.mark.asyncio
async def test_project_configurations_are_persisted_and_project_scoped() -> None:
    database_url = os.getenv("SWARMCORE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("SWARMCORE_TEST_DATABASE_URL is not configured")

    tenant_id, other_tenant_id, project_id = uuid4(), uuid4(), uuid4()
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO tenants (id, name, status, created_at, updated_at) "
                "VALUES (:tenant, :name, 'ACTIVE', now(), now()), "
                "(:other, :other_name, 'ACTIVE', now(), now())"
            ),
            {
                "tenant": tenant_id,
                "name": f"configuration-tenant-{tenant_id}",
                "other": other_tenant_id,
                "other_name": f"configuration-tenant-{other_tenant_id}",
            },
        )
        await connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"),
            {"tenant": str(tenant_id)},
        )
        await connection.execute(
            text(
                "INSERT INTO projects "
                "(id, tenant_id, name, settings, created_at, updated_at) "
                "VALUES (:project, :tenant, 'configuration-project', '{}', now(), now())"
            ),
            {"project": project_id, "tenant": tenant_id},
        )
    await engine.dispose()

    headers = {"X-Tenant-ID": str(tenant_id)}
    base = f"/v1/projects/{project_id}/configurations/model"
    payload = {
        "name": "生产模型",
        "sourceRef": "model://general@1",
        "configuration": {"spec": {"defaults": {"model": "model://general@1"}}},
    }
    with TestClient(
        create_app(Settings(database_url=database_url, telemetry_enabled=False))
    ) as client:
        created = client.post(base, headers=headers, json=payload)
        assert created.status_code == 201
        configuration_id = created.json()["configurationId"]

        listed = client.get(base, headers=headers)
        assert listed.status_code == 200
        assert listed.json()["items"][0]["name"] == "生产模型"

        duplicate = client.post(base, headers=headers, json=payload)
        assert duplicate.status_code == 409

        updated_payload = {
            **payload,
            "name": "生产模型-更新",
            "sourceRef": "model://fake-deterministic@1",
            "configuration": {
                "spec": {"defaults": {"model": "model://fake-deterministic@1"}}
            },
        }
        updated = client.put(
            f"{base}/{configuration_id}", headers=headers, json=updated_payload
        )
        assert updated.status_code == 200
        assert updated.json()["configurationId"] == configuration_id
        assert updated.json()["name"] == "生产模型-更新"
        assert updated.json()["revision"] == 2
        assert client.get(base, headers=headers).json()["items"][0]["sourceRef"] == (
            "model://fake-deterministic@1"
        )
        audit = client.get(
            f"/v1/projects/{project_id}/audit-logs?limit=20", headers=headers
        )
        assert audit.status_code == 200
        assert "configuration.update" in {
            item["action"] for item in audit.json()["items"]
        }

        isolated = client.get(base, headers={"X-Tenant-ID": str(other_tenant_id)})
        assert isolated.status_code == 200
        assert isolated.json()["total"] == 0
        isolated_update = client.put(
            f"{base}/{configuration_id}",
            headers={"X-Tenant-ID": str(other_tenant_id)},
            json=updated_payload,
        )
        assert isolated_update.status_code == 404

        deleted = client.delete(f"{base}/{configuration_id}", headers=headers)
        assert deleted.status_code == 204
        assert client.get(base, headers=headers).json()["total"] == 0
