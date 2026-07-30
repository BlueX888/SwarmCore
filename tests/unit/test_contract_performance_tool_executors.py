from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from swarmcore_application import capability_tool_executors as executors_module
from swarmcore_application.capability_tool_executors import (
    ContractPerformanceRecorderExecutor,
    contract_performance_change_apply,
    contract_performance_evidence_match,
    contract_performance_finalize,
    contract_performance_plan_normalize,
    contract_performance_report_render,
    contract_performance_schedule_build,
    contract_performance_source_collect,
    contract_performance_status_calculate,
)
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import Evaluation, Finding, Report, WorkItem


@pytest.mark.asyncio
async def test_contract_performance_tools_run_deterministic_pipeline() -> None:
    normalized = await contract_performance_plan_normalize(
        {
            "candidates": {
                "contract": {"contractNumber": "C-001"},
                "obligations": [
                    {
                        "id": "obl-1",
                        "title": "交付",
                        "evidenceRefs": [{"documentVersionId": "doc-v1"}],
                    }
                ],
                "deliverables": [],
                "acceptanceCriteria": [],
                "serviceLevels": [],
                "paymentConditions": [],
                "milestones": [
                    {
                        "id": "ms-1",
                        "title": "验收",
                        "dueDate": "2026-07-01",
                        "dependencies": [],
                        "evidenceRequirements": ["ACCEPTANCE"],
                        "contractKeys": {"contractNumber": "C-001"},
                    }
                ],
                "changes": [],
            },
            "configuration": {"timezone": "Asia/Shanghai", "currency": "CNY"},
        },
        "effect-1",
    )
    plan = normalized["plan"]
    plan["status"] = "PUBLISHED"

    matched = await contract_performance_evidence_match(
        {
            "plan": plan,
            "evidence": [
                {
                    "id": "ev-1",
                    "type": "ACCEPTANCE",
                    "contractKeys": {"contractNumber": "C-001"},
                }
            ],
            "candidates": [{"evidenceId": "ev-1", "targetId": "ms-1"}],
        },
        "effect-2",
    )
    performance = await contract_performance_status_calculate(
        {
            "plan": plan,
            "evidence": [
                {
                    "id": "ev-1",
                    "type": "ACCEPTANCE",
                    "contractKeys": {"contractNumber": "C-001"},
                }
            ],
            "links": matched["links"],
            "asOf": "2026-07-27",
        },
        "effect-3",
    )
    assert performance["status"] == "COMPLETED"
    assert performance["milestones"][0]["status"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_initialize_finalize_rejects_approved_empty_plan() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "PLAN_MINIMUM_CONTENT_REQUIRED:"
            "contract,obligations,deliverables,milestones,"
            "acceptanceCriteria,serviceLevels,paymentConditions"
        ),
    ):
        await contract_performance_finalize(
            {
                "operation": "INITIALIZE",
                "caseId": "case-empty",
                "plan": {
                    "contract": {},
                    "obligations": [],
                    "deliverables": [],
                    "milestones": [],
                    "acceptanceCriteria": [],
                    "serviceLevels": [],
                    "paymentConditions": [],
                },
                "approval": {"approved": True},
                "asOf": "2026-07-27",
            },
            "effect-empty",
        )


@pytest.mark.asyncio
async def test_initialize_finalize_publishes_complete_minimum_plan() -> None:
    result = await contract_performance_finalize(
        {
            "operation": "INITIALIZE",
            "caseId": "case-complete",
            "plan": {
                "contract": {"contractNumber": "C-001"},
                "obligations": [{"id": "obl-1", "title": "Deliver"}],
                "deliverables": [{"id": "del-1", "title": "Release"}],
                "milestones": [
                    {
                        "id": "ms-1",
                        "title": "Acceptance",
                        "startDate": "2026-01-01",
                        "dueDate": "2026-01-31",
                        "dependencies": [],
                        "paymentConditionIds": [],
                        "acceptanceCriterionIds": [],
                    }
                ],
                "acceptanceCriteria": [{"id": "acc-1", "title": "Signed acceptance"}],
                "serviceLevels": [{"id": "sla-1", "title": "Availability"}],
                "paymentConditions": [{"id": "pay-1", "title": "Payment"}],
            },
            "approval": {"approved": True},
            "asOf": "2026-07-27",
        },
        "effect-complete",
    )

    assert result["plan"]["status"] == "PUBLISHED"
    assert result["performance"]["reviewRequired"] is False


@pytest.mark.asyncio
async def test_initialize_finalize_preserves_plan_gaps_and_change_history() -> None:
    difference = {
        "changeId": "chg-value",
        "path": "/contract/totalAmount",
        "before": 1_200_000,
        "after": 1_280_000,
    }
    result = await contract_performance_finalize(
        {
            "operation": "INITIALIZE",
            "caseId": "case-review",
            "plan": {
                "contract": {"contractNumber": "C-001", "totalAmount": 1_280_000},
                "obligations": [{"id": "obl-1", "title": "Deliver"}],
                "deliverables": [{"id": "del-1", "title": "Release"}],
                "milestones": [{"id": "ms-1", "dependencies": []}],
                "acceptanceCriteria": [{"id": "acc-1"}],
                "serviceLevels": [{"id": "sla-1"}],
                "paymentConditions": [{"id": "pay-1", "amount": 1_200_000}],
                "changes": [{"id": "chg-value", "status": "APPROVED"}],
                "conflicts": [],
                "gaps": [
                    {
                        "code": "PAYMENT_TOTAL_MISMATCH",
                        "contractTotal": 1_280_000,
                        "paymentTotal": 1_200_000,
                        "difference": 80_000,
                    }
                ],
                "changeHistory": {
                    "appliedChanges": [{"id": "chg-value", "status": "APPROVED"}],
                    "differences": [difference],
                    "unapprovedChangeRisks": [],
                },
            },
            "approval": {"approved": True},
            "asOf": "2026-07-27",
        },
        "effect-review",
    )

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["performance"]["reviewRequired"] is True
    assert result["performance"]["findings"] == [
        {
            "code": "PAYMENT_TOTAL_MISMATCH",
            "contractTotal": 1_280_000,
            "paymentTotal": 1_200_000,
            "difference": 80_000,
            "severity": "HIGH",
            "reviewType": "FINANCE",
        }
    ]
    assert result["changeHistory"]["differences"] == [difference]


@pytest.mark.asyncio
async def test_source_collection_is_partial_and_does_not_advance_failed_source() -> None:
    result = await contract_performance_source_collect(
        {
            "sources": [
                {
                    "sourceRef": "erp",
                    "status": "SUCCEEDED",
                    "nextCursor": "11",
                    "records": [{"id": "r1", "type": "DISPATCH"}],
                },
                {"sourceRef": "wms", "status": "FAILED", "nextCursor": "22"},
            ]
        },
        "effect",
    )
    assert result["collectionStatus"] == "PARTIAL"
    assert result["nextCursors"] == {"erp": "11"}
    assert result["evidence"][0]["sourceRef"] == "erp"


@pytest.mark.asyncio
async def test_source_collection_reads_and_freezes_real_public_dfe_csv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        b"Department Family,Entity,Date,Expense Type,Expense Area,Supplier,"
        b"Transaction Number,Amount,Description\r\n"
        b"Department for Education,Core,19/04/2024,Other Goods and Services,"
        b"Apprenticeships and Skills Bootcamps,Cogrammar Ltd,SB-001,"
        b'"1,329,075.00",Professional Services - Education Services\r\n'
        b"Department for Education,Core,19/04/2024,Other Goods and Services,"
        b"Another Area,Another Supplier,OTHER-001,25000.00,Other\r\n"
    )
    monkeypatch.setattr(
        executors_module,
        "_download_contract_public_source",
        lambda _url: (
            content,
            {
                "etag": '"public-etag"',
                "lastModified": "Fri, 26 Jul 2024 10:00:00 GMT",
                "contentType": "text/csv",
            },
        ),
    )
    source = {
        "sourceRef": "public://dfe-spend/2024-04",
        "kind": "PUBLIC_DFE_SPEND_CSV",
        "url": (
            "https://assets.publishing.service.gov.uk/media/example/"
            "DfE_Spend__25k_April_2024.csv"
        ),
        "filters": {
            "Supplier": "Cogrammar Ltd",
            "Expense Area": "Apprenticeships and Skills Bootcamps",
        },
        "currency": "GBP",
    }

    result = await contract_performance_source_collect({"sources": [source]}, "effect")

    assert result["collectionStatus"] == "COMPLETE"
    assert len(result["evidence"]) == 1
    evidence = result["evidence"][0]
    assert evidence["sourceRecordId"] == "SB-001"
    assert evidence["businessDate"] == "2024-04-19"
    assert evidence["amount"] == 1329075.0
    assert evidence["contractKeys"] == {
        "supplier": "Cogrammar Ltd",
        "expenseArea": "Apprenticeships and Skills Bootcamps",
    }
    assert evidence["provenance"]["sourceSha256"]
    assert evidence["evidence"][0]["row"] == 2
    cursor = result["nextCursors"]["public://dfe-spend/2024-04"]

    repeated = await contract_performance_source_collect(
        {"sources": [{**source, "cursor": cursor}]},
        "effect-2",
    )
    assert repeated["evidence"] == []
    assert repeated["nextCursors"] == {"public://dfe-spend/2024-04": cursor}


@pytest.mark.asyncio
async def test_public_source_failure_is_isolated_and_does_not_advance_cursor() -> None:
    result = await contract_performance_source_collect(
        {
            "sources": [
                {
                    "sourceRef": "public://blocked",
                    "kind": "PUBLIC_DFE_SPEND_CSV",
                    "url": "https://example.com/spend.csv",
                },
                {
                    "sourceRef": "erp",
                    "status": "SUCCEEDED",
                    "nextCursor": "12",
                    "records": [{"id": "r1", "type": "DISPATCH"}],
                },
            ]
        },
        "effect",
    )

    assert result["collectionStatus"] == "PARTIAL"
    assert result["nextCursors"] == {"erp": "12"}
    assert result["sourceResults"][0] == {
        "sourceRef": "public://blocked",
        "status": "FAILED",
        "code": "PUBLIC_SOURCE_URL_NOT_ALLOWED",
        "attempts": 1,
    }


@pytest.mark.asyncio
async def test_public_source_retries_retryable_failures_three_times(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def unavailable(_url: str) -> tuple[bytes, dict[str, str]]:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("PUBLIC_SOURCE_HTTP_503")

    pause = AsyncMock()
    monkeypatch.setattr(executors_module, "_download_contract_public_source", unavailable)
    monkeypatch.setattr(executors_module, "sleep", pause)

    result = await contract_performance_source_collect(
        {
            "sources": [
                {
                    "sourceRef": "public://retry",
                    "kind": "PUBLIC_DFE_SPEND_CSV",
                    "url": (
                        "https://assets.publishing.service.gov.uk/media/example/"
                        "DfE_Spend__25k_April_2024.csv"
                    ),
                }
            ]
        },
        "effect",
    )

    assert attempts == 3
    assert pause.await_args_list[0].args == (1,)
    assert pause.await_args_list[1].args == (2,)
    assert result["collectionStatus"] == "FAILED"
    assert result["sourceResults"][0]["attempts"] == 3


@pytest.mark.asyncio
async def test_change_and_schedule_tools_preserve_original_date() -> None:
    plan = {
        "status": "PUBLISHED",
        "milestones": [
            {
                "id": "ms-1",
                "title": "交付",
                "startDate": "2026-01-01",
                "dueDate": "2026-01-10",
                "duration": 9,
                "dependencies": [],
            }
        ],
    }
    changed = await contract_performance_change_apply(
        {
            "plan": plan,
            "changes": [
                {
                    "id": "chg-1",
                    "status": "APPROVED",
                    "effectiveAt": "2026-01-02",
                    "changedPaths": [{"path": "/milestones/0/dueDate", "after": "2026-01-20"}],
                }
            ],
            "asOf": "2026-01-05",
        },
        "effect",
    )
    gantt = await contract_performance_schedule_build(
        {
            "plan": changed["currentBaseline"],
            "originalPlan": changed["originalBaseline"],
            "asOf": "2026-01-05",
        },
        "effect",
    )
    assert gantt["milestones"][0]["originalDueDate"] == "2026-01-10"
    assert gantt["milestones"][0]["currentDueDate"] == "2026-01-20"


@pytest.mark.asyncio
async def test_contract_performance_recorder_persists_reports_and_findings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = await contract_performance_finalize(
        {
            "caseId": "case-1",
            "planVersion": 1,
            "plan": {"status": "PUBLISHED", "milestones": []},
            "performance": {
                "asOf": "2026-07-27",
                "status": "AT_RISK",
                "collectionStatus": "COMPLETE",
                "milestones": [],
                "findings": [
                    {
                        "code": "MILESTONE_AT_RISK",
                        "milestoneId": "ms-1",
                        "severity": "HIGH",
                        "summary": "里程碑存在延期风险",
                    }
                ],
                "reviewRequired": True,
            },
            "gantt": {"milestones": [], "quality": {"status": "COMPLETE"}},
        },
        "effect-finalize",
    )
    rendered = await contract_performance_report_render(
        {"result": result}, "effect-report"
    )
    tenant_id = uuid4()
    project_id = uuid4()
    evaluation_id = uuid4()
    evaluation = MagicMock(spec=Evaluation)
    evaluation.id = evaluation_id
    evaluation.work_item_id = uuid4()
    evaluation.result = None
    evaluation.status = "RUNNING"
    evaluation.report_template_version = "report://contract-performance@1"
    evaluation.output_schema_version = "schema://contract-performance/result@1"
    item = MagicMock(spec=WorkItem)
    item.id = evaluation.work_item_id
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[evaluation, item])
    session.flush = AsyncMock()

    @asynccontextmanager
    async def fake_transaction(*args: object, **kwargs: object) -> AsyncIterator[MagicMock]:
        del args, kwargs
        yield session

    monkeypatch.setattr(executors_module, "tenant_transaction", fake_transaction)
    monkeypatch.setattr(AuditRepository, "append", AsyncMock())
    context = SimpleNamespace(
        tenant_id=str(tenant_id),
        project_id=str(project_id),
        execution_id=str(uuid4()),
        run_id=str(uuid4()),
    )

    receipt = await ContractPerformanceRecorderExecutor(None).execute(  # type: ignore[arg-type]
        {
            "evaluationId": str(evaluation_id),
            "result": result,
            "report": rendered,
        },
        "effect-record",
        context,
    )

    reports = session.add_all.call_args.args[0]
    assert [value.format for value in reports] == ["JSON", "PDF"]
    assert all(isinstance(value, Report) for value in reports)
    assert any(isinstance(call.args[0], Finding) for call in session.add.call_args_list)
    assert evaluation.status == "SUCCEEDED"
    assert item.status == "IN_REVIEW"
    assert receipt["recorded"] is True
