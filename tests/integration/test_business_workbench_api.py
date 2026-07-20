from __future__ import annotations

import base64
import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_api import create_app
from swarmcore_api.business_routes import capability_packs
from swarmcore_api.settings import Settings
from swarmcore_application import (
    AgentRuntimeStatus,
    CapabilityCenterService,
    CapabilityReadinessService,
    ModelRuntimeStatus,
    ToolRuntimeStatus,
)
from swarmcore_artifact_gateway.main import Settings as ArtifactSettings
from swarmcore_artifact_gateway.main import create_app as create_artifact_app
from swarmcore_capability_contract_integrity import DEFAULT_RULES, MANIFEST
from swarmcore_governance import BlobCapabilityIssuer
from swarmcore_registry import builtin_registry
from swarmcore_tool_gateway import CapabilityTokenIssuer
from swarmcore_tool_gateway_api.main import Settings as ToolGatewaySettings
from swarmcore_tool_gateway_api.main import create_app as create_tool_gateway

_CAPABILITY_SECRET = b"development-artifact-capability-secret-32-bytes"


class ReadyRuntime:
    async def inspect_tool(self, **_: object) -> ToolRuntimeStatus:
        return ToolRuntimeStatus(executor_registered=True, healthy=True)

    async def inspect_model(self, **_: object) -> ModelRuntimeStatus:
        return ModelRuntimeStatus(
            route_registered=True,
            secret_available=True,
            endpoint_healthy=True,
        )

    async def inspect_agent(self, **_: object) -> AgentRuntimeStatus:
        return AgentRuntimeStatus(adapter_available=True)


@pytest.mark.asyncio
async def test_fixed_contract_integrity_scenario_and_protocol_equivalence(
    tmp_path: Path,
) -> None:
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
                "name": f"business-tenant-{tenant_id}",
                "other": other_tenant_id,
                "other_name": f"business-tenant-{other_tenant_id}",
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
                "VALUES (:project, :tenant, 'business-project', '{}', now(), now())"
            ),
            {"project": project_id, "tenant": tenant_id},
        )
    await engine.dispose()

    headers = {"X-Tenant-ID": str(tenant_id)}
    base = f"/v1/projects/{project_id}"
    capability_secret = _CAPABILITY_SECRET.decode()
    tool_secret = "integration-capability-secret-at-least-32-bytes"
    api_app = create_app(
        Settings(
            database_url=database_url,
            artifact_capability_secret=capability_secret,
            telemetry_enabled=False,
        )
    )
    with (
        TestClient(api_app) as client,
        TestClient(
            create_artifact_app(
                ArtifactSettings(
                    database_url=database_url,
                    artifact_root=str(tmp_path / "blobs"),
                    artifact_capability_secret=capability_secret,
                    telemetry_enabled=False,
                )
            )
        ) as artifact_client,
        TestClient(
            create_tool_gateway(
                ToolGatewaySettings(
                    database_url=database_url,
                    tool_capability_secret=tool_secret,
                    telemetry_enabled=False,
                )
            ),
            raise_server_exceptions=False,
        ) as tool_client,
    ):
        runtime = ReadyRuntime()
        capability_packs.attach_readiness(
            CapabilityCenterService(
                builtin_registry(),
                CapabilityReadinessService(
                    tools=runtime,
                    models=runtime,
                    agents=runtime,
                ),
            ),
            environment="development",
        )
        tool_readiness = tool_client.get("/internal/v1/readiness")
        assert tool_readiness.status_code == 200
        assert all(
            item["executorRegistered"] and item["healthy"]
            for item in tool_readiness.json()["tools"]
        )
        packs = client.get(f"{base}/capability-packs", headers=headers)
        assert packs.status_code == 200, packs.text
        version_id = packs.json()["items"][0]["versionId"]
        strategy_list = client.get(f"{base}/strategies", headers=headers)
        assert strategy_list.status_code == 200, strategy_list.text
        selected_strategy = next(
            item
            for item in strategy_list.json()["items"]
            if item["name"] == "trusted-contract-integrity-validate"
        )
        strategy_versions = client.get(
            f"{base}/strategies/{selected_strategy['strategyId']}/versions",
            headers=headers,
        )
        assert strategy_versions.status_code == 200, strategy_versions.text
        selected_version = strategy_versions.json()["items"][0]
        custom_manifest = deepcopy(MANIFEST)
        custom_manifest["metadata"] = {"name": "custom-review", "version": "1.0.0"}
        custom_manifest["spec"]["strategies"] = {
            "execute": (
                f"strategy://project/{selected_strategy['strategyId']}"
                f"@{selected_version['version']}"
            )
        }
        custom_manifest["spec"]["events"] = {
            "namespace": "capability.custom-review"
        }
        custom_pack = client.post(
            f"{base}/capability-packs",
            headers=headers,
            json={
                "manifest": custom_manifest,
                "strategyVersionId": selected_version["strategyVersionId"],
            },
        )
        assert custom_pack.status_code == 201, custom_pack.text
        assert custom_pack.json()["name"] == "custom-review"
        assert custom_pack.json()["enabled"] is False
        enabled = client.post(
            f"{base}/capability-packs/{version_id}:enable",
            headers={**headers, "Idempotency-Key": "enable-contract-v1"},
            json={"configuration": {"reviewMode": "strict"}},
        )
        assert enabled.status_code == 200, enabled.text
        assert enabled.json()["configuration"] == {"reviewMode": "strict"}
        listed = client.get(f"{base}/capability-packs", headers=headers)
        configured = next(
            item for item in listed.json()["items"] if item["versionId"] == version_id
        )
        assert configured["configuration"] == {"reviewMode": "strict"}
        denied_enable = client.post(
            f"{base}/capability-packs/{version_id}:enable",
            headers={
                "X-Tenant-ID": str(other_tenant_id),
                "Idempotency-Key": "cross-tenant-enable",
            },
            json={"configuration": {}},
        )
        assert denied_enable.status_code == 404

        rule_set = client.post(
            f"{base}/rule-sets",
            headers={**headers, "Idempotency-Key": "create-purchase-rules"},
            json={
                "name": "采购合同资料规则",
                "purpose": "采购合同资料完整性校验",
                "rules": DEFAULT_RULES,
            },
        )
        assert rule_set.status_code == 201, rule_set.text
        draft_id = rule_set.json()["draftId"]
        published = client.post(
            f"{base}/rule-set-drafts/{draft_id}:publish",
            headers={**headers, "Idempotency-Key": "publish-purchase-rules-v1"},
        )
        assert published.status_code == 200, published.text
        rule_version_id = published.json()["ruleSetVersionId"]

        created = client.post(
            f"{base}/work-items",
            headers={**headers, "Idempotency-Key": "create-contract-case"},
            json={
                "workItemType": "contract-case",
                "payload": {"title": "采购合同 A", "contractType": "purchase"},
                "owner": "legal-team",
            },
        )
        assert created.status_code == 201, created.text
        work_item_id = created.json()["workItemId"]
        first_revision_id = created.json()["revisionId"]
        created_replay = client.post(
            f"{base}/work-items",
            headers={**headers, "Idempotency-Key": "create-contract-case"},
            json={
                "workItemType": "contract-case",
                "payload": {"title": "采购合同 A", "contractType": "purchase"},
                "owner": "legal-team",
            },
        )
        assert created_replay.json()["revisionId"] == first_revision_id

        contract_blob_id, contract_read_token = _attach(
            client, artifact_client, base, headers, work_item_id, "contract"
        )
        _attach(client, artifact_client, base, headers, work_item_id, "business-license")
        first = client.post(
            f"{base}/work-items/{work_item_id}:execute",
            headers={**headers, "Idempotency-Key": "evaluate-contract-v1"},
        )
        assert first.status_code == 202, first.text
        first_body = first.json()
        assert first_body["workItemRevisionId"] == first_revision_id
        assert first_body["ruleSetVersionId"] == rule_version_id
        assert first_body["result"]["passed"] is False
        assert [finding["code"] for finding in first_body["result"]["findings"]] == [
            "DOCUMENT_MISSING"
        ]
        first_evaluation_id = first_body["evaluationId"]
        tool_content = b"controlled contract text"
        tool_input = {
            "documentId": str(uuid4()),
            "filename": "contract.txt",
            "mediaType": "text/plain",
            "sha256": hashlib.sha256(tool_content).hexdigest(),
            "contentBase64": base64.b64encode(tool_content).decode(),
        }
        tool_token = CapabilityTokenIssuer(tool_secret).issue(
            tenant_id=str(tenant_id),
            project_id=str(project_id),
            run_id=first_body["runId"],
            node_key="document-read",
            tool_ref="tool://document/read@1",
            execution_id="integration-document-read",
            effect_id="document-read-1",
            approved=False,
        )
        invocation = {
            "token": tool_token,
            "effectId": "document-read-1",
            "input": tool_input,
        }
        invoked = tool_client.post("/internal/v1/tools/invoke", json=invocation)
        replayed = tool_client.post("/internal/v1/tools/invoke", json=invocation)
        assert invoked.status_code == 200, invoked.text
        assert replayed.json() == invoked.json()
        assert invoked.json()["content"]["pages"] == [
            {"page": 1, "text": "controlled contract text"}
        ]

        draft_rules = json.loads(json.dumps(DEFAULT_RULES))
        draft_rules["requirements"][-1]["required"] = False
        updated_draft = client.put(
            f"{base}/rule-set-drafts/{draft_id}",
            headers={
                **headers,
                "Idempotency-Key": "edit-unpublished-rules",
                "If-Match": '"1"',
            },
            json={"rules": draft_rules},
        )
        assert updated_draft.status_code == 200, updated_draft.text

        replay = client.post(
            f"{base}/work-items/{work_item_id}:execute",
            headers={**headers, "Idempotency-Key": "evaluate-contract-v1"},
        )
        assert replay.status_code == 202
        assert replay.json()["evaluationId"] == first_evaluation_id

        findings = client.get(f"{base}/work-items/{work_item_id}/findings", headers=headers)
        assert findings.status_code == 200
        assert [(item["ruleKey"], item["status"]) for item in findings.json()["items"]] == [
            ("authorization", "OPEN")
        ]

        _attach(client, artifact_client, base, headers, work_item_id, "authorization")
        second = client.post(
            f"{base}/work-items/{work_item_id}:execute",
            headers={**headers, "Idempotency-Key": "evaluate-contract-v2"},
        )
        assert second.status_code == 202, second.text
        second_body = second.json()
        assert second_body["workItemRevisionId"] != first_revision_id
        assert second_body["result"]["passed"] is True
        assert second_body["result"]["findings"] == []
        assert second_body["attachmentManifestHash"] != first_body["attachmentManifestHash"]

        resolved = client.get(f"{base}/work-items/{work_item_id}/findings", headers=headers)
        assert resolved.json()["items"][0]["status"] == "RESOLVED"
        for evaluation_id in (first_evaluation_id, second_body["evaluationId"]):
            evaluation = client.get(f"{base}/evaluations/{evaluation_id}", headers=headers)
            reports = client.get(f"{base}/evaluations/{evaluation_id}/reports", headers=headers)
            assert evaluation.status_code == 200
            assert evaluation.json()["ruleSetVersionId"] == rule_version_id
            assert {item["format"] for item in reports.json()["items"]} == {"HTML", "JSON"}

        mcp = client.post(
            "/mcp",
            headers={**headers, "Mcp-Protocol-Version": "2025-11-25"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "execute_work_item",
                    "arguments": {
                        "projectId": str(project_id),
                        "workItemId": work_item_id,
                        "idempotencyKey": "evaluate-contract-v2",
                    },
                },
            },
        )
        assert mcp.status_code == 200
        structured = mcp.json()["result"]["structuredContent"]
        assert structured["evaluationId"] == second_body["evaluationId"]
        assert structured["result"] == second_body["result"]

        engine = create_async_engine(database_url)
        async with engine.begin() as connection:
            run_row = (
                (
                    await connection.execute(
                        text(
                            "SELECT r.status, r.input, r.output, "
                            "sv.normalized_spec, sv.plan, o.status AS outbox_status "
                            "FROM evaluations e JOIN runs r ON r.id = e.run_id "
                            "JOIN strategy_versions sv ON sv.id = r.strategy_version_id "
                            "JOIN outbox_events o ON o.aggregate_id = r.id "
                            "AND o.destination = 'temporal' "
                            "WHERE e.id = :evaluation_id"
                        ),
                        {"evaluation_id": second_body["evaluationId"]},
                    )
                )
                .mappings()
                .one()
            )
        await engine.dispose()
        assert run_row["status"] == "SUCCEEDED"
        assert run_row["output"] == second_body["result"]
        assert run_row["outbox_status"] == "DELIVERED"
        assert run_row["input"]["configuration"] == {"reviewMode": "strict"}
        assert run_row["input"]["evaluationId"] == second_body["evaluationId"]
        assert set(run_row["normalized_spec"]["spec"]["agents"]) == {
            "classify",
            "extract",
        }
        assert set(run_row["plan"]["resolved_tools"]) == set(MANIFEST["spec"]["tools"])
        assert "model://fake-deterministic@1" not in run_row["plan"]["resolved_models"]

        isolated = client.get(f"{base}/work-items", headers={"X-Tenant-ID": str(other_tenant_id)})
        assert isolated.status_code == 200
        assert isolated.json()["total"] == 0

        cross_tenant_token = BlobCapabilityIssuer(_CAPABILITY_SECRET).issue(
            action="blob.read",
            tenant_id=str(other_tenant_id),
            project_id=str(project_id),
            blob_id=contract_blob_id,
            subject_id="cross-tenant-test",
        )
        cross_tenant_read = artifact_client.post(
            f"/internal/v1/blobs/{contract_blob_id}/content",
            params={"capability_token": cross_tenant_token},
        )
        assert cross_tenant_read.status_code == 404

        engine = create_async_engine(database_url)
        async with engine.begin() as connection:
            await connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": str(tenant_id)},
            )
            await connection.execute(
                text("SELECT set_config('app.project_id', :project, true)"),
                {"project": str(project_id)},
            )
            await connection.execute(
                text(
                    "UPDATE blob_objects SET retention_until = "
                    "now() - interval '1 second' WHERE id = :id"
                ),
                {"id": contract_blob_id},
            )
        await engine.dispose()
        expired = artifact_client.post(
            f"/internal/v1/blobs/{contract_blob_id}/content",
            params={"capability_token": contract_read_token},
        )
        assert expired.status_code == 404


def _attach(
    client: TestClient,
    artifact_client: TestClient,
    base: str,
    headers: dict[str, str],
    work_item_id: str,
    document_type: str,
) -> tuple[str, str]:
    content = f"{document_type}-content".encode()
    digest = hashlib.sha256(content).hexdigest()
    initiated = client.post(
        f"{base}/work-items/{work_item_id}/attachments:initiate",
        headers={**headers, "Idempotency-Key": f"initiate-{document_type}"},
        json={
            "documentType": document_type,
            "filename": f"{document_type}.pdf",
            "mediaType": "application/pdf",
            "sizeBytes": len(content),
            "sha256": digest,
            "retentionDays": 30,
        },
    )
    assert initiated.status_code == 201, initiated.text
    initiated_replay = client.post(
        f"{base}/work-items/{work_item_id}/attachments:initiate",
        headers={**headers, "Idempotency-Key": f"initiate-{document_type}"},
        json={
            "documentType": document_type,
            "filename": f"{document_type}.pdf",
            "mediaType": "application/pdf",
            "sizeBytes": len(content),
            "sha256": digest,
            "retentionDays": 30,
        },
    )
    assert initiated_replay.json()["blobId"] == initiated.json()["blobId"]
    attachment_id = initiated.json()["attachmentId"]
    uploaded = artifact_client.post(
        initiated.json()["uploadRef"],
        json={
            "capabilityToken": initiated.json()["capabilityToken"],
            "contentBase64": base64.b64encode(content).decode(),
        },
    )
    assert uploaded.status_code == 200, uploaded.text
    blob_id = initiated.json()["blobId"]
    read_token = BlobCapabilityIssuer(_CAPABILITY_SECRET).issue(
        action="blob.read",
        tenant_id=headers["X-Tenant-ID"],
        project_id=base.rsplit("/", 1)[-1],
        blob_id=blob_id,
        subject_id="integration-reader",
    )
    read = artifact_client.post(
        f"/internal/v1/blobs/{blob_id}/content",
        params={"capability_token": read_token},
    )
    assert read.status_code == 200
    assert read.content == content
    completed = client.post(
        f"{base}/attachments/{attachment_id}:complete",
        headers={**headers, "Idempotency-Key": f"complete-{document_type}"},
        json={"sha256": digest, "scanStatus": "CLEAN"},
    )
    assert completed.status_code == 200, completed.text
    return blob_id, read_token
