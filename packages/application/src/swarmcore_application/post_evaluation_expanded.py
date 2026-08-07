from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from typing import Any

from pydantic import ValidationError
from swarmcore_persistence.repositories import canonical_hash

from .post_evaluation import PostEvaluationPayload

_DOMAIN_KEYWORDS = {
    "contract": (
        "合同",
        "协议",
        "金额",
        "甲方",
        "乙方",
        "期限",
        "交付",
        "标的",
    ),
    "performance": (
        "履约",
        "交付",
        "进度",
        "验收",
        "质量",
        "完成",
        "延期",
        "整改",
    ),
    "finance": (
        "发票",
        "付款",
        "金额",
        "税",
        "成本",
        "结算",
        "含税",
        "票号",
    ),
    "governance": (
        "偏差",
        "风险",
        "变更",
        "整改",
        "关闭",
        "逾期",
        "严重",
        "供应商",
    ),
    "commercial": (
        "发票",
        "合同",
        "订单",
        "采购",
        "收货",
        "验收",
        "供应商",
        "付款",
        "预算",
    ),
    "execution": (
        "发货",
        "到货",
        "签收",
        "验收",
        "付款",
        "服务",
        "会议",
        "变更",
        "dispatch",
        "receipt",
        "acceptance",
        "payment",
        "service",
        "meeting",
        "change",
    ),
    "procurement": (
        "招标",
        "投标",
        "中标",
        "采购",
        "合同",
        "供应商",
    ),
}

_DOMAIN_CATEGORIES = {
    "contract": {"CONTRACT", "PROCUREMENT", "SUPPLEMENTAL_FACTS"},
    "performance": {"PERFORMANCE", "ACCEPTANCE", "SUPPLEMENTAL_FACTS"},
    "finance": {"INVOICE", "PAYMENT", "CONTRACT", "SUPPLEMENTAL_FACTS"},
    "governance": {"DEVIATION", "RISK", "SUPPLIER", "SUPPLEMENTAL_FACTS"},
    "commercial": {
        "INVOICE_ORIGINAL",
        "CONTRACT_ORDER",
        "RECEIPT_ACCEPTANCE",
        "SUPPLIER_MASTER",
        "AP_LEDGER",
        "BUDGET_PAYMENT_POLICY",
    },
    "execution": {
        "DISPATCH_LOGISTICS",
        "RECEIPT_ARRIVAL",
        "DELIVERY_ACCEPTANCE",
        "PAYMENT_EVIDENCE",
        "PROGRESS_SERVICE",
        "MEETING_CORRESPONDENCE",
        "APPROVED_CHANGE",
        "SUPPLEMENTAL_FACTS",
    },
    "procurement": {"TENDER", "BID", "AWARD", "CONTRACT", "SUPPLEMENTAL_FACTS"},
}

_PAYLOAD_ITEM_FIELDS = {
    "documents": {"documentId", "category", "required", "status"},
    "obligations": {"obligationId", "category", "timeliness", "quality"},
    "deviations": {
        "deviationId",
        "category",
        "severity",
        "status",
        "costImpact",
        "delayDays",
    },
    "invoices": {
        "invoiceId",
        "amount",
        "contractMatched",
        "acceptanceMatched",
        "taxValid",
        "duplicate",
    },
    "risks": {"riskId", "category", "level", "status", "actionOverdue"},
}


def normalize_post_evaluation_payload(payload: dict[str, Any]) -> PostEvaluationPayload:
    """Drop model-only annotations before the deterministic scoring boundary."""
    cleaned = deepcopy(payload)
    period = cleaned.get("evaluationPeriod")
    if isinstance(period, dict):
        cleaned["evaluationPeriod"] = {
            key: value for key, value in period.items() if key in {"start", "end"}
        }
    contract = cleaned.get("contract")
    if isinstance(contract, dict):
        cleaned["contract"] = {
            key: value
            for key, value in contract.items()
            if key
            in {
                "contractId",
                "contractName",
                "contractAmount",
                "actualCost",
                "currency",
            }
        }
    for field, allowed in _PAYLOAD_ITEM_FIELDS.items():
        values = cleaned.get(field)
        if isinstance(values, list):
            cleaned[field] = [
                {key: value for key, value in item.items() if key in allowed}
                if isinstance(item, dict)
                else item
                for item in values
            ]
    availability = cleaned.get("evidenceAvailability")
    if isinstance(availability, dict):
        cleaned["evidenceAvailability"] = {
            str(key): value for key, value in availability.items() if isinstance(value, str)
        }
    return PostEvaluationPayload.model_validate(cleaned)


def _content_text(document: dict[str, Any]) -> str:
    data = document.get("data")
    if not isinstance(data, dict):
        return ""
    content = data.get("content")
    if not isinstance(content, dict):
        return ""
    values: list[str] = []
    excerpt = content.get("textExcerpt")
    if isinstance(excerpt, str):
        values.append(excerpt)
    # Filename/media metadata proves identity, not readable business content.
    # Only extracted text or structured table/sheet values qualify here.
    for key in ("tables", "sheets"):
        value = content.get(key)
        if value not in (None, [], {}):
            values.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return "\n".join(values).strip()


def search_evidence(
    documents: list[dict[str, Any]],
    *,
    domain: str,
    keywords: list[str] | None = None,
    max_hits: int = 12,
    contextual: bool = False,
) -> dict[str, Any]:
    normalized_domain = domain.strip().lower()
    if normalized_domain not in _DOMAIN_KEYWORDS:
        raise ValueError(f"unsupported evidence domain: {domain}")
    terms = tuple(
        value.strip()
        for value in (keywords or list(_DOMAIN_KEYWORDS[normalized_domain]))
        if value.strip()
    )
    category_candidates = _DOMAIN_CATEGORIES[normalized_domain]
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    available = 0
    for document in documents:
        segments = (
            _contextual_content_segments(document)
            if contextual
            else [(_content_text(document), {}, [])]
        )
        if any(text for text, _, _ in segments):
            available += 1
        category = str(document.get("category", "")).upper()
        document_version_id = str(document.get("documentVersionId", ""))
        document_evidence = document.get("evidence")
        for segment_no, (text, segment_locator, segment_evidence) in enumerate(segments):
            folded = text.casefold()
            windows = (
                _context_windows(text, terms)
                if contextual
                else [(0, min(len(text), 1_500))]
            )
            for window_no, (start, end) in enumerate(windows):
                excerpt = text[start:end]
                search_text = excerpt.casefold() if contextual else folded
                matches = [term for term in terms if term.casefold() in search_text]
                score = len(matches) * 10 + (
                    20 if category in category_candidates else 0
                )
                if not text:
                    score -= 100
                if score <= 0:
                    continue
                locator = {
                    **segment_locator,
                    "characterStart": start,
                    "characterEnd": end,
                }
                evidence = (
                    _evidence_for_excerpt(segment_evidence, excerpt)
                    or (
                        list(document_evidence)[:5]
                        if isinstance(document_evidence, list)
                        else []
                    )
                )
                evidence_pages = sorted(
                    {
                        int(value["page"])
                        for value in evidence
                        if isinstance(value.get("page"), int)
                    }
                )
                if evidence_pages:
                    locator["pages"] = evidence_pages
                ranked.append(
                    (
                        score,
                        f"{document_version_id}:{segment_no:04d}:{window_no:04d}",
                        {
                            "documentId": str(document.get("documentId", "")),
                            "documentVersionId": document_version_id,
                            "sourceRef": str(document.get("sourceRef", "")),
                            "sourceRecordId": str(document.get("sourceRecordId", "")),
                            "name": str(
                                document.get("name") or document.get("filename") or ""
                            ),
                            "category": category,
                            "score": score,
                            "matchedKeywords": matches,
                            "excerpt": excerpt,
                            "locator": locator,
                            "evidence": evidence,
                        },
                    )
                )
    ranked.sort(key=lambda item: (-item[0], item[1]))
    hits = [item[2] for item in ranked[:max_hits]]
    return {
        "domain": normalized_domain,
        "searchedDocuments": len(documents),
        "contentAvailableDocuments": available,
        "hits": hits,
        "contentHash": canonical_hash(hits),
    }


def _contextual_content_segments(
    document: dict[str, Any],
) -> list[tuple[str, dict[str, Any], list[dict[str, Any]]]]:
    data = document.get("data")
    if not isinstance(data, dict):
        return [("", {}, [])]
    content = data.get("content")
    if not isinstance(content, dict):
        return [("", {}, [])]
    chunks = content.get("chunks")
    if isinstance(chunks, list):
        segments: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = []
        for index, raw_chunk in enumerate(chunks, start=1):
            if not isinstance(raw_chunk, dict):
                continue
            text = str(raw_chunk.get("text") or "").strip()
            if not text:
                continue
            pages = [
                int(value)
                for value in raw_chunk.get("pages") or []
                if isinstance(value, int)
            ]
            if not pages:
                page_start = raw_chunk.get("pageStart")
                page_end = raw_chunk.get("pageEnd")
                if isinstance(page_start, int) and isinstance(page_end, int):
                    pages = list(range(page_start, page_end + 1))
            locator: dict[str, Any] = {
                "chunkOrdinal": int(raw_chunk.get("ordinal") or index),
            }
            if pages:
                locator["pages"] = pages
            evidence = [
                dict(value)
                for value in (
                    raw_chunk.get("evidence")
                    or raw_chunk.get("evidenceRefs")
                    or []
                )
                if isinstance(value, dict)
            ]
            segments.append((text, locator, evidence))
        if segments:
            return segments
    return [(_content_text(document), {}, [])]


def _evidence_for_excerpt(
    evidence: list[dict[str, Any]],
    excerpt: str,
) -> list[dict[str, Any]]:
    if not evidence:
        return []
    excerpt_tokens = set(excerpt.casefold().split())
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(evidence):
        evidence_text = str(item.get("text") or "")
        evidence_tokens = set(evidence_text.casefold().split())
        overlap = len(excerpt_tokens & evidence_tokens)
        if overlap:
            ranked.append((overlap, -index, item))
    ranked.sort(key=lambda value: (-value[0], -value[1]))
    return [dict(value[2]) for value in ranked[:5]]


def _context_windows(
    text: str,
    terms: tuple[str, ...],
    *,
    radius: int = 700,
) -> list[tuple[int, int]]:
    folded = text.casefold()
    ranges: list[tuple[int, int]] = []
    for term in terms:
        needle = term.casefold()
        if not needle:
            continue
        offset = 0
        while (position := folded.find(needle, offset)) >= 0:
            ranges.append(
                (
                    max(0, position - radius),
                    min(len(text), position + len(needle) + radius),
                )
            )
            offset = position + len(needle)
    if not ranges:
        return [(0, min(len(text), 1_500))]
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return [
        (start, min(end, start + 1_500))
        for start, end in merged
    ]


def check_document_coverage(
    documents: list[dict[str, Any]], requirements: list[dict[str, Any]]
) -> dict[str, Any]:
    category_counts = Counter(str(item.get("category", "")).upper() for item in documents)
    sha_counts = Counter(str(item.get("sha256", "")) for item in documents)
    duplicates = sorted(value for value, count in sha_counts.items() if value and count > 1)
    unreadable = [
        str(item.get("documentVersionId", ""))
        for item in documents
        if not _content_text(item)
    ]
    entries: list[dict[str, Any]] = []
    for requirement in requirements:
        category = str(requirement["category"]).upper()
        minimum = int(requirement.get("minCount", 1 if requirement.get("required", True) else 0))
        maximum = requirement.get("maxCount")
        count = category_counts[category]
        satisfied = count >= minimum and (maximum is None or count <= int(maximum))
        entries.append(
            {
                "key": str(requirement.get("key", category)),
                "category": category,
                "required": bool(requirement.get("required", True)),
                "minCount": minimum,
                "maxCount": maximum,
                "actualCount": count,
                "satisfied": satisfied,
            }
        )
    missing_required = [
        item["key"] for item in entries if item["required"] and not item["satisfied"]
    ]
    warnings = [
        f"{len(unreadable)} document(s) have no readable processed content"
        if unreadable
        else "",
        f"{len(duplicates)} duplicate content hash(es) selected" if duplicates else "",
    ]
    return {
        "complete": not missing_required,
        "reviewRequired": bool(missing_required or unreadable or duplicates),
        "documentCount": len(documents),
        "contentAvailableCount": len(documents) - len(unreadable),
        "requirements": entries,
        "missingRequired": missing_required,
        "unreadableDocumentVersionIds": unreadable,
        "duplicateSha256": duplicates,
        "warnings": [value for value in warnings if value],
    }


def merge_domain_analyses(
    base_payload: dict[str, Any],
    analyses: dict[str, dict[str, Any]],
    upstream_evaluations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload = deepcopy(base_payload)
    PostEvaluationPayload.model_validate(payload)
    facts: list[dict[str, Any]] = []
    conflicts: list[str] = []
    missing_evidence: list[str] = []
    source_agents: list[str] = []
    for key in sorted(analyses):
        analysis = analyses[key]
        if not isinstance(analysis, dict):
            raise ValueError(f"domain analysis {key!r} must be an object")
        source_agents.append(key)
        patch = analysis.get("payloadPatch", {})
        if not isinstance(patch, dict):
            raise ValueError(f"domain analysis {key!r} payloadPatch must be an object")
        for field in (
            "title",
            "evaluationPeriod",
            "contract",
            "documents",
            "obligations",
            "deviations",
            "invoices",
            "risks",
            "evidenceAvailability",
        ):
            value = patch.get(field)
            if value not in (None, [], {}):
                expected_type = (
                    str
                    if field == "title"
                    else list
                    if field
                    in {
                        "documents",
                        "obligations",
                        "deviations",
                        "invoices",
                        "risks",
                    }
                    else dict
                )
                if not isinstance(value, expected_type):
                    conflicts.append(
                        f"{key} returned invalid {field} patch; retained base payload"
                    )
                    continue
                candidate = deepcopy(payload)
                if field in {"contract", "evidenceAvailability"} and isinstance(value, dict):
                    existing = candidate.get(field)
                    merged = dict(existing) if isinstance(existing, dict) else {}
                    merged.update(deepcopy(value))
                    candidate[field] = merged
                else:
                    candidate[field] = deepcopy(value)
                try:
                    PostEvaluationPayload.model_validate(candidate)
                except ValidationError:
                    conflicts.append(
                        f"{key} returned invalid {field} values; retained base payload"
                    )
                    continue
                payload = candidate
        analysis_facts = analysis.get("facts", [])
        if isinstance(analysis_facts, list):
            facts.extend(dict(value) for value in analysis_facts if isinstance(value, dict))
        analysis_conflicts = analysis.get("conflicts", [])
        if isinstance(analysis_conflicts, list):
            conflicts.extend(str(value) for value in analysis_conflicts if str(value))
        analysis_missing = analysis.get("missingEvidence", [])
        if isinstance(analysis_missing, list):
            missing_evidence.extend(str(value) for value in analysis_missing if str(value))
    upstream_refs: list[dict[str, str]] = []
    for upstream in upstream_evaluations or []:
        result = upstream.get("result")
        if not isinstance(result, dict):
            continue
        projected = _project_upstream_evaluation(result)
        candidate = deepcopy(payload)
        reused_fields: list[str] = []
        for field in ("obligations", "deviations", "invoices", "risks"):
            value = projected.get(field)
            if not isinstance(value, list) or not value:
                continue
            candidate[field] = deepcopy(value)
            try:
                PostEvaluationPayload.model_validate(candidate)
            except ValidationError:
                candidate[field] = payload.get(field, [])
                conflicts.append(
                    f"upstream evaluation {upstream.get('evaluationId')} returned invalid {field}"
                )
                continue
            payload = deepcopy(candidate)
            reused_fields.append(field)
        upstream_refs.append(
            {
                "evaluationId": str(upstream.get("evaluationId", "")),
                "businessWorkKey": str(upstream.get("businessWorkKey", "")),
                "outputSchemaVersion": str(upstream.get("outputSchemaVersion", "")),
                "resultHash": str(upstream.get("resultHash", "")),
                "reusedFields": ",".join(reused_fields),
            }
        )
    return {
        "payload": payload,
        "evidenceFacts": facts,
        "conflicts": sorted(set(conflicts)),
        "missingEvidence": sorted(set(missing_evidence)),
        "sourceAgents": source_agents,
        "upstreamEvaluationRefs": upstream_refs,
    }


def _project_upstream_evaluation(result: dict[str, Any]) -> dict[str, Any]:
    nested = result.get("payload")
    if isinstance(nested, dict):
        return nested
    schema_version = str(result.get("schemaVersion") or "")
    if schema_version == "schema://contract-performance/result@1":
        return {"obligations": _performance_obligations(result)}
    if schema_version == "schema://invoice-assurance/result@1":
        invoice = _invoice_fact(result)
        return {"invoices": [invoice] if invoice else []}
    if schema_version in {
        "schema://deviation-analysis/result@1",
        "schema://deviation-analysis/result@2",
    }:
        return {"deviations": _deviation_facts(result)}
    if schema_version == "schema://procurement-supplier-risk/result@1":
        return {"risks": [_supplier_risk_fact(result)]}
    return result


def _performance_obligations(result: dict[str, Any]) -> list[dict[str, Any]]:
    plan = result.get("plan") if isinstance(result.get("plan"), dict) else {}
    performance = (
        result.get("performance") if isinstance(result.get("performance"), dict) else {}
    )
    actual_by_id = {
        str(value.get("milestoneId") or ""): value
        for value in performance.get("milestones", [])
        if isinstance(value, dict)
    }
    obligations: list[dict[str, Any]] = []
    for value in plan.get("milestones", []):
        if not isinstance(value, dict) or not value.get("id"):
            continue
        actual = actual_by_id.get(str(value["id"]), {})
        status = str(actual.get("status") or "NOT_STARTED")
        timeliness = (
            "OVERDUE"
            if status == "OVERDUE"
            else "LATE"
            if status in {"REJECTED", "EVIDENCE_PENDING"}
            else "ON_TIME"
            if status in {"ACCEPTED", "CONDITIONALLY_ACCEPTED"}
            else "NOT_DUE"
        )
        quality = {
            "ACCEPTED": "ACCEPTED",
            "CONDITIONALLY_ACCEPTED": "CONDITIONALLY_ACCEPTED",
            "REJECTED": "REJECTED",
        }.get(status, "PENDING" if status != "NOT_STARTED" else "NOT_ASSESSED")
        obligations.append(
            {
                "obligationId": str(value["id"]),
                "category": str(value.get("title") or "合同里程碑"),
                "timeliness": timeliness,
                "quality": quality,
            }
        )
    return obligations


def _invoice_fact(result: dict[str, Any]) -> dict[str, Any] | None:
    fact_set = (
        result.get("invoiceFactSet")
        if isinstance(result.get("invoiceFactSet"), dict)
        else {}
    )
    totals = fact_set.get("totals") if isinstance(fact_set.get("totals"), dict) else {}
    amount = totals.get("amountIncludingTax") or fact_set.get("amountIncludingTax")
    try:
        normalized_amount = float(amount)
    except (TypeError, ValueError):
        return None
    if normalized_amount <= 0:
        return None
    outcome = str(result.get("outcome") or "")
    verification = result.get("verification") if isinstance(result.get("verification"), dict) else {}
    duplication = result.get("duplication") if isinstance(result.get("duplication"), dict) else {}
    return {
        "invoiceId": str(fact_set.get("invoiceNumber") or result.get("resultHash") or "invoice"),
        "amount": normalized_amount,
        "contractMatched": outcome == "PAYMENT_READY",
        "acceptanceMatched": outcome == "PAYMENT_READY",
        "taxValid": str(verification.get("status") or "") == "MATCHED",
        "duplicate": bool(duplication.get("duplicate") or duplication.get("duplicates")),
    }


def _deviation_facts(result: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for index, finding in enumerate(result.get("findings", []), start=1):
        if not isinstance(finding, dict):
            continue
        status = str(finding.get("status") or "")
        facts.append(
            {
                "deviationId": str(finding.get("code") or f"deviation-{index}"),
                "category": str(finding.get("dimension") or "偏差"),
                "severity": "HIGH" if finding.get("material") else "MEDIUM",
                "status": "CLOSED" if status in {"CLOSED", "RESOLVED"} else "OPEN",
                "costImpact": 0,
                "delayDays": 0,
            }
        )
    return facts


def _supplier_risk_fact(result: dict[str, Any]) -> dict[str, Any]:
    risk_level = str(result.get("riskLevel") or "MEDIUM")
    level = risk_level if risk_level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM"
    supplier = result.get("supplier") if isinstance(result.get("supplier"), dict) else {}
    decision = str(result.get("decision") or "")
    return {
        "riskId": str(result.get("assessmentId") or result.get("resultHash") or "supplier-risk"),
        "category": f"供应商风险：{supplier.get('name') or supplier.get('supplierName') or '未命名'}",
        "level": level,
        "status": "CLOSED" if decision == "PASS" else "OPEN",
        "actionOverdue": decision in {"BLOCK", "REVIEW_REQUIRED"},
    }


def calculate_timeline(payload: dict[str, Any]) -> dict[str, Any]:
    obligations = list(payload.get("obligations") or [])
    counts = Counter(str(item.get("timeliness", "UNKNOWN")) for item in obligations)
    due = sum(counts[key] for key in ("ON_TIME", "LATE", "OVERDUE"))
    weighted_complete = counts["ON_TIME"] + counts["LATE"] * 0.5
    return {
        "obligationCount": len(obligations),
        "dueCount": due,
        "onTime": counts["ON_TIME"],
        "late": counts["LATE"],
        "overdue": counts["OVERDUE"],
        "notDue": counts["NOT_DUE"],
        "timelinessRate": round(weighted_complete / due * 100, 2) if due else None,
    }


def reconcile_amounts(payload: dict[str, Any]) -> dict[str, Any]:
    contract = dict(payload.get("contract") or {})
    contract_amount = float(contract.get("contractAmount") or 0)
    actual_raw = contract.get("actualCost")
    actual_cost = float(actual_raw) if actual_raw is not None else None
    invoice_total = round(
        sum(float(item.get("amount") or 0) for item in payload.get("invoices") or []), 2
    )
    overrun = (
        round(max(0.0, actual_cost - contract_amount), 2)
        if actual_cost is not None
        else None
    )
    return {
        "contractAmount": contract_amount,
        "actualCost": actual_cost,
        "invoiceTotal": invoice_total,
        "overrunAmount": overrun,
        "invoiceToContractRate": (
            round(invoice_total / contract_amount * 100, 2) if contract_amount else None
        ),
        "balanced": (
            abs(invoice_total - actual_cost) <= 0.01 if actual_cost is not None else None
        ),
    }


def assure_invoices(payload: dict[str, Any]) -> dict[str, Any]:
    invoices = list(payload.get("invoices") or [])
    exception_ids: list[str] = []
    total = 0.0
    compliant = 0.0
    seen: set[str] = set()
    duplicate_ids: list[str] = []
    for invoice in invoices:
        invoice_id = str(invoice.get("invoiceId", ""))
        amount = float(invoice.get("amount") or 0)
        total += amount
        if invoice_id in seen or bool(invoice.get("duplicate")):
            duplicate_ids.append(invoice_id)
        seen.add(invoice_id)
        valid = (
            bool(invoice.get("contractMatched"))
            and bool(invoice.get("acceptanceMatched"))
            and bool(invoice.get("taxValid"))
            and not bool(invoice.get("duplicate"))
            and invoice_id not in duplicate_ids
        )
        if valid:
            compliant += amount
        else:
            exception_ids.append(invoice_id)
    return {
        "invoiceCount": len(invoices),
        "totalAmount": round(total, 2),
        "compliantAmount": round(compliant, 2),
        "complianceRate": round(compliant / total * 100, 2) if total else 100.0,
        "exceptionInvoiceIds": sorted(set(exception_ids)),
        "duplicateInvoiceIds": sorted(set(duplicate_ids)),
    }


def aggregate_deviations(payload: dict[str, Any]) -> dict[str, Any]:
    values = list(payload.get("deviations") or [])
    closed = sum(str(item.get("status")) == "CLOSED" for item in values)
    open_high = sum(
        str(item.get("status")) != "CLOSED"
        and str(item.get("severity")) in {"HIGH", "CRITICAL"}
        for item in values
    )
    return {
        "count": len(values),
        "closed": closed,
        "open": len(values) - closed,
        "openHigh": open_high,
        "closureRate": round(closed / len(values) * 100, 2) if values else 100.0,
        "totalDelayDays": sum(int(item.get("delayDays") or 0) for item in values),
        "totalCostImpact": round(
            sum(float(item.get("costImpact") or 0) for item in values), 2
        ),
    }


def aggregate_risks(payload: dict[str, Any]) -> dict[str, Any]:
    values = list(payload.get("risks") or [])
    closed = sum(str(item.get("status")) == "CLOSED" for item in values)
    overdue = sum(bool(item.get("actionOverdue")) for item in values)
    high_open = sum(
        str(item.get("status")) != "CLOSED"
        and str(item.get("level")) in {"HIGH", "CRITICAL"}
        for item in values
    )
    return {
        "count": len(values),
        "closed": closed,
        "open": len(values) - closed,
        "highOpen": high_open,
        "overdueActions": overdue,
        "closureRate": round(closed / len(values) * 100, 2) if values else 100.0,
    }


def check_evidence_consistency(
    payload: dict[str, Any],
    evidence_facts: list[dict[str, Any]],
    declared_conflicts: list[str],
) -> dict[str, Any]:
    conflicts = list(declared_conflicts)
    warnings: list[str] = []
    ids_by_collection: dict[str, list[str]] = {}
    for collection, identifier in (
        ("documents", "documentId"),
        ("obligations", "obligationId"),
        ("deviations", "deviationId"),
        ("invoices", "invoiceId"),
        ("risks", "riskId"),
    ):
        values = [
            str(item.get(identifier, ""))
            for item in payload.get(collection) or []
            if isinstance(item, dict)
        ]
        duplicates = sorted(
            value for value, count in Counter(values).items() if value and count > 1
        )
        ids_by_collection[collection] = duplicates
        conflicts.extend(f"duplicate {collection} identifier: {value}" for value in duplicates)
    unsupported = [
        str(item.get("factId", ""))
        for item in evidence_facts
        if not item.get("evidenceRefs")
    ]
    low_confidence = [
        str(item.get("factId", ""))
        for item in evidence_facts
        if float(item.get("confidence", 0)) < 0.7
    ]
    if unsupported:
        warnings.append(f"{len(unsupported)} extracted fact(s) have no evidence reference")
    if low_confidence:
        warnings.append(f"{len(low_confidence)} extracted fact(s) are below confidence 0.70")
    normalized_conflicts = sorted(set(value for value in conflicts if value))
    return {
        "reviewRequired": bool(normalized_conflicts or low_confidence),
        "conflicts": normalized_conflicts,
        "warnings": warnings,
        "unsupportedFactIds": unsupported,
        "lowConfidenceFactIds": low_confidence,
        "duplicateIds": ids_by_collection,
        "checkedFactCount": len(evidence_facts),
    }


def finalize_expanded_result(
    *,
    score: dict[str, Any],
    review: dict[str, Any],
    narrative: dict[str, Any],
    coverage: dict[str, Any],
    consistency: dict[str, Any],
    diagnostics: dict[str, Any],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    result = deepcopy(score)
    result["schemaVersion"] = "schema://contract/post-evaluation-result@2"
    review_required = bool(
        result.get("reviewRequired")
        or coverage.get("reviewRequired")
        or consistency.get("reviewRequired")
        or review.get("reviewRequired")
    )
    result["reviewRequired"] = review_required
    result["passed"] = bool(result.get("passed")) and not review_required
    executive_summary = narrative.get("executiveSummary")
    if isinstance(executive_summary, str) and executive_summary.strip():
        result["executiveSummary"] = executive_summary.strip()
    result["evidenceSummary"] = {
        "documentCount": int(coverage.get("documentCount", 0)),
        "contentAvailableCount": int(coverage.get("contentAvailableCount", 0)),
        "coverageComplete": bool(coverage.get("complete")),
        "missingRequired": list(coverage.get("missingRequired") or []),
        "unreadableDocumentVersionIds": list(
            coverage.get("unreadableDocumentVersionIds") or []
        ),
        "conflicts": list(consistency.get("conflicts") or []),
        "warnings": [
            *list(coverage.get("warnings") or []),
            *list(consistency.get("warnings") or []),
        ],
    }
    result["review"] = {
        "required": review_required,
        "reasons": list(review.get("reasons") or []),
        "acceptedFactIds": list(review.get("acceptedFactIds") or []),
        "rejectedFactIds": list(review.get("rejectedFactIds") or []),
    }
    result["narrative"] = {
        "dimensionNarratives": dict(narrative.get("dimensionNarratives") or {}),
        "recommendations": list(narrative.get("recommendations") or []),
        "managementConclusions": list(narrative.get("managementConclusions") or []),
        "limitations": list(narrative.get("limitations") or []),
    }
    result["diagnostics"] = deepcopy(diagnostics)
    result["provenance"] = deepcopy(provenance)
    return result


def validate_expanded_result(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "evaluationPeriod",
        "contractId",
        "overallScore",
        "grade",
        "riskLevel",
        "passed",
        "reviewRequired",
        "executiveSummary",
        "dimensions",
        "findings",
        "evidenceSummary",
        "review",
        "narrative",
        "diagnostics",
        "provenance",
    }
    if value.get("schemaVersion") != "schema://contract/post-evaluation-result@2":
        raise ValueError("expanded post-evaluation result has an unsupported schemaVersion")
    missing = sorted(required - set(value))
    if missing:
        raise ValueError(f"expanded post-evaluation result is missing: {', '.join(missing)}")
    if len(value.get("dimensions") or []) != 7:
        raise ValueError("expanded post-evaluation result must contain seven dimensions")
    return deepcopy(value)
