from __future__ import annotations

import json
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_api import create_app
from swarmcore_api.settings import Settings


@pytest.mark.asyncio
async def test_project_overview_is_project_scoped_and_lightweight() -> None:
    database_url = os.getenv("SWARMCORE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("SWARMCORE_TEST_DATABASE_URL is not configured")

    tenant_id, other_tenant_id = uuid4(), uuid4()
    project_id, other_project_id = uuid4(), uuid4()
    strategy_id, other_strategy_id = uuid4(), uuid4()
    version_id, other_version_id = uuid4(), uuid4()
    running_id, failed_id, other_running_id = uuid4(), uuid4(), uuid4()
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO tenants (id, name, status, created_at, updated_at) VALUES "
                "(:tenant, :tenant_name, 'ACTIVE', now(), now()), "
                "(:other_tenant, :other_tenant_name, 'ACTIVE', now(), now())"
            ),
            {
                "tenant": tenant_id,
                "tenant_name": f"overview-{tenant_id}",
                "other_tenant": other_tenant_id,
                "other_tenant_name": f"overview-{other_tenant_id}",
            },
        )
        await connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"),
            {"tenant": str(tenant_id)},
        )
        await connection.execute(
            text(
                "INSERT INTO projects "
                "(id, tenant_id, name, settings, created_at, updated_at) VALUES "
                "(:project, :tenant, 'overview-primary', '{}', now(), now()), "
                "(:other_project, :tenant, 'overview-other', '{}', now(), now())"
            ),
            {
                "tenant": tenant_id,
                "project": project_id,
                "other_project": other_project_id,
            },
        )
        await connection.execute(
            text(
                "INSERT INTO strategies "
                "(id, tenant_id, project_id, name, lifecycle, created_at, updated_at) VALUES "
                "(:strategy, :tenant, :project, :strategy_name, 'ACTIVE', now(), now()), "
                "(:other_strategy, :tenant, :other_project, :other_strategy_name, "
                "'ACTIVE', now(), now())"
            ),
            {
                "tenant": tenant_id,
                "project": project_id,
                "other_project": other_project_id,
                "strategy": strategy_id,
                "strategy_name": f"overview-direct-{strategy_id}",
                "other_strategy": other_strategy_id,
                "other_strategy_name": f"overview-direct-{other_strategy_id}",
            },
        )
        await connection.execute(
            text(
                "INSERT INTO strategy_versions "
                "(id, tenant_id, strategy_id, version, lifecycle, raw_spec, normalized_spec, "
                "plan, plan_hash, schema_version, runtime_version, created_at) VALUES "
                "(:version, :tenant, :strategy, 1, 'PUBLISHED', '{}', '{}', '{}', "
                ":plan_hash, 'v1', 'v1', now()), "
                "(:other_version, :tenant, :other_strategy, 1, 'PUBLISHED', '{}', '{}', '{}', "
                ":other_plan_hash, 'v1', 'v1', now())"
            ),
            {
                "tenant": tenant_id,
                "strategy": strategy_id,
                "version": version_id,
                "plan_hash": "1" * 64,
                "other_strategy": other_strategy_id,
                "other_version": other_version_id,
                "other_plan_hash": "2" * 64,
            },
        )
        await connection.execute(
            text(
                "INSERT INTO runs "
                "(id, tenant_id, project_id, strategy_version_id, status, input, budgets, usage, "
                "plan_hash, runtime_version, temporal_workflow_id, next_event_seq, "
                "earliest_available_seq, version, initiated_by, submitted_scopes, "
                "auth_context_hash, policy_revision, started_at, completed_at, created_at, "
                "updated_at) VALUES "
                "(:running, :tenant, :project, :version, 'RUNNING', "
                "'{\"operatorName\":\"项目负责人\"}', '{}', '{}', :plan_hash, 'v1', "
                ":running_workflow, 4, 1, 1, 'integration-test', '[]', :auth_hash, 'v1', "
                "now(), NULL, now(), now()), "
                "(:failed, :tenant, :project, :version, 'FAILED', '{}', '{}', '{}', "
                ":plan_hash, 'v1', :failed_workflow, 2, 1, 1, 'integration-test', '[]', "
                ":auth_hash, 'v1', now() - interval '2 minutes', now() - interval '1 minute', "
                "now() - interval '2 minutes', now() - interval '1 minute'), "
                "(:other_running, :tenant, :other_project, :other_version, 'RUNNING', '{}', "
                "'{}', '{}', :other_plan_hash, 'v1', :other_workflow, 7, 1, 1, "
                "'integration-test', '[]', :auth_hash, 'v1', now(), NULL, now(), now())"
            ),
            {
                "tenant": tenant_id,
                "project": project_id,
                "other_project": other_project_id,
                "version": version_id,
                "other_version": other_version_id,
                "running": running_id,
                "failed": failed_id,
                "other_running": other_running_id,
                "plan_hash": "1" * 64,
                "other_plan_hash": "2" * 64,
                "running_workflow": f"overview-running-{running_id}",
                "failed_workflow": f"overview-failed-{failed_id}",
                "other_workflow": f"overview-other-{other_running_id}",
                "auth_hash": "3" * 64,
            },
        )
        await connection.execute(
            text(
                "INSERT INTO approval_requests "
                "(id, tenant_id, project_id, run_id, node_key, prompt, input_schema, status, "
                "requested_by, requires_distinct_approver, created_at) VALUES "
                "(:id, :tenant, :project, :run, 'approval', '请审批', '{}', 'PENDING', "
                "'workflow', false, now())"
            ),
            {"id": uuid4(), "tenant": tenant_id, "project": project_id, "run": running_id},
        )
        await connection.execute(
            text(
                "INSERT INTO external_input_requests "
                "(id, tenant_id, project_id, run_id, node_key, prompt, input_schema, status, "
                "requested_by, created_at) VALUES "
                "(:id, :tenant, :project, :run, 'input', '请补充', '{}', 'PENDING', "
                "'workflow', now())"
            ),
            {"id": uuid4(), "tenant": tenant_id, "project": project_id, "run": running_id},
        )
        document_rows = [
            (project_id, "AVAILABLE"),
            (project_id, "REVIEW_REQUIRED"),
            (project_id, "FAILED"),
            (other_project_id, "FAILED"),
        ]
        for document_project_id, status in document_rows:
            document_id = uuid4()
            await connection.execute(
                text(
                    "INSERT INTO business_documents "
                    "(id, tenant_id, project_id, name, category, tags, status, current_version, "
                    "created_by, created_at, updated_at) VALUES "
                    "(:id, :tenant, :project, :name, 'contract', '[]', :status, 0, "
                    "'integration-test', now(), now())"
                ),
                {
                    "id": document_id,
                    "tenant": tenant_id,
                    "project": document_project_id,
                    "name": f"overview-document-{document_id}",
                    "status": status,
                },
            )
    await engine.dispose()

    headers = {"X-Tenant-ID": str(tenant_id)}
    url = f"/v1/projects/{project_id}/overview"
    with TestClient(
        create_app(Settings(database_url=database_url, telemetry_enabled=False))
    ) as client:
        response = client.get(url, headers=headers)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["counts"] == {
            "pendingApprovals": 1,
            "pendingInputs": 1,
            "documentsAvailable": 1,
            "documentsReviewRequired": 1,
            "documentsFailed": 1,
            "activeRuns": 1,
            "waitingRuns": 0,
        }
        assert len(body["businessWorks"]) == 10
        assert [item["runId"] for item in body["recentRuns"]] == [
            str(running_id),
            str(failed_id),
        ]
        assert all(item["businessWorkName"] == "平台运行" for item in body["recentRuns"])
        assert len(json.dumps(body, ensure_ascii=False).encode()) < 100_000
        forbidden = {"input", "output", "tasks", "manifest", "documents"}
        assert not forbidden.intersection(body)
        assert not forbidden.intersection(body["recentRuns"][0])

        cross_tenant = client.get(
            url,
            headers={"X-Tenant-ID": str(other_tenant_id)},
        )
        assert cross_tenant.status_code == 404
