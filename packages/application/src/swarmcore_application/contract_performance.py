from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from swarmcore_persistence.repositories import canonical_hash

SCHEMA_VERSION = "schema://contract-performance/result@1"
PLAN_SCHEMA_VERSION = "schema://contract-performance/plan@1"
RULE_VERSION = "rule://contract-performance@2"

_PLAN_STATUSES = frozenset({"DRAFT", "CANDIDATE", "REVIEW_REQUIRED", "PUBLISHED", "SUPERSEDED"})
_MILESTONE_STATUSES = frozenset(
    {
        "NOT_STARTED",
        "IN_PROGRESS",
        "EVIDENCE_PENDING",
        "SUBMITTED",
        "ACCEPTED",
        "CONDITIONALLY_ACCEPTED",
        "REJECTED",
        "OVERDUE",
        "WAIVED",
    }
)
_EVIDENCE_TYPES = frozenset(
    {
        "DISPATCH",
        "RECEIPT",
        "ACCEPTANCE",
        "PAYMENT",
        "PROGRESS",
        "SERVICE",
        "MEETING",
        "CHANGE",
    }
)
_MATCH_STATUSES = frozenset({"MATCHED", "CANDIDATE", "CONFLICT", "UNMATCHED", "EXCLUDED"})


def _as_date(value: Any, *, field: str) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _as_decimal(value: Any, *, field: str) -> Decimal | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc


def _money(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value.quantize(Decimal("0.01")))


def _items(value: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    raw = value.get(key) or []
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes | bytearray):
        raise ValueError(f"{key} must be an array")
    return [dict(item) for item in raw if isinstance(item, Mapping)]


def _stable_id(prefix: str, item: Mapping[str, Any], index: int) -> str:
    value = item.get("id")
    return str(value) if value not in (None, "") else f"{prefix}-{index + 1:03d}"


def _evidence_refs(item: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs = item.get("evidenceRefs") or []
    if not isinstance(refs, Sequence) or isinstance(refs, str | bytes | bytearray):
        return []
    return [dict(ref) for ref in refs if isinstance(ref, Mapping)]


def _fact_text(item: Mapping[str, Any]) -> str:
    values = [
        item.get("title"),
        item.get("description"),
        item.get("metric"),
        item.get("dueRule"),
        *(item.get("evidenceRequirements") or []),
        *(
            ref.get("text")
            for ref in _evidence_refs(item)
            if isinstance(ref.get("text"), str)
        ),
    ]
    return " ".join(str(value) for value in values if value not in (None, "")).lower()


def _derive_acceptance_criteria(
    milestones: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    keywords = (
        "accept",
        "evidence",
        "verify",
        "confirm",
        "achiev",
        "completion",
        "outcome",
        "验收",
        "证据",
        "确认",
        "完成",
        "成果",
    )
    derived: list[dict[str, Any]] = []
    for milestone in milestones:
        evidence_refs = _evidence_refs(milestone)
        if not evidence_refs or not any(keyword in _fact_text(milestone) for keyword in keywords):
            continue
        requirements = [
            str(value).strip()
            for value in milestone.get("evidenceRequirements") or []
            if str(value).strip()
        ]
        title = (
            requirements[0]
            if requirements
            else f"Contractual evidence review for {milestone.get('title') or milestone['id']}"
        )
        derived.append(
            {
                "id": f"acc-derived-{len(derived) + 1:03d}",
                "title": title,
                "subjectId": str(milestone["id"]),
                "metric": None,
                "operator": None,
                "target": None,
                "unit": None,
                "method": "contractual evidence review",
                "requiredSigner": None,
                "evidenceType": "CONTRACTUAL_EVIDENCE",
                "evidenceRefs": evidence_refs,
                "confidenceBand": "MEDIUM",
                "qualityFlags": [
                    "DERIVED_FROM_MILESTONE_EVIDENCE",
                    "HUMAN_REVIEW_REQUIRED",
                ],
            }
        )
    return derived


def _derive_service_levels(
    obligations: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    keywords = (
        "performance measure",
        "service level",
        "quality standard",
        "timely",
        "accurate",
        "complete",
        "reporting",
        "outcome rate",
        "completion rate",
        "绩效",
        "服务水平",
        "质量标准",
        "及时",
        "准确",
        "完整",
        "报送",
    )
    derived: list[dict[str, Any]] = []
    for obligation in obligations:
        evidence_refs = _evidence_refs(obligation)
        if not evidence_refs or not any(keyword in _fact_text(obligation) for keyword in keywords):
            continue
        derived.append(
            {
                "id": f"sla-derived-{len(derived) + 1:03d}",
                "title": str(obligation.get("title") or obligation["id"]),
                "metric": str(obligation.get("title") or obligation["id"]),
                "operator": None,
                "target": None,
                "unit": None,
                "measurementPeriod": obligation.get("dueRule"),
                "remedy": None,
                "escalation": None,
                "evidenceRefs": evidence_refs,
                "confidenceBand": "MEDIUM",
                "qualityFlags": [
                    "DERIVED_FROM_OBLIGATION_EVIDENCE",
                    "HUMAN_REVIEW_REQUIRED",
                ],
            }
        )
    return derived


def _derive_supplemental_obligations(
    *,
    needed: int,
    service_levels: Sequence[Mapping[str, Any]],
    milestones: Sequence[Mapping[str, Any]],
    acceptance_criteria: Sequence[Mapping[str, Any]],
    payment_conditions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    source_groups = (
        ("SERVICE_LEVEL", "Meet service level", service_levels),
        ("MILESTONE", "Achieve contractual milestone", milestones),
        ("ACCEPTANCE", "Satisfy acceptance condition", acceptance_criteria),
        ("PAYMENT_CONDITION", "Satisfy payment condition", payment_conditions),
    )
    derived: list[dict[str, Any]] = []
    for source_kind, title_prefix, sources in source_groups:
        for source in sources:
            evidence_refs = _evidence_refs(source)
            if not evidence_refs:
                continue
            source_id = str(source.get("id") or "")
            source_title = str(source.get("title") or source_id).strip()
            derived.append(
                {
                    "id": f"obl-derived-{len(derived) + 1:03d}",
                    "title": f"{title_prefix}: {source_title}",
                    "type": source_kind,
                    "responsibleParty": None,
                    "dueRule": source.get("measurementPeriod") or source.get("dueDate"),
                    "evidenceRequirements": list(source.get("evidenceRequirements") or []),
                    "evidenceRefs": evidence_refs,
                    "confidenceBand": "MEDIUM",
                    "qualityFlags": [
                        f"DERIVED_FROM_{source_kind}",
                        "HUMAN_REVIEW_REQUIRED",
                    ],
                    "derivedFrom": {"kind": source_kind, "id": source_id},
                }
            )
            if len(derived) >= needed:
                return derived
    return derived


def normalize_plan(
    candidates: Mapping[str, Any],
    *,
    timezone: str = "Asia/Shanghai",
    currency: str = "CNY",
) -> dict[str, Any]:
    """Normalize extracted candidates without inventing missing business facts."""
    if len(_items(candidates, "obligations")) > 500:
        raise ValueError("contract-performance supports at most 500 obligations")
    if len(_items(candidates, "milestones")) > 200:
        raise ValueError("contract-performance supports at most 200 milestones")
    conflicts: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    obligations: list[dict[str, Any]] = []
    for index, raw in enumerate(_items(candidates, "obligations")):
        item = deepcopy(raw)
        item["id"] = _stable_id("obl", item, index)
        item["title"] = str(item.get("title") or item.get("description") or "").strip()
        item.setdefault("type", "OTHER")
        item["responsibleParty"] = item.get("responsibleParty") or item.get("party")
        item.setdefault("dueRule", None)
        item.setdefault("evidenceRequirements", [])
        item["evidenceRefs"] = _evidence_refs(item)
        if not item["title"]:
            gaps.append({"code": "OBLIGATION_TITLE_MISSING", "targetId": item["id"]})
        if not item["evidenceRefs"]:
            gaps.append({"code": "EVIDENCE_REFERENCE_MISSING", "targetId": item["id"]})
        obligations.append(item)

    obligation_ids = {item["id"] for item in obligations}
    deliverables: list[dict[str, Any]] = []
    for index, raw in enumerate(_items(candidates, "deliverables")):
        item = deepcopy(raw)
        item["id"] = _stable_id("del", item, index)
        item["title"] = str(item.get("title") or item.get("description") or "").strip()
        item.setdefault("obligationId", None)
        item.setdefault("qualityRequirements", [])
        quantity = _as_decimal(item.get("quantity"), field=f"deliverables[{index}].quantity")
        item["quantity"] = float(quantity) if quantity is not None else None
        if item["obligationId"] and item["obligationId"] not in obligation_ids:
            conflicts.append(
                {
                    "code": "UNKNOWN_OBLIGATION",
                    "targetId": item["id"],
                    "value": item["obligationId"],
                }
            )
        deliverables.append(item)

    acceptance_criteria = _normalize_named_items(_items(candidates, "acceptanceCriteria"), "acc")
    service_levels = _normalize_named_items(_items(candidates, "serviceLevels"), "sla")

    payment_conditions: list[dict[str, Any]] = []
    for index, raw in enumerate(_items(candidates, "paymentConditions")):
        item = deepcopy(raw)
        item["id"] = _stable_id("pay", item, index)
        item["title"] = str(item.get("title") or item.get("description") or "").strip()
        item["amount"] = _money(
            _as_decimal(item.get("amount"), field=f"paymentConditions[{index}].amount")
        )
        rate = _as_decimal(item.get("rate"), field=f"paymentConditions[{index}].rate")
        item["rate"] = float(rate) if rate is not None else None
        cap = _as_decimal(
            item.get("cumulativeCap"), field=f"paymentConditions[{index}].cumulativeCap"
        )
        item["cumulativeCap"] = _money(cap)
        item.setdefault("prerequisites", [])
        item.setdefault("retention", None)
        payment_conditions.append(item)

    milestones: list[dict[str, Any]] = []
    for index, raw in enumerate(_items(candidates, "milestones")):
        item = deepcopy(raw)
        item["id"] = _stable_id("ms", item, index)
        item["title"] = str(item.get("title") or item.get("description") or "").strip()
        due = _as_date(item.get("dueDate"), field=f"milestones[{index}].dueDate")
        start = _as_date(item.get("startDate"), field=f"milestones[{index}].startDate")
        item["dueDate"] = due.isoformat() if due else None
        item["startDate"] = start.isoformat() if start else None
        item["dependencies"] = [str(value) for value in item.get("dependencies") or []]
        item["paymentConditionIds"] = [
            str(value) for value in item.get("paymentConditionIds") or []
        ]
        item["acceptanceCriterionIds"] = [
            str(value) for value in item.get("acceptanceCriterionIds") or []
        ]
        item.setdefault("duration", None)
        item.setdefault("calendar", None)
        item.setdefault("evidenceRequirements", [])
        item["evidenceRefs"] = _evidence_refs(item)
        milestones.append(item)

    milestone_ids = {item["id"] for item in milestones}
    milestone_aliases = {
        str(alias): item["id"]
        for raw, item in zip(_items(candidates, "milestones"), milestones, strict=True)
        for alias in (raw.get("id"), raw.get("milestoneId"))
        if alias not in (None, "")
    }
    for item in milestones:
        item["dependencies"] = [
            milestone_aliases.get(value, value) for value in item["dependencies"]
        ]
    for item in payment_conditions:
        milestone_id = item.get("milestoneId")
        if milestone_id not in (None, ""):
            item["milestoneId"] = milestone_aliases.get(str(milestone_id), str(milestone_id))
            target = next(
                (value for value in milestones if value["id"] == item["milestoneId"]),
                None,
            )
            if target is not None and item["id"] not in target["paymentConditionIds"]:
                target["paymentConditionIds"].append(item["id"])
    for item in acceptance_criteria:
        subject_id = item.get("subjectId")
        if subject_id not in (None, ""):
            item["subjectId"] = milestone_aliases.get(str(subject_id), str(subject_id))
            target = next(
                (value for value in milestones if value["id"] == item["subjectId"]),
                None,
            )
            if target is not None and item["id"] not in target["acceptanceCriterionIds"]:
                target["acceptanceCriterionIds"].append(item["id"])
    if not acceptance_criteria:
        acceptance_criteria = _derive_acceptance_criteria(milestones)
        for item in acceptance_criteria:
            target = next(
                (value for value in milestones if value["id"] == item["subjectId"]),
                None,
            )
            if target is not None:
                target["acceptanceCriterionIds"].append(item["id"])
    if not service_levels:
        service_levels = _derive_service_levels(obligations)
    if len(obligations) < 10:
        obligations.extend(
            _derive_supplemental_obligations(
                needed=10 - len(obligations),
                service_levels=service_levels,
                milestones=milestones,
                acceptance_criteria=acceptance_criteria,
                payment_conditions=payment_conditions,
            )
        )
    payment_ids = {item["id"] for item in payment_conditions}
    acceptance_ids = {item["id"] for item in acceptance_criteria}
    for item in milestones:
        for dependency in item["dependencies"]:
            if dependency not in milestone_ids:
                conflicts.append(
                    {
                        "code": "UNKNOWN_DEPENDENCY",
                        "targetId": item["id"],
                        "value": dependency,
                    }
                )
        for value in item["paymentConditionIds"]:
            if value not in payment_ids:
                conflicts.append(
                    {
                        "code": "UNKNOWN_PAYMENT_CONDITION",
                        "targetId": item["id"],
                        "value": value,
                    }
                )
        for value in item["acceptanceCriterionIds"]:
            if value not in acceptance_ids:
                conflicts.append(
                    {
                        "code": "UNKNOWN_ACCEPTANCE_CRITERION",
                        "targetId": item["id"],
                        "value": value,
                    }
                )

    cycle = dependency_cycle(milestones)
    if cycle:
        conflicts.append({"code": "DEPENDENCY_CYCLE", "path": cycle})

    plan: dict[str, Any] = {
        "schemaVersion": PLAN_SCHEMA_VERSION,
        "status": "REVIEW_REQUIRED" if conflicts or gaps else "CANDIDATE",
        "timezone": timezone,
        "currency": currency,
        "contract": deepcopy(candidates.get("contract") or {}),
        "obligations": obligations,
        "deliverables": deliverables,
        "milestones": milestones,
        "acceptanceCriteria": acceptance_criteria,
        "serviceLevels": service_levels,
        "paymentConditions": payment_conditions,
        "changes": _normalize_named_items(_items(candidates, "changes"), "chg"),
        "conflicts": conflicts,
        "gaps": gaps,
    }
    plan["planHash"] = canonical_hash(plan)
    return plan


def _normalize_named_items(items: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(items):
        item = deepcopy(raw)
        item["id"] = _stable_id(prefix, item, index)
        item["title"] = str(item.get("title") or item.get("description") or "").strip()
        item["evidenceRefs"] = _evidence_refs(item)
        normalized.append(item)
    return normalized


def dependency_cycle(milestones: Sequence[Mapping[str, Any]]) -> list[str]:
    dependencies = {
        str(item.get("id")): [str(value) for value in item.get("dependencies") or []]
        for item in milestones
    }
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        state[node] = 1
        stack.append(node)
        for dependency in dependencies.get(node, []):
            if dependency not in dependencies:
                continue
            if state.get(dependency) == 1:
                start = stack.index(dependency)
                return [*stack[start:], dependency]
            if state.get(dependency, 0) == 0:
                found = visit(dependency)
                if found:
                    return found
        stack.pop()
        state[node] = 2
        return []

    for node in dependencies:
        if state.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return []


def apply_approved_changes(
    plan: Mapping[str, Any],
    changes: Sequence[Mapping[str, Any]],
    *,
    as_of: date | str,
) -> dict[str, Any]:
    """Apply only approved, effective changes and preserve the original baseline."""
    current = deepcopy(dict(plan))
    original = deepcopy(dict(plan))
    cutoff = _as_date(as_of, field="asOf")
    assert cutoff is not None
    applied: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    differences: list[dict[str, Any]] = []

    for raw in changes:
        change = deepcopy(dict(raw))
        status = str(change.get("status") or "PROPOSED")
        effective = _as_date(change.get("effectiveAt"), field="change.effectiveAt")
        if status != "APPROVED" or effective is None or effective > cutoff:
            risks.append(
                {
                    "changeId": change.get("id"),
                    "code": "UNAPPROVED_OR_NOT_EFFECTIVE",
                    "status": status,
                }
            )
            continue
        for patch in change.get("changedPaths") or []:
            if not isinstance(patch, Mapping):
                continue
            path = str(patch.get("path") or "")
            before = _read_path(current, path)
            after = deepcopy(patch.get("after"))
            _write_path(current, path, after)
            differences.append(
                {
                    "changeId": change.get("id"),
                    "path": path,
                    "before": before,
                    "after": after,
                }
            )
        applied.append(change)

    current["planHash"] = canonical_hash({k: v for k, v in current.items() if k != "planHash"})
    return {
        "originalBaseline": original,
        "currentBaseline": current,
        "appliedChanges": applied,
        "unapprovedChangeRisks": risks,
        "differences": differences,
    }


def _path_parts(path: str) -> list[str]:
    value = path.removeprefix("/")
    parts = [part.replace("~1", "/").replace("~0", "~") for part in value.split("/") if part]
    if not parts:
        raise ValueError("change path is required")
    return parts


def _read_path(value: Mapping[str, Any], path: str) -> Any:
    current: Any = value
    for part in _path_parts(path):
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, Mapping):
            current = current.get(part)
        else:
            return None
    return deepcopy(current)


def _write_path(value: dict[str, Any], path: str, replacement: Any) -> None:
    parts = _path_parts(path)
    current: Any = value
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    last = parts[-1]
    if isinstance(current, list):
        current[int(last)] = replacement
    else:
        current[last] = replacement


def build_schedule(
    plan: Mapping[str, Any],
    *,
    as_of: date | str,
    actuals: Mapping[str, Mapping[str, Any]] | None = None,
    original_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    milestones = _items(plan, "milestones")
    cycle = dependency_cycle(milestones)
    if cycle:
        return {
            "asOf": str(as_of),
            "milestones": [],
            "criticalPath": None,
            "quality": {"status": "REVIEW_REQUIRED", "reasons": ["DEPENDENCY_CYCLE"]},
            "cycle": cycle,
        }
    actual_by_id = actuals or {}
    original_by_id = {
        str(item.get("id")): item for item in _items(original_plan or plan, "milestones")
    }
    rows: list[dict[str, Any]] = []
    for item in milestones:
        milestone_id = str(item["id"])
        actual = actual_by_id.get(milestone_id, {})
        original = original_by_id.get(milestone_id, {})
        rows.append(
            {
                "id": milestone_id,
                "title": item.get("title"),
                "dependencies": list(item.get("dependencies") or []),
                "originalStartDate": original.get("startDate"),
                "originalDueDate": original.get("dueDate"),
                "currentStartDate": item.get("startDate"),
                "currentDueDate": item.get("dueDate"),
                "actualStartDate": actual.get("actualStartDate"),
                "actualFinishDate": actual.get("actualFinishDate"),
                "forecastDate": actual.get("forecastDate"),
                "status": actual.get("status", "NOT_STARTED"),
                "evidenceStatus": actual.get("evidenceStatus", "UNKNOWN"),
            }
        )
    has_complete_network = bool(rows) and all(
        row["currentStartDate"] and row["currentDueDate"] for row in rows
    )
    critical_path = _critical_path(milestones) if has_complete_network else None
    result = {
        "asOf": cutoff_iso(as_of),
        "milestones": rows,
        "criticalPath": critical_path,
        "quality": {
            "status": "COMPLETE" if has_complete_network else "MILESTONE_ONLY",
            "reasons": [] if has_complete_network else ["INSUFFICIENT_DEPENDENCY_OR_DURATION_DATA"],
        },
    }
    result["ganttHash"] = canonical_hash(result)
    return result


def cutoff_iso(value: date | str) -> str:
    parsed = _as_date(value, field="asOf")
    assert parsed is not None
    return parsed.isoformat()


def _critical_path(milestones: Sequence[Mapping[str, Any]]) -> list[str]:
    by_id = {str(item["id"]): item for item in milestones}
    children: dict[str, list[str]] = defaultdict(list)
    indegree = {key: 0 for key in by_id}
    for key, item in by_id.items():
        for dependency in item.get("dependencies") or []:
            dep = str(dependency)
            if dep in by_id:
                children[dep].append(key)
                indegree[key] += 1
    queue = deque(key for key, value in indegree.items() if value == 0)
    distance = {key: 0 for key in by_id}
    previous: dict[str, str] = {}
    while queue:
        node = queue.popleft()
        duration = int(by_id[node].get("duration") or 0)
        for child in children[node]:
            candidate = distance[node] + duration
            if candidate >= distance[child]:
                distance[child] = candidate
                previous[child] = node
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if not distance:
        return []
    end = max(
        distance,
        key=lambda key: distance[key] + int(by_id[key].get("duration") or 0),
    )
    path = [end]
    while end in previous:
        end = previous[end]
        path.append(end)
    return list(reversed(path))


def match_evidence(
    plan: Mapping[str, Any],
    evidence: Sequence[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Validate candidate links using stable contract keys and evidence sequence."""
    targets = {
        str(item["id"]): ("MILESTONE", item)
        for item in _items(plan, "milestones")
        if item.get("id")
    }
    targets.update(
        {
            str(item["id"]): ("OBLIGATION", item)
            for item in _items(plan, "obligations")
            if item.get("id")
        }
    )
    for key, target_type in (
        ("deliverables", "DELIVERABLE"),
        ("acceptanceCriteria", "ACCEPTANCE_CRITERION"),
        ("serviceLevels", "SERVICE_LEVEL"),
        ("paymentConditions", "PAYMENT_CONDITION"),
    ):
        targets.update(
            {
                str(item["id"]): (target_type, item)
                for item in _items(plan, key)
                if item.get("id")
            }
        )
    proposed = defaultdict(list)
    for candidate in candidates:
        proposed[str(candidate.get("evidenceId"))].append(str(candidate.get("targetId")))

    links: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    unmatched: list[str] = []
    for raw in evidence:
        item = dict(raw)
        evidence_id = str(item.get("id") or "")
        evidence_type = str(item.get("type") or "").upper()
        if evidence_type not in _EVIDENCE_TYPES:
            unmatched.append(evidence_id)
            continue
        target_ids = proposed.get(evidence_id, [])
        valid = [target_id for target_id in target_ids if target_id in targets]
        if len(valid) != 1:
            status = "CONFLICT" if len(valid) > 1 else "UNMATCHED"
            links.append(
                {
                    "evidenceId": evidence_id,
                    "targetType": None,
                    "targetId": None,
                    "matchStatus": status,
                    "matchReasons": ["MULTIPLE_CANDIDATES" if len(valid) > 1 else "NO_STABLE_KEY"],
                }
            )
            if status == "CONFLICT":
                conflicts.append({"evidenceId": evidence_id, "candidateTargetIds": valid})
            else:
                unmatched.append(evidence_id)
            continue
        target_id = valid[0]
        target_type, target = targets[target_id]
        reasons = _key_mismatch_reasons(plan, target, item)
        status = "CANDIDATE" if reasons else "MATCHED"
        links.append(
            {
                "evidenceId": evidence_id,
                "targetType": target_type,
                "targetId": target_id,
                "matchStatus": status,
                "matchReasons": reasons or ["STABLE_KEYS_MATCHED"],
                "confirmedBy": None,
            }
        )
    return {"links": links, "conflicts": conflicts, "unmatchedEvidenceIds": unmatched}


def _key_mismatch_reasons(
    plan: Mapping[str, Any], target: Mapping[str, Any], evidence: Mapping[str, Any]
) -> list[str]:
    expected = dict(plan.get("contract") or {})
    expected.update(dict(target.get("contractKeys") or {}))
    actual = dict(evidence.get("contractKeys") or {})
    reasons: list[str] = []
    comparable = (("contractNumber", "CONTRACT_NUMBER"), ("poNumber", "PO_NUMBER"))
    matched_key = False
    for key, label in comparable:
        if expected.get(key) and actual.get(key):
            matched_key = True
            if str(expected[key]).casefold() != str(actual[key]).casefold():
                reasons.append(f"{label}_MISMATCH")
    if not matched_key:
        reasons.append("NO_STABLE_CROSS_KEY")
    return reasons


def calculate_status(
    plan: Mapping[str, Any],
    evidence: Sequence[Mapping[str, Any]],
    links: Sequence[Mapping[str, Any]],
    *,
    as_of: date | str,
    collection_status: str = "COMPLETE",
    approved_exceptions: Iterable[str] = (),
) -> dict[str, Any]:
    if str(plan.get("status")) != "PUBLISHED":
        raise ValueError("only a PUBLISHED plan can be evaluated")
    cutoff = _as_date(as_of, field="asOf")
    assert cutoff is not None
    evidence_by_id = {str(item.get("id")): dict(item) for item in evidence}
    by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unresolved_links = False
    for link in links:
        status = str(link.get("matchStatus") or "UNMATCHED")
        if status == "MATCHED" and link.get("targetId"):
            evidence_item = evidence_by_id.get(str(link.get("evidenceId")))
            if evidence_item:
                by_target[str(link["targetId"])].append(evidence_item)
        elif status in {"CANDIDATE", "CONFLICT", "UNMATCHED"}:
            unresolved_links = True

    exceptions = set(approved_exceptions)
    findings: list[dict[str, Any]] = []
    milestone_results: list[dict[str, Any]] = []
    payment_gate_results: list[dict[str, Any]] = []
    for milestone in _items(plan, "milestones"):
        milestone_id = str(milestone["id"])
        matched = by_target.get(milestone_id, [])
        types = {str(item.get("type") or "").upper() for item in matched}
        required = {str(value).upper() for value in milestone.get("evidenceRequirements") or []}
        due = _as_date(milestone.get("dueDate"), field=f"milestone.{milestone_id}.dueDate")
        rejected = any(str(item.get("result") or "").upper() == "REJECTED" for item in matched)
        conditional = any(
            str(item.get("result") or "").upper() == "CONDITIONALLY_ACCEPTED" for item in matched
        )
        missing = sorted(required - types)
        if rejected:
            status = "REJECTED"
        elif required and not missing:
            status = "CONDITIONALLY_ACCEPTED" if conditional else "ACCEPTED"
        elif due and due < cutoff:
            status = "OVERDUE"
        elif matched:
            status = "EVIDENCE_PENDING" if missing else "SUBMITTED"
        else:
            status = "OVERDUE" if due and due < cutoff else "NOT_STARTED"
        observed_dates = [
            observed
            for item in matched
            if (
                observed := _as_date(
                    item.get("occurredAt")
                    or item.get("effectiveAt")
                    or item.get("date")
                    or item.get("capturedAt"),
                    field=f"evidence.{item.get('id')}.occurredAt",
                )
            )
            is not None
        ]
        completion_dates = [
            observed
            for item in matched
            if str(item.get("type") or "").upper() == "ACCEPTANCE"
            and (
                observed := _as_date(
                    item.get("occurredAt")
                    or item.get("effectiveAt")
                    or item.get("date")
                    or item.get("capturedAt"),
                    field=f"evidence.{item.get('id')}.occurredAt",
                )
            )
            is not None
        ]
        milestone_results.append(
            {
                "milestoneId": milestone_id,
                "status": status,
                "missingEvidenceTypes": missing,
                "evidenceIds": [str(item.get("id")) for item in matched],
                "actualStartDate": min(observed_dates).isoformat() if observed_dates else None,
                "actualFinishDate": (
                    max(completion_dates).isoformat()
                    if completion_dates
                    and status in {"ACCEPTED", "CONDITIONALLY_ACCEPTED", "REJECTED"}
                    else None
                ),
            }
        )
        if status in {"OVERDUE", "REJECTED", "EVIDENCE_PENDING"}:
            findings.append(
                {
                    "code": f"MILESTONE_{status}",
                    "severity": "HIGH" if status in {"OVERDUE", "REJECTED"} else "MEDIUM",
                    "targetId": milestone_id,
                }
            )

        for payment_id in milestone.get("paymentConditionIds") or []:
            payment = next(
                (
                    item
                    for item in _items(plan, "paymentConditions")
                    if str(item.get("id")) == str(payment_id)
                ),
                None,
            )
            if payment is None:
                continue
            has_payment = "PAYMENT" in types
            observed_amount = sum(
                (
                    (
                        _as_decimal(item.get("amount"), field="paymentEvidence.amount")
                        or Decimal("0")
                    )
                    for item in matched
                    if str(item.get("type") or "").upper() == "PAYMENT"
                ),
                start=Decimal("0"),
            )
            acceptance_required = "ACCEPTANCE" in {
                str(value).upper() for value in payment.get("prerequisites") or []
            }
            has_acceptance = "ACCEPTANCE" in types or status in {
                "ACCEPTED",
                "CONDITIONALLY_ACCEPTED",
            }
            exception_key = f"payment:{payment_id}"
            allowed = (not acceptance_required or has_acceptance) and status not in {
                "REJECTED",
                "OVERDUE",
            }
            cumulative_cap = _as_decimal(
                payment.get("cumulativeCap"),
                field=f"paymentCondition.{payment_id}.cumulativeCap",
            )
            cap_exceeded = cumulative_cap is not None and observed_amount > cumulative_cap
            if cap_exceeded:
                allowed = False
            if exception_key in exceptions:
                allowed = True
            gate = "ALLOWED" if allowed else "BLOCKED"
            payment_gate_results.append(
                {
                    "paymentConditionId": str(payment_id),
                    "milestoneId": milestone_id,
                    "gateStatus": gate,
                    "paymentObserved": has_payment,
                    "observedAmount": _money(observed_amount),
                    "cumulativeCap": _money(cumulative_cap),
                    "capExceeded": cap_exceeded,
                    "acceptanceSatisfied": has_acceptance,
                    "exceptionApplied": exception_key in exceptions,
                }
            )
            if has_payment and not allowed:
                findings.append(
                    {
                        "code": "PAYMENT_BEFORE_PREREQUISITES",
                        "severity": "HIGH",
                        "targetId": str(payment_id),
                        "reviewType": "FINANCE",
                    }
                )
                if cap_exceeded:
                    findings.append(
                        {
                            "code": "PAYMENT_CUMULATIVE_CAP_EXCEEDED",
                            "severity": "HIGH",
                            "targetId": str(payment_id),
                            "reviewType": "FINANCE",
                        }
                    )

        payment_dates = sorted(
            value
            for item in matched
            if str(item.get("type") or "").upper() == "PAYMENT"
            if (value := _as_date(item.get("businessDate"), field="evidence.businessDate"))
            is not None
        )
        acceptance_dates = sorted(
            value
            for item in matched
            if str(item.get("type") or "").upper() == "ACCEPTANCE"
            if (value := _as_date(item.get("businessDate"), field="evidence.businessDate"))
            is not None
        )
        if payment_dates and acceptance_dates and payment_dates[0] < acceptance_dates[0]:
            findings.append(
                {
                    "code": "PAYMENT_BEFORE_ACCEPTANCE",
                    "severity": "HIGH",
                    "targetId": milestone_id,
                    "reviewType": "FINANCE",
                }
            )

    service_level_results: list[dict[str, Any]] = []
    for service_level in _items(plan, "serviceLevels"):
        service_level_id = str(service_level["id"])
        matched = by_target.get(service_level_id, [])
        measurements = [
            item.get("value")
            for item in matched
            if str(item.get("type") or "").upper() == "SERVICE"
        ]
        status = "UNKNOWN"
        if measurements:
            actual = _as_decimal(measurements[-1], field="serviceEvidence.value")
            target = _as_decimal(service_level.get("target"), field="serviceLevel.target")
            if actual is not None and target is not None:
                status = (
                    "MET"
                    if _compare_metric(actual, target, str(service_level.get("operator") or ">="))
                    else "BREACHED"
                )
        service_level_results.append(
            {
                "serviceLevelId": service_level_id,
                "status": status,
                "evidenceIds": [str(item.get("id")) for item in matched],
            }
        )
        if status == "BREACHED":
            findings.append(
                {
                    "code": "SERVICE_LEVEL_BREACHED",
                    "severity": "HIGH",
                    "targetId": service_level_id,
                }
            )

    if unresolved_links:
        findings.append(
            {
                "code": "EVIDENCE_MATCH_REVIEW_REQUIRED",
                "severity": "MEDIUM",
                "targetId": None,
            }
        )

    statuses = {item["status"] for item in milestone_results}
    if collection_status == "FAILED" or "REJECTED" in statuses or unresolved_links:
        overall = "REVIEW_REQUIRED"
    elif "OVERDUE" in statuses:
        overall = "OVERDUE"
    elif any(
        item["gateStatus"] == "BLOCKED" and item["paymentObserved"] for item in payment_gate_results
    ):
        overall = "AT_RISK"
    elif "EVIDENCE_PENDING" in statuses:
        overall = "EVIDENCE_PENDING"
    elif collection_status == "PARTIAL":
        overall = "AT_RISK"
    elif milestone_results and statuses <= {"ACCEPTED", "CONDITIONALLY_ACCEPTED", "WAIVED"}:
        overall = "COMPLETED"
    elif findings or collection_status == "PARTIAL":
        overall = "AT_RISK"
    else:
        overall = "ON_TRACK"
    return {
        "asOf": cutoff.isoformat(),
        "status": overall,
        "collectionStatus": collection_status,
        "milestones": milestone_results,
        "paymentGates": payment_gate_results,
        "serviceLevels": service_level_results,
        "findings": findings,
        "reviewRequired": overall == "REVIEW_REQUIRED"
        or any(item.get("reviewType") for item in findings),
        "ruleVersion": RULE_VERSION,
    }


def _compare_metric(actual: Decimal, target: Decimal, operator: str) -> bool:
    operations = {
        ">=": actual >= target,
        ">": actual > target,
        "<=": actual <= target,
        "<": actual < target,
        "==": actual == target,
        "=": actual == target,
    }
    if operator not in operations:
        raise ValueError(f"unsupported metric operator: {operator}")
    return operations[operator]


def finalize_contract_performance(
    *,
    case_id: str,
    plan_version: int,
    plan: Mapping[str, Any],
    performance: Mapping[str, Any],
    gantt: Mapping[str, Any],
    evidence_ledger: Mapping[str, Any],
    change_history: Mapping[str, Any],
    provenance: Mapping[str, Any],
    approvals: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "caseId": case_id,
        "planVersion": plan_version,
        "asOf": performance.get("asOf"),
        "status": performance.get("status"),
        "collectionStatus": performance.get("collectionStatus"),
        "plan": deepcopy(dict(plan)),
        "performance": deepcopy(dict(performance)),
        "gantt": deepcopy(dict(gantt)),
        "evidenceLedger": deepcopy(dict(evidence_ledger)),
        "changeHistory": deepcopy(dict(change_history)),
        "approvals": [deepcopy(dict(item)) for item in approvals],
        "provenance": deepcopy(dict(provenance)),
    }
    result["resultHash"] = canonical_hash(result)
    return result


def build_daily_reminders(
    plan: Mapping[str, Any],
    performance: Mapping[str, Any],
    *,
    as_of: date | str,
    lead_days: int = 7,
) -> list[dict[str, Any]]:
    if lead_days < 0:
        raise ValueError("leadDays must be non-negative")
    cutoff = _as_date(as_of, field="asOf")
    assert cutoff is not None
    statuses = {
        str(item.get("milestoneId")): str(item.get("status"))
        for item in performance.get("milestones") or []
        if isinstance(item, Mapping)
    }
    reminders: list[dict[str, Any]] = []
    terminal = {"ACCEPTED", "CONDITIONALLY_ACCEPTED", "REJECTED", "WAIVED"}
    for milestone in _items(plan, "milestones"):
        milestone_id = str(milestone["id"])
        status = statuses.get(milestone_id, "NOT_STARTED")
        due = _as_date(milestone.get("dueDate"), field=f"milestone.{milestone_id}.dueDate")
        kind: str | None = None
        if status == "OVERDUE":
            kind = "OVERDUE"
        elif status == "EVIDENCE_PENDING":
            kind = "EVIDENCE_PENDING"
        elif due is not None and status not in terminal and 0 <= (due - cutoff).days <= lead_days:
            kind = "DUE_SOON"
        if kind is None:
            continue
        reminders.append(
            {
                "type": f"contract.performance.milestone.{kind.lower()}.v1",
                "milestoneId": milestone_id,
                "title": milestone.get("title"),
                "dueDate": due.isoformat() if due else None,
                "status": status,
                "responsibleParty": milestone.get("responsibleParty"),
                "deduplicationKey": canonical_hash(
                    {
                        "planHash": plan.get("planHash"),
                        "asOf": cutoff.isoformat(),
                        "milestoneId": milestone_id,
                        "kind": kind,
                    }
                ),
            }
        )
    return reminders


def validate_contract_performance_result(result: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(result))
    if value.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("unsupported contract-performance schema")
    if value.get("status") not in {
        "ON_TRACK",
        "AT_RISK",
        "OVERDUE",
        "EVIDENCE_PENDING",
        "REVIEW_REQUIRED",
        "COMPLETED",
    }:
        raise ValueError("invalid contract-performance status")
    expected = value.pop("resultHash", None)
    actual = canonical_hash(value)
    if expected != actual:
        raise ValueError("contract-performance result hash mismatch")
    value["resultHash"] = actual
    return value


def contract_performance_report_lines(result: Mapping[str, Any]) -> list[str]:
    validated = validate_contract_performance_result(result)
    performance = validated.get("performance") or {}
    milestones = performance.get("milestones") or []
    findings = performance.get("findings") or []
    return [
        "合同履约状态报告",
        f"截至日期: {validated.get('asOf') or '-'}",
        f"总体状态: {validated.get('status')}",
        f"计划版本: {validated.get('planVersion')}",
        f"里程碑数量: {len(milestones)}",
        f"风险与缺口: {len(findings)}",
        f"结果哈希: {validated.get('resultHash')}",
    ]


__all__ = [
    "PLAN_SCHEMA_VERSION",
    "RULE_VERSION",
    "SCHEMA_VERSION",
    "apply_approved_changes",
    "build_daily_reminders",
    "build_schedule",
    "calculate_status",
    "contract_performance_report_lines",
    "dependency_cycle",
    "finalize_contract_performance",
    "match_evidence",
    "normalize_plan",
    "validate_contract_performance_result",
]
