from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from swarmcore_persistence.repositories import canonical_hash

_DOCUMENT_ROLES = ("TENDER", "BID", "AWARD", "CONTRACT")
_SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "BLOCKER": 4}
_BLOCKER_CATEGORIES = {
    "PARTY",
    "SUBJECT",
    "PRICE",
    "SCOPE",
    "QUANTITY",
    "QUALITY",
    "PERFORMANCE_PERIOD",
}
_HIGH_CATEGORIES = {
    "PAYMENT",
    "ACCEPTANCE",
    "GUARANTEE",
    "LIABILITY",
    "LIABILITY_CAP",
    "BREACH",
    "DISPUTE",
    "INTELLECTUAL_PROPERTY",
    "DATA_SECURITY",
    "SUBCONTRACTING",
}
_RISK_DIMENSIONS: dict[str, tuple[str, int]] = {
    "GOVERNMENT_PROCUREMENT_BAN": ("PROCUREMENT", 30),
    "GOVERNMENT_PROCUREMENT_VIOLATION": ("PROCUREMENT", 18),
    "INTERNAL_BLACKLIST": ("PROCUREMENT", 30),
    "LOST_CREDIT_EXECUTION": ("JUDICIAL", 25),
    "RESTRICTED_CONSUMPTION": ("JUDICIAL", 18),
    "ENFORCEMENT_CASE": ("JUDICIAL", 10),
    "TAX_SERIOUS_DISHONESTY": ("TAX_ADMIN", 20),
    "SERIOUS_ADMIN_PENALTY": ("TAX_ADMIN", 15),
    "ADMIN_PENALTY": ("TAX_ADMIN", 8),
    "SERIOUS_ILLEGAL": ("OPERATING", 15),
    "QUALIFICATION_INVALID": ("OPERATING", 15),
    "BUSINESS_ABNORMAL": ("OPERATING", 8),
    "REGISTRATION_CANCELLED": ("OPERATING", 15),
    "RELATION_CONFLICT": ("RELATION", 10),
}
_RISK_DIMENSION_CAPS = {
    "PROCUREMENT": 30,
    "JUDICIAL": 25,
    "TAX_ADMIN": 20,
    "OPERATING": 15,
    "RELATION": 10,
}
_HARD_GATE_TYPES = {
    "GOVERNMENT_PROCUREMENT_BAN",
    "INTERNAL_BLACKLIST",
    "TAX_SERIOUS_DISHONESTY",
    "SERIOUS_ADMIN_PENALTY",
    "QUALIFICATION_INVALID",
    "REGISTRATION_CANCELLED",
}
_PERFORMANCE_WEIGHTS = {
    "ON_TIME_DELIVERY": Decimal("25"),
    "QUALITY_FIRST_PASS": Decimal("25"),
    "ACCEPTANCE_SERVICE": Decimal("20"),
    "COMMERCIAL_COMPLIANCE": Decimal("15"),
    "REMEDIATION": Decimal("15"),
}


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _rounded(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _percentage(value: Decimal | None) -> float | None:
    return _rounded(value * Decimal(100)) if value is not None else None


def _normalized_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalized_value(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_normalized_value(item) for item in value]
    number = _decimal(value)
    if number is not None and not isinstance(value, str):
        return str(number.normalize())
    if isinstance(value, str):
        return " ".join(value.split()).casefold()
    return value


def _evidence_refs(*values: Any) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in values:
        for item in value if isinstance(value, list) else []:
            if not isinstance(item, dict):
                continue
            key = canonical_hash(item)
            if key in seen:
                continue
            seen.add(key)
            refs.append(dict(item))
    return refs


def _clause_key(clause: dict[str, Any], ordinal: int) -> str:
    explicit = str(clause.get("matchKey") or "").strip()
    if explicit:
        return explicit
    category = str(clause.get("category") or "OTHER").upper()
    return f"{category}:{ordinal}"


def _severity(category: str, change_type: str, proposed: str | None = None) -> str:
    if category in _BLOCKER_CATEGORIES and change_type in {
        "MISSING",
        "CONFLICT",
        "WEAKENED",
        "CHANGED",
    }:
        baseline = "BLOCKER"
    elif category in _HIGH_CATEGORIES or change_type == "WEAKENED":
        baseline = "HIGH"
    elif change_type in {"MISSING", "CONFLICT", "ADDED"}:
        baseline = "MEDIUM"
    else:
        baseline = "LOW"
    candidate = str(proposed or "").upper()
    if candidate in _SEVERITY_RANK and _SEVERITY_RANK[candidate] > _SEVERITY_RANK[baseline]:
        return candidate
    return baseline


def compare_procurement_clauses(payload: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic four-way clause lineages and material differences."""

    raw_documents = payload.get("clauses") or {}
    if not isinstance(raw_documents, dict):
        raise ValueError("clauses must be an object keyed by document role")
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for role in _DOCUMENT_ROLES:
        raw_clauses = raw_documents.get(role) or []
        if not isinstance(raw_clauses, list):
            raise ValueError(f"{role} clauses must be an array")
        category_ordinals: dict[str, int] = defaultdict(int)
        for raw in raw_clauses:
            if not isinstance(raw, dict):
                continue
            category = str(raw.get("category") or "OTHER").upper()
            ordinal = category_ordinals[category]
            category_ordinals[category] += 1
            clause = {**raw, "category": category, "documentRole": role}
            clause.setdefault("clauseId", f"{role.lower()}-{category.lower()}-{ordinal + 1}")
            grouped[_clause_key(clause, ordinal)][role] = clause

    proposals = {
        str(item.get("matchKey")): item
        for item in payload.get("semanticProposals") or []
        if isinstance(item, dict) and item.get("matchKey")
    }
    approved_exceptions = {
        str(item) for item in payload.get("approvedExceptionKeys") or [] if str(item).strip()
    }
    lineages: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for match_key in sorted(grouped):
        by_role = grouped[match_key]
        proposal = proposals.get(match_key, {})
        categories = {
            str(item.get("category") or "OTHER").upper() for item in by_role.values()
        }
        category = sorted(categories)[0] if categories else "OTHER"
        reference = by_role.get("AWARD") or by_role.get("BID") or by_role.get("TENDER")
        contract = by_role.get("CONTRACT")
        reference_value = (
            _normalized_value(reference.get("normalizedValue", reference.get("text")))
            if reference is not None
            else None
        )
        contract_value = (
            _normalized_value(contract.get("normalizedValue", contract.get("text")))
            if contract is not None
            else None
        )
        values_by_role = {
            role: _normalized_value(item.get("normalizedValue", item.get("text")))
            for role, item in by_role.items()
        }
        distinct = {canonical_hash(value) for value in values_by_role.values()}
        if reference is not None and contract is None:
            change_type = "MISSING"
        elif reference is None and contract is not None:
            change_type = "ADDED"
        elif len(distinct) <= 1:
            change_type = "UNCHANGED"
        elif reference_value != contract_value:
            proposed_change = str(proposal.get("changeType") or "").upper()
            change_type = (
                proposed_change
                if proposed_change in {"CONFLICT", "WEAKENED", "CHANGED"}
                else "CHANGED"
            )
        else:
            change_type = "INTERMEDIATE_VARIANCE"

        lineage = {
            "matchKey": match_key,
            "category": category,
            "clauses": {
                role: {
                    "clauseId": by_role[role]["clauseId"],
                    "text": by_role[role].get("text"),
                    "normalizedValue": by_role[role].get("normalizedValue"),
                    "evidenceRefs": list(by_role[role].get("evidenceRefs") or []),
                }
                for role in _DOCUMENT_ROLES
                if role in by_role
            },
            "changeType": change_type,
        }
        lineages.append(lineage)
        if change_type in {"UNCHANGED", "INTERMEDIATE_VARIANCE"}:
            continue
        severity = _severity(category, change_type, str(proposal.get("severity") or ""))
        exception_approved = match_key in approved_exceptions
        evidence = _evidence_refs(
            *(item.get("evidenceRefs") for item in by_role.values()),
            proposal.get("evidenceRefs"),
        )
        finding_seed = {
            "matchKey": match_key,
            "category": category,
            "changeType": change_type,
            "values": values_by_role,
        }
        findings.append(
            {
                "findingId": f"consistency-{canonical_hash(finding_seed)[:20]}",
                "code": f"PROCUREMENT_{change_type}",
                "category": category,
                "severity": severity,
                "changeType": change_type,
                "title": f"{category} 条款{change_type.lower()}",
                "summary": str(
                    proposal.get("summary")
                    or f"合同与采购/中标基线在 {category} 条款上存在{change_type.lower()}。"
                ),
                "matchKey": match_key,
                "evidenceRefs": evidence,
                "confidence": float(proposal.get("confidence") or 1),
                "approvedException": exception_approved,
            }
        )

    counts = {
        severity: sum(item["severity"] == severity for item in findings)
        for severity in ("BLOCKER", "HIGH", "MEDIUM", "LOW")
    }
    return {
        "clauseLineages": lineages,
        "findings": findings,
        "counts": counts,
        "blocking": counts["BLOCKER"] > 0,
        "reviewRequired": counts["BLOCKER"] > 0 or counts["HIGH"] > 0,
        "ruleVersion": str(payload.get("ruleVersion") or "rule://procurement-consistency@1"),
    }


def collect_risk_observations(payload: dict[str, Any]) -> dict[str, Any]:
    supplier = dict(payload.get("supplier") or {})
    credit_code = str(supplier.get("creditCode") or "").strip().upper()
    supplier_name = "".join(str(supplier.get("name") or "").split()).casefold()
    if not credit_code:
        raise ValueError("supplier.creditCode is required")
    source_statuses: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    for source in payload.get("sources") or []:
        if not isinstance(source, dict):
            continue
        source_ref = str(source.get("sourceRef") or "").strip()
        status = str(source.get("status") or "SUCCEEDED").upper()
        source_statuses.append(
            {
                "sourceRef": source_ref,
                "status": status,
                "fetchedAt": source.get("fetchedAt"),
                "errorCode": source.get("errorCode"),
            }
        )
        if status != "SUCCEEDED":
            continue
        for record in source.get("records") or []:
            if not isinstance(record, dict):
                continue
            record_code = str(
                record.get("creditCode")
                or record.get("supplierCreditCode")
                or record.get("unifiedSocialCreditCode")
                or ""
            ).strip().upper()
            record_name = "".join(
                str(
                    record.get("supplierName")
                    or record.get("enterpriseName")
                    or record.get("name")
                    or ""
                ).split()
            ).casefold()
            identity_match = (
                "EXACT_CREDIT_CODE"
                if record_code and record_code == credit_code
                else "NAME_ONLY"
                if supplier_name and record_name == supplier_name
                else "UNMATCHED"
            )
            observation = {
                **record,
                "sourceRef": source_ref,
                "sourceRecordId": str(
                    record.get("sourceRecordId")
                    or record.get("id")
                    or canonical_hash(record)[:24]
                ),
                "riskType": str(record.get("riskType") or "OTHER").upper(),
                "creditCode": record_code or None,
                "identityMatch": identity_match,
                "publishedAt": record.get("publishedAt"),
                "fetchedAt": source.get("fetchedAt") or record.get("fetchedAt"),
                "contentHash": str(record.get("contentHash") or canonical_hash(record)),
                "evidenceRefs": list(record.get("evidenceRefs") or []),
            }
            observations.append(observation)
    succeeded = sum(item["status"] == "SUCCEEDED" for item in source_statuses)
    coverage = succeeded / len(source_statuses) if source_statuses else 0
    return {
        "supplier": {**supplier, "creditCode": credit_code},
        "sourceStatuses": source_statuses,
        "observations": observations,
        "coverage": round(coverage, 4),
        "collectionStatus": (
            "COMPLETE"
            if source_statuses and succeeded == len(source_statuses)
            else "PARTIAL"
            if succeeded
            else "FAILED"
        ),
    }


def _record_rate(records: list[dict[str, Any]], numerator: str, denominator: str) -> Decimal | None:
    top = Decimal(0)
    bottom = Decimal(0)
    for record in records:
        numerator_value = _decimal(record.get(numerator))
        denominator_value = _decimal(record.get(denominator))
        if numerator_value is None or denominator_value is None or denominator_value <= 0:
            continue
        top += numerator_value
        bottom += denominator_value
    return max(Decimal(0), min(Decimal(1), top / bottom)) if bottom else None


def _boolean_rate(records: list[dict[str, Any]], field: str) -> Decimal | None:
    values = [bool(record[field]) for record in records if record.get(field) is not None]
    if not values:
        return None
    return Decimal(sum(values)) / Decimal(len(values))


def calculate_supplier_performance(payload: dict[str, Any]) -> dict[str, Any]:
    records = [dict(item) for item in payload.get("records") or [] if isinstance(item, dict)]
    metrics: dict[str, Decimal | None] = {}
    delivery_values: list[bool] = []
    for record in records:
        planned = _date(record.get("plannedDeliveryAt"))
        actual = _date(record.get("actualDeliveryAt"))
        if planned is not None and actual is not None:
            delivery_values.append(actual <= planned)
    metrics["ON_TIME_DELIVERY"] = (
        Decimal(sum(delivery_values)) / Decimal(len(delivery_values))
        if delivery_values
        else None
    )
    metrics["QUALITY_FIRST_PASS"] = _record_rate(
        records, "qualityPassedQty", "qualityInspectedQty"
    )
    acceptance = _boolean_rate(records, "acceptanceSlaMet")
    service = _boolean_rate(records, "serviceSlaMet")
    acceptance_components = [item for item in (acceptance, service) if item is not None]
    metrics["ACCEPTANCE_SERVICE"] = (
        sum(acceptance_components, Decimal(0)) / Decimal(len(acceptance_components))
        if acceptance_components
        else None
    )
    metrics["COMMERCIAL_COMPLIANCE"] = _boolean_rate(records, "commercialCompliant")
    complaint_rate = _record_rate(records, "resolvedComplaints", "complaints")
    rectification_rate = _boolean_rate(records, "rectificationOnTime")
    remediation_components = [
        item for item in (complaint_rate, rectification_rate) if item is not None
    ]
    metrics["REMEDIATION"] = (
        sum(remediation_components, Decimal(0)) / Decimal(len(remediation_components))
        if remediation_components
        else None
    )

    available_weight = sum(
        (_PERFORMANCE_WEIGHTS[key] for key, value in metrics.items() if value is not None),
        Decimal(0),
    )
    weighted = sum(
        (
            (value or Decimal(0)) * _PERFORMANCE_WEIGHTS[key]
            for key, value in metrics.items()
            if value is not None
        ),
        Decimal(0),
    )
    coverage = available_weight / Decimal(100)
    score = weighted / available_weight * Decimal(100) if available_weight else None
    sample_size = len({str(item.get("orderId") or index) for index, item in enumerate(records)})
    sufficient = coverage >= Decimal("0.60") and sample_size >= int(
        payload.get("minimumSampleSize") or 3
    )
    return {
        "periodStart": payload.get("periodStart"),
        "periodEnd": payload.get("periodEnd"),
        "sampleSize": sample_size,
        "metrics": [
            {
                "key": key,
                "weight": float(weight),
                "value": _percentage(metrics[key]),
                "available": metrics[key] is not None,
            }
            for key, weight in _PERFORMANCE_WEIGHTS.items()
        ],
        "score": _rounded(score) if score is not None else None,
        "coverage": _rounded(coverage * Decimal(100)),
        "status": "SCORED" if sufficient else "INSUFFICIENT_DATA",
        "sourceRecordRefs": [
            str(item.get("sourceRecordRef") or item.get("orderId") or "")
            for item in records
        ],
        "ruleVersion": str(payload.get("ruleVersion") or "rule://supplier-performance@1"),
    }


def _is_active(observation: dict[str, Any], as_of: date) -> bool:
    explicit = observation.get("active")
    if explicit is not None:
        return bool(explicit)
    start = _date(observation.get("effectiveFrom"))
    end = _date(observation.get("effectiveTo"))
    return (start is None or start <= as_of) and (end is None or end >= as_of)


def decide_supplier_risk(payload: dict[str, Any]) -> dict[str, Any]:
    collection = dict(payload.get("riskCollection") or {})
    performance = dict(payload.get("performance") or {})
    as_of = _date(payload.get("asOf")) or datetime.now(UTC).date()
    observations = [
        {**item, "active": _is_active(item, as_of)}
        for item in collection.get("observations") or []
        if isinstance(item, dict)
    ]
    dimension_points = {key: 0 for key in _RISK_DIMENSION_CAPS}
    hard_gates: list[dict[str, Any]] = []
    for observation in observations:
        risk_type = str(observation.get("riskType") or "OTHER").upper()
        mapping = _RISK_DIMENSIONS.get(risk_type)
        verified_identity = observation.get("identityMatch") in {
            "EXACT_CREDIT_CODE",
            "INTERNAL_MASTER",
        }
        if mapping is not None and observation["active"] and verified_identity:
            dimension, points = mapping
            dimension_points[dimension] = min(
                _RISK_DIMENSION_CAPS[dimension], dimension_points[dimension] + points
            )
        exact_identity = observation.get("identityMatch") == "EXACT_CREDIT_CODE"
        internal_identity = risk_type == "INTERNAL_BLACKLIST" and observation.get(
            "identityMatch"
        ) in {"EXACT_CREDIT_CODE", "INTERNAL_MASTER"}
        if (
            risk_type in _HARD_GATE_TYPES
            and observation["active"]
            and (exact_identity or internal_identity)
        ):
            hard_gates.append(
                {
                    "code": risk_type,
                    "sourceRef": observation.get("sourceRef"),
                    "sourceRecordId": observation.get("sourceRecordId"),
                    "effectiveTo": observation.get("effectiveTo"),
                    "evidenceRefs": list(observation.get("evidenceRefs") or []),
                }
            )
    external_risk = min(100, sum(dimension_points.values()))
    performance_score = _decimal(performance.get("score"))
    performance_coverage = _decimal(performance.get("coverage")) or Decimal(0)
    if performance_score is not None and performance_coverage >= Decimal(60):
        overall_risk = (
            Decimal(external_risk) * Decimal("0.70")
            + (Decimal(100) - performance_score) * Decimal("0.30")
        )
        scoring_mode = "EXTERNAL_AND_PERFORMANCE"
    else:
        overall_risk = Decimal(external_risk)
        scoring_mode = "EXTERNAL_ONLY"
    if hard_gates or overall_risk > 60:
        risk_level = "D"
    elif overall_risk > 40:
        risk_level = "C"
    elif overall_risk > 20:
        risk_level = "B"
    else:
        risk_level = "A"
    collection_status = str(collection.get("collectionStatus") or "FAILED")
    identity_review_required = any(
        item.get("active") and item.get("identityMatch") == "NAME_ONLY"
        for item in observations
    )
    decision = (
        "BLOCK"
        if hard_gates
        else "INSUFFICIENT_EVIDENCE"
        if collection_status == "FAILED"
        else "CONDITIONAL_PASS"
        if risk_level in {"C", "D"} or collection_status == "PARTIAL"
        else "PASS"
    )
    return {
        "asOf": as_of.isoformat(),
        "supplier": dict(collection.get("supplier") or {}),
        "observations": observations,
        "sourceStatuses": list(collection.get("sourceStatuses") or []),
        "dataCoverage": float(collection.get("coverage") or 0),
        "dataFreshness": [
            {
                "sourceRef": item.get("sourceRef"),
                "fetchedAt": item.get("fetchedAt"),
                "status": item.get("status"),
            }
            for item in collection.get("sourceStatuses") or []
        ],
        "dimensionPoints": dimension_points,
        "externalRiskScore": external_risk,
        "performanceScore": float(performance_score) if performance_score is not None else None,
        "performanceCoverage": float(performance_coverage),
        "overallRiskScore": _rounded(overall_risk),
        "scoringMode": scoring_mode,
        "riskLevel": risk_level,
        "hardGates": hard_gates,
        "decision": decision,
        "reviewRequired": bool(hard_gates)
        or risk_level in {"C", "D"}
        or identity_review_required
        or collection_status != "COMPLETE",
        "identityReviewRequired": identity_review_required,
        "ruleVersion": str(payload.get("ruleVersion") or "rule://supplier-risk@1"),
    }


def diff_supplier_risk_snapshots(
    previous: dict[str, Any] | None, current: dict[str, Any]
) -> dict[str, Any]:
    has_previous = bool(
        previous
        and (
            previous.get("snapshotHash")
            or previous.get("asOf")
            or previous.get("observations")
            or previous.get("riskLevel")
        )
    )
    previous = previous or {}

    def index(values: Iterable[Any]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for raw in values:
            if not isinstance(raw, dict):
                continue
            key = "|".join(
                (
                    str(raw.get("sourceRef") or ""),
                    str(raw.get("sourceRecordId") or ""),
                    str(raw.get("riskType") or ""),
                )
            )
            result[key] = raw
        return result

    before = index(previous.get("observations") or [])
    after = index(current.get("observations") or [])
    added = [after[key] for key in sorted(after.keys() - before.keys())]
    removed = [before[key] for key in sorted(before.keys() - after.keys())]
    changed = [
        {"before": before[key], "after": after[key]}
        for key in sorted(before.keys() & after.keys())
        if canonical_hash(before[key]) != canonical_hash(after[key])
    ]
    return {
        "previousSnapshotHash": previous.get("snapshotHash"),
        "added": added,
        "removed": removed,
        "changed": changed,
        "riskLevelChange": {
            "from": previous.get("riskLevel"),
            "to": current.get("riskLevel"),
        },
        "decisionChange": {
            "from": previous.get("decision"),
            "to": current.get("decision"),
        },
        "hasMaterialChange": has_previous
        and (
            bool(added or removed or changed)
            or previous.get("riskLevel") != current.get("riskLevel")
            or previous.get("decision") != current.get("decision")
        ),
    }


def finalize_procurement_supplier_risk(payload: dict[str, Any]) -> dict[str, Any]:
    consistency = dict(payload.get("consistency") or {})
    risk = dict(payload.get("risk") or {})
    performance = dict(payload.get("performance") or {})
    history = dict(payload.get("history") or {})
    approval = payload.get("approval")
    consistency_blocking = bool(consistency.get("blocking"))
    risk_blocking = risk.get("decision") == "BLOCK"
    approved = bool(approval.get("approved")) if isinstance(approval, dict) else False
    if risk_blocking or consistency_blocking:
        final_decision = "BLOCK"
    elif (
        consistency.get("reviewRequired")
        or risk.get("reviewRequired")
        or performance.get("status") == "INSUFFICIENT_DATA"
    ):
        final_decision = "CONDITIONAL_PASS" if approved else "REVIEW_REQUIRED"
    else:
        final_decision = "PASS"
    result = {
        "schemaVersion": "schema://procurement-supplier-risk/result@1",
        "caseId": str(payload.get("caseId") or ""),
        "monitorId": payload.get("monitorId"),
        "assessmentId": str(payload.get("assessmentId") or ""),
        "asOf": risk.get("asOf") or payload.get("asOf"),
        "supplier": dict(risk.get("supplier") or payload.get("supplier") or {}),
        "decision": final_decision,
        "riskLevel": (
            "D"
            if final_decision == "BLOCK"
            else risk.get("riskLevel") or "UNKNOWN"
        ),
        "consistency": consistency,
        "risk": risk,
        "performance": performance,
        "history": history,
        "review": dict(payload.get("review") or {}),
        "approval": dict(approval) if isinstance(approval, dict) else None,
        "provenance": dict(payload.get("provenance") or {}),
    }
    result["snapshotHash"] = canonical_hash(
        {
            "supplier": result["supplier"],
            "asOf": result["asOf"],
            "riskLevel": result["riskLevel"],
            "decision": result["decision"],
            "observations": risk.get("observations") or [],
            "performance": performance,
        }
    )
    result["resultHash"] = canonical_hash(result)
    return result


def validate_procurement_supplier_risk_result(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("schemaVersion") != "schema://procurement-supplier-risk/result@1":
        raise ValueError("unexpected procurement supplier risk schema version")
    expected = canonical_hash({key: value for key, value in result.items() if key != "resultHash"})
    if result.get("resultHash") != expected:
        raise ValueError("procurement supplier risk result hash mismatch")
    if result.get("decision") not in {
        "PASS",
        "CONDITIONAL_PASS",
        "REVIEW_REQUIRED",
        "BLOCK",
    }:
        raise ValueError("invalid procurement supplier risk decision")
    return result
