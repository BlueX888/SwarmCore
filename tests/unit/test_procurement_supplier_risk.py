from __future__ import annotations

from swarmcore_application.procurement_supplier_risk import (
    calculate_supplier_performance,
    collect_risk_observations,
    compare_procurement_clauses,
    decide_supplier_risk,
    diff_supplier_risk_snapshots,
    finalize_procurement_supplier_risk,
    validate_procurement_supplier_risk_result,
)


def _evidence(role: str, page: int) -> list[dict[str, object]]:
    return [{"documentRole": role, "page": page, "blockId": f"{role}-{page}"}]


def test_four_way_clause_compare_is_deterministic_and_blocks_material_change() -> None:
    result = compare_procurement_clauses(
        {
            "clauses": {
                "TENDER": [
                    {
                        "matchKey": "price",
                        "category": "PRICE",
                        "normalizedValue": 1000000,
                        "text": "最高限价100万元",
                        "evidenceRefs": _evidence("TENDER", 3),
                    }
                ],
                "BID": [
                    {
                        "matchKey": "price",
                        "category": "PRICE",
                        "normalizedValue": 980000,
                        "text": "投标报价98万元",
                        "evidenceRefs": _evidence("BID", 12),
                    }
                ],
                "AWARD": [
                    {
                        "matchKey": "price",
                        "category": "PRICE",
                        "normalizedValue": 980000,
                        "text": "中标金额98万元",
                        "evidenceRefs": _evidence("AWARD", 1),
                    }
                ],
                "CONTRACT": [
                    {
                        "matchKey": "price",
                        "category": "PRICE",
                        "normalizedValue": 1050000,
                        "text": "合同总价105万元",
                        "evidenceRefs": _evidence("CONTRACT", 4),
                    }
                ],
            }
        }
    )
    assert result["blocking"] is True
    assert result["counts"]["BLOCKER"] == 1
    assert result["findings"][0]["changeType"] == "CHANGED"
    assert len(result["findings"][0]["evidenceRefs"]) == 4
    assert compare_procurement_clauses(
        {
            "clauses": {
                role: [
                    {
                        "matchKey": "price",
                        "category": "PRICE",
                        "normalizedValue": value,
                    }
                ]
                for role, value in {
                    "TENDER": 1000000,
                    "BID": 980000,
                    "AWARD": 980000,
                    "CONTRACT": 1050000,
                }.items()
            }
        }
    )["findings"][0]["findingId"] == result["findings"][0]["findingId"]


def test_exact_active_blacklist_is_a_hard_gate_and_name_only_is_not() -> None:
    collection = collect_risk_observations(
        {
            "supplier": {"name": "真实供应商", "creditCode": "91310000TEST000001"},
            "sources": [
                {
                    "sourceRef": "ccgp",
                    "status": "SUCCEEDED",
                    "fetchedAt": "2026-07-28T08:00:00Z",
                    "records": [
                        {
                            "sourceRecordId": "ccgp-1",
                            "creditCode": "91310000TEST000001",
                            "riskType": "GOVERNMENT_PROCUREMENT_BAN",
                            "effectiveFrom": "2026-01-01",
                            "effectiveTo": "2026-12-31",
                        },
                        {
                            "sourceRecordId": "court-name-only",
                            "riskType": "LOST_CREDIT_EXECUTION",
                        },
                    ],
                }
            ],
        }
    )
    decision = decide_supplier_risk(
        {
            "asOf": "2026-07-28",
            "riskCollection": collection,
            "performance": {"score": 100, "coverage": 100},
        }
    )
    assert decision["decision"] == "BLOCK"
    assert decision["riskLevel"] == "D"
    assert decision["hardGates"][0]["code"] == "GOVERNMENT_PROCUREMENT_BAN"
    assert decision["overallRiskScore"] > 0

    name_only = {
        **collection,
        "observations": [
            {
                **collection["observations"][0],
                "identityMatch": "NAME_ONLY",
            }
        ],
    }
    assert decide_supplier_risk(
        {"asOf": "2026-07-28", "riskCollection": name_only, "performance": {}}
    )["hardGates"] == []


def test_performance_uses_available_denominators_and_reports_coverage() -> None:
    value = calculate_supplier_performance(
        {
            "periodStart": "2026-01-01",
            "periodEnd": "2026-06-30",
            "records": [
                {
                    "orderId": "PO-1",
                    "plannedDeliveryAt": "2026-01-10",
                    "actualDeliveryAt": "2026-01-09",
                    "qualityPassedQty": 90,
                    "qualityInspectedQty": 100,
                    "acceptanceSlaMet": True,
                    "serviceSlaMet": True,
                    "commercialCompliant": True,
                    "complaints": 1,
                    "resolvedComplaints": 1,
                    "rectificationOnTime": True,
                },
                {
                    "orderId": "PO-2",
                    "plannedDeliveryAt": "2026-02-10",
                    "actualDeliveryAt": "2026-02-12",
                    "qualityPassedQty": 100,
                    "qualityInspectedQty": 100,
                    "acceptanceSlaMet": True,
                    "serviceSlaMet": False,
                    "commercialCompliant": True,
                    "complaints": 0,
                    "resolvedComplaints": 0,
                    "rectificationOnTime": True,
                },
                {
                    "orderId": "PO-3",
                    "plannedDeliveryAt": "2026-03-10",
                    "actualDeliveryAt": "2026-03-10",
                    "qualityPassedQty": 100,
                    "qualityInspectedQty": 100,
                    "acceptanceSlaMet": True,
                    "serviceSlaMet": True,
                    "commercialCompliant": False,
                    "rectificationOnTime": False,
                },
            ],
        }
    )
    assert value["status"] == "SCORED"
    assert value["coverage"] == 100
    assert 0 < value["score"] < 100
    assert value["sampleSize"] == 3


def test_missing_performance_does_not_reduce_external_risk() -> None:
    decision = decide_supplier_risk(
        {
            "asOf": "2026-07-28",
            "riskCollection": {
                "supplier": {"creditCode": "91310000TEST000001"},
                "collectionStatus": "COMPLETE",
                "coverage": 1,
                "sourceStatuses": [],
                "observations": [
                    {
                        "riskType": "BUSINESS_ABNORMAL",
                        "identityMatch": "EXACT_CREDIT_CODE",
                        "active": True,
                    }
                ],
            },
            "performance": {"status": "INSUFFICIENT_DATA", "coverage": 25},
        }
    )
    assert decision["scoringMode"] == "EXTERNAL_ONLY"
    assert decision["overallRiskScore"] == decision["externalRiskScore"]


def test_history_diff_and_final_result_are_hash_verified() -> None:
    previous = {
        "snapshotHash": "previous",
        "riskLevel": "A",
        "decision": "PASS",
        "observations": [],
    }
    current = {
        "riskLevel": "D",
        "decision": "BLOCK",
        "observations": [
            {
                "sourceRef": "ccgp",
                "sourceRecordId": "ccgp-1",
                "riskType": "GOVERNMENT_PROCUREMENT_BAN",
            }
        ],
    }
    history = diff_supplier_risk_snapshots(previous, current)
    assert history["hasMaterialChange"] is True
    assert len(history["added"]) == 1

    result = finalize_procurement_supplier_risk(
        {
            "caseId": "case-1",
            "assessmentId": "assessment-1",
            "asOf": "2026-07-28",
            "consistency": {"blocking": False, "reviewRequired": False},
            "risk": {
                **current,
                "supplier": {"creditCode": "91310000TEST000001"},
                "asOf": "2026-07-28",
            },
            "performance": {"status": "INSUFFICIENT_DATA"},
            "history": history,
        }
    )
    assert result["decision"] == "BLOCK"
    assert validate_procurement_supplier_risk_result(result) == result
