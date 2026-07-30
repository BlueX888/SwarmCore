from __future__ import annotations

from io import BytesIO
from typing import Any

from pypdf import PdfReader
from swarmcore_application import (
    assess_document_readability,
    compose_formal_post_evaluation_report,
    finalize_formal_report_quality,
    render_formal_post_evaluation_pdf,
    verify_report_citations,
)

DIMENSIONS = (
    ("DOCUMENT_COMPLETENESS", "文件完整性"),
    ("DELIVERY_TIMELINESS", "进度履约"),
    ("DELIVERY_QUALITY", "质量履约"),
    ("COST_CONTROL", "成本控制"),
    ("INVOICE_COMPLIANCE", "发票合规"),
    ("DEVIATION_GOVERNANCE", "偏差治理"),
    ("RISK_GOVERNANCE", "风险治理"),
)


def _source_result() -> dict[str, Any]:
    return {
        "schemaVersion": "schema://contract/post-evaluation-result@2",
        "contractId": "DEMO-C-001",
        "evaluationPeriod": {"start": "2026-01-01", "end": "2026-06-30"},
        "overallScore": 85,
        "grade": "良好",
        "riskLevel": "LOW",
        "passed": True,
        "reviewRequired": False,
        "executiveSummary": "采购合同总体履约稳定。",
        "dimensions": [
            {
                "code": code,
                "name": name,
                "weight": 14 if index < 6 else 16,
                "score": 85,
                "status": "PASS",
                "summary": "该维度履约表现稳定。",
                "metrics": {},
                "evidenceRefs": ["document:contract-main"],
            }
            for index, (code, name) in enumerate(DIMENSIONS)
        ],
        "findings": [],
        "provenance": {},
    }


def _formal_result() -> dict[str, object]:
    source = _source_result()
    coverage = {
        "documentCount": 10,
        "contentAvailableCount": 9,
        "missingRequired": [],
        "complete": True,
        "warnings": [],
    }
    readability = assess_document_readability(coverage)
    report = compose_formal_post_evaluation_report(
        title="采购合同履约后评价报告",
        result=source,
        readability=readability,
        section_drafts={},
        editorial={"recommendations": ["持续跟踪关键里程碑。"]},
        review={"acceptedFactIds": ["document:contract-main"]},
        coverage=coverage,
        consistency={},
        diagnostics={},
        approval=None,
    )
    citations = verify_report_citations(report, source)
    return finalize_formal_report_quality(
        source_result=source,
        report_document=report,
        citation_check=citations,
        model_review={"issues": []},
        readability=readability,
    )


def test_readability_gate_downgrades_below_eighty_percent() -> None:
    result = assess_document_readability(
        {
            "documentCount": 10,
            "contentAvailableCount": 7,
            "missingRequired": [],
        }
    )

    assert result["formalEligible"] is False
    assert result["reportMode"] == "PRE_REVIEW_REPORT"
    assert result["readabilityRate"] == 0.7


def test_formal_report_has_seven_sections_and_passes_quality_gate() -> None:
    result = _formal_result()

    assert result["schemaVersion"] == "schema://contract/post-evaluation-result@3"
    assert result["readabilityGate"]["reportMode"] == "FORMAL_REPORT"
    assert len(result["reportDocument"]["dimensionSections"]) == 7
    assert result["reportQuality"]["passed"] is True
    assert result["reportQuality"]["checks"]["scoreConsistency"] is True


def test_formal_report_normalizes_timeline_and_internal_evidence_terms() -> None:
    source = _source_result()
    source["dimensions"][0]["evidenceRefs"] = []
    source["passed"] = False
    source["reviewRequired"] = True
    coverage = {
        "documentCount": 10,
        "contentAvailableCount": 9,
        "missingRequired": [],
        "complete": True,
        "warnings": ["1 document(s) have no readable processed content"],
    }
    readability = assess_document_readability(coverage)

    report = compose_formal_post_evaluation_report(
        title="采购合同履约后评价报告",
        result=source,
        readability=readability,
        section_drafts={},
        editorial={
            "executiveSummary": "评价结论为通过且无需复核，holistic analysis 已完成。",
            "dimensionNarratives": {
                "DOCUMENT_COMPLETENESS": (
                    "依据E001与UUID归档记录形成结论。"
                    + " document:contract-main" * 5
                )
            }
        },
        review={"acceptedFactIds": ["document:contract-main"]},
        coverage=coverage,
        consistency={
            "conflicts": [
                "Contract document version 019fa16f-2801-77c1-b77a-80a65239bfca "
                "is UNREADABLE, preventing full verification of delivery milestones",
                "Four INVOICE category documents exist but evidence confirms these contain only "
                "blank templates and samples, not actual transaction invoices",
            ],
            "warnings": [
                "baseline returned invalid contract values; retained base payload"
            ],
        },
        diagnostics={
            "timeline": {
                "dueCount": 2,
                "onTime": 2,
                "late": 0,
            }
        },
        approval=None,
    )

    conclusion = report["dimensionSections"][0]["conclusion"]
    assert report["timeline"][0]["status"] == "到期2项，按期2项，延期0项"
    assert "E001" not in conclusion
    assert "UUID" not in conclusion
    assert "缺少直接业务凭证" in conclusion
    assert conclusion.count("受控归档资料") <= 1
    assert "通过且无需复核" not in report["managementSummary"]["executiveSummary"]
    assert "待人工复核" in report["managementSummary"]["executiveSummary"]
    assert "整体性分析" in report["managementSummary"]["executiveSummary"]
    assert report["evidenceAndLimitations"]["conflicts"] == [
        "一份合同类归档资料不可读取，无法完整核验交付、验收及合同条款。",
        "发票类资料仅包含空白票样和测试说明，不属于本合同的真实交易发票。",
    ]
    assert "有1份资料未提取到可读正文。" in report["evidenceAndLimitations"]["limitations"]
    assert "部分 Agent 的结构化输出未通过约束校验" in " ".join(
        report["evidenceAndLimitations"]["limitations"]
    )
    assert all(
        set(item) == {"label"}
        for item in report["evidenceAndLimitations"]["evidenceIndex"]
    )
    assert all(
        set(citation) == {"label"}
        for section in report["dimensionSections"]
        for citation in section["evidenceCitations"]
    )


def test_quality_gate_does_not_publish_raw_english_review_diagnostics() -> None:
    source = _source_result()
    coverage = {
        "documentCount": 10,
        "contentAvailableCount": 9,
        "missingRequired": [],
        "complete": True,
        "warnings": [],
    }
    readability = assess_document_readability(coverage)
    report = compose_formal_post_evaluation_report(
        title="采购合同履约后评价报告",
        result=source,
        readability=readability,
        section_drafts={},
        editorial={},
        review={"acceptedFactIds": ["document:contract-main"]},
        coverage=coverage,
        consistency={},
        diagnostics={},
        approval=None,
    )
    citations = verify_report_citations(report, source)

    result = finalize_formal_report_quality(
        source_result=source,
        report_document=report,
        citation_check=citations,
        model_review={
            "issues": [
                {
                    "severity": "WARNING",
                    "detail": "Contains untranslated placeholder text and raw internal identifiers "
                    "instead of proper document descriptions in a formal business report.",
                }
            ]
        },
        readability=readability,
    )

    warnings = result["reportQuality"]["warnings"]
    assert warnings == [
        "自动审查发现非阻断性表达问题，详细诊断已保存在运行审计记录中。"
    ]


def test_formal_report_corrects_model_claim_about_insufficient_dimension_weight() -> None:
    source = _source_result()
    insufficient_names = [name for _, name in DIMENSIONS[:4]]
    for dimension, weight in zip(source["dimensions"][:4], (10, 20, 15, 15), strict=True):
        dimension["score"] = None
        dimension["status"] = "DATA_INSUFFICIENT"
        dimension["weight"] = weight
    source["narrative"] = {
        "managementConclusions": [
            f"{'、'.join(insufficient_names)}数据不足，合计权重45%，需补充资料。"
        ],
        "limitations": [
            f"{'、'.join(insufficient_names)}无法评价，合计约占总权重45%。"
        ],
    }
    coverage = {
        "documentCount": 10,
        "contentAvailableCount": 10,
        "missingRequired": [],
        "complete": True,
        "warnings": [],
    }
    readability = assess_document_readability(coverage)

    report = compose_formal_post_evaluation_report(
        title="采购合同履约后评价报告",
        result=source,
        readability=readability,
        section_drafts={},
        editorial={
            "executiveSummary": (
                f"{'、'.join(insufficient_names)}数据不足，合计权重为45%。"
            )
        },
        review={},
        coverage=coverage,
        consistency={},
        diagnostics={},
        approval=None,
    )

    visible = str(report)
    assert "45%" not in visible
    assert visible.count("合计权重60%") == 3


def test_formal_report_pdf_is_deterministic_and_business_sized() -> None:
    result = _formal_result()

    first = render_formal_post_evaluation_pdf(result)
    second = render_formal_post_evaluation_pdf(result)
    reader = PdfReader(BytesIO(first))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert first == second
    assert first.startswith(b"%PDF-")
    assert len(reader.pages) >= 14
    assert "管理层摘要" in text
    assert "整改行动计划" in text
    assert "合同履约总体良好" not in text
