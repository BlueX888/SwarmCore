from __future__ import annotations

import base64
import hashlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator
from swarmcore_application import (
    capability_executors,
    cross_file_consistency,
    document_read,
    post_evaluation_assemble,
    post_evaluation_evaluate,
    post_evaluation_report_render,
    report_render,
    rules_evaluate,
)
from swarmcore_application.capability_tool_executors import PostEvaluationRecorderExecutor
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import Evaluation, Report, WorkItem
from swarmcore_registry import builtin_registry

PHASE_SIX_OPERATIONS = {
    "contract.document_read",
    "contract.rules_evaluate",
    "contract.cross_file_consistency",
    "workbench.record_evaluation",
    "report.render",
    "contract.post_evaluation",
    "contract.post_evaluation_assemble",
    "document.read_versions",
    "resource.read_bound",
    "report.render_post_evaluation",
    "workbench.record_post_evaluation",
}


def test_phase_six_tools_have_executors_and_closed_contracts() -> None:
    registrations = {
        item.operation: item
        for item in builtin_registry().tools
        if item.operation in PHASE_SIX_OPERATIONS
    }
    assert set(registrations) == PHASE_SIX_OPERATIONS
    assert set(capability_executors(None)) == PHASE_SIX_OPERATIONS  # type: ignore[arg-type]
    for registration in registrations.values():
        Draft202012Validator.check_schema(registration.input_schema)
        Draft202012Validator.check_schema(registration.output_schema)
        assert registration.input_schema["additionalProperties"] is False
        assert registration.output_schema["additionalProperties"] is False
        assert registration.recovery_policy == "idempotent"


@pytest.mark.asyncio
async def test_document_read_verifies_content_and_returns_real_pages() -> None:
    content = "第一页\f第二页".encode()
    result = await document_read(
        {
            "documentId": "00000000-0000-0000-0000-000000000001",
            "filename": "contract.txt",
            "mediaType": "text/plain",
            "sha256": hashlib.sha256(content).hexdigest(),
            "contentBase64": base64.b64encode(content).decode(),
        },
        "effect-1",
    )
    assert [page["text"] for page in result["pages"]] == ["第一页", "第二页"]
    with pytest.raises(ValueError, match="sha256"):
        await document_read(
            {
                "documentId": "00000000-0000-0000-0000-000000000001",
                "filename": "contract.txt",
                "mediaType": "text/plain",
                "sha256": "0" * 64,
                "contentBase64": base64.b64encode(content).decode(),
            },
            "effect-2",
        )


@pytest.mark.asyncio
async def test_rules_evaluate_executes_integrity_rules() -> None:
    result = await rules_evaluate(
        {
            "ruleSetVersionId": "rules-1",
            "attachmentManifestHash": "manifest",
            "rules": {
                "schemaVersion": "schema://contract/checklist-rule@1",
                "match": {},
                "requirements": [{"key": "contract", "documentType": "contract", "required": True}],
            },
            "attachments": [],
        },
        "effect-1",
    )
    assert result["passed"] is False
    assert result["findings"][0]["code"] == "DOCUMENT_MISSING"


@pytest.mark.asyncio
async def test_report_render_returns_a_verifiable_pdf() -> None:
    first = await report_render({"title": "Evidence", "results": [], "rules": []}, "effect-1")
    retried = await report_render({"title": "Evidence", "results": [], "rules": []}, "effect-2")
    assert retried == first
    content = base64.b64decode(first["contentBase64"])
    assert content.startswith(b"%PDF-")
    assert hashlib.sha256(content).hexdigest() == first["sha256"]


@pytest.mark.asyncio
async def test_post_evaluation_tools_generate_structured_result_and_pdf() -> None:
    input_value = {
        "payload": {
            "title": "合同后评价",
            "evaluationPeriod": {"start": "2026-01-01", "end": "2026-06-30"},
            "contract": {
                "contractId": "contract-1",
                "contractName": "采购合同",
                "contractAmount": 100,
                "actualCost": 100,
            },
            "documents": [{"documentId": "doc-1", "category": "合同", "status": "VALID"}],
            "obligations": [
                {
                    "obligationId": "obligation-1",
                    "category": "交付",
                    "timeliness": "ON_TIME",
                    "quality": "ACCEPTED",
                }
            ],
            "deviations": [],
            "invoices": [],
            "risks": [],
        },
        "configuration": {},
        "attachmentManifestHash": "manifest-hash",
    }
    result = await post_evaluation_evaluate(input_value, "effect-1")
    report = await post_evaluation_report_render(
        {"title": "合同后评价", "result": result}, "effect-2"
    )

    assert result["overallScore"] == 100
    assert len(result["dimensions"]) == 7
    content = base64.b64decode(report["contentBase64"])
    assert content.startswith(b"%PDF-")
    assert hashlib.sha256(content).hexdigest() == report["sha256"]


@pytest.mark.asyncio
async def test_post_evaluation_assemble_uses_bound_resource_facts() -> None:
    result = await post_evaluation_assemble(
        {
            "payload": {
                "title": "合同后评价",
                "evaluationPeriod": {"start": "2026-01-01", "end": "2026-06-30"},
                "contract": {
                    "contractId": "contract-1",
                    "contractName": "采购合同",
                    "contractAmount": 100,
                },
                "documents": [],
                "obligations": [],
                "deviations": [],
                "invoices": [],
                "risks": [],
            },
            "sources": [
                {
                    "slot": "contract-files",
                    "data": {
                        "documents": [
                            {"documentId": "doc-1", "category": "合同", "status": "VALID"}
                        ]
                    },
                },
                {
                    "slot": "performance-data",
                    "data": {
                        "contract": {
                            "contractId": "contract-1",
                            "contractName": "采购合同",
                            "contractAmount": 100,
                            "actualCost": 98,
                        },
                        "obligations": [
                            {
                                "obligationId": "ob-1",
                                "category": "交付",
                                "timeliness": "ON_TIME",
                                "quality": "ACCEPTED",
                            }
                        ],
                    },
                },
                {"slot": "deviation-data", "data": {"deviations": []}},
                {"slot": "invoice-data", "data": {"invoices": []}},
                {"slot": "risk-data", "data": {"risks": []}},
            ],
        },
        "effect-assemble",
    )

    assert result["documents"][0]["documentId"] == "doc-1"
    assert result["contract"]["actualCost"] == 98
    assert result["obligations"][0]["quality"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_post_evaluation_recorder_persists_json_and_pdf_reports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import swarmcore_application.capability_tool_executors as executors_module

    generated = await post_evaluation_evaluate(
        {
            "payload": {
                "title": "合同后评价",
                "evaluationPeriod": {"start": "2026-01-01", "end": "2026-06-30"},
                "contract": {
                    "contractId": "contract-1",
                    "contractName": "采购合同",
                    "contractAmount": 100,
                    "actualCost": 100,
                },
                "documents": [{"documentId": "doc-1", "category": "合同", "status": "VALID"}],
                "obligations": [
                    {
                        "obligationId": "obligation-1",
                        "category": "交付",
                        "timeliness": "ON_TIME",
                        "quality": "ACCEPTED",
                    }
                ],
                "deviations": [],
                "invoices": [],
                "risks": [],
            },
            "configuration": {},
            "attachmentManifestHash": "manifest-hash",
        },
        "effect-evaluate",
    )
    rendered = await post_evaluation_report_render(
        {"title": "合同后评价", "result": generated}, "effect-report"
    )
    tenant_id = uuid4()
    project_id = uuid4()
    evaluation_id = uuid4()
    evaluation = MagicMock(spec=Evaluation)
    evaluation.id = evaluation_id
    evaluation.work_item_id = uuid4()
    evaluation.result = None
    evaluation.status = "RUNNING"
    evaluation.report_template_version = "report://contract/post-evaluation@1"
    evaluation.output_schema_version = "schema://contract/post-evaluation-result@1"
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

    receipt = await PostEvaluationRecorderExecutor(None).execute(  # type: ignore[arg-type]
        {
            "evaluationId": str(evaluation_id),
            "result": generated,
            "report": rendered,
        },
        "effect-record",
        context,
    )

    reports = session.add_all.call_args.args[0]
    assert [value.format for value in reports] == ["JSON", "PDF"]
    assert all(isinstance(value, Report) for value in reports)
    assert evaluation.status == "SUCCEEDED"
    assert item.status == "COMPLETED"
    assert receipt["recorded"] is True


@pytest.mark.asyncio
async def test_cross_file_consistency_rejects_invalid_structured_results() -> None:
    with pytest.raises(ValueError):
        await cross_file_consistency(
            {"results": [{"status": "COMPLETED"}], "rules": []}, "effect-1"
        )
