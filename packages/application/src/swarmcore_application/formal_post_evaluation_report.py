"""Business-grade contract post-evaluation report composition and rendering."""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from datetime import date, timedelta
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont, TTFError
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DIMENSION_ORDER = (
    "DOCUMENT_COMPLETENESS",
    "DELIVERY_TIMELINESS",
    "DELIVERY_QUALITY",
    "COST_CONTROL",
    "INVOICE_COMPLIANCE",
    "DEVIATION_GOVERNANCE",
    "RISK_GOVERNANCE",
)
DIMENSION_NAMES = {
    "DOCUMENT_COMPLETENESS": "文件完整性",
    "DELIVERY_TIMELINESS": "进度履约",
    "DELIVERY_QUALITY": "质量履约",
    "COST_CONTROL": "成本控制",
    "INVOICE_COMPLIANCE": "发票合规",
    "DEVIATION_GOVERNANCE": "偏差治理",
    "RISK_GOVERNANCE": "风险治理",
}
REQUIRED_REPORT_SECTIONS = (
    "managementSummary",
    "contractProfile",
    "methodology",
    "dimensionOverview",
    "dimensionSections",
    "timeline",
    "financialAnalysis",
    "invoiceAnalysis",
    "deviationAndRisk",
    "evidenceAndLimitations",
    "remediationPlan",
    "approval",
    "provenance",
)
INTERNAL_TOKEN_PATTERN = re.compile(
    r"(?:DEMO-SUPPLEMENT|PUBLIC-CORE|MISSING:|tool://|agent://|schema://)"
)


def assess_document_readability(
    coverage: dict[str, Any], *, formal_threshold: float = 0.8
) -> dict[str, Any]:
    document_count = max(0, int(coverage.get("documentCount") or 0))
    readable_count = max(0, int(coverage.get("contentAvailableCount") or 0))
    rate = readable_count / document_count if document_count else 0.0
    formal_eligible = (
        document_count > 0
        and rate >= formal_threshold
        and not coverage.get("missingRequired")
    )
    reasons: list[str] = []
    if document_count == 0:
        reasons.append("未冻结任何业务资料。")
    if rate < formal_threshold:
        reasons.append(
            f"资料正文可读取率为{rate:.1%}，低于正式报告门槛{formal_threshold:.0%}。"
        )
    if coverage.get("missingRequired"):
        reasons.append("存在缺失的必备资料。")
    return {
        "documentCount": document_count,
        "readableDocumentCount": readable_count,
        "readabilityRate": round(rate, 4),
        "formalThreshold": formal_threshold,
        "formalEligible": formal_eligible,
        "reportMode": "FORMAL_REPORT" if formal_eligible else "PRE_REVIEW_REPORT",
        "reasons": reasons,
    }


def compose_formal_post_evaluation_report(
    *,
    title: str,
    result: dict[str, Any],
    readability: dict[str, Any],
    section_drafts: dict[str, dict[str, Any]],
    editorial: dict[str, Any],
    review: dict[str, Any],
    coverage: dict[str, Any],
    consistency: dict[str, Any],
    diagnostics: dict[str, Any],
    approval: dict[str, Any] | None,
) -> dict[str, Any]:
    dimensions = [
        deepcopy(item)
        for item in result.get("dimensions", [])
        if isinstance(item, dict)
    ]
    by_code = {str(item.get("code")): item for item in dimensions}
    evidence_refs = _collect_evidence_refs(result, review, consistency)
    evidence_index = {
        ref: {
            "code": f"E{index:03d}",
            "label": _human_evidence_label(ref),
            "sourceRef": ref,
        }
        for index, ref in enumerate(evidence_refs, start=1)
    }
    dimension_narratives = dict(editorial.get("dimensionNarratives") or {})
    for draft in section_drafts.values():
        if isinstance(draft, dict):
            dimension_narratives.update(draft.get("dimensionNarratives") or {})
    dimensions_out: list[dict[str, Any]] = []
    for code in DIMENSION_ORDER:
        dimension = by_code.get(code, {})
        refs = [
            str(value)
            for value in dimension.get("evidenceRefs", [])
            if str(value).strip()
        ]
        finding_items = [
            item
            for item in result.get("findings", [])
            if isinstance(item, dict) and item.get("dimension") == code
        ]
        narrative = str(dimension_narratives.get(code) or "").strip()
        if not narrative:
            narrative = _dimension_fallback(dimension)
        conclusion = _sanitize_text(narrative, evidence_index)
        citation_labels = list(
            dict.fromkeys(
                evidence_index[ref]["label"] for ref in refs if ref in evidence_index
            )
        )
        if not refs:
            conclusion = (
                f"{conclusion} 本维度缺少直接业务凭证，当前得分仅反映结构化记录的"
                "零异常结果，不代表已完成实质合规核验。"
            )
        dimensions_out.append(
            {
                "code": code,
                "name": str(dimension.get("name") or DIMENSION_NAMES[code]),
                "weight": int(dimension.get("weight") or 0),
                "score": dimension.get("score"),
                "status": str(dimension.get("status") or "DATA_INSUFFICIENT"),
                "conclusion": conclusion,
                "summary": _sanitize_text(
                    str(dimension.get("summary") or "暂无评价摘要。"), evidence_index
                ),
                "metrics": deepcopy(dimension.get("metrics") or {}),
                "evidenceCitations": [
                    {"label": label}
                    for label in citation_labels
                ],
                "risks": [
                    _sanitize_text(str(item.get("detail") or item.get("title") or ""), evidence_index)
                    for item in finding_items
                ],
            }
        )

    recommendations = [
        _sanitize_text(str(value), evidence_index)
        for value in editorial.get("recommendations", [])
        if str(value).strip()
    ]
    if not recommendations:
        recommendations = _fallback_recommendations(result)
    remediation = _build_remediation_plan(
        recommendations, dimensions_out, result.get("evaluationPeriod") or {}
    )
    timeline = _timeline_rows(diagnostics.get("timeline"))
    financial = _financial_analysis(diagnostics.get("amounts"), result)
    invoices = _invoice_analysis(diagnostics.get("invoices"))
    deviations_and_risks = _deviation_risk_analysis(
        diagnostics.get("deviations"), diagnostics.get("risks")
    )
    executive_summary = str(editorial.get("executiveSummary") or "").strip()
    if not executive_summary:
        executive_summary = str(result.get("executiveSummary") or "").strip()
    executive_summary = _sanitize_text(executive_summary, evidence_index)
    executive_summary = _normalize_management_outcome(executive_summary, result)
    source_narrative = result.get("narrative") or {}
    management_conclusions = [
        _sanitize_text(str(value), evidence_index)
        for value in source_narrative.get("managementConclusions", [])
        if str(value).strip()
    ]
    key_findings = [
        _sanitize_text(str(item.get("detail") or item.get("title") or ""), evidence_index)
        for item in result.get("findings", [])
        if isinstance(item, dict)
    ]
    limitations = [
        _sanitize_text(str(value), evidence_index)
        for value in editorial.get("limitations", [])
        if str(value).strip()
    ]
    limitations.extend(
        _sanitize_text(str(value), evidence_index)
        for value in source_narrative.get("limitations", [])
        if str(value).strip()
    )
    limitations.extend(
        _sanitize_text(str(value), evidence_index) for value in readability.get("reasons", [])
    )
    limitations.extend(
        _sanitize_text(str(value), evidence_index) for value in coverage.get("warnings", [])
    )
    limitations.extend(
        _sanitize_text(str(value), evidence_index) for value in consistency.get("warnings", [])
    )
    limitations = list(dict.fromkeys(value for value in limitations if value))
    contract_id = _display_identifier(str(result.get("contractId") or "未提供"))
    period = deepcopy(result.get("evaluationPeriod") or {})
    report_no_seed = json.dumps(
        {
            "contractId": result.get("contractId"),
            "period": period,
            "title": title,
        },
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    report_number = f"CPE-{hashlib.sha256(report_no_seed).hexdigest()[:12].upper()}"
    approval_value = approval or {}
    approval_comment = _sanitize_text(
        str(approval_value.get("comment") or "本次运行未触发人工批准。"),
        evidence_index,
    )
    report_document = {
        "schemaVersion": "schema://report/contract-post-evaluation-document@1",
        "title": title,
        "reportNumber": report_number,
        "version": "1.0",
        "reportMode": readability.get("reportMode", "PRE_REVIEW_REPORT"),
        "formalEligible": bool(readability.get("formalEligible")),
        "contractProfile": {
            "contractId": contract_id,
            "evaluationStart": period.get("start"),
            "evaluationEnd": period.get("end"),
            "contractAmount": financial.get("contractAmount"),
            "actualCost": financial.get("actualCost"),
            "currency": financial.get("currency", "CNY"),
        },
        "managementSummary": {
            "overallScore": result.get("overallScore"),
            "grade": result.get("grade"),
            "riskLevel": result.get("riskLevel"),
            "passed": bool(result.get("passed")),
            "reviewRequired": bool(result.get("reviewRequired")),
            "executiveSummary": executive_summary,
            "keyFindings": [*management_conclusions, *key_findings],
            "dataQualityNotice": "；".join(readability.get("reasons", []))
            or "资料可读率满足正式报告门槛。",
        },
        "methodology": {
            "description": (
                "本报告以冻结文件版本为证据源，由领域 Agent 提取事实，"
                "确定性工具完成七维评分、金额、发票、偏差和风险计算；"
                "模型仅负责解释已冻结结果，不能修改分数、等级和证据。"
            ),
            "dimensionCount": len(dimensions_out),
            "weightsTotal": sum(item["weight"] for item in dimensions_out),
            "readabilityThreshold": readability.get("formalThreshold"),
        },
        "dimensionOverview": [
            {
                "code": item["code"],
                "name": item["name"],
                "weight": item["weight"],
                "score": item["score"],
                "status": item["status"],
            }
            for item in dimensions_out
        ],
        "dimensionSections": dimensions_out,
        "timeline": timeline,
        "financialAnalysis": financial,
        "invoiceAnalysis": invoices,
        "deviationAndRisk": deviations_and_risks,
        "evidenceAndLimitations": {
            "documentCount": int(coverage.get("documentCount") or 0),
            "readableDocumentCount": int(coverage.get("contentAvailableCount") or 0),
            "readabilityRate": readability.get("readabilityRate"),
            "coverageComplete": bool(coverage.get("complete")),
            "conflicts": list(
                dict.fromkeys(
                    _sanitize_text(str(value), evidence_index)
                    for value in consistency.get("conflicts", [])
                    if str(value).strip()
                )
            ),
            "limitations": limitations,
            "evidenceIndex": [
                {"label": label}
                for label in dict.fromkeys(
                    item["label"] for item in evidence_index.values()
                )
            ],
        },
        "remediationPlan": remediation,
        "approval": {
            "required": bool(result.get("reviewRequired")),
            "status": "APPROVED"
            if approval_value.get("approved") is True
            else "NOT_REQUIRED"
            if not result.get("reviewRequired")
            else "PENDING",
            "comment": approval_comment,
        },
        "provenance": {
            **deepcopy(result.get("provenance") or {}),
            "scoreSchemaVersion": result.get("schemaVersion"),
            "reportComposer": "tool://report/compose-post-evaluation@1",
        },
    }
    return report_document


def verify_report_citations(
    report_document: dict[str, Any], source_result: dict[str, Any]
) -> dict[str, Any]:
    index = report_document.get("evidenceAndLimitations", {}).get("evidenceIndex", [])
    index_labels = {
        str(item.get("label"))
        for item in index
        if isinstance(item, dict) and item.get("label")
    }
    cited_labels: set[str] = set()
    missing_citations: list[str] = []
    for section in report_document.get("dimensionSections", []):
        if not isinstance(section, dict):
            continue
        citations = section.get("evidenceCitations") or []
        if not citations:
            missing_citations.append(str(section.get("name") or section.get("code")))
        for citation in citations:
            if isinstance(citation, dict) and citation.get("label"):
                cited_labels.add(str(citation["label"]))
    unknown = sorted(cited_labels - index_labels)
    source_scores = {
        str(item.get("code")): item.get("score")
        for item in source_result.get("dimensions", [])
        if isinstance(item, dict)
    }
    report_scores = {
        str(item.get("code")): item.get("score")
        for item in report_document.get("dimensionOverview", [])
        if isinstance(item, dict)
    }
    score_mismatches = sorted(
        code
        for code, value in source_scores.items()
        if code not in report_scores or report_scores[code] != value
    )
    return {
        "passed": not unknown and not score_mismatches,
        "indexedEvidenceCount": len(index_labels),
        "citedEvidenceCount": len(cited_labels),
        "unknownCitationCodes": unknown,
        "dimensionsWithoutCitations": missing_citations,
        "scoreMismatches": score_mismatches,
    }


def finalize_formal_report_quality(
    *,
    source_result: dict[str, Any],
    report_document: dict[str, Any],
    citation_check: dict[str, Any],
    model_review: dict[str, Any],
    readability: dict[str, Any],
) -> dict[str, Any]:
    blocking: list[str] = []
    warnings: list[str] = []
    missing_sections = [
        section for section in REQUIRED_REPORT_SECTIONS if section not in report_document
    ]
    if missing_sections:
        blocking.append(f"缺少报告章节：{', '.join(missing_sections)}")
    overview = report_document.get("dimensionOverview") or []
    sections = report_document.get("dimensionSections") or []
    if len(overview) != 7 or len(sections) != 7:
        blocking.append("七维评价章节不完整。")
    if citation_check.get("scoreMismatches"):
        blocking.append("报告分数与冻结 Evaluation 不一致。")
    if citation_check.get("unknownCitationCodes"):
        blocking.append("报告包含未登记的证据引用。")
    if citation_check.get("dimensionsWithoutCitations"):
        warnings.append(
            "部分评价维度缺少直接证据引用："
            + "、".join(citation_check["dimensionsWithoutCitations"])
        )
    visible_text = _visible_report_text(report_document)
    if INTERNAL_TOKEN_PATTERN.search(visible_text):
        blocking.append("面向业务人员的正文仍包含内部标识符。")
    for issue in model_review.get("issues", []):
        if not isinstance(issue, dict):
            continue
        detail = str(issue.get("detail") or issue.get("message") or "").strip()
        if not detail:
            continue
        if str(issue.get("severity") or "").upper() in {"BLOCKING", "CRITICAL"}:
            blocking.append(detail)
        else:
            warnings.append(_business_quality_warning(detail))
    if not readability.get("formalEligible"):
        warnings.append("资料可读率不足，报告已降级为资料质量预审报告。")
    passed = not blocking
    quality = {
        "passed": passed,
        "blockingIssues": list(dict.fromkeys(blocking)),
        "warnings": list(dict.fromkeys(warnings)),
        "checks": {
            "requiredSections": not missing_sections,
            "sevenDimensions": len(overview) == 7 and len(sections) == 7,
            "scoreConsistency": not citation_check.get("scoreMismatches"),
            "citationIntegrity": not citation_check.get("unknownCitationCodes"),
            "businessFacingLanguage": not INTERNAL_TOKEN_PATTERN.search(visible_text),
            "formalEligibility": bool(readability.get("formalEligible")),
        },
    }
    result = deepcopy(source_result)
    result["schemaVersion"] = "schema://contract/post-evaluation-result@3"
    result["readabilityGate"] = deepcopy(readability)
    result["reportDocument"] = deepcopy(report_document)
    result["reportQuality"] = quality
    return result


def render_formal_post_evaluation_pdf(result: dict[str, Any]) -> bytes:
    quality = dict(result.get("reportQuality") or {})
    if not quality.get("passed"):
        raise ValueError("REPORT_QUALITY_GATE_FAILED")
    report = dict(result["reportDocument"])
    font = _register_business_font()
    stream = BytesIO()
    document = SimpleDocTemplate(
        stream,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=str(report.get("title") or "合同履约后评价报告"),
        author="SwarmCore",
        subject="合同履约后评价",
    )
    styles = _report_styles(font)
    story: list[Any] = []
    _build_cover(story, report, styles)
    _build_toc(story, styles)
    _build_management_summary(story, report, styles)
    _build_contract_and_methodology(story, report, styles)
    _build_dimension_overview(story, report, styles, font)
    for section in report.get("dimensionSections", []):
        _build_dimension_section(story, section, styles)
    _build_timeline(story, report, styles)
    _build_finance_and_invoice(story, report, styles)
    _build_deviation_and_risk(story, report, styles)
    _build_evidence_and_limitations(story, report, styles)
    _build_remediation(story, report, styles)
    _build_approval_and_provenance(story, report, quality, styles)

    def canvas_factory(filename: Any, **kwargs: Any) -> Canvas:
        kwargs["invariant"] = 1
        return Canvas(filename, **kwargs)

    def page_decorator(canvas: Canvas, doc: Any) -> None:
        canvas.saveState()
        if doc.page > 1:
            canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
            canvas.line(18 * mm, A4[1] - 14 * mm, A4[0] - 18 * mm, A4[1] - 14 * mm)
            canvas.setFont(font, 8)
            canvas.setFillColor(colors.HexColor("#64748B"))
            canvas.drawString(18 * mm, A4[1] - 11 * mm, "合同履约后评价报告")
            canvas.drawRightString(
                A4[0] - 18 * mm,
                A4[1] - 11 * mm,
                str(report.get("reportNumber") or ""),
            )
            canvas.drawCentredString(A4[0] / 2, 10 * mm, f"第 {doc.page} 页")
        if report.get("reportMode") == "PRE_REVIEW_REPORT":
            canvas.saveState()
            canvas.setFillColor(colors.Color(0.85, 0.1, 0.1, alpha=0.08))
            canvas.setFont(font, 42)
            canvas.translate(A4[0] / 2, A4[1] / 2)
            canvas.rotate(35)
            canvas.drawCentredString(0, 0, "资料质量预审")
            canvas.restoreState()
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=page_decorator,
        onLaterPages=page_decorator,
        canvasmaker=canvas_factory,
    )
    return stream.getvalue()


def _collect_evidence_refs(
    result: dict[str, Any], review: dict[str, Any], consistency: dict[str, Any]
) -> list[str]:
    values: list[str] = []
    for dimension in result.get("dimensions", []):
        if isinstance(dimension, dict):
            values.extend(str(value) for value in dimension.get("evidenceRefs", []))
    for finding in result.get("findings", []):
        if isinstance(finding, dict):
            values.extend(str(value) for value in finding.get("evidenceRefs", []))
    values.extend(str(value) for value in review.get("acceptedFactIds", []))
    values.extend(str(value) for value in review.get("rejectedFactIds", []))
    values.extend(str(value) for value in consistency.get("unsupportedFactIds", []))
    return list(dict.fromkeys(value for value in values if value.strip()))


def _human_evidence_label(value: str) -> str:
    if re.fullmatch(
        r"[A-Fa-f0-9]{8}(?:-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12}",
        value,
    ):
        return "受控归档资料"
    _, _, suffix = value.partition(":")
    readable = suffix or value
    readable = readable.replace("_", " ").replace("-", " ").strip()
    translations = {
        "AWARD NOTICE": "中标通知",
        "SIGNED CONTRACT LOT 4": "签署合同",
        "ACCEPTANCE REPORT": "验收报告",
        "REAL TRANSACTION INVOICE": "真实交易发票",
        "PERFORMANCE REGISTER": "履约登记",
        "COST PAYMENT REGISTER": "成本付款登记",
        "DEVIATION REGISTER": "偏差登记",
        "FACT UNREADABLE DOC 001": "不可读资料标识",
        "DELIVERY LOT4 QUALITY": "标段4交付质量记录",
        "DELIVERY LOT4 TIMELINESS": "标段4交付时效记录",
        "ACCEPTANCE LOT4 QUALITY": "标段4验收质量记录",
        "ACCEPTANCE LOT4 TIMELINESS": "标段4验收时效记录",
        "SERVICE LOT4 QUALITY": "标段4服务质量记录",
        "SERVICE LOT4 TIMELINESS": "标段4服务时效记录",
        "EVIDENCE COVERAGE DELIVERY": "交付证据覆盖情况",
        "PROJECT IDENTITY CONFLICT": "项目身份冲突",
        "CONTRACT DOCUMENT ACCESSIBILITY": "合同资料可读性",
        "CONTRACT ID": "合同编号",
        "CONTRACT NAME": "合同名称",
        "FACT CONTRACT CHANGE 001": "合同变更事实",
        "FACT SUPPLIER PENALTY 001": "供应商处罚事实",
        "GAP 002": "证据缺口二",
        "GAP 003": "证据缺口三",
        "PERF CONTRACT ID": "履约合同编号",
        "PERF EVAL START": "评价期开始日期",
        "PERF EVAL END": "评价期结束日期",
        "PERF CONTRACT NAME": "履约合同名称",
        "PERF CONTRACT AMOUNT": "履约合同金额",
        "PERF ACTUAL COST": "实际发生成本",
        "PAYMENT EVIDENCE STATUS": "付款证据状态",
        "CONTRACT AMENDMENTS": "合同变更资料",
        "TAX EVIDENCE STATUS": "税务证据状态",
        "PERF DELIVERY STATUS": "交付状态",
        "PERF DELIVERY TIMELINESS": "交付时效",
        "PERF ACCEPTANCE STATUS": "验收状态",
        "PERF ACCEPTANCE TIMELINESS": "验收时效",
        "PERF SERVICE STATUS": "服务状态",
        "PERF SERVICE TIMELINESS": "服务时效",
        "PERF MILESTONE DELIVERY": "交付里程碑",
        "PERF MILESTONE ACCEPTANCE": "验收里程碑",
    }
    return translations.get(readable.upper(), readable.title() or "业务证据")


def _display_identifier(value: str) -> str:
    value = re.sub(r"^(?:DEMO[-_:]*)+", "", value, flags=re.IGNORECASE)
    return value or "未提供"


def _sanitize_text(value: str, evidence_index: dict[str, dict[str, str]]) -> str:
    text = _translate_operational_message(value)
    for code, name in DIMENSION_NAMES.items():
        text = text.replace(code, name)
    for ref, indexed in sorted(evidence_index.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(ref, f"证据“{indexed['label']}”")
    text = re.sub(
        r"(?<![A-Za-z0-9])E\d{3}(?![A-Za-z0-9])(?:（[^）]*）)?",
        "对应证据",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(?<![A-Za-z0-9])UUID(?![A-Za-z0-9])",
        "唯一标识",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{8}(?:-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12}(?![A-Fa-f0-9])",
        "对应归档文件",
        text,
    )
    text = re.sub(r"\bholistic analysis\b", "整体性分析", text, flags=re.IGNORECASE)
    text = re.sub(r"\bLOW\b", "低", text)
    text = text.replace("immediate履约障碍", "当前履约障碍")
    text = text.replace("basePayload", "案件基础数据")
    text = text.replace("documentVersionId", "归档版本标识")
    text = text.replace("retained base payload", "已保留案件基础数据")
    text = text.replace("Contract Id", "合同编号")
    text = text.replace("Contract Name", "合同名称")
    text = text.replace("Fact Contract Change 001", "合同变更事实")
    text = text.replace("Fact Supplier Penalty 001", "供应商处罚事实")
    text = text.replace("SPC统计过程控制", "统计过程控制（SPC）")
    controlled_reference = "证据“受控归档资料”"
    if text.count(controlled_reference) > 3:
        text = text.replace(controlled_reference, "")
        text = f"依据受控归档资料清单，{text}"
        text = re.sub(r"(?:[、,，;；]\s*){2,}", "，", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _translate_operational_message(value: str) -> str:
    text = value.strip()
    lowered = text.lower()
    if "acceptance document" in lowered and "conflicts with contract subject" in lowered:
        return "验收资料引用的项目名称与合同标的不一致，需核清项目身份后再作为履约证据。"
    if "base payload specifies contract amount" in lowered and "no immutable" in lowered:
        return "合同金额与实际成本虽在案件数据中一致，但缺少可交叉验证的不可变付款或对账凭证。"
    if "contract amount in evidence shows ocr artifacts" in lowered:
        return "合同金额的文字识别结果存在小数伪影，金额判断应以签署合同及财务凭证复核结果为准。"
    if "contract document" in lowered and "unreadable" in lowered:
        return "一份合同类归档资料不可读取，无法完整核验交付、验收及合同条款。"
    if "contract name in base payload" in lowered and (
        "differs from evidence" in lowered or "differs from signed" in lowered
    ):
        return "案件合同名称与归档合同标题不一致，需统一项目身份和合同名称口径。"
    if "real internal delivery notes" in lowered and "evidence gap" in lowered:
        return "公开资料未披露内部交付单、验收签收单及入库单，实物交付证据存在缺口。"
    if "invoice category documents" in lowered and "blank templates" in lowered:
        return "发票类资料仅包含空白票样和测试说明，不属于本合同的真实交易发票。"
    if "invoice document" in lowered and "unreadable" in lowered:
        return "一份发票类资料不可读取，无法核验其中是否包含与本合同相关的财务信息。"
    unreadable = re.fullmatch(
        r"(\d+) document\(s\) have no readable processed content",
        text,
        flags=re.IGNORECASE,
    )
    if unreadable:
        return f"有{unreadable.group(1)}份资料未提取到可读正文。"
    unsupported = re.fullmatch(
        r"(\d+) extracted fact\(s\) have no evidence reference",
        text,
        flags=re.IGNORECASE,
    )
    if unsupported:
        return f"有{unsupported.group(1)}项提取事实缺少直接证据引用。"
    if re.fullmatch(
        r"[A-Za-z-]+ returned invalid .+ values; retained base payload",
        text,
        flags=re.IGNORECASE,
    ):
        return "部分 Agent 的结构化输出未通过约束校验，系统已保留案件基础数据。"
    acceptance_conflict = re.fullmatch(
        r"Acceptance document .+ references '([^']+)'(?: \([^)]*\))? "
        r"which conflicts with contract subject '([^']+)'(?: \([^)]*\))?",
        text,
        flags=re.IGNORECASE,
    )
    if acceptance_conflict:
        return (
            f"验收资料指向“{acceptance_conflict.group(1)}”，"
            f"与合同标的“{acceptance_conflict.group(2)}”不一致。"
        )
    contract_id_conflict = re.fullmatch(
        r"Contract ID in base payload \('([^']+)'\) includes lot suffix '([^']+)' "
        r"not present in contract document header \('([^']+)'\)",
        text,
        flags=re.IGNORECASE,
    )
    if contract_id_conflict:
        return (
            f"案件合同编号“{contract_id_conflict.group(1)}”包含标段后缀"
            f"“{contract_id_conflict.group(2)}”，但合同正文编号为"
            f"“{contract_id_conflict.group(3)}”，需核实编号口径。"
        )
    if re.fullmatch(
        r"Contract document version .+ is UNREADABLE, preventing full verification of .+",
        text,
        flags=re.IGNORECASE,
    ):
        return "一份合同类归档资料不可读取，无法完整核验交付里程碑、验收标准与合同条款。"
    contract_name_conflict = re.fullmatch(
        r"Contract name in base payload \('([^']+)'\) differs from "
        r"signed contract document title \('([^']+)'\)",
        text,
        flags=re.IGNORECASE,
    )
    if contract_name_conflict:
        return (
            f"案件合同名称“{contract_name_conflict.group(1)}”与签署合同标题"
            f"“{contract_name_conflict.group(2)}”不一致，需统一项目身份。"
        )
    english_words = re.findall(r"\b[A-Za-z]{3,}\b", text)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    if len(english_words) >= 8 and len(english_words) > len(chinese_chars):
        return "自动一致性检查发现一项需人工复核的资料冲突，原始诊断已保存在运行审计记录中。"
    return text


def _normalize_management_outcome(value: str, result: dict[str, Any]) -> str:
    text = value
    review_required = bool(result.get("reviewRequired"))
    passed = bool(result.get("passed"))
    if review_required:
        replacements = (
            (r"(?:评价|评估)(?:结论)?为?通过且无需(?:人工)?复核", "评分达到通过阈值，但需人工复核"),
            (r"无需人工复核", "需人工复核"),
            (r"无需复核", "需人工复核"),
            (r"评估通过", "评分达到通过阈值"),
            (r"评价通过", "评分达到通过阈值"),
        )
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        outcome = "待人工复核"
        reason = "存在证据缺口或冲突"
    elif passed:
        outcome = "通过"
        reason = "结构化评分与质量门禁均满足要求"
    else:
        outcome = "不通过"
        reason = "结构化评分或控制条件未满足要求"
    prefix = (
        f"结构化评价结论为“{outcome}”（综合得分{result.get('overallScore')}分，"
        f"等级{result.get('grade')}，风险等级{result.get('riskLevel')}），原因：{reason}。"
    )
    return f"{prefix}{text}".strip()


def _business_quality_warning(value: str) -> str:
    english_words = re.findall(r"\b[A-Za-z]{3,}\b", value)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", value)
    if len(english_words) >= 6 and len(english_words) > len(chinese_chars):
        return "自动审查发现非阻断性表达问题，详细诊断已保存在运行审计记录中。"
    return value


def _dimension_fallback(dimension: dict[str, Any]) -> str:
    name = str(dimension.get("name") or DIMENSION_NAMES.get(str(dimension.get("code")), "该维度"))
    score = dimension.get("score")
    if score is None:
        return f"{name}缺少足够证据，暂不能形成正式评价结论。"
    status = "表现稳定" if float(score) >= 80 else "存在改进空间"
    return f"{name}得分{float(score):.2f}分，{status}。{dimension.get('summary') or ''}".strip()


def _fallback_recommendations(result: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for item in result.get("findings", []):
        if not isinstance(item, dict):
            continue
        name = DIMENSION_NAMES.get(str(item.get("dimension")), "相关维度")
        values.append(f"针对{name}建立整改台账，明确责任人、完成期限和验收证据。")
    return values or ["保持现有履约控制措施，并按季度复核关键证据和风险状态。"]


def _build_remediation_plan(
    recommendations: list[str],
    dimensions: list[dict[str, Any]],
    evaluation_period: dict[str, Any],
) -> list[dict[str, Any]]:
    end_raw = str(evaluation_period.get("end") or "")
    try:
        baseline = date.fromisoformat(end_raw)
    except ValueError:
        baseline = date(2000, 1, 1)
    low_dimensions = sorted(
        (
            item
            for item in dimensions
            if item.get("score") is None or float(item.get("score") or 0) < 80
        ),
        key=lambda item: float(item.get("score") or 0),
    )
    rows: list[dict[str, Any]] = []
    for index, action in enumerate(recommendations[:8], start=1):
        dimension = low_dimensions[(index - 1) % len(low_dimensions)] if low_dimensions else None
        priority = "高" if index <= 2 else "中"
        rows.append(
            {
                "actionId": f"A{index:02d}",
                "priority": priority,
                "dimension": dimension["name"] if dimension else "综合治理",
                "action": action,
                "owner": "合同负责人" if index % 2 else "供应商项目负责人",
                "dueDate": (baseline + timedelta(days=30 * index)).isoformat(),
                "acceptanceCriteria": "整改完成并提交可追溯证据，经业务负责人复核关闭。",
            }
        )
    return rows


def _timeline_rows(value: Any) -> list[dict[str, Any]]:
    payload = value if isinstance(value, dict) else {}
    rows = payload.get("milestones") or payload.get("items") or []
    if isinstance(rows, list) and rows:
        return [deepcopy(item) for item in rows if isinstance(item, dict)][:20]
    return [
        {
            "milestone": "评价期履约汇总",
            "plannedDate": "未形成单项计划日期",
            "actualDate": "按评价期汇总",
            "status": (
                f"到期{payload.get('dueCount', 0)}项，"
                f"按期{payload.get('onTimeCount', payload.get('onTime', 0))}项，"
                f"延期{payload.get('lateCount', payload.get('late', 0))}项"
            ),
        }
    ]


def _financial_analysis(value: Any, result: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(value) if isinstance(value, dict) else {}
    cost_dimension = next(
        (
            item
            for item in result.get("dimensions", [])
            if isinstance(item, dict) and item.get("code") == "COST_CONTROL"
        ),
        {},
    )
    metrics = cost_dimension.get("metrics") or {}
    return {
        "currency": payload.get("currency") or "CNY",
        "contractAmount": payload.get("contractAmount", metrics.get("contractAmount")),
        "actualCost": payload.get("actualCost", metrics.get("actualCost")),
        "varianceAmount": payload.get("varianceAmount", metrics.get("overrunAmount")),
        "varianceRate": payload.get("varianceRate", metrics.get("overrunRate")),
        "conflicts": list(payload.get("conflicts") or []),
        "conclusion": "金额与成本数据由确定性工具对账，冲突项需以批准的合同变更为准。",
    }


def _invoice_analysis(value: Any) -> dict[str, Any]:
    payload = deepcopy(value) if isinstance(value, dict) else {}
    return {
        "count": payload.get("count", payload.get("invoiceCount", 0)),
        "totalAmount": payload.get("totalAmount", 0),
        "exceptionCount": payload.get("exceptionCount", 0),
        "duplicates": list(payload.get("duplicates") or []),
        "exceptions": list(payload.get("exceptions") or []),
        "conclusion": "发票合规结论依据合同、验收、税务和重复性四类校验形成。",
    }


def _deviation_risk_analysis(deviations: Any, risks: Any) -> dict[str, Any]:
    deviation_payload = deepcopy(deviations) if isinstance(deviations, dict) else {}
    risk_payload = deepcopy(risks) if isinstance(risks, dict) else {}
    return {
        "deviations": deviation_payload,
        "risks": risk_payload,
        "matrix": [
            {
                "area": "偏差治理",
                "openCount": deviation_payload.get("openCount", 0),
                "highCount": deviation_payload.get("openHigh", 0),
                "level": "高" if deviation_payload.get("openHigh", 0) else "中",
            },
            {
                "area": "风险治理",
                "openCount": risk_payload.get("openCount", 0),
                "highCount": risk_payload.get("highOpenCount", 0),
                "level": "高"
                if risk_payload.get("highOpenCount", 0)
                or risk_payload.get("overdueActions", 0)
                else "中",
            },
        ],
    }


def _visible_report_text(report: dict[str, Any]) -> str:
    visible = deepcopy(report)
    visible.pop("provenance", None)
    visible.pop("schemaVersion", None)
    evidence = visible.get("evidenceAndLimitations")
    if isinstance(evidence, dict):
        for item in evidence.get("evidenceIndex", []):
            if isinstance(item, dict):
                item.pop("sourceRef", None)
    return json.dumps(visible, ensure_ascii=False, sort_keys=True)


def _register_business_font() -> str:
    name = "SwarmCoreCJK"
    if name in pdfmetrics.getRegisteredFontNames():
        return name
    candidates = (
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    )
    for path in candidates:
        if path.is_file():
            try:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
            except TTFError:
                continue
            return name
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    return "STSong-Light"


def _report_styles(font: str) -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "coverTitle": ParagraphStyle(
            "CoverTitle",
            parent=sample["Title"],
            fontName=font,
            fontSize=26,
            leading=38,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#163B65"),
            spaceAfter=10 * mm,
        ),
        "coverSub": ParagraphStyle(
            "CoverSub",
            fontName=font,
            fontSize=13,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
        ),
        "h1": ParagraphStyle(
            "H1",
            fontName=font,
            fontSize=19,
            leading=27,
            textColor=colors.HexColor("#163B65"),
            spaceAfter=6 * mm,
        ),
        "h2": ParagraphStyle(
            "H2",
            fontName=font,
            fontSize=14,
            leading=21,
            textColor=colors.HexColor("#1D4E89"),
            spaceBefore=4 * mm,
            spaceAfter=3 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName=font,
            fontSize=10,
            leading=17,
            textColor=colors.HexColor("#253247"),
            alignment=TA_LEFT,
            spaceAfter=2.5 * mm,
            wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "Small",
            fontName=font,
            fontSize=8,
            leading=13,
            textColor=colors.HexColor("#526173"),
            wordWrap="CJK",
        ),
        "metric": ParagraphStyle(
            "Metric",
            fontName=font,
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0F766E"),
        ),
        "table": ParagraphStyle(
            "Table",
            fontName=font,
            fontSize=8.5,
            leading=13,
            textColor=colors.HexColor("#253247"),
            wordWrap="CJK",
        ),
        "warning": ParagraphStyle(
            "Warning",
            fontName=font,
            fontSize=10,
            leading=16,
            textColor=colors.HexColor("#9A3412"),
            backColor=colors.HexColor("#FFF7ED"),
            borderColor=colors.HexColor("#FDBA74"),
            borderWidth=0.5,
            borderPadding=8,
            spaceAfter=4 * mm,
        ),
    }


def _p(value: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(value or "")).replace("\n", "<br/>"), style)


def _section_title(story: list[Any], title: str, styles: dict[str, ParagraphStyle]) -> None:
    story.append(_p(title, styles["h1"]))
    story.append(
        HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#2F6DAA"))
    )
    story.append(Spacer(1, 4 * mm))


def _table(
    rows: list[list[Any]],
    *,
    widths: list[float] | None,
    styles: dict[str, ParagraphStyle],
    header: bool = True,
) -> Table:
    values = [[_p(cell, styles["table"]) for cell in row] for row in rows]
    table = Table(values, colWidths=widths, repeatRows=1 if header else 0)
    commands: list[tuple[Any, ...]] = [
        ("FONTNAME", (0, 0), (-1, -1), styles["table"].fontName),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [
            colors.white,
            colors.HexColor("#F8FAFC"),
        ]),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEAF7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#163B65")),
            ]
        )
    table.setStyle(TableStyle(commands))
    return table


def _build_cover(
    story: list[Any], report: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> None:
    story.extend(
        [
            Spacer(1, 38 * mm),
            _p("合同履约后评价报告", styles["coverTitle"]),
            _p(report.get("title"), styles["coverSub"]),
            Spacer(1, 20 * mm),
            _p(f"报告编号：{report.get('reportNumber')}", styles["coverSub"]),
            _p(f"版本：{report.get('version')}", styles["coverSub"]),
            _p(
                f"评价期间：{report.get('contractProfile', {}).get('evaluationStart')} 至 "
                f"{report.get('contractProfile', {}).get('evaluationEnd')}",
                styles["coverSub"],
            ),
            Spacer(1, 22 * mm),
        ]
    )
    if report.get("reportMode") == "PRE_REVIEW_REPORT":
        story.append(
            _p(
                "资料质量预审报告：当前资料可读率未达到正式报告门槛，"
                "本文件不得替代最终签发版本。",
                styles["warning"],
            )
        )
    story.extend(
        [
            Spacer(1, 25 * mm),
            _p("SwarmCore 受控生成", styles["coverSub"]),
            _p("评分与证据可追溯 · 模型叙述不可修改冻结结论", styles["coverSub"]),
            PageBreak(),
        ]
    )


def _build_toc(story: list[Any], styles: dict[str, ParagraphStyle]) -> None:
    _section_title(story, "目录", styles)
    rows = [
        ["01", "管理层摘要"],
        ["02", "合同概况与评价方法"],
        ["03", "七维评价总览"],
        ["04-10", "七维评价明细"],
        ["11", "履约时间轴"],
        ["12", "金额、成本、发票与付款分析"],
        ["13", "偏差与风险矩阵"],
        ["14", "证据、冲突与资料局限"],
        ["15", "整改行动计划"],
        ["16", "审批记录与生成溯源"],
    ]
    story.append(_table(rows, widths=[28 * mm, 130 * mm], styles=styles, header=False))
    story.append(PageBreak())


def _build_management_summary(
    story: list[Any], report: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> None:
    summary = report["managementSummary"]
    _section_title(story, "01 管理层摘要", styles)
    metrics = [
        [
            _p("综合得分", styles["small"]),
            _p("评价等级", styles["small"]),
            _p("风险等级", styles["small"]),
            _p("是否通过", styles["small"]),
        ],
        [
            _p(f"{float(summary.get('overallScore') or 0):.2f}", styles["metric"]),
            _p(summary.get("grade"), styles["metric"]),
            _p(summary.get("riskLevel"), styles["metric"]),
            _p("是" if summary.get("passed") else "否", styles["metric"]),
        ],
    ]
    story.append(Table(metrics, colWidths=[40 * mm] * 4, style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F1F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ])))
    story.extend(
        [
            Spacer(1, 6 * mm),
            _p("总体结论", styles["h2"]),
            _p(summary.get("executiveSummary"), styles["body"]),
            _p("关键关注事项", styles["h2"]),
        ]
    )
    findings = summary.get("keyFindings") or ["本期未形成需升级的关注事项。"]
    for item in findings:
        story.append(_p(f"• {item}", styles["body"]))
    story.extend(
        [
            _p("数据质量声明", styles["h2"]),
            _p(summary.get("dataQualityNotice"), styles["warning"]),
            PageBreak(),
        ]
    )


def _build_contract_and_methodology(
    story: list[Any], report: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> None:
    profile = report["contractProfile"]
    method = report["methodology"]
    _section_title(story, "02 合同概况与评价方法", styles)
    rows = [
        ["合同标识", profile.get("contractId"), "评价版本", report.get("version")],
        ["评价开始", profile.get("evaluationStart"), "评价结束", profile.get("evaluationEnd")],
        ["合同金额", _money(profile.get("contractAmount")), "实际成本", _money(profile.get("actualCost"))],
        ["报告模式", _mode_label(report.get("reportMode")), "报告编号", report.get("reportNumber")],
    ]
    story.append(
        _table(rows, widths=[25 * mm, 55 * mm, 25 * mm, 55 * mm], styles=styles, header=False)
    )
    story.extend(
        [
            Spacer(1, 5 * mm),
            _p("评价方法", styles["h2"]),
            _p(method.get("description"), styles["body"]),
            _p(
                f"评价维度：{method.get('dimensionCount')}个；"
                f"权重合计：{method.get('weightsTotal')}%；"
                f"正式报告可读率门槛：{float(method.get('readabilityThreshold') or 0):.0%}。",
                styles["body"],
            ),
            _p("内容责任边界", styles["h2"]),
            _p(
                "事实抽取和报告叙述可能使用模型；评分、金额核算、风险等级、"
                "证据索引和质量门禁由确定性程序执行。人工审批意见作为独立审计记录保留。",
                styles["body"],
            ),
            PageBreak(),
        ]
    )


def _build_dimension_overview(
    story: list[Any],
    report: dict[str, Any],
    styles: dict[str, ParagraphStyle],
    font: str,
) -> None:
    overview = report["dimensionOverview"]
    _section_title(story, "03 七维评价总览", styles)
    story.append(_radar_chart(overview, font))
    rows = [["评价维度", "权重", "得分", "状态"]]
    rows.extend(
        [
            item.get("name"),
            f"{item.get('weight')}%",
            "数据不足" if item.get("score") is None else f"{float(item['score']):.2f}",
            "已评价" if item.get("status") == "EVALUATED" else "数据不足",
        ]
        for item in overview
    )
    story.extend(
        [
            Spacer(1, 4 * mm),
            _table(rows, widths=[70 * mm, 25 * mm, 30 * mm, 35 * mm], styles=styles),
            PageBreak(),
        ]
    )


def _radar_chart(overview: list[dict[str, Any]], font: str) -> Drawing:
    size = 125 * mm
    drawing = Drawing(size, size)
    center = size / 2
    radius = 43 * mm
    count = max(1, len(overview))
    for level in range(1, 6):
        points: list[float] = []
        for index in range(count):
            angle = -math.pi / 2 + 2 * math.pi * index / count
            scale = level / 5
            points.extend(
                [center + radius * scale * math.cos(angle), center + radius * scale * math.sin(angle)]
            )
        drawing.add(
            Polygon(points, fillColor=None, strokeColor=colors.HexColor("#CBD5E1"), strokeWidth=0.6)
        )
    score_points: list[float] = []
    for index, item in enumerate(overview):
        angle = -math.pi / 2 + 2 * math.pi * index / count
        x = center + radius * math.cos(angle)
        y = center + radius * math.sin(angle)
        drawing.add(Line(center, center, x, y, strokeColor=colors.HexColor("#CBD5E1")))
        score = float(item.get("score") or 0) / 100
        score_points.extend(
            [center + radius * score * math.cos(angle), center + radius * score * math.sin(angle)]
        )
        label_x = center + (radius + 12 * mm) * math.cos(angle)
        label_y = center + (radius + 9 * mm) * math.sin(angle)
        drawing.add(
            String(
                label_x,
                label_y,
                str(item.get("name") or ""),
                fontName=font,
                fontSize=7.5,
                textAnchor="middle",
                fillColor=colors.HexColor("#334155"),
            )
        )
    if score_points:
        drawing.add(
            Polygon(
                score_points,
                fillColor=colors.Color(0.12, 0.45, 0.68, alpha=0.22),
                strokeColor=colors.HexColor("#1D6FA5"),
                strokeWidth=1.8,
            )
        )
        for index in range(0, len(score_points), 2):
            drawing.add(
                Circle(
                    score_points[index],
                    score_points[index + 1],
                    2.2,
                    fillColor=colors.HexColor("#1D6FA5"),
                    strokeColor=None,
                )
            )
    return drawing


def _build_dimension_section(
    story: list[Any], section: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> None:
    _section_title(story, f"七维评价 · {section.get('name')}", styles)
    score = section.get("score")
    summary_rows = [
        ["权重", "得分", "状态"],
        [
            f"{section.get('weight')}%",
            "数据不足" if score is None else f"{float(score):.2f}",
            "已评价" if section.get("status") == "EVALUATED" else "数据不足",
        ],
    ]
    story.append(_table(summary_rows, widths=[52 * mm] * 3, styles=styles))
    story.extend(
        [
            Spacer(1, 5 * mm),
            _p("评价结论", styles["h2"]),
            _p(section.get("conclusion"), styles["body"]),
            _p("评分依据", styles["h2"]),
            _p(section.get("summary"), styles["body"]),
            _p("关键指标", styles["h2"]),
        ]
    )
    metrics = section.get("metrics") or {}
    metric_rows = [["指标", "值"]]
    metric_rows.extend([_human_metric_name(str(key)), _format_metric(value)] for key, value in metrics.items())
    if len(metric_rows) == 1:
        metric_rows.append(["数据状态", "未提供可展示指标"])
    story.append(_table(metric_rows, widths=[75 * mm, 85 * mm], styles=styles))
    story.append(_p("证据引用", styles["h2"]))
    citations = section.get("evidenceCitations") or []
    if citations:
        for citation in citations:
            story.append(_p(str(citation.get("label") or "业务证据"), styles["body"]))
    else:
        story.append(_p("暂无直接证据引用，已列入资料补充清单。", styles["warning"]))
    risks = section.get("risks") or []
    if risks:
        story.append(_p("风险与关注事项", styles["h2"]))
        for risk in risks:
            story.append(_p(f"• {risk}", styles["body"]))
    story.append(PageBreak())


def _build_timeline(
    story: list[Any], report: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> None:
    _section_title(story, "11 履约时间轴", styles)
    rows = [["里程碑", "计划日期", "实际日期", "状态"]]
    for item in report.get("timeline", []):
        rows.append(
            [
                item.get("milestone") or item.get("name") or "履约事项",
                item.get("plannedDate") or item.get("dueDate") or "-",
                item.get("actualDate") or item.get("completedDate") or "-",
                item.get("status") or "-",
            ]
        )
    story.append(
        _table(rows, widths=[55 * mm, 30 * mm, 30 * mm, 45 * mm], styles=styles)
    )
    story.extend(
        [
            Spacer(1, 5 * mm),
            _p(
                "说明：时间轴仅展示冻结证据中可核验的计划与实际节点；"
                "无法解析的扫描件不会被模型补造为里程碑。",
                styles["body"],
            ),
            PageBreak(),
        ]
    )


def _build_finance_and_invoice(
    story: list[Any], report: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> None:
    finance = report["financialAnalysis"]
    invoices = report["invoiceAnalysis"]
    _section_title(story, "12 金额、成本、发票与付款分析", styles)
    rows = [
        ["项目", "金额/比例"],
        ["合同金额", _money(finance.get("contractAmount"))],
        ["实际成本", _money(finance.get("actualCost"))],
        ["偏差金额", _money(finance.get("varianceAmount"))],
        ["偏差率", _percent(finance.get("varianceRate"))],
    ]
    story.append(_table(rows, widths=[75 * mm, 85 * mm], styles=styles))
    story.extend(
        [
            _p("成本结论", styles["h2"]),
            _p(finance.get("conclusion"), styles["body"]),
            _p("发票合规", styles["h2"]),
        ]
    )
    invoice_rows = [
        ["发票数量", "发票总额", "异常数量", "重复数量"],
        [
            invoices.get("count"),
            _money(invoices.get("totalAmount")),
            invoices.get("exceptionCount"),
            len(invoices.get("duplicates") or []),
        ],
    ]
    story.append(
        _table(invoice_rows, widths=[40 * mm] * 4, styles=styles)
    )
    story.append(_p(invoices.get("conclusion"), styles["body"]))
    conflicts = finance.get("conflicts") or []
    if conflicts:
        story.append(_p("金额冲突", styles["h2"]))
        for value in conflicts:
            story.append(_p(f"• {value}", styles["warning"]))
    story.append(PageBreak())


def _build_deviation_and_risk(
    story: list[Any], report: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> None:
    payload = report["deviationAndRisk"]
    _section_title(story, "13 偏差与风险矩阵", styles)
    rows = [["领域", "未关闭数量", "高风险数量", "综合级别"]]
    rows.extend(
        [
            item.get("area"),
            item.get("openCount"),
            item.get("highCount"),
            item.get("level"),
        ]
        for item in payload.get("matrix", [])
    )
    story.append(
        _table(rows, widths=[55 * mm, 35 * mm, 35 * mm, 35 * mm], styles=styles)
    )
    story.extend(
        [
            _p("偏差治理诊断", styles["h2"]),
            _p(_diagnostic_summary(payload.get("deviations")), styles["body"]),
            _p("风险治理诊断", styles["h2"]),
            _p(_diagnostic_summary(payload.get("risks")), styles["body"]),
            PageBreak(),
        ]
    )


def _build_evidence_and_limitations(
    story: list[Any], report: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> None:
    evidence = report["evidenceAndLimitations"]
    _section_title(story, "14 证据、冲突与资料局限", styles)
    story.append(
        _table(
            [
                ["冻结资料", "可读取资料", "可读取率", "覆盖状态"],
                [
                    evidence.get("documentCount"),
                    evidence.get("readableDocumentCount"),
                    _percent(evidence.get("readabilityRate")),
                    "完整" if evidence.get("coverageComplete") else "不完整",
                ],
            ],
            widths=[40 * mm] * 4,
            styles=styles,
        )
    )
    story.append(_p("证据索引", styles["h2"]))
    index_rows = [["编号", "业务证据名称"]]
    index_rows.extend(
        [f"资料{index:02d}", item.get("label")]
        for index, item in enumerate(evidence.get("evidenceIndex", []), start=1)
    )
    story.append(
        _table(index_rows or [["编号", "业务证据名称"], ["-", "无"]], widths=[25 * mm, 135 * mm], styles=styles)
    )
    if evidence.get("conflicts"):
        story.append(_p("证据冲突", styles["h2"]))
        for item in evidence["conflicts"]:
            story.append(_p(f"• {item}", styles["warning"]))
    story.append(_p("资料局限", styles["h2"]))
    for item in evidence.get("limitations") or ["未发现需要披露的资料局限。"]:
        story.append(_p(f"• {item}", styles["body"]))
    story.append(PageBreak())


def _build_remediation(
    story: list[Any], report: dict[str, Any], styles: dict[str, ParagraphStyle]
) -> None:
    _section_title(story, "15 整改行动计划", styles)
    rows = [["编号", "优先级", "评价领域", "整改行动", "责任主体", "期限"]]
    for item in report.get("remediationPlan", []):
        rows.append(
            [
                item.get("actionId"),
                item.get("priority"),
                item.get("dimension"),
                item.get("action"),
                item.get("owner"),
                item.get("dueDate"),
            ]
        )
    story.append(
        _table(
            rows,
            widths=[14 * mm, 16 * mm, 24 * mm, 66 * mm, 24 * mm, 22 * mm],
            styles=styles,
        )
    )
    story.append(_p("统一验收标准", styles["h2"]))
    criteria = list(
        dict.fromkeys(
            str(item.get("acceptanceCriteria"))
            for item in report.get("remediationPlan", [])
            if item.get("acceptanceCriteria")
        )
    )
    for value in criteria:
        story.append(_p(f"• {value}", styles["body"]))
    story.append(PageBreak())


def _build_approval_and_provenance(
    story: list[Any],
    report: dict[str, Any],
    quality: dict[str, Any],
    styles: dict[str, ParagraphStyle],
) -> None:
    approval = report["approval"]
    provenance = report["provenance"]
    _section_title(story, "16 审批记录与生成溯源", styles)
    story.append(
        _table(
            [
                ["是否要求审批", "审批状态", "审批意见"],
                [
                    "是" if approval.get("required") else "否",
                    {
                        "APPROVED": "已批准",
                        "PENDING": "待审批",
                        "NOT_REQUIRED": "无需审批",
                    }.get(str(approval.get("status")), approval.get("status")),
                    approval.get("comment"),
                ],
            ],
            widths=[32 * mm, 32 * mm, 96 * mm],
            styles=styles,
        )
    )
    story.extend(
        [
            _p("质量门禁", styles["h2"]),
            _p(
                "通过" if quality.get("passed") else "未通过",
                styles["body"] if quality.get("passed") else styles["warning"],
            ),
        ]
    )
    for warning in quality.get("warnings", []):
        story.append(_p(f"• {warning}", styles["body"]))
    story.extend(
        [
            _p("不可变生成溯源", styles["h2"]),
            _table(
                [
                    ["项目", "值"],
                    ["评分 Schema", provenance.get("scoreSchemaVersion")],
                    ["报告组装器", provenance.get("reportComposer")],
                    ["文件内容哈希", provenance.get("documentContentHash")],
                    ["附件清单哈希", provenance.get("attachmentManifestHash")],
                ],
                widths=[42 * mm, 118 * mm],
                styles=styles,
            ),
            Spacer(1, 10 * mm),
            _p(
                "本报告由受控流程生成。任何脱离本报告编号、版本、文件哈希和审批记录的"
                "复制件，均不得作为最终履约评价依据。",
                styles["warning"],
            ),
        ]
    )


def _money(value: Any) -> str:
    try:
        return f"¥{float(value):,.2f}"
    except (TypeError, ValueError):
        return "-"


def _percent(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if abs(number) <= 1:
        number *= 100
    return f"{number:.2f}%"


def _format_metric(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


def _human_metric_name(value: str) -> str:
    names = {
        "valid": "有效资料数",
        "required": "必备资料数",
        "due": "到期义务数",
        "late": "延期完成数",
        "onTime": "按期完成数",
        "overdue": "逾期未完成数",
        "accepted": "验收通过数",
        "assessed": "已评价交付数",
        "rejected": "拒收数",
        "actualCost": "实际成本",
        "contractAmount": "合同金额",
        "overrunRate": "超支率",
        "overrunAmount": "超支金额",
        "count": "记录数量",
        "totalAmount": "合计金额",
        "exceptionCount": "异常数量",
        "closed": "已关闭数量",
        "openHigh": "未关闭高风险数量",
        "overdueActions": "逾期措施数量",
    }
    return names.get(value, value)


def _mode_label(value: Any) -> str:
    return "正式报告" if value == "FORMAL_REPORT" else "资料质量预审报告"


def _diagnostic_summary(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "当前未形成可展示的结构化诊断。"
    parts = [
        f"{_human_metric_name(str(key))}：{_format_metric(item)}"
        for key, item in value.items()
        if isinstance(item, str | int | float | bool)
    ]
    return "；".join(parts[:12]) or "诊断结果已保存于结构化附件。"


__all__ = [
    "assess_document_readability",
    "compose_formal_post_evaluation_report",
    "finalize_formal_report_quality",
    "render_formal_post_evaluation_pdf",
    "verify_report_citations",
]
