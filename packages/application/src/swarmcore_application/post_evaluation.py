from __future__ import annotations

from copy import deepcopy
from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PostEvaluationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class DocumentStatus(StrEnum):
    VALID = "VALID"
    MISSING = "MISSING"
    EXPIRED = "EXPIRED"
    UNREADABLE = "UNREADABLE"


class TimelinessStatus(StrEnum):
    ON_TIME = "ON_TIME"
    LATE = "LATE"
    OVERDUE = "OVERDUE"
    NOT_DUE = "NOT_DUE"


class QualityStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    CONDITIONALLY_ACCEPTED = "CONDITIONALLY_ACCEPTED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    NOT_ASSESSED = "NOT_ASSESSED"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GovernanceStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"


class EvaluationPeriod(PostEvaluationModel):
    start: date
    end: date

    @model_validator(mode="after")
    def valid_period(self) -> EvaluationPeriod:
        if self.end < self.start:
            raise ValueError("evaluation period end must not precede start")
        return self


class ContractFacts(PostEvaluationModel):
    contract_id: str = Field(alias="contractId", min_length=1, max_length=256)
    contract_name: str = Field(alias="contractName", min_length=1, max_length=256)
    contract_amount: float = Field(alias="contractAmount", ge=0)
    actual_cost: float | None = Field(default=None, alias="actualCost", ge=0)
    currency: str = Field(default="CNY", min_length=3, max_length=3)


class DocumentFact(PostEvaluationModel):
    document_id: str = Field(alias="documentId", min_length=1, max_length=256)
    category: str = Field(min_length=1, max_length=128)
    required: bool = True
    status: DocumentStatus


class ObligationFact(PostEvaluationModel):
    obligation_id: str = Field(alias="obligationId", min_length=1, max_length=256)
    category: str = Field(min_length=1, max_length=128)
    timeliness: TimelinessStatus
    quality: QualityStatus = QualityStatus.NOT_ASSESSED


class DeviationFact(PostEvaluationModel):
    deviation_id: str = Field(alias="deviationId", min_length=1, max_length=256)
    category: str = Field(min_length=1, max_length=128)
    severity: Severity
    status: GovernanceStatus
    cost_impact: float = Field(default=0, alias="costImpact", ge=0)
    delay_days: int = Field(default=0, alias="delayDays", ge=0)


class InvoiceFact(PostEvaluationModel):
    invoice_id: str = Field(alias="invoiceId", min_length=1, max_length=256)
    amount: float = Field(gt=0)
    contract_matched: bool = Field(alias="contractMatched")
    acceptance_matched: bool = Field(alias="acceptanceMatched")
    tax_valid: bool = Field(alias="taxValid")
    duplicate: bool = False


class RiskFact(PostEvaluationModel):
    risk_id: str = Field(alias="riskId", min_length=1, max_length=256)
    category: str = Field(min_length=1, max_length=128)
    level: Severity
    status: GovernanceStatus
    action_overdue: bool = Field(default=False, alias="actionOverdue")


class PostEvaluationPayload(PostEvaluationModel):
    title: str = Field(min_length=1, max_length=256)
    evaluation_period: EvaluationPeriod = Field(alias="evaluationPeriod")
    contract: ContractFacts
    documents: tuple[DocumentFact, ...]
    obligations: tuple[ObligationFact, ...]
    deviations: tuple[DeviationFact, ...]
    invoices: tuple[InvoiceFact, ...]
    risks: tuple[RiskFact, ...]
    evidence_availability: dict[str, str] = Field(
        default_factory=dict, alias="evidenceAvailability"
    )


_SOURCE_FIELDS = {
    "contract-files": ("documents",),
    "performance-data": ("contract", "obligations"),
    "deviation-data": ("deviations",),
    "invoice-data": ("invoices",),
    "risk-data": ("risks",),
}


def assemble_post_evaluation_payload(
    payload: dict[str, Any], sources: list[dict[str, Any]]
) -> PostEvaluationPayload:
    """Merge normalized bound-resource facts into a case payload.

    A source can expose a named object (for example ``{"invoices": [...]}``) or a
    direct collection through ``value``. Bound source facts take precedence over
    payload placeholders so an assessment always reflects the resource snapshot.
    """

    merged = deepcopy(payload)
    availability = dict(merged.get("evidenceAvailability", {}))
    for source in sources:
        slot = str(source.get("slot", ""))
        fields = _SOURCE_FIELDS.get(slot)
        if fields is None:
            continue
        data = source.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(f"bound resource {slot!r} did not return an object")
        evidence_status = data.get("evidenceStatus")
        if isinstance(evidence_status, str):
            availability[slot] = evidence_status
        copied = False
        for field in fields:
            if field in data:
                merged[field] = deepcopy(data[field])
                copied = True
        if not copied and len(fields) == 1 and "value" in data:
            merged[fields[0]] = deepcopy(data["value"])
    merged["evidenceAvailability"] = availability
    return PostEvaluationPayload.model_validate(merged)


class DimensionWeights(PostEvaluationModel):
    document_completeness: int = Field(default=10, alias="documentCompleteness", ge=0, le=100)
    delivery_timeliness: int = Field(default=20, alias="deliveryTimeliness", ge=0, le=100)
    delivery_quality: int = Field(default=15, alias="deliveryQuality", ge=0, le=100)
    cost_control: int = Field(default=15, alias="costControl", ge=0, le=100)
    invoice_compliance: int = Field(default=15, alias="invoiceCompliance", ge=0, le=100)
    deviation_governance: int = Field(default=10, alias="deviationGovernance", ge=0, le=100)
    risk_governance: int = Field(default=15, alias="riskGovernance", ge=0, le=100)

    @model_validator(mode="after")
    def total_is_one_hundred(self) -> DimensionWeights:
        if sum(self.as_dict().values()) != 100:
            raise ValueError("seven dimension weights must total 100")
        return self

    def as_dict(self) -> dict[str, int]:
        return {
            "DOCUMENT_COMPLETENESS": self.document_completeness,
            "DELIVERY_TIMELINESS": self.delivery_timeliness,
            "DELIVERY_QUALITY": self.delivery_quality,
            "COST_CONTROL": self.cost_control,
            "INVOICE_COMPLIANCE": self.invoice_compliance,
            "DEVIATION_GOVERNANCE": self.deviation_governance,
            "RISK_GOVERNANCE": self.risk_governance,
        }


class PostEvaluationConfiguration(PostEvaluationModel):
    weights: DimensionWeights = Field(default_factory=DimensionWeights)


class DimensionResult(PostEvaluationModel):
    code: str
    name: str
    weight: int
    score: float | None
    status: str
    summary: str
    metrics: dict[str, str | int | float | bool | None]
    evidence_refs: tuple[str, ...] = Field(alias="evidenceRefs")


class PostEvaluationFinding(PostEvaluationModel):
    dimension: str
    severity: Severity
    code: str
    title: str
    detail: str
    evidence_refs: tuple[str, ...] = Field(alias="evidenceRefs")


class PostEvaluationResult(PostEvaluationModel):
    schema_version: str = Field(
        default="schema://contract/post-evaluation-result@1", alias="schemaVersion"
    )
    evaluation_period: EvaluationPeriod = Field(alias="evaluationPeriod")
    contract_id: str = Field(alias="contractId")
    overall_score: float = Field(alias="overallScore", ge=0, le=100)
    grade: str
    risk_level: Severity = Field(alias="riskLevel")
    passed: bool
    review_required: bool = Field(alias="reviewRequired")
    executive_summary: str = Field(alias="executiveSummary")
    dimensions: tuple[DimensionResult, ...]
    findings: tuple[PostEvaluationFinding, ...]


_DIMENSION_NAMES = {
    "DOCUMENT_COMPLETENESS": "文件完整性",
    "DELIVERY_TIMELINESS": "进度履约",
    "DELIVERY_QUALITY": "质量履约",
    "COST_CONTROL": "成本控制",
    "INVOICE_COMPLIANCE": "发票合规",
    "DEVIATION_GOVERNANCE": "偏差治理",
    "RISK_GOVERNANCE": "风险治理",
}
_SEVERITY_WEIGHT = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 4,
    Severity.CRITICAL: 8,
}


def evaluate_post_evaluation(
    payload: PostEvaluationPayload,
    configuration: PostEvaluationConfiguration | None = None,
) -> PostEvaluationResult:
    config = configuration or PostEvaluationConfiguration()
    weights = config.weights.as_dict()
    dimensions = (
        _document_dimension(payload, weights["DOCUMENT_COMPLETENESS"]),
        _timeliness_dimension(payload, weights["DELIVERY_TIMELINESS"]),
        _quality_dimension(payload, weights["DELIVERY_QUALITY"]),
        _cost_dimension(payload, weights["COST_CONTROL"]),
        _invoice_dimension(payload, weights["INVOICE_COMPLIANCE"]),
        _deviation_dimension(payload, weights["DEVIATION_GOVERNANCE"]),
        _risk_dimension(payload, weights["RISK_GOVERNANCE"]),
    )
    evaluated = [item for item in dimensions if item.score is not None]
    total_weight = sum(item.weight for item in dimensions)
    overall = (
        round(
            sum((item.score or 0) * item.weight for item in evaluated) / total_weight,
            2,
        )
        if total_weight
        else 0.0
    )
    findings = tuple(_dimension_finding(item) for item in dimensions if _needs_finding(item))
    review_required = any(item.score is None for item in dimensions)
    risk_level = _risk_level(payload, overall, review_required)
    grade = _grade(overall)
    return PostEvaluationResult(
        evaluationPeriod=payload.evaluation_period,
        contractId=payload.contract.contract_id,
        overallScore=overall,
        grade=grade,
        riskLevel=risk_level,
        passed=overall >= 60 and risk_level != Severity.CRITICAL and not review_required,
        reviewRequired=review_required,
        executiveSummary=(
            f"{payload.contract.contract_name}七维后评价得分{overall:.2f}, 等级{grade}, "
            f"风险级别{risk_level.value}; 发现{len(findings)}项需关注事项。"
        ),
        dimensions=dimensions,
        findings=findings,
    )


def _dimension(
    code: str,
    weight: int,
    score: float | None,
    summary: str,
    metrics: dict[str, str | int | float | bool | None],
    evidence_refs: tuple[str, ...],
) -> DimensionResult:
    return DimensionResult(
        code=code,
        name=_DIMENSION_NAMES[code],
        weight=weight,
        score=None if score is None else round(max(0, min(100, score)), 2),
        status="DATA_INSUFFICIENT" if score is None else "EVALUATED",
        summary=summary,
        metrics=metrics,
        evidenceRefs=evidence_refs,
    )


def _document_dimension(payload: PostEvaluationPayload, weight: int) -> DimensionResult:
    required = [item for item in payload.documents if item.required]
    valid = [item for item in required if item.status == DocumentStatus.VALID]
    score = len(valid) / len(required) * 100 if required else None
    return _dimension(
        "DOCUMENT_COMPLETENESS",
        weight,
        score,
        "必备文件有效率" if required else "未提供必备文件清单, 需人工复核。",
        {"required": len(required), "valid": len(valid)},
        tuple(item.document_id for item in required),
    )


def _timeliness_dimension(payload: PostEvaluationPayload, weight: int) -> DimensionResult:
    due = [item for item in payload.obligations if item.timeliness != TimelinessStatus.NOT_DUE]
    on_time = sum(item.timeliness == TimelinessStatus.ON_TIME for item in due)
    late = sum(item.timeliness == TimelinessStatus.LATE for item in due)
    overdue = sum(item.timeliness == TimelinessStatus.OVERDUE for item in due)
    score = (on_time + late * 0.5) / len(due) * 100 if due else None
    return _dimension(
        "DELIVERY_TIMELINESS",
        weight,
        score,
        "到期义务按期完成情况" if due else "评价期内没有可评价的到期义务。",
        {"due": len(due), "onTime": on_time, "late": late, "overdue": overdue},
        tuple(item.obligation_id for item in due),
    )


def _quality_dimension(payload: PostEvaluationPayload, weight: int) -> DimensionResult:
    assessed = [item for item in payload.obligations if item.quality != QualityStatus.NOT_ASSESSED]
    points = {
        QualityStatus.ACCEPTED: 1.0,
        QualityStatus.CONDITIONALLY_ACCEPTED: 0.7,
        QualityStatus.REJECTED: 0.0,
        QualityStatus.PENDING: 0.0,
    }
    score = (
        sum(points[item.quality] for item in assessed) / len(assessed) * 100
        if assessed
        else None
    )
    accepted = sum(item.quality == QualityStatus.ACCEPTED for item in assessed)
    rejected = sum(item.quality == QualityStatus.REJECTED for item in assessed)
    return _dimension(
        "DELIVERY_QUALITY",
        weight,
        score,
        "已验收交付物的质量结果" if assessed else "未提供可评价的验收结果。",
        {"assessed": len(assessed), "accepted": accepted, "rejected": rejected},
        tuple(item.obligation_id for item in assessed),
    )


def _cost_dimension(payload: PostEvaluationPayload, weight: int) -> DimensionResult:
    contract = payload.contract
    if contract.actual_cost is None or contract.contract_amount <= 0:
        return _dimension(
            "COST_CONTROL",
            weight,
            None,
            "合同金额或实际成本不足, 无法自动计算成本偏差。",
            {"contractAmount": contract.contract_amount, "actualCost": contract.actual_cost},
            (contract.contract_id,),
        )
    overrun = max(0.0, contract.actual_cost - contract.contract_amount)
    overrun_rate = overrun / contract.contract_amount * 100
    return _dimension(
        "COST_CONTROL",
        weight,
        100 - overrun_rate * 5,
        "按合同金额与实际成本计算超支率。",
        {
            "contractAmount": contract.contract_amount,
            "actualCost": contract.actual_cost,
            "overrunAmount": round(overrun, 2),
            "overrunRate": round(overrun_rate, 2),
        },
        (contract.contract_id,),
    )


def _invoice_dimension(payload: PostEvaluationPayload, weight: int) -> DimensionResult:
    if payload.evidence_availability.get("invoice-data") == "NOT_PUBLICLY_AVAILABLE":
        return _dimension(
            "INVOICE_COMPLIANCE",
            weight,
            None,
            "未取得发票或付款流水, 无法评价发票合规性。",
            {"count": 0, "totalAmount": 0, "exceptionCount": None},
            (),
        )
    total = sum(item.amount for item in payload.invoices)
    compliant = sum(
        item.amount
        for item in payload.invoices
        if item.contract_matched
        and item.acceptance_matched
        and item.tax_valid
        and not item.duplicate
    )
    score = compliant / total * 100 if total else 100.0
    exceptions = sum(
        not (
            item.contract_matched
            and item.acceptance_matched
            and item.tax_valid
            and not item.duplicate
        )
        for item in payload.invoices
    )
    return _dimension(
        "INVOICE_COMPLIANCE",
        weight,
        score,
        "按发票金额校验合同、验收、税务与重复性。",
        {"count": len(payload.invoices), "totalAmount": total, "exceptionCount": exceptions},
        tuple(item.invoice_id for item in payload.invoices),
    )


def _deviation_dimension(payload: PostEvaluationPayload, weight: int) -> DimensionResult:
    if payload.evidence_availability.get("deviation-data") == "NOT_PUBLICLY_AVAILABLE":
        return _dimension(
            "DEVIATION_GOVERNANCE",
            weight,
            None,
            "未取得偏差台账, 不能据空集合断言不存在偏差。",
            {"count": 0, "closed": None, "openHigh": None},
            (),
        )
    if not payload.deviations:
        return _dimension(
            "DEVIATION_GOVERNANCE",
            weight,
            100,
            "评价期内无登记偏差。",
            {"count": 0, "closed": 0, "openHigh": 0},
            (),
        )
    closed = sum(item.status == GovernanceStatus.CLOSED for item in payload.deviations)
    total_weight = sum(_SEVERITY_WEIGHT[item.severity] for item in payload.deviations)
    open_weight = sum(
        _SEVERITY_WEIGHT[item.severity]
        for item in payload.deviations
        if item.status != GovernanceStatus.CLOSED
    )
    closure_rate = closed / len(payload.deviations)
    control_rate = 1 - open_weight / total_weight
    return _dimension(
        "DEVIATION_GOVERNANCE",
        weight,
        (closure_rate * 0.7 + control_rate * 0.3) * 100,
        "综合偏差关闭率与未关闭偏差严重度。",
        {
            "count": len(payload.deviations),
            "closed": closed,
            "openHigh": sum(
                item.status != GovernanceStatus.CLOSED
                and item.severity in {Severity.HIGH, Severity.CRITICAL}
                for item in payload.deviations
            ),
        },
        tuple(item.deviation_id for item in payload.deviations),
    )


def _risk_dimension(payload: PostEvaluationPayload, weight: int) -> DimensionResult:
    if payload.evidence_availability.get("risk-data") == "NOT_PUBLICLY_AVAILABLE":
        return _dimension(
            "RISK_GOVERNANCE",
            weight,
            None,
            "未取得内部风险台账, 不能据空集合断言不存在风险。",
            {"count": 0, "closed": None, "overdueActions": None},
            (),
        )
    if not payload.risks:
        return _dimension(
            "RISK_GOVERNANCE",
            weight,
            100,
            "评价期内无登记风险。",
            {"count": 0, "closed": 0, "overdueActions": 0},
            (),
        )
    closed = sum(item.status == GovernanceStatus.CLOSED for item in payload.risks)
    total_weight = sum(_SEVERITY_WEIGHT[item.level] for item in payload.risks)
    uncontrolled_weight = sum(
        _SEVERITY_WEIGHT[item.level]
        for item in payload.risks
        if item.status != GovernanceStatus.CLOSED or item.action_overdue
    )
    closure_rate = closed / len(payload.risks)
    control_rate = 1 - min(1.0, uncontrolled_weight / total_weight)
    return _dimension(
        "RISK_GOVERNANCE",
        weight,
        (closure_rate * 0.6 + control_rate * 0.4) * 100,
        "综合风险关闭率、风险级别与措施逾期情况。",
        {
            "count": len(payload.risks),
            "closed": closed,
            "overdueActions": sum(item.action_overdue for item in payload.risks),
        },
        tuple(item.risk_id for item in payload.risks),
    )


def _needs_finding(item: DimensionResult) -> bool:
    return item.score is None or item.score < 80


def _dimension_finding(item: DimensionResult) -> PostEvaluationFinding:
    if item.score is None:
        severity = Severity.HIGH
        code = "DATA_INSUFFICIENT"
        detail = f"{item.name}缺少自动评价所需数据, 请补充证据后复核。"
    else:
        severity = (
            Severity.HIGH
            if item.score < 60
            else Severity.MEDIUM
            if item.score < 70
            else Severity.LOW
        )
        code = "DIMENSION_BELOW_TARGET"
        detail = f"{item.name}得分{item.score:.2f}, 低于80分关注线。"
    return PostEvaluationFinding(
        dimension=item.code,
        severity=severity,
        code=code,
        title=f"{item.name}需关注",
        detail=detail,
        evidenceRefs=item.evidence_refs,
    )


def _risk_level(
    payload: PostEvaluationPayload, overall: float, review_required: bool
) -> Severity:
    if any(
        item.level == Severity.CRITICAL and item.status != GovernanceStatus.CLOSED
        for item in payload.risks
    ) or overall < 60:
        return Severity.CRITICAL
    if any(
        item.level == Severity.HIGH and item.status != GovernanceStatus.CLOSED
        for item in payload.risks
    ) or overall < 70:
        return Severity.HIGH
    if review_required or overall < 80:
        return Severity.MEDIUM
    return Severity.LOW


def _grade(score: float) -> str:
    if score >= 90:
        return "优秀"
    if score >= 80:
        return "良好"
    if score >= 70:
        return "中等"
    if score >= 60:
        return "待改进"
    return "不合格"


def post_evaluation_report_lines(result: PostEvaluationResult) -> tuple[str, ...]:
    lines = [
        "Contract Post-Evaluation Report",
        f"Contract: {result.contract_id}",
        f"Period: {result.evaluation_period.start} - {result.evaluation_period.end}",
        f"Overall: {result.overall_score:.2f} / 100",
        f"Grade: {result.grade}; Risk: {result.risk_level.value}",
    ]
    lines.extend(
        f"{item.code}: {'N/A' if item.score is None else f'{item.score:.2f}'} "
        f"(weight {item.weight}%)"
        for item in result.dimensions
    )
    lines.extend(
        f"Finding {item.severity.value}: {item.code} / {item.dimension}"
        for item in result.findings
    )
    return tuple(lines)
