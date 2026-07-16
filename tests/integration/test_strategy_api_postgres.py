from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_api import create_app
from swarmcore_api.settings import Settings
from swarmcore_compiler import sequential


@pytest.mark.asyncio
async def test_strategy_queries_are_project_scoped_and_versioned() -> None:
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
                "name": f"api-tenant-{tenant_id}",
                "other": other_tenant_id,
                "other_name": f"api-tenant-{other_tenant_id}",
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
                "VALUES (:project, :tenant, 'api-project', '{}', now(), now())"
            ),
            {"project": project_id, "tenant": tenant_id},
        )
    await engine.dispose()

    agent = {"role": "worker", "instructions": "work"}
    spec = sequential("api-strategy", {"one": agent}).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    headers = {"X-Tenant-ID": str(tenant_id)}
    base = f"/v1/projects/{project_id}/strategies"
    with TestClient(create_app(Settings(database_url=database_url))) as client:
        initial_editor_state = {
            "positions": {"one": {"x": 10, "y": 20}},
            "viewport": {"x": 1, "y": 2, "zoom": 0.8},
        }
        created = client.post(
            base,
            headers=headers,
            json={"name": "api-strategy", "spec": spec, "editorState": initial_editor_state},
        )
        assert created.status_code == 201
        handle = created.json()

        listed = client.get(base, headers=headers)
        assert listed.status_code == 200
        assert listed.json()["items"][0]["strategyId"] == handle["strategyId"]

        detail = client.get(f"{base}/{handle['strategyId']}", headers=headers)
        assert detail.status_code == 200

        draft_url = (
            f"{base}/{handle['strategyId']}/drafts/{handle['draftId']}"
        )
        draft = client.get(draft_url, headers=headers)
        assert draft.status_code == 200
        assert draft.headers["etag"] == '"1"'
        assert draft.json()["editorState"] == initial_editor_state

        conflict = client.put(
            draft_url,
            headers={**headers, "If-Match": '"0"'},
            json={"spec": spec},
        )
        assert conflict.status_code == 409

        published = client.post(
            f"{base}/{handle['strategyId']}/publish",
            headers=headers,
            json={"draftId": handle["draftId"]},
        )
        assert published.status_code == 200
        version_id = published.json()["strategyVersionId"]
        initial_plan_hash = published.json()["planHash"]

        moved_editor_state = {
            "positions": {"one": {"x": 900, "y": 700}},
            "viewport": {"x": -50, "y": 25, "zoom": 1.25},
        }
        moved = client.put(
            draft_url,
            headers={**headers, "If-Match": '"1"'},
            json={"spec": spec, "editorState": moved_editor_state},
        )
        assert moved.status_code == 200
        assert moved.headers["etag"] == '"2"'
        assert moved.json()["editorState"] == moved_editor_state
        refreshed = client.get(draft_url, headers=headers)
        assert refreshed.json()["editorState"] == moved_editor_state

        republished = client.post(
            f"{base}/{handle['strategyId']}/publish",
            headers=headers,
            json={"draftId": handle["draftId"]},
        )
        assert republished.status_code == 200
        assert republished.json()["planHash"] == initial_plan_hash

        changed_spec = spec | {
            "spec": spec["spec"]
            | {
                "agents": spec["spec"]["agents"]
                | {"one": {"role": "worker", "instructions": "changed semantics"}}
            }
        }
        changed = client.put(
            draft_url,
            headers={**headers, "If-Match": '"2"'},
            json={"spec": changed_spec, "editorState": moved_editor_state},
        )
        assert changed.status_code == 200
        changed_publish = client.post(
            f"{base}/{handle['strategyId']}/publish",
            headers=headers,
            json={"draftId": handle["draftId"]},
        )
        assert changed_publish.status_code == 200
        assert changed_publish.json()["planHash"] != initial_plan_hash

        versions = client.get(f"{base}/{handle['strategyId']}/versions", headers=headers)
        assert versions.json()["total"] == 3
        version = client.get(
            f"{base}/{handle['strategyId']}/versions/{version_id}", headers=headers
        )
        assert version.status_code == 200
        assert version.json()["planHash"] == published.json()["planHash"]

        isolated = client.get(
            f"{base}/{handle['strategyId']}",
            headers={"X-Tenant-ID": str(other_tenant_id)},
        )
        assert isolated.status_code == 404
        assert isolated.json()["code"] == "NOT_FOUND"
