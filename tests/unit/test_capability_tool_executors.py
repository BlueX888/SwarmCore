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
    aggregate_deviations,
    aggregate_risks,
    assure_invoices,
    calculate_timeline,
    capability_executors,
    check_document_coverage,
    check_evidence_consistency,
    cross_file_consistency,
    document_read,
    finalize_expanded_result,
    merge_domain_analyses,
    post_evaluation_assemble,
    post_evaluation_evaluate,
    post_evaluation_report_render,
    post_evaluation_report_render_v2,
    post_evaluation_report_render_v3,
    reconcile_amounts,
    report_render,
    rules_evaluate,
    search_evidence,
)
from swarmcore_application.capability_tool_executors import (
    BoundDocumentReadExecutor,
    DeviationRecorderExecutor,
    PostEvaluationRecorderExecutor,
    deviation_report_render,
)
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import Evaluation, Finding, Report, WorkItem
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

EXPANDED_POST_EVALUATION_OPERATIONS = {
    "evidence.search",
    "document.coverage_check",
    "contract.post_evaluation_merge_domains",
    "contract.post_evaluation_timeline",
    "finance.post_evaluation_amounts",
    "invoice.post_evaluation_assurance",
    "deviation.post_evaluation_aggregate",
    "risk.post_evaluation_aggregate",
    "evidence.consistency_check",
    "contract.post_evaluation_finalize",
    "document.post_evaluation_readability_gate",
    "report.compose_post_evaluation",
    "report.verify_post_evaluation_citations",
    "report.check_post_evaluation_quality",
    "report.render_post_evaluation_v2",
    "report.render_post_evaluation_v3",
    "report.render_post_evaluation_v4",
}

DEVIATION_ANALYSIS_OPERATIONS = {
    "deviation.facts_merge",
    "deviation.time_calculate",
    "deviation.content_compare",
    "deviation.cost_calculate",
    "deviation.history_read",
    "deviation.trend_build",
    "deviation.responsibility_aggregate",
    "deviation.finalize",
    "report.render_deviation_analysis",
    "workbench.record_deviation_analysis",
}


def test_phase_six_tools_have_executors_and_closed_contracts() -> None:
    registrations = {
        item.operation: item
        for item in builtin_registry().tools
        if item.operation in PHASE_SIX_OPERATIONS
    }
    assert set(registrations) == PHASE_SIX_OPERATIONS
    assert set(capability_executors(None)) >= (  # type: ignore[arg-type]
        PHASE_SIX_OPERATIONS
        | EXPANDED_POST_EVALUATION_OPERATIONS
        | DEVIATION_ANALYSIS_OPERATIONS
    )
    for registration in registrations.values():
        Draft202012Validator.check_schema(registration.input_schema)
        Draft202012Validator.check_schema(registration.output_schema)
        assert registration.input_schema["additionalProperties"] is False
        assert registration.output_schema["additionalProperties"] is False
        assert registration.recovery_policy == "idempotent"


def _expanded_payload() -> dict[str, object]:
    return {
        "title": "扩展后评价",
        "evaluationPeriod": {"start": "2026-01-01", "end": "2026-06-30"},
        "contract": {
            "contractId": "contract-1",
            "contractName": "测试合同",
            "contractAmount": 100,
            "actualCost": 105,
            "currency": "CNY",
        },
        "documents": [
            {
                "documentId": "doc-contract",
                "category": "CONTRACT",
                "required": True,
                "status": "VALID",
            },
            {
                "documentId": "doc-acceptance",
                "category": "ACCEPTANCE",
                "required": True,
                "status": "VALID",
            },
        ],
        "obligations": [
            {
                "obligationId": "ob-1",
                "category": "交付",
                "timeliness": "LATE",
                "quality": "ACCEPTED",
            }
        ],
        "deviations": [
            {
                "deviationId": "dev-1",
                "category": "进度",
                "severity": "HIGH",
                "status": "OPEN",
                "costImpact": 5,
                "delayDays": 3,
            }
        ],
        "invoices": [
            {
                "invoiceId": "inv-1",
                "amount": 105,
                "contractMatched": True,
                "acceptanceMatched": True,
                "taxValid": True,
                "duplicate": False,
            }
        ],
        "risks": [
            {
                "riskId": "risk-1",
                "category": "履约",
                "level": "HIGH",
                "status": "OPEN",
                "actionOverdue": True,
            }
        ],
        "evidenceAvailability": {},
    }


def test_expanded_evidence_search_and_coverage_are_deterministic() -> None:
    documents = [
        {
            "documentId": "doc-1",
            "documentVersionId": "version-1",
            "name": "主合同",
            "category": "CONTRACT",
            "sha256": "a" * 64,
            "data": {"content": {"textExcerpt": "合同金额100万元, 乙方按期交付。"}},
            "evidence": [{"page": 1}],
        },
        {
            "documentId": "doc-2",
            "documentVersionId": "version-2",
            "name": "验收报告",
            "category": "ACCEPTANCE",
            "sha256": "b" * 64,
            "data": {"content": {"textExcerpt": "项目验收通过, 质量符合要求。"}},
            "evidence": [{"page": 2}],
        },
    ]

    search = search_evidence(documents, domain="contract")
    coverage = check_document_coverage(
        documents,
        [
            {"key": "contract", "category": "CONTRACT", "required": True},
            {"key": "acceptance", "category": "ACCEPTANCE", "required": True},
        ],
    )

    assert search["contentAvailableDocuments"] == 2
    assert search["hits"][0]["documentVersionId"] == "version-1"
    assert coverage["complete"] is True
    assert coverage["reviewRequired"] is False


def test_coverage_does_not_treat_embedded_metadata_as_readable_content() -> None:
    documents = [
        {
            "documentId": "doc-1",
            "documentVersionId": "version-1",
            "name": "扫描合同",
            "category": "CONTRACT",
            "sha256": "a" * 64,
            "data": {
                "content": {
                    "textExcerpt": "",
                    "tables": [],
                    "sheets": [],
                    "embeddedMetadata": {"filename": "scan.pdf"},
                    "needsOcr": True,
                }
            },
            "evidence": [],
        }
    ]

    coverage = check_document_coverage(
        documents,
        [{"key": "contract", "category": "CONTRACT", "required": True}],
    )

    assert coverage["contentAvailableCount"] == 0
    assert coverage["unreadableDocumentVersionIds"] == ["version-1"]
    assert coverage["reviewRequired"] is True


def test_expanded_domain_merge_and_diagnostics_preserve_fallbacks() -> None:
    payload = _expanded_payload()
    merged = merge_domain_analyses(
        payload,
        {
            "baseline": {
                "domain": "contract",
                "payloadPatch": {"contract": {"actualCost": 104}},
                "facts": [
                    {
                        "factId": "fact-1",
                        "factType": "actual_cost",
                        "value": 104,
                        "confidence": 0.95,
                        "evidenceRefs": ["version-1#page=1"],
                    }
                ],
                "conflicts": [],
                "missingEvidence": [],
            },
            "performance": {
                "domain": "performance",
                "payloadPatch": {},
                "facts": [],
                "conflicts": [],
                "missingEvidence": [],
            },
        },
    )
    normalized = merged["payload"]

    assert normalized["contract"]["contractAmount"] == 100
    assert normalized["contract"]["actualCost"] == 104
    assert calculate_timeline(normalized)["timelinessRate"] == 50
    assert reconcile_amounts(normalized)["overrunAmount"] == 4
    assert assure_invoices(normalized)["complianceRate"] == 100
    assert aggregate_deviations(normalized)["openHigh"] == 1
    assert aggregate_risks(normalized)["overdueActions"] == 1
    consistency = check_evidence_consistency(
        normalized, merged["evidenceFacts"], merged["conflicts"]
    )
    assert consistency["reviewRequired"] is False
    assert consistency["checkedFactCount"] == 1


def test_expanded_domain_merge_ignores_wrong_typed_model_patches() -> None:
    payload = _expanded_payload()

    merged = merge_domain_analyses(
        payload,
        {
            "baseline": {
                "domain": "contract",
                "payloadPatch": {
                    "documents": {"doc-1": {"status": "VALID"}},
                    "contract": {"actualCost": 104, "amendments": []},
                },
                "facts": [],
                "conflicts": [],
                "missingEvidence": [],
            }
        },
    )

    assert merged["payload"]["documents"] == payload["documents"]
    assert merged["payload"]["contract"]["actualCost"] == payload["contract"]["actualCost"]
    assert merged["conflicts"] == [
        "baseline returned invalid contract values; retained base payload",
        "baseline returned invalid documents patch; retained base payload",
    ]


@pytest.mark.asyncio
async def test_evaluation_drops_model_annotations_before_scoring() -> None:
    payload = _expanded_payload()
    payload["contract"]["amendments"] = [{"amendmentId": "a-1"}]
    payload["deviations"][0]["evidence"] = "version-1"
    payload["risks"][0]["remediationStatus"] = "PENDING"

    result = await post_evaluation_evaluate(
        {
            "payload": payload,
            "configuration": {},
            "attachmentManifestHash": "manifest",
        },
        "effect-score",
    )

    assert result["schemaVersion"] == "schema://contract/post-evaluation-result@1"
    assert result["contractId"] == "contract-1"


@pytest.mark.asyncio
async def test_expanded_result_is_frozen_and_rendered_as_pdf() -> None:
    score = await post_evaluation_evaluate(
        {
            "payload": _expanded_payload(),
            "configuration": {},
            "attachmentManifestHash": "manifest",
        },
        "effect-score",
    )
    result = finalize_expanded_result(
        score=score,
        review={
            "reviewRequired": False,
            "reasons": [],
            "acceptedFactIds": ["fact-1"],
            "rejectedFactIds": [],
        },
        narrative={
            "executiveSummary": "测试合同后评价已完成。",
            "dimensionNarratives": {"COST_CONTROL": "存在轻微超支。"},
            "recommendations": ["跟踪整改闭环。"],
        },
        coverage={
            "complete": True,
            "reviewRequired": False,
            "documentCount": 2,
            "contentAvailableCount": 2,
            "requirements": [],
            "missingRequired": [],
            "unreadableDocumentVersionIds": [],
            "duplicateSha256": [],
            "warnings": [],
        },
        consistency={
            "reviewRequired": False,
            "conflicts": [],
            "warnings": [],
            "unsupportedFactIds": [],
            "lowConfidenceFactIds": [],
            "duplicateIds": {},
            "checkedFactCount": 1,
        },
        diagnostics={"timeline": {"dueCount": 1}},
        provenance={"documentContentHash": "a" * 64},
    )
    pdf = await post_evaluation_report_render_v2(
        {"title": "扩展后评价", "result": result}, "effect-report"
    )
    cjk_pdf = await post_evaluation_report_render_v3(
        {"title": "扩展后评价", "result": result}, "effect-report-v3"
    )

    assert result["schemaVersion"] == "schema://contract/post-evaluation-result@2"
    assert result["executiveSummary"] == "测试合同后评价已完成。"
    assert result["evidenceSummary"]["documentCount"] == 2
    assert base64.b64decode(pdf["contentBase64"]).startswith(b"%PDF-")
    assert base64.b64decode(cjk_pdf["contentBase64"]).startswith(b"%PDF-")
    assert b"STSong-Light" in base64.b64decode(cjk_pdf["contentBase64"])


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
async def test_bound_document_reader_uses_readable_review_required_processing_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import swarmcore_application.capability_tool_executors as executors_module

    tenant_id = uuid4()
    project_id = uuid4()
    evaluation_id = uuid4()
    document_id = uuid4()
    version_id = uuid4()
    blob_id = uuid4()
    snapshot = SimpleNamespace(sha256="a" * 64, blob_id=blob_id)
    version = SimpleNamespace(
        id=version_id,
        business_document_id=document_id,
        blob_id=blob_id,
        sha256="a" * 64,
        filename="contract.txt",
        media_type="text/plain",
        size_bytes=8,
        version=1,
    )
    document = SimpleNamespace(id=document_id, name="合同", category="CONTRACT")
    processing = SimpleNamespace(
        result={
            "status": "READY",
            "content": {
                "textExcerpt": "合同内容" * 600,
                "pages": [{"number": 1, "text": "合同内容"}],
                "paragraphs": [{"text": "合同内容"}],
            },
        },
        evidence=[{"documentVersionId": str(version_id)}],
    )
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[snapshot, version, document, processing])

    @asynccontextmanager
    async def fake_transaction(*args: object, **kwargs: object) -> AsyncIterator[MagicMock]:
        del args, kwargs
        yield session

    monkeypatch.setattr(executors_module, "tenant_transaction", fake_transaction)
    context = SimpleNamespace(tenant_id=str(tenant_id), project_id=str(project_id))

    result = await BoundDocumentReadExecutor(None).execute(  # type: ignore[arg-type]
        {
            "evaluationId": str(evaluation_id),
            "documents": [{"documentVersionId": str(version_id)}],
        },
        "effect-read",
        context,
    )

    processing_query = session.scalar.call_args_list[3].args[0]
    processing_statuses = str(processing_query.compile().params)
    assert "READY" in processing_statuses
    assert "REVIEW_REQUIRED" in processing_statuses
    assert len(result["documents"][0]["data"]["content"]["textExcerpt"]) == 2_000
    assert result["documents"][0]["data"]["content"]["textTruncated"] is True
    assert "pages" not in result["documents"][0]["data"]["content"]
    assert "paragraphs" not in result["documents"][0]["data"]["content"]
    assert result["documents"][0]["evidence"] == [
        {"documentVersionId": str(version_id)}
    ]


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
async def test_deviation_recorder_persists_same_frozen_result_as_json_and_pdf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import swarmcore_application.capability_tool_executors as executors_module

    result = {
        "schemaVersion": "schema://deviation-analysis/result@1",
        "title": "项目偏差分析",
        "subject": {"subjectId": "P-1", "subjectType": "project"},
        "period": {"start": "2026-01-01", "end": "2026-06-30"},
        "asOf": "2026-06-30",
        "qualityStatus": "READY",
        "reviewRequired": False,
        "dimensions": {
            "TIME": {
                "status": "OK",
                "metrics": {"maximumDelayDays": 2},
                "reasons": [],
                "evidenceRefs": ["doc:v1:p1"],
            }
        },
        "rootCauses": [],
        "trends": {"status": "DATA_INSUFFICIENT", "points": []},
        "responsibility": {
            "status": "NO_PROPOSAL",
            "proposals": [],
            "decisions": [],
            "humanConfirmationRequired": False,
        },
        "assessment": {
            "subjectId": "P-1",
            "periodStart": "2026-01-01",
            "periodEnd": "2026-06-30",
            "asOf": "2026-06-30",
            "baselineHash": "b",
            "selectionManifestHash": "s",
        },
        "coverage": {"complete": True},
        "time": {
            "status": "OK",
            "metrics": {"maximumDelayDays": 2},
            "reasons": [],
            "evidenceRefs": ["doc:v1:p1"],
        },
        "content": {
            "status": "NOT_APPLICABLE",
            "metrics": {},
            "reasons": ["dimension not requested"],
            "evidenceRefs": [],
        },
        "cost": {
            "status": "NOT_APPLICABLE",
            "metrics": {},
            "reasons": ["dimension not requested"],
            "evidenceRefs": [],
        },
        "findings": [
            {
                "code": "TIME_OK",
                "dimension": "TIME",
                "status": "OK",
                "material": True,
                "evidenceRefs": ["doc:v1:p1"],
            }
        ],
        "actions": [],
        "evidence": ["doc:v1:p1"],
        "qualityFlags": [],
        "evidenceReview": {"reviewRequired": False, "reasons": []},
        "narrative": {"executiveSummary": "总体偏差可控。"},
        "provenance": {
            "documentContentHash": "d",
            "attachmentManifestHash": "a",
            "selectionManifestHash": "s",
            "baselineHash": "b",
            "configurationHash": "c",
            "agents": [],
        },
        "artifacts": [],
    }
    rendered = await deviation_report_render({"result": result}, "effect-report")
    pdf_content = base64.b64decode(rendered["contentBase64"])
    assert pdf_content.startswith(b"%PDF-")
    assert b"/FontFile2" in pdf_content

    tenant_id = uuid4()
    project_id = uuid4()
    evaluation_id = uuid4()
    evaluation = MagicMock(spec=Evaluation)
    evaluation.id = evaluation_id
    evaluation.work_item_id = uuid4()
    evaluation.result = None
    evaluation.status = "RUNNING"
    evaluation.report_template_version = "report://deviation-analysis@1"
    evaluation.output_schema_version = "schema://deviation-analysis/result@1"
    item = MagicMock(spec=WorkItem)
    item.id = evaluation.work_item_id
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[evaluation, item])
    scalar_result = MagicMock()
    scalar_result.all.return_value = []
    session.scalars = AsyncMock(return_value=scalar_result)
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
    receipt = await DeviationRecorderExecutor(None).execute(  # type: ignore[arg-type]
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
    assert evaluation.status == "SUCCEEDED"
    assert item.status == "COMPLETED"
    assert any(
        isinstance(call.args[0], Finding)
        for call in session.add.call_args_list
        if call.args
    )
    assert receipt["recorded"] is True


@pytest.mark.asyncio
async def test_cross_file_consistency_rejects_invalid_structured_results() -> None:
    with pytest.raises(ValueError):
        await cross_file_consistency(
            {"results": [{"status": "COMPLETED"}], "rules": []}, "effect-1"
        )
