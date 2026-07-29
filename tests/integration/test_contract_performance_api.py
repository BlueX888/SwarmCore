from __future__ import annotations

from uuid import uuid4

import pytest
from runtime_harness import RuntimeHarness
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_contract_performance_lifecycle_is_idempotent(
    runtime_harness: RuntimeHarness,
) -> None:
    business_object = runtime_harness.api.post(
        runtime_harness.project_url("business-objects"),
        headers={**runtime_harness.headers, "Idempotency-Key": "performance-contract"},
        json={
            "objectType": "contract",
            "canonicalKey": "CP-001",
            "schemaRef": "schema://contract/facts@1",
            "data": {"contractNumber": "CP-001"},
            "provenance": {"source": "integration"},
        },
    )
    assert business_object.status_code == 201, business_object.text

    create_payload = {
        "contractObjectId": business_object.json()["businessObjectId"],
        "timezone": "Asia/Shanghai",
        "currency": "CNY",
    }
    case = runtime_harness.api.post(
        runtime_harness.project_url("contract-performance/cases"),
        headers={**runtime_harness.headers, "Idempotency-Key": "performance-case"},
        json=create_payload,
    )
    replayed_case = runtime_harness.api.post(
        runtime_harness.project_url("contract-performance/cases"),
        headers={**runtime_harness.headers, "Idempotency-Key": "performance-case"},
        json=create_payload,
    )
    assert case.status_code == 201, case.text
    assert replayed_case.json()["caseId"] == case.json()["caseId"]
    case_id = case.json()["caseId"]

    initialized = runtime_harness.api.post(
        runtime_harness.project_url(f"contract-performance/cases/{case_id}:initialize"),
        headers=runtime_harness.headers,
        json={
            "asOf": "2026-07-01",
            "coverage": {"required": 1, "available": 1},
            "candidates": {
                "contract": {"contractNumber": "CP-001"},
                "obligations": [
                    {
                        "id": "obl-1",
                        "title": "完成交付并通过验收",
                        "evidenceRefs": [{"documentVersionId": "contract-v1"}],
                    }
                ],
                "deliverables": [],
                "acceptanceCriteria": [],
                "serviceLevels": [],
                "paymentConditions": [],
                "milestones": [
                    {
                        "id": "ms-1",
                        "title": "最终验收",
                        "dueDate": "2026-07-31",
                        "dependencies": [],
                        "evidenceRequirements": ["ACCEPTANCE"],
                        "contractKeys": {"contractNumber": "CP-001"},
                    }
                ],
                "changes": [],
            },
        },
    )
    assert initialized.status_code == 202, initialized.text
    assert initialized.json()["status"] == "CANDIDATE"

    published = runtime_harness.api.post(
        runtime_harness.project_url(
            f"contract-performance/cases/{case_id}/plans/1:publish"
        ),
        headers=runtime_harness.headers,
        json={"approvalId": str(uuid4()), "confirmations": []},
    )
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "PUBLISHED"

    collect_payload = {
        "asOf": "2026-07-27",
        "collectionStatus": "COMPLETE",
        "sources": [
            {"sourceRef": "acceptance-system", "status": "SUCCEEDED", "nextCursor": "2"}
        ],
        "evidence": [
            {
                "id": "acceptance-1",
                "type": "ACCEPTANCE",
                "sourceRef": "acceptance-system",
                "sourceRecordId": "acceptance-1",
                "occurredAt": "2026-07-25T10:00:00+08:00",
                "contractKeys": {"contractNumber": "CP-001"},
            }
        ],
        "candidateLinks": [{"evidenceId": "acceptance-1", "targetId": "ms-1"}],
    }
    collected = runtime_harness.api.post(
        runtime_harness.project_url(f"contract-performance/cases/{case_id}:collect"),
        headers={**runtime_harness.headers, "Idempotency-Key": "performance-collect"},
        json=collect_payload,
    )
    replayed = runtime_harness.api.post(
        runtime_harness.project_url(f"contract-performance/cases/{case_id}:collect"),
        headers={**runtime_harness.headers, "Idempotency-Key": "performance-collect"},
        json=collect_payload,
    )
    assert collected.status_code == 202, collected.text
    assert collected.json()["status"] == "COMPLETED"
    assert replayed.json()["snapshotId"] == collected.json()["snapshotId"]

    snapshot = runtime_harness.api.get(
        runtime_harness.project_url(
            f"contract-performance/cases/{case_id}/snapshots/"
            f"{collected.json()['snapshotId']}"
        ),
        headers=runtime_harness.headers,
    )
    evidence = runtime_harness.api.get(
        runtime_harness.project_url(f"contract-performance/cases/{case_id}/evidence"),
        headers=runtime_harness.headers,
    )
    gantt = runtime_harness.api.get(
        runtime_harness.project_url(f"contract-performance/cases/{case_id}/gantt"),
        headers=runtime_harness.headers,
        params={"asOf": "2026-07-27"},
    )
    assert snapshot.status_code == 200, snapshot.text
    assert snapshot.json()["resultHash"] == collected.json()["resultHash"]
    assert evidence.status_code == 200, evidence.text
    assert evidence.json()["total"] == 1
    assert gantt.status_code == 200, gantt.text
    assert gantt.json()["milestones"][0]["status"] == "ACCEPTED"
    assert gantt.json()["milestones"][0]["actualFinishDate"] == "2026-07-25"

    engine = create_async_engine(runtime_harness.database_url)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        await connection.execute(
            text("SELECT set_config('app.tenant_id', :value, true)"),
            {"value": str(runtime_harness.tenant_id)},
        )
        await connection.execute(
            text("SELECT set_config('app.project_id', :value, true)"),
            {"value": str(runtime_harness.project_id)},
        )
        with pytest.raises(DBAPIError, match="immutable"):
            await connection.execute(
                text(
                    "UPDATE contract_performance_snapshots "
                    "SET status = 'AT_RISK' WHERE id = :snapshot"
                ),
                {"snapshot": collected.json()["snapshotId"]},
            )
        await transaction.rollback()
    await engine.dispose()
