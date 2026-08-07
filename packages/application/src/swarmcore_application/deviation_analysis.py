from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from uuid import UUID

SCHEMA_VERSION = "schema://deviation-analysis/result@1"
DIMENSIONS = ("TIME", "CONTENT", "COST")
_CONTENT_SCORES = {
    "ACCEPTED": Decimal("1"),
    "CONDITIONAL": Decimal("0.5"),
    "PENDING": Decimal("0.25"),
    "MISSING": Decimal("0"),
    "REJECTED": Decimal("0"),
}
_EMPTY_TIME_METRICS = {"maximumDelayDays": None}
_EMPTY_CONTENT_METRICS = {"contentVarianceRate": None}
_EMPTY_COST_METRICS = {"costVarianceRate": None}


def _decimal(value: Any, *, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} must be a number")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc


def _number(value: Decimal | None, places: str = "0.01") -> float | None:
    if value is None:
        return None
    return float(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def _date(value: Any, *, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _status_payload(
    status: str,
    *,
    metrics: Mapping[str, Any] | None = None,
    reasons: Iterable[str] = (),
    evidence_refs: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "status": status,
        "metrics": dict(metrics or {}),
        "reasons": list(dict.fromkeys(reasons)),
        "evidenceRefs": list(dict.fromkeys(evidence_refs)),
    }


def _evidence_refs(value: Mapping[str, Any]) -> list[str]:
    raw = value.get("evidenceRefs", [])
    return [str(item) for item in raw] if isinstance(raw, list) else []


def merge_deviation_facts(
    base_payload: Mapping[str, Any],
    analyses: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Merge bounded agent fact patches without letting agents calculate metrics."""
    payload = dict(base_payload)
    facts: list[dict[str, Any]] = []
    conflicts: list[str] = []
    missing: list[str] = []
    for domain in sorted(analyses):
        analysis = analyses[domain]
        patch = analysis.get("payloadPatch", {})
        if isinstance(patch, Mapping):
            for key, value in patch.items():
                if key in payload and payload[key] not in (None, [], {}) and payload[key] != value:
                    conflicts.append(f"{domain}:{key}")
                    continue
                payload[key] = value
        raw_facts = analysis.get("facts", [])
        if isinstance(raw_facts, list):
            facts.extend(dict(item) for item in raw_facts if isinstance(item, Mapping))
        raw_conflicts = analysis.get("conflicts", [])
        if isinstance(raw_conflicts, list):
            conflicts.extend(str(item) for item in raw_conflicts)
        raw_missing = analysis.get("missingEvidence", [])
        if isinstance(raw_missing, list):
            missing.extend(str(item) for item in raw_missing)
    return {
        "payload": payload,
        "facts": facts,
        "conflicts": list(dict.fromkeys(conflicts)),
        "missingEvidence": list(dict.fromkeys(missing)),
    }


def upstream_performance_analysis(
    upstream_evaluations: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Convert the latest confirmed performance result into reusable deviation facts."""

    for upstream in upstream_evaluations:
        result = upstream.get("result")
        if not isinstance(result, Mapping) or result.get("schemaVersion") != (
            "schema://contract-performance/result@1"
        ):
            continue
        plan = result.get("plan")
        performance = result.get("performance")
        if not isinstance(plan, Mapping) or not isinstance(performance, Mapping):
            continue
        actual_by_id = {
            str(value.get("milestoneId") or ""): value
            for value in performance.get("milestones", [])
            if isinstance(value, Mapping)
        }
        evidence_ref = (
            f"evaluation://{upstream.get('evaluationId')}"
            f"#{upstream.get('resultHash') or result.get('resultHash') or ''}"
        )
        milestones: list[dict[str, Any]] = []
        for item in plan.get("milestones", []):
            if not isinstance(item, Mapping):
                continue
            milestone_id = str(item.get("id") or "")
            actual = actual_by_id.get(milestone_id, {})
            actual_finish = actual.get("actualFinishDate")
            if not actual_finish:
                continue
            milestones.append(
                {
                    "milestoneId": milestone_id,
                    "name": str(item.get("title") or milestone_id),
                    "baselineDate": item.get("dueDate"),
                    "actualDate": actual_finish,
                    "critical": item.get("critical"),
                    "evidenceRefs": [evidence_ref],
                }
            )
        return {
            "payloadPatch": {"time": {"milestones": milestones}} if milestones else {},
            "facts": [
                {
                    "factId": f"upstream-performance-{upstream.get('evaluationId')}",
                    "factType": "CONFIRMED_CONTRACT_PERFORMANCE",
                    "value": str(result.get("status") or ""),
                    "confidence": 1.0,
                    "evidenceRefs": [evidence_ref],
                }
            ],
            "conflicts": [],
            "missingEvidence": [],
            "source": {
                "evaluationId": upstream.get("evaluationId"),
                "resultHash": upstream.get("resultHash") or result.get("resultHash"),
            },
        }
    return {
        "payloadPatch": {},
        "facts": [],
        "conflicts": [],
        "missingEvidence": [],
        "source": None,
    }


def calculate_time_deviation(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("time")
    if not isinstance(data, Mapping):
        return _status_payload(
            "DATA_INSUFFICIENT",
            metrics=_EMPTY_TIME_METRICS,
            reasons=("missing time facts",),
        )
    milestones = data.get("milestones")
    if not isinstance(milestones, list) or not milestones:
        return _status_payload(
            "DATA_INSUFFICIENT",
            metrics=_EMPTY_TIME_METRICS,
            reasons=("missing milestones",),
        )

    results: list[dict[str, Any]] = []
    evidence_refs: list[str] = []
    on_time = 0
    critical_complete = True
    critical_delays: list[int] = []
    for index, raw in enumerate(milestones):
        if not isinstance(raw, Mapping):
            continue
        baseline_value = raw.get("currentBaselineDate") or raw.get("baselineDate")
        actual_value = raw.get("actualDate") or raw.get("forecastDate")
        if not baseline_value or not actual_value:
            continue
        baseline = _date(baseline_value, field=f"milestones[{index}].baselineDate")
        actual = _date(actual_value, field=f"milestones[{index}].actualOrForecastDate")
        variance_days = (actual - baseline).days
        if variance_days <= 0:
            on_time += 1
        is_critical = raw.get("critical") is True
        if is_critical:
            critical_delays.append(variance_days)
        elif "critical" not in raw:
            critical_complete = False
        refs = raw.get("evidenceRefs", [])
        if isinstance(refs, list):
            evidence_refs.extend(str(value) for value in refs)
        results.append(
            {
                "milestoneId": str(raw.get("milestoneId") or raw.get("name") or index + 1),
                "name": str(raw.get("name") or raw.get("milestoneId") or f"里程碑 {index + 1}"),
                "baselineDate": baseline.isoformat(),
                "actualOrForecastDate": actual.isoformat(),
                "dateBasis": "ACTUAL" if raw.get("actualDate") else "FORECAST",
                "varianceDays": variance_days,
                "critical": raw.get("critical"),
            }
        )
    if not results:
        return _status_payload(
            "DATA_INSUFFICIENT",
            metrics=_EMPTY_TIME_METRICS,
            reasons=("no milestone has both baseline and actual/forecast date",),
        )
    pv = data.get("pv")
    ev = data.get("ev")
    spi: float | None = None
    spi_reason: str | None = None
    if pv is not None and ev is not None:
        pv_value = _decimal(pv, field="time.pv")
        ev_value = _decimal(ev, field="time.ev")
        if pv_value > 0:
            spi = _number(ev_value / pv_value, "0.0001")
        else:
            spi_reason = "PV must be greater than zero"
    else:
        spi_reason = "PV and EV are both required"
    metrics = {
        "milestones": results,
        "milestoneCount": len(results),
        "onTimeCount": on_time,
        "onTimeRate": _number(Decimal(on_time) / Decimal(len(results)), "0.0001"),
        "maximumDelayDays": max(item["varianceDays"] for item in results),
        "criticalPathDelayDays": (
            max(critical_delays) if critical_delays and critical_complete else None
        ),
        "criticalPathAvailable": bool(critical_delays) and critical_complete,
        "spi": spi,
        "spiUnavailableReason": spi_reason,
    }
    thresholds = payload.get("thresholds", {})
    time_threshold = (
        int(thresholds.get("delayDaysHigh", thresholds.get("timeDays", 15)))
        if isinstance(thresholds, Mapping)
        else 15
    )
    metrics["material"] = metrics["maximumDelayDays"] > time_threshold
    return _status_payload("OK", metrics=metrics, evidence_refs=evidence_refs)


def compare_content_deviation(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("content")
    if not isinstance(data, Mapping):
        return _status_payload(
            "DATA_INSUFFICIENT",
            metrics=_EMPTY_CONTENT_METRICS,
            reasons=("missing content facts",),
        )
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return _status_payload(
            "DATA_INSUFFICIENT",
            metrics=_EMPTY_CONTENT_METRICS,
            reasons=("missing deliverable items",),
        )
    valid = [item for item in items if isinstance(item, Mapping)]
    if not valid:
        return _status_payload(
            "DATA_INSUFFICIENT",
            metrics=_EMPTY_CONTENT_METRICS,
            reasons=("no valid deliverable item",),
        )
    has_explicit_weights = all(item.get("weight") is not None for item in valid)
    weights = (
        [_decimal(item["weight"], field="content.items.weight") for item in valid]
        if has_explicit_weights
        else [Decimal("1") for _ in valid]
    )
    if any(weight < 0 for weight in weights) or sum(weights) <= 0:
        return _status_payload(
            "CONFLICTED",
            metrics=_EMPTY_CONTENT_METRICS,
            reasons=("content weights must sum to a positive value",),
        )
    total_weight = sum(weights)
    weighted_score = Decimal("0")
    evidence_refs: list[str] = []
    details: list[dict[str, Any]] = []
    for index, (item, weight) in enumerate(zip(valid, weights, strict=True)):
        status = str(item.get("status", "MISSING")).upper()
        if status not in _CONTENT_SCORES:
            return _status_payload(
                "CONFLICTED",
                metrics=_EMPTY_CONTENT_METRICS,
                reasons=(f"unsupported content status: {status}",),
            )
        score = _CONTENT_SCORES[status]
        weighted_score += score * weight
        refs = item.get("evidenceRefs", [])
        if isinstance(refs, list):
            evidence_refs.extend(str(value) for value in refs)
        details.append(
            {
                "itemId": str(item.get("itemId") or index + 1),
                "name": str(item.get("name") or f"交付项 {index + 1}"),
                "status": status,
                "weight": _number(weight / total_weight, "0.0001"),
                "completionScore": _number(score, "0.0001"),
            }
        )
    actual = weighted_score / total_weight
    thresholds = payload.get("thresholds", {})
    content_threshold = _decimal(
        thresholds.get(
            "contentVarianceRateHigh",
            abs(float(thresholds.get("contentVarianceRate", -0.1))),
        )
        if isinstance(thresholds, Mapping)
        else 0.1,
        field="thresholds.contentVarianceRateHigh",
    )
    return _status_payload(
        "OK",
        metrics={
            "items": details,
            "plannedCompletionRate": 1.0,
            "actualCompletionRate": _number(actual, "0.0001"),
            "contentVarianceRate": _number(actual - Decimal("1"), "0.0001"),
            "equalWeightFallback": not has_explicit_weights,
            "material": abs(min(actual - Decimal("1"), Decimal("0")))
            >= content_threshold,
        },
        evidence_refs=evidence_refs,
        reasons=("equal weights applied because one or more weights were missing",)
        if not has_explicit_weights
        else (),
    )


def calculate_cost_deviation(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("cost")
    if not isinstance(data, Mapping):
        return _status_payload(
            "DATA_INSUFFICIENT",
            metrics=_EMPTY_COST_METRICS,
            reasons=("missing cost facts",),
        )
    currency = str(data.get("currency") or payload.get("currency") or "").upper()
    currencies = {
        str(item).upper()
        for item in data.get("currencies", [])
        if isinstance(item, str) and item
    }
    if currency:
        currencies.add(currency)
    if len(currencies) > 1:
        normalized_currency = str(data.get("normalizedToCurrency") or "").upper()
        if (
            not data.get("exchangeRates")
            or not data.get("exchangeRatesHash")
            or normalized_currency != currency
        ):
            return _status_payload(
                "CONFLICTED",
                metrics=_EMPTY_COST_METRICS,
                reasons=(
                    "cross-currency facts require frozen rates and normalized amounts",
                ),
            )
    original = data.get("originalBAC")
    eac = data.get("eac")
    if original is None or eac is None:
        return _status_payload(
            "DATA_INSUFFICIENT",
            metrics=_EMPTY_COST_METRICS,
            reasons=("originalBAC and EAC are required",),
        )
    original_value = _decimal(original, field="cost.originalBAC")
    eac_value = _decimal(eac, field="cost.eac")
    changes = data.get("approvedChanges", [])
    if isinstance(changes, list):
        approved = sum(
            (_decimal(item.get("amount"), field="cost.approvedChanges.amount") for item in changes
             if isinstance(item, Mapping) and item.get("approved", True) is True),
            Decimal("0"),
        )
    else:
        approved = _decimal(changes, field="cost.approvedChanges")
    current_bac = original_value + approved
    overrun = eac_value - current_bac
    overrun_rate = overrun / current_bac if current_bac else None
    ac = _decimal(data["ac"], field="cost.ac") if data.get("ac") is not None else None
    commitments = (
        _decimal(data["commitments"], field="cost.commitments")
        if data.get("commitments") is not None
        else None
    )
    ev = _decimal(data["ev"], field="cost.ev") if data.get("ev") is not None else None
    cv = ev - ac if ev is not None and ac is not None else None
    cpi = ev / ac if ev is not None and ac is not None and ac > 0 else None
    refs = data.get("evidenceRefs", [])
    thresholds = payload.get("thresholds", {})
    cost_threshold = _decimal(
        thresholds.get(
            "forecastOverrunRateHigh",
            thresholds.get("costVarianceRate", 0.05),
        )
        if isinstance(thresholds, Mapping)
        else 0.05,
        field="thresholds.forecastOverrunRateHigh",
    )
    return _status_payload(
        "OK",
        metrics={
            "currency": currency or None,
            "originalBAC": _number(original_value),
            "approvedChangeAmount": _number(approved),
            "currentBAC": _number(current_bac),
            "eac": _number(eac_value),
            "costVariance": _number(overrun),
            "costVarianceRate": _number(overrun_rate, "0.0001"),
            "ac": _number(ac),
            "commitments": _number(commitments),
            "actualPlusCommitments": _number(ac + commitments)
            if ac is not None and commitments is not None
            else None,
            "evmCV": _number(cv),
            "cpi": _number(cpi, "0.0001"),
            "material": overrun_rate is not None and overrun_rate >= cost_threshold,
        },
        evidence_refs=[str(value) for value in refs] if isinstance(refs, list) else (),
    )


def build_deviation_trends(
    current: Mapping[str, Any],
    history: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    compatible = [
        item
        for item in history
        if item.get("baselineHash") == current.get("baselineHash")
        and item.get("configurationHash") == current.get("configurationHash")
        and item.get("subjectId") == current.get("subjectId")
    ]
    points = [
        {
            "asOf": item.get("asOf"),
            "timeVarianceDays": item.get("timeVarianceDays"),
            "contentVarianceRate": item.get("contentVarianceRate"),
            "costVarianceRate": item.get("costVarianceRate"),
        }
        for item in (*compatible, current)
    ]
    points.sort(key=lambda item: str(item.get("asOf") or ""))
    if len(points) < 2:
        return {
            "status": "DATA_INSUFFICIENT",
            "points": points,
            "summary": "首次评估或无同口径历史结果; 暂不判断趋势。",
        }
    return {
        "status": "OK",
        "points": points,
        "summary": "已按同基线、同配置口径生成趋势。",
    }


def aggregate_responsibility(
    proposals: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    for index, proposal in enumerate(proposals):
        refs = proposal.get("evidenceRefs", [])
        confidence = float(proposal.get("confidence") or 0)
        if not 0 <= confidence <= 1:
            raise ValueError("responsibility confidence must be between 0 and 1")
        immutable_refs = [
            document_version_id
            for value in refs
            if (document_version_id := _leading_uuid(value))
        ] if isinstance(refs, list) else []
        normalized.append(
            {
                "proposalId": str(proposal.get("proposalId") or index + 1),
                "party": str(proposal.get("party") or "待确认"),
                "scope": str(proposal.get("scope") or "UNSPECIFIED"),
                "rationale": str(proposal.get("rationale") or "证据不足; 需人工确认"),
                "confidence": confidence,
                "evidenceRefs": list(dict.fromkeys(immutable_refs)),
                "status": "PROPOSED",
            }
        )
    return {
        "status": "PENDING_CONFIRMATION" if normalized else "NO_PROPOSAL",
        "proposals": normalized,
        "decisions": [],
        "humanConfirmationRequired": bool(normalized),
    }


def _leading_uuid(value: Any) -> str | None:
    text = str(value).strip()
    if len(text) < 36:
        return None
    try:
        return str(UUID(text[:36]))
    except ValueError:
        return None


def finalize_deviation_result(
    *,
    payload: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    root_causes: Iterable[Mapping[str, Any]],
    trends: Mapping[str, Any],
    responsibility: Mapping[str, Any],
    coverage: Mapping[str, Any],
    evidence_review: Mapping[str, Any],
    narrative: Mapping[str, Any],
    provenance: Mapping[str, Any],
    approvals: Iterable[Mapping[str, Any]] = (),
    schema_version: str = SCHEMA_VERSION,
) -> dict[str, Any]:
    requested = [str(value).upper() for value in payload.get("dimensions", DIMENSIONS)]
    dimension_results = {
        code: dict(dimensions.get(code, _status_payload("DATA_INSUFFICIENT")))
        for code in requested
        if code in DIMENSIONS
    }
    conflicted = any(
        item["status"] == "CONFLICTED" for item in dimension_results.values()
    )
    unsupported_dimensions = [
        code
        for code, item in dimension_results.items()
        if item["status"] == "OK" and not item.get("evidenceRefs")
    ]
    responsibility_items = responsibility.get("proposals", [])
    review_required = (
        bool(evidence_review.get("reviewRequired"))
        or conflicted
        or bool(responsibility_items)
        or bool(unsupported_dimensions)
    )
    quality_status = (
        "BLOCKED"
        if conflicted
        else "REVIEW_REQUIRED"
        if review_required
        else "READY"
    )
    period = payload.get("period", {})
    subject = payload.get("subject", {})
    root_cause_values = [dict(item) for item in root_causes]
    evidence_refs = list(
        dict.fromkeys(
            [
                *(
                    str(reference)
                    for dimension in dimension_results.values()
                    for reference in dimension.get("evidenceRefs", [])
                ),
                *(
                    str(reference)
                    for cause in root_cause_values
                    for reference in _evidence_refs(cause)
                ),
                *(
                    str(reference)
                    for proposal in responsibility_items
                    if isinstance(proposal, Mapping)
                    for reference in _evidence_refs(proposal)
                ),
            ]
        )
    )
    quality_flags = [
        {
            "dimension": code,
            "status": dimension["status"],
            "reason": reason,
        }
        for code, dimension in dimension_results.items()
        for reason in dimension.get("reasons", [])
    ]
    quality_flags.extend(
        {
            "dimension": code,
            "status": "EVIDENCE_REQUIRED",
            "reason": "evaluated metrics have no immutable evidence reference",
        }
        for code in unsupported_dimensions
    )
    findings = [
        {
            "code": f"{code}_{dimension['status']}",
            "dimension": code,
            "status": dimension["status"],
            "material": bool(dimension.get("metrics", {}).get("material")),
        }
        for code, dimension in dimension_results.items()
        if dimension["status"] != "OK"
        or bool(dimension.get("metrics", {}).get("material"))
    ]
    findings.extend(
        {
            "code": f"RESPONSIBILITY_PROPOSAL_{proposal.get('proposalId', index + 1)}",
            "dimension": "RESPONSIBILITY",
            "status": "PENDING_CONFIRMATION",
            "material": True,
            "party": str(proposal.get("party") or "待确认"),
            "rationale": str(proposal.get("rationale") or ""),
            "evidenceRefs": _evidence_refs(proposal),
        }
        for index, proposal in enumerate(responsibility_items)
        if isinstance(proposal, Mapping)
    )
    assessment = {
        "subjectId": subject.get("subjectId")
        if isinstance(subject, Mapping)
        else None,
        "periodStart": period.get("start") if isinstance(period, Mapping) else None,
        "periodEnd": period.get("end") if isinstance(period, Mapping) else None,
        "asOf": payload.get("asOf"),
        "baselineHash": provenance.get("baselineHash"),
        "selectionManifestHash": provenance.get("selectionManifestHash"),
    }
    result = {
        "schemaVersion": schema_version,
        "title": str(payload.get("title") or "偏差分析报告"),
        "assessment": assessment,
        "subject": dict(subject) if isinstance(subject, Mapping) else {},
        "period": dict(period) if isinstance(period, Mapping) else {},
        "asOf": payload.get("asOf"),
        "qualityStatus": quality_status,
        "reviewRequired": review_required,
        "dimensions": dimension_results,
        "time": dimension_results.get(
            "TIME",
            _status_payload("NOT_APPLICABLE", reasons=("dimension not requested",)),
        ),
        "content": dimension_results.get(
            "CONTENT",
            _status_payload("NOT_APPLICABLE", reasons=("dimension not requested",)),
        ),
        "cost": dimension_results.get(
            "COST",
            _status_payload("NOT_APPLICABLE", reasons=("dimension not requested",)),
        ),
        "coverage": dict(coverage),
        "rootCauses": root_cause_values,
        "trends": dict(trends),
        "responsibility": dict(responsibility),
        "findings": findings,
        "actions": [],
        "evidence": evidence_refs,
        "qualityFlags": quality_flags,
        "evidenceReview": dict(evidence_review),
        "narrative": dict(narrative),
        "provenance": dict(provenance),
        "artifacts": [],
    }
    if schema_version == "schema://deviation-analysis/result@2":
        result["approvals"] = [dict(value) for value in approvals]
    return result


def validate_deviation_result(value: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(value)
    if result.get("schemaVersion") not in {
        SCHEMA_VERSION,
        "schema://deviation-analysis/result@2",
    }:
        raise ValueError("unexpected deviation-analysis result schemaVersion")
    required = {
        "assessment",
        "coverage",
        "time",
        "content",
        "cost",
        "rootCauses",
        "trends",
        "findings",
        "actions",
        "evidence",
        "qualityFlags",
        "artifacts",
        "provenance",
    }
    missing = sorted(required - result.keys())
    if result.get("schemaVersion") == "schema://deviation-analysis/result@2" and (
        "approvals" not in result
    ):
        missing.append("approvals")
    if missing:
        raise ValueError(
            f"deviation-analysis result missing fields: {', '.join(missing)}"
        )
    dimensions = result.get("dimensions")
    if not isinstance(dimensions, Mapping) or not dimensions:
        raise ValueError("deviation-analysis result must contain dimensions")
    allowed_dimension_statuses = {
        "OK",
        "DATA_INSUFFICIENT",
        "CONFLICTED",
        "NOT_APPLICABLE",
    }
    for code, dimension in dimensions.items():
        if code not in DIMENSIONS or not isinstance(dimension, Mapping):
            raise ValueError("invalid deviation dimension")
        if dimension.get("status") not in allowed_dimension_statuses:
            raise ValueError("invalid deviation dimension status")
    for code, alias in (("TIME", "time"), ("CONTENT", "content"), ("COST", "cost")):
        expected = dimensions.get(
            code,
            _status_payload(
                "NOT_APPLICABLE",
                reasons=("dimension not requested",),
            ),
        )
        if result.get(alias) != expected:
            raise ValueError(f"{alias} must match dimensions.{code}")
    responsibility = result.get("responsibility")
    if not isinstance(responsibility, Mapping):
        raise ValueError("deviation-analysis result must contain responsibility")
    if responsibility.get("status") not in {
        "NO_PROPOSAL",
        "PENDING_CONFIRMATION",
        "CONFIRMED",
        "DISPUTED",
    }:
        raise ValueError("invalid responsibility summary status")
    for item in responsibility.get("proposals", []):
        if not isinstance(item, Mapping) or item.get("status") not in {
            "PROPOSED",
            "CONFIRMED",
            "DISPUTED",
        }:
            raise ValueError("invalid responsibility status")
    provenance = result.get("provenance")
    if not isinstance(provenance, Mapping) or any(
        not provenance.get(key)
        for key in (
            "documentContentHash",
            "attachmentManifestHash",
            "selectionManifestHash",
            "baselineHash",
            "configurationHash",
        )
    ):
        raise ValueError("deviation-analysis provenance hashes are required")
    return result


def deviation_report_lines(result: Mapping[str, Any]) -> tuple[str, ...]:
    lines = [
        str(result.get("title") or "偏差分析报告"),
        "运行结论",
        f"数据质量状态: {result.get('qualityStatus', 'UNKNOWN')}",
        f"是否需要复核: {'是' if result.get('reviewRequired') else '否'}",
        "三维偏差",
    ]
    dimensions = result.get("dimensions", {})
    if isinstance(dimensions, Mapping):
        time_result = dimensions.get("TIME", {})
        time_metrics = (
            time_result.get("metrics", {}) if isinstance(time_result, Mapping) else {}
        )
        milestones = (
            time_metrics.get("milestones", []) if isinstance(time_metrics, Mapping) else []
        )
        milestone = milestones[0] if isinstance(milestones, list) and milestones else {}
        if isinstance(milestone, Mapping):
            basis = "实际" if milestone.get("dateBasis") == "ACTUAL" else "预测"
            lines.append(
                f"- 时间偏差: {int(milestone.get('varianceDays') or 0):,} 天"
                f" (基线 {milestone.get('baselineDate')} → {basis} "
                f"{milestone.get('actualOrForecastDate')})"
            )

        cost_result = dimensions.get("COST", {})
        cost_metrics = (
            cost_result.get("metrics", {}) if isinstance(cost_result, Mapping) else {}
        )
        if isinstance(cost_metrics, Mapping):
            variance = float(cost_metrics.get("costVariance") or 0) / 1_000_000_000
            rate = float(cost_metrics.get("costVarianceRate") or 0)
            original = float(cost_metrics.get("originalBAC") or 0) / 1_000_000_000
            eac = float(cost_metrics.get("eac") or 0) / 1_000_000_000
            lines.append(
                f"- 成本偏差: GBP {variance:.2f}bn ({rate:.2%}), "
                f"原始预算 GBP {original:.2f}bn, EAC GBP {eac:.2f}bn"
            )

        content_result = dimensions.get("CONTENT", {})
        content_metrics = (
            content_result.get("metrics", {}) if isinstance(content_result, Mapping) else {}
        )
        if isinstance(content_metrics, Mapping):
            actual = float(content_metrics.get("actualCompletionRate") or 0)
            variance = float(content_metrics.get("contentVarianceRate") or 0)
            lines.append(
                f"- 内容偏差: 实际完成率 {actual:.2%}, 相对计划 {variance:.2%}"
            )
            content_items = content_metrics.get("items", [])
            if isinstance(content_items, list):
                lines.extend(
                    f"- 内容项: {item.get('name') or item.get('itemId')} "
                    f"[{item.get('status') or 'UNKNOWN'}]"
                    for item in content_items
                    if isinstance(item, Mapping)
                )
    trends = result.get("trends", {})
    if isinstance(trends, Mapping):
        lines.append("趋势可视化 (同基线、同配置)")
        points = trends.get("points", [])
        if isinstance(points, list) and points:
            labels = [
                str(point.get("asOf", ""))[:4]
                for point in points
                if isinstance(point, Mapping)
            ]
            time_values = [
                f"{int(point.get('timeVarianceDays') or 0):,}"
                for point in points
                if isinstance(point, Mapping)
            ]
            cost_values = [
                f"{float(point.get('costVarianceRate') or 0):.2%}"
                for point in points
                if isinstance(point, Mapping)
            ]
            content_values = [
                f"{float(point.get('contentVarianceRate') or 0):.2%}"
                for point in points
                if isinstance(point, Mapping)
            ]
            time_trend = " → ".join(
                f"{label} {value}"
                for label, value in zip(labels, time_values, strict=True)
            )
            cost_trend = " → ".join(
                f"{label} {value}"
                for label, value in zip(labels, cost_values, strict=True)
            )
            content_trend = " → ".join(
                f"{label} {value}"
                for label, value in zip(labels, content_values, strict=True)
            )
            lines.extend(
                (
                    f"- 时间偏差 (天): {time_trend}",
                    f"- 成本偏差率: {cost_trend}",
                    f"- 内容偏差率: {content_trend}",
                    str(trends.get("summary") or "无同口径趋势结论"),
                )
            )
    narrative = result.get("narrative", {})
    if isinstance(narrative, Mapping) and narrative.get("executiveSummary"):
        lines.extend(("管理摘要", str(narrative["executiveSummary"])))
    root_causes = result.get("rootCauses", [])
    if isinstance(root_causes, list) and root_causes:
        lines.append("AI 根因假设")
        for item in root_causes:
            if not isinstance(item, Mapping):
                continue
            confidence = float(item.get("confidence") or 0)
            lines.append(
                f"- {item.get('causeId') or 'RC'}: "
                f"{item.get('title') or item.get('hypothesis') or '待复核根因'!s}"
                f" (置信度 {confidence:.0%})"
            )
            refs = _evidence_refs(item)
            if refs:
                lines.append(f"  证据版本: {', '.join(refs)}")
    responsibility = result.get("responsibility", {})
    if isinstance(responsibility, Mapping):
        proposals = responsibility.get("proposals", [])
        if isinstance(proposals, list) and proposals:
            lines.append("责任归属建议")
            lines.append(
                f"总体状态: {responsibility.get('status') or 'PENDING_CONFIRMATION'}; "
                "全部责任项仅为 PROPOSED。"
            )
            for item in proposals:
                if not isinstance(item, Mapping):
                    continue
                lines.append(
                    f"- {item.get('party') or '待确认'!s} "
                    f"[{item.get('status') or 'PROPOSED'}]"
                )
                lines.append(f"  建议范围: {item.get('scope') or '待确认'}")
                refs = _evidence_refs(item)
                if refs:
                    lines.append(f"  证据版本: {', '.join(refs)}")
    evidence = result.get("evidence", [])
    if isinstance(evidence, list) and evidence:
        lines.append("不可变证据版本")
        lines.extend(f"- {reference}" for reference in evidence)
    lines.extend(
        (
            "复核与免责声明",
            "内容完成率为公开案例运行口径, 不代表法律意义上的全项目验收率。",
            "责任归属为 AI 建议; 状态仅为 PROPOSED / PENDING_CONFIRMATION, "
            "须经人工确认后方可作为正式结论。",
            "本报告用于公开案例运行验证, 不构成企业生产结论或法律责任认定。",
        )
    )
    return tuple(lines)
