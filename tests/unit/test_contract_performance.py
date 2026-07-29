from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

import pytest
from swarmcore_application.contract_performance import (
    apply_approved_changes,
    build_daily_reminders,
    build_schedule,
    calculate_status,
    dependency_cycle,
    finalize_contract_performance,
    match_evidence,
    normalize_plan,
    validate_contract_performance_result,
)


def _candidate_plan() -> dict[str, object]:
    evidence_ref = {
        "evidenceRef": "clause-1",
        "documentVersionId": "11111111-1111-1111-1111-111111111111",
        "locator": {"page": 12},
        "excerptHash": "a" * 64,
        "contentHash": "b" * 64,
        "confidenceBand": "HIGH",
    }
    return {
        "contract": {"contractNumber": "ESFA-25001", "currency": "GBP"},
        "obligations": [
            {
                "id": "obl-1",
                "title": "完成课程交付",
                "evidenceRefs": [evidence_ref],
            }
        ],
        "deliverables": [
            {"id": "del-1", "obligationId": "obl-1", "description": "训练营", "quantity": "100"}
        ],
        "acceptanceCriteria": [
            {"id": "acc-1", "metric": "completionRate", "operator": ">=", "target": 0.8}
        ],
        "serviceLevels": [],
        "paymentConditions": [
            {
                "id": "pay-1",
                "amount": "25000.00",
                "prerequisites": ["ACCEPTANCE"],
            }
        ],
        "milestones": [
            {
                "id": "ms-1",
                "title": "首批交付",
                "startDate": "2026-01-01",
                "dueDate": "2026-01-31",
                "duration": 30,
                "dependencies": [],
                "acceptanceCriterionIds": ["acc-1"],
                "paymentConditionIds": ["pay-1"],
                "evidenceRequirements": ["DISPATCH", "RECEIPT", "ACCEPTANCE"],
                "contractKeys": {"contractNumber": "ESFA-25001"},
            },
            {
                "id": "ms-2",
                "title": "二批交付",
                "startDate": "2026-02-01",
                "dueDate": "2026-02-28",
                "duration": 27,
                "dependencies": ["ms-1"],
                "evidenceRequirements": ["ACCEPTANCE"],
            },
        ],
        "changes": [],
    }


def test_normalize_plan_and_schedule_are_deterministic() -> None:
    plan = normalize_plan(_candidate_plan(), currency="GBP")
    assert plan["status"] == "CANDIDATE"
    assert plan["paymentConditions"][0]["amount"] == 25000.0
    assert dependency_cycle(plan["milestones"]) == []

    schedule = build_schedule(plan, as_of="2026-02-10")
    assert schedule["criticalPath"] == ["ms-1", "ms-2"]
    assert schedule["milestones"][0]["originalDueDate"] == "2026-01-31"
    assert schedule["ganttHash"]


def test_normalize_plan_preserves_explicit_model_aliases_and_cross_references() -> None:
    evidence_ref = {
        "documentVersionId": "11111111-1111-1111-1111-111111111111",
        "page": 1,
        "text": "M2 测试环境部署应在 2026-07-25 前完成, 依赖 M1。",
    }
    plan = normalize_plan(
        {
            "contract": {"contractNumber": "SC-001"},
            "obligations": [
                {
                    "id": "obl-1",
                    "description": "完成测试环境部署",
                    "party": "乙方",
                    "evidenceRefs": [evidence_ref],
                }
            ],
            "deliverables": [],
            "acceptanceCriteria": [
                {
                    "id": "acc-1",
                    "description": "双方确认测试环境",
                    "subjectId": "M2",
                    "evidenceRefs": [evidence_ref],
                }
            ],
            "serviceLevels": [],
            "paymentConditions": [
                {
                    "id": "pay-1",
                    "description": "M2 完成后支付",
                    "milestoneId": "M2",
                    "evidenceRefs": [evidence_ref],
                }
            ],
            "milestones": [
                {
                    "id": "ms-1",
                    "milestoneId": "M1",
                    "description": "需求确认",
                    "dueDate": "2026-07-10",
                    "dependencies": [],
                    "evidenceRefs": [evidence_ref],
                },
                {
                    "id": "ms-2",
                    "milestoneId": "M2",
                    "description": "测试环境部署",
                    "dueDate": "2026-07-25",
                    "dependencies": ["M1"],
                    "evidenceRefs": [evidence_ref],
                },
            ],
            "changes": [],
        }
    )

    assert plan["obligations"][0]["title"] == "完成测试环境部署"
    assert plan["obligations"][0]["responsibleParty"] == "乙方"
    assert plan["milestones"][1]["title"] == "测试环境部署"
    assert plan["milestones"][1]["dependencies"] == ["ms-1"]
    assert plan["milestones"][1]["paymentConditionIds"] == ["pay-1"]
    assert plan["milestones"][1]["acceptanceCriterionIds"] == ["acc-1"]
    assert plan["paymentConditions"][0]["milestoneId"] == "ms-2"
    assert plan["acceptanceCriteria"][0]["subjectId"] == "ms-2"
    assert not any(item["code"] == "OBLIGATION_TITLE_MISSING" for item in plan["gaps"])


def test_normalize_plan_derives_reviewable_cross_class_facts_from_existing_evidence() -> None:
    evidence_ref = {
        "documentVersionId": "11111111-1111-1111-1111-111111111111",
        "page": 12,
        "text": "The Supplier shall comply with the Performance Measures.",
    }
    candidates = deepcopy(_candidate_plan())
    candidates["acceptanceCriteria"] = []
    candidates["serviceLevels"] = []
    candidates["obligations"] = [
        {
            "id": "obl-performance",
            "title": "Comply with Performance Measures",
            "dueRule": "continuous",
            "evidenceRefs": [evidence_ref],
        }
    ]
    milestones = cast(list[dict[str, Any]], candidates["milestones"])
    milestones[0]["evidenceRefs"] = [
        {
            **evidence_ref,
            "text": "Payment requires evidence confirming learner commencement.",
        }
    ]
    milestones[1]["evidenceRefs"] = []

    plan = normalize_plan(candidates)

    assert len(plan["acceptanceCriteria"]) == 1
    assert plan["acceptanceCriteria"][0]["subjectId"] == "ms-1"
    assert plan["acceptanceCriteria"][0]["qualityFlags"] == [
        "DERIVED_FROM_MILESTONE_EVIDENCE",
        "HUMAN_REVIEW_REQUIRED",
    ]
    assert "acc-derived-001" in plan["milestones"][0]["acceptanceCriterionIds"]
    assert any(
        item["code"] == "UNKNOWN_ACCEPTANCE_CRITERION" for item in plan["conflicts"]
    )
    assert len(plan["serviceLevels"]) == 1
    assert plan["serviceLevels"][0]["id"] == "sla-derived-001"
    assert plan["serviceLevels"][0]["target"] is None
    assert plan["serviceLevels"][0]["qualityFlags"] == [
        "DERIVED_FROM_OBLIGATION_EVIDENCE",
        "HUMAN_REVIEW_REQUIRED",
    ]
    supplemental = [
        item for item in plan["obligations"] if item["id"].startswith("obl-derived-")
    ]
    assert supplemental
    assert supplemental[0]["derivedFrom"]["kind"] == "SERVICE_LEVEL"
    assert supplemental[0]["qualityFlags"] == [
        "DERIVED_FROM_SERVICE_LEVEL",
        "HUMAN_REVIEW_REQUIRED",
    ]


def test_cycle_blocks_gantt() -> None:
    plan = normalize_plan(_candidate_plan())
    plan["milestones"][0]["dependencies"] = ["ms-2"]
    schedule = build_schedule(plan, as_of="2026-02-10")
    assert schedule["quality"]["status"] == "REVIEW_REQUIRED"
    assert schedule["criticalPath"] is None
    assert schedule["cycle"] == ["ms-1", "ms-2", "ms-1"]


def test_only_approved_effective_change_updates_current_baseline() -> None:
    plan = normalize_plan(_candidate_plan())
    result = apply_approved_changes(
        plan,
        [
            {
                "id": "chg-1",
                "status": "APPROVED",
                "effectiveAt": "2026-02-01",
                "changedPaths": [{"path": "/milestones/1/dueDate", "after": "2026-03-15"}],
            },
            {
                "id": "chg-2",
                "status": "PROPOSED",
                "effectiveAt": "2026-01-01",
                "changedPaths": [{"path": "/milestones/0/dueDate", "after": "2026-01-01"}],
            },
        ],
        as_of="2026-02-10",
    )
    assert result["originalBaseline"]["milestones"][1]["dueDate"] == "2026-02-28"
    assert result["currentBaseline"]["milestones"][1]["dueDate"] == "2026-03-15"
    assert result["currentBaseline"]["milestones"][0]["dueDate"] == "2026-01-31"
    assert result["unapprovedChangeRisks"][0]["changeId"] == "chg-2"


def test_match_status_and_payment_gate_require_stable_keys_and_acceptance() -> None:
    plan = normalize_plan(_candidate_plan())
    plan["status"] = "PUBLISHED"
    evidence = [
        {
            "id": "ev-dispatch",
            "type": "DISPATCH",
            "contractKeys": {"contractNumber": "ESFA-25001"},
        },
        {
            "id": "ev-receipt",
            "type": "RECEIPT",
            "contractKeys": {"contractNumber": "ESFA-25001"},
        },
        {
            "id": "ev-payment",
            "type": "PAYMENT",
            "contractKeys": {"contractNumber": "ESFA-25001"},
        },
    ]
    candidates = [{"evidenceId": item["id"], "targetId": "ms-1"} for item in evidence]
    matches = match_evidence(plan, evidence, candidates)
    assert {item["matchStatus"] for item in matches["links"]} == {"MATCHED"}

    performance = calculate_status(
        plan,
        evidence,
        matches["links"],
        as_of="2026-02-10",
    )
    assert performance["status"] == "OVERDUE"
    assert performance["milestones"][0]["status"] == "OVERDUE"
    assert performance["paymentGates"][0]["gateStatus"] == "BLOCKED"
    assert any(item["code"] == "PAYMENT_BEFORE_PREREQUISITES" for item in performance["findings"])


def test_public_payment_without_contract_key_stays_candidate() -> None:
    plan = normalize_plan(_candidate_plan())
    evidence = [{"id": "ev-public", "type": "PAYMENT", "contractKeys": {"supplier": "Cogrammar"}}]
    matches = match_evidence(
        plan,
        evidence,
        [{"evidenceId": "ev-public", "targetId": "ms-1"}],
    )
    assert matches["links"][0]["matchStatus"] == "CANDIDATE"
    assert matches["links"][0]["matchReasons"] == ["NO_STABLE_CROSS_KEY"]


def test_unmatched_public_payment_requires_review_when_agent_proposes_no_link() -> None:
    plan = normalize_plan(_candidate_plan())
    plan["status"] = "PUBLISHED"
    evidence = [{"id": "ev-public", "type": "PAYMENT", "contractKeys": {"supplier": "Cogrammar"}}]
    links = match_evidence(plan, evidence, [])["links"]

    performance = calculate_status(plan, evidence, links, as_of="2026-01-01")

    assert links[0]["matchStatus"] == "UNMATCHED"
    assert performance["status"] == "REVIEW_REQUIRED"
    assert performance["reviewRequired"] is True
    assert any(item["code"] == "EVIDENCE_MATCH_REVIEW_REQUIRED" for item in performance["findings"])


def test_finalize_hash_detects_mutation() -> None:
    plan = normalize_plan(_candidate_plan())
    plan["status"] = "PUBLISHED"
    performance = calculate_status(plan, [], [], as_of="2026-01-01")
    gantt = build_schedule(plan, as_of="2026-01-01")
    result = finalize_contract_performance(
        case_id="case-1",
        plan_version=1,
        plan=plan,
        performance=performance,
        gantt=gantt,
        evidence_ledger={"evidence": [], "links": []},
        change_history={"appliedChanges": [], "differences": []},
        provenance={"planHash": plan["planHash"]},
    )
    assert validate_contract_performance_result(result)["resultHash"] == result["resultHash"]
    changed = deepcopy(result)
    changed["status"] = "COMPLETED"
    with pytest.raises(ValueError, match="hash mismatch"):
        validate_contract_performance_result(changed)


def test_partial_collection_and_sla_breach_cannot_be_reported_completed() -> None:
    candidate = _candidate_plan()
    candidate["serviceLevels"] = [
        {"id": "sla-1", "metric": "responseRate", "operator": ">=", "target": "0.95"}
    ]
    plan = normalize_plan(candidate)
    plan["status"] = "PUBLISHED"
    evidence = [
        {
            "id": "ev-service",
            "type": "SERVICE",
            "value": "0.80",
            "contractKeys": {"contractNumber": "ESFA-25001"},
        }
    ]
    links = match_evidence(
        plan,
        evidence,
        [{"evidenceId": "ev-service", "targetId": "sla-1"}],
    )["links"]
    performance = calculate_status(
        plan,
        evidence,
        links,
        as_of="2026-01-01",
        collection_status="PARTIAL",
    )
    assert performance["status"] == "AT_RISK"
    assert performance["serviceLevels"][0]["status"] == "BREACHED"
    assert any(item["code"] == "SERVICE_LEVEL_BREACHED" for item in performance["findings"])


def test_payment_before_acceptance_requires_finance_review_even_when_both_exist() -> None:
    plan = normalize_plan(_candidate_plan())
    plan["status"] = "PUBLISHED"
    evidence = [
        {
            "id": "ev-payment",
            "type": "PAYMENT",
            "businessDate": "2026-01-05",
            "contractKeys": {"contractNumber": "ESFA-25001"},
        },
        {
            "id": "ev-acceptance",
            "type": "ACCEPTANCE",
            "businessDate": "2026-01-10",
            "contractKeys": {"contractNumber": "ESFA-25001"},
        },
        {
            "id": "ev-dispatch",
            "type": "DISPATCH",
            "businessDate": "2026-01-01",
            "contractKeys": {"contractNumber": "ESFA-25001"},
        },
        {
            "id": "ev-receipt",
            "type": "RECEIPT",
            "businessDate": "2026-01-03",
            "contractKeys": {"contractNumber": "ESFA-25001"},
        },
    ]
    links = match_evidence(
        plan,
        evidence,
        [{"evidenceId": item["id"], "targetId": "ms-1"} for item in evidence],
    )["links"]
    performance = calculate_status(plan, evidence, links, as_of="2026-01-20")
    assert performance["reviewRequired"] is True
    assert any(
        item["code"] == "PAYMENT_BEFORE_ACCEPTANCE"
        and item["reviewType"] == "FINANCE"
        for item in performance["findings"]
    )


def test_daily_reminders_are_stable_for_due_and_evidence_pending_milestones() -> None:
    plan = normalize_plan(_candidate_plan())
    performance = {
        "milestones": [
            {"milestoneId": "ms-1", "status": "EVIDENCE_PENDING"},
            {"milestoneId": "ms-2", "status": "NOT_STARTED"},
        ]
    }
    first = build_daily_reminders(plan, performance, as_of="2026-01-26", lead_days=7)
    second = build_daily_reminders(plan, performance, as_of="2026-01-26", lead_days=7)
    assert first == second
    assert [item["type"] for item in first] == [
        "contract.performance.milestone.evidence_pending.v1",
    ]
