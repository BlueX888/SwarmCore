from __future__ import annotations

import pytest
from swarmcore_application.procurement_supplier_risk import (
    collect_risk_observations_v2,
    compare_procurement_clauses_v2,
    decide_supplier_risk_v2,
    finalize_procurement_supplier_risk_v2,
    normalize_registered_risk_sources,
    resolve_procurement_baseline,
    validate_clause_evidence_analyst_output,
    validate_procurement_supplier_risk_result,
)


def _ev(role: str) -> list[dict[str, object]]:
    return [
        {
            "documentId": f"doc-{role}",
            "documentVersionId": f"ver-{role}",
            "category": role,
            "text": "证据",
        }
    ]


def test_clause_analyst_output_rejects_severity() -> None:
    with pytest.raises(ValueError, match="severity"):
        validate_clause_evidence_analyst_output(
            {
                "clauseFacts": [
                    {
                        "clauseId": "c1",
                        "matchKey": "PAYMENT:0",
                        "category": "PAYMENT",
                        "documentRole": "CONTRACT",
                        "text": "验收后60日付款",
                        "evidenceRefs": _ev("CONTRACT"),
                    }
                ],
                "mappingCandidates": [
                    {
                        "matchKey": "PAYMENT:0",
                        "category": "PAYMENT",
                        "proposedRelation": "WEAKENED",
                        "severity": "HIGH",
                        "confidence": 0.9,
                        "rationale": "付款周期延长",
                        "evidenceRefs": _ev("CONTRACT"),
                    }
                ],
                "ambiguities": [],
            }
        )


def test_clause_analyst_output_normalizes_facts() -> None:
    result = validate_clause_evidence_analyst_output(
        {
            "clauseFacts": [
                {
                    "clauseId": "c1",
                    "matchKey": "PRICE:0",
                    "category": "PRICE",
                    "documentRole": "TENDER",
                    "text": "最高限价100万",
                    "normalizedValue": 1000000,
                    "evidenceRefs": _ev("TENDER"),
                },
                {
                    "clauseId": "c2",
                    "matchKey": "PRICE:0",
                    "category": "PRICE",
                    "documentRole": "CONTRACT",
                    "text": "合同价98万",
                    "normalizedValue": 980000,
                    "evidenceRefs": _ev("CONTRACT"),
                },
            ],
            "mappingCandidates": [
                {
                    "matchKey": "PRICE:0",
                    "category": "PRICE",
                    "proposedRelation": "CHANGED",
                    "confidence": 0.8,
                    "rationale": "金额不同",
                    "evidenceRefs": _ev("CONTRACT"),
                }
            ],
            "ambiguities": [],
        }
    )
    assert result["valid"] is True
    assert set(result["clauses"]) == {"TENDER", "CONTRACT"}
    assert "severity" not in result["mappingCandidates"][0]


def test_baseline_prefers_clarification_over_tender() -> None:
    baseline = resolve_procurement_baseline(
        {
            "clauses": {
                "TENDER": [
                    {
                        "matchKey": "PAYMENT:0",
                        "category": "PAYMENT",
                        "normalizedValue": "30天",
                        "text": "验收后30日付款",
                        "evidenceRefs": _ev("TENDER"),
                    }
                ],
                "CLARIFICATION": [
                    {
                        "matchKey": "PAYMENT:0",
                        "category": "PAYMENT",
                        "normalizedValue": "45天",
                        "text": "澄清后验收后45日付款",
                        "evidenceRefs": _ev("CLARIFICATION"),
                    }
                ],
            }
        }
    )
    assert baseline["baselineClauses"][0]["sourceRole"] == "CLARIFICATION"
    assert baseline["baselineClauses"][0]["normalizedValue"] == "45天"
    assert baseline["baselineClauses"][0]["clarificationApplied"] is True


def test_consistency_v2_price_reduction_is_not_automatic_blocker() -> None:
    result = compare_procurement_clauses_v2(
        {
            "clauses": {
                "AWARD": [
                    {
                        "matchKey": "PRICE:0",
                        "category": "PRICE",
                        "normalizedValue": 980000,
                        "text": "中标98万",
                        "evidenceRefs": _ev("AWARD"),
                    }
                ],
                "CONTRACT": [
                    {
                        "matchKey": "PRICE:0",
                        "category": "PRICE",
                        "normalizedValue": 950000,
                        "text": "合同95万",
                        "evidenceRefs": _ev("CONTRACT"),
                    }
                ],
            }
        }
    )
    assert result["findings"][0]["severity"] == "HIGH"
    assert result["blocking"] is False


def test_risk_sources_reject_client_records_and_endpoints() -> None:
    with pytest.raises(ValueError, match="raw risk records"):
        normalize_registered_risk_sources(
            {"sources": [{"providerConfigId": "builtin:CCGP_SERIOUS_ILLEGAL", "records": []}]}
        )
    with pytest.raises(ValueError, match="endpoints"):
        normalize_registered_risk_sources(
            {
                "sources": [
                    {
                        "providerConfigId": "builtin:CCGP_SERIOUS_ILLEGAL",
                        "endpoint": "https://evil.example/risk",
                    }
                ]
            }
        )


def test_required_source_matrix_prevents_complete_on_partial_config() -> None:
    collection = collect_risk_observations_v2(
        {
            "supplier": {"name": "测试", "creditCode": "91310000TEST000001"},
            "asOf": "2026-07-28",
            "sources": [{"providerConfigId": "builtin:INTERNAL_BLACKLIST"}],
            "requiredProviderConfigIds": [
                "builtin:CCGP_SERIOUS_ILLEGAL",
                "builtin:INTERNAL_BLACKLIST",
            ],
            "resolvedSources": [
                {
                    "providerConfigId": "builtin:INTERNAL_BLACKLIST",
                    "sourceRef": "internal://supplier-blacklist",
                    "status": "SUCCEEDED",
                    "records": [],
                }
            ],
        }
    )
    assert collection["collectionStatus"] != "COMPLETE"


def test_eligibility_split_and_request_evidence_holds() -> None:
    risk = decide_supplier_risk_v2(
        {
            "asOf": "2026-07-28",
            "riskCollection": {
                "supplier": {"creditCode": "91310000TEST000001"},
                "collectionStatus": "COMPLETE",
                "coverage": 1,
                "sourceStatuses": [],
                "observations": [
                    {
                        "riskType": "GOVERNMENT_PROCUREMENT_BAN",
                        "identityMatch": "EXACT_CREDIT_CODE",
                        "active": True,
                        "sourceRef": "ccgp",
                        "sourceRecordId": "1",
                    }
                ],
            },
            "performance": {"status": "SCORED", "score": 90, "coverage": 100},
        }
    )
    assert risk["eligibilityDecision"] == "INELIGIBLE"
    assert risk["riskTier"] == "D"

    held = finalize_procurement_supplier_risk_v2(
        {
            "caseId": "case-1",
            "assessmentId": "assessment-1",
            "asOf": "2026-07-28",
            "consistency": {
                "blocking": False,
                "reviewRequired": True,
                "consistencyDecision": "EXCEPTION_REQUIRED",
                "clauseLineages": [],
                "findings": [],
                "counts": {"BLOCKER": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0},
            },
            "risk": {
                "asOf": "2026-07-28",
                "supplier": {"creditCode": "91310000TEST000001"},
                "eligibilityDecision": "ELIGIBLE",
                "riskTier": "B",
                "decision": "PASS",
                "riskLevel": "B",
                "observations": [],
                "sourceStatuses": [],
                "externalRiskScore": 10,
                "overallRiskScore": 10,
                "hardGates": [],
                "reviewRequired": False,
            },
            "performance": {"status": "SCORED", "metrics": [], "coverage": 100},
            "history": {},
            "evidenceGate": {"evidenceStatus": "INSUFFICIENT", "reviewRequired": True},
            "approval": {"approved": True, "action": "REQUEST_EVIDENCE"},
        }
    )
    assert held["finalDecision"]["action"] == "HOLD"
    assert held["decision"] == "REVIEW_REQUIRED"
    assert validate_procurement_supplier_risk_result(held) == held
