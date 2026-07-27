from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from swarmcore_application import (
    aggregate_responsibility,
    build_deviation_trends,
    calculate_cost_deviation,
    calculate_time_deviation,
    compare_content_deviation,
    finalize_deviation_result,
    validate_deviation_result,
)
from swarmcore_application.capability_tool_executors import deviation_facts_merge
from swarmcore_capability_deviation_analysis import SCHEMAS


def test_calculates_time_content_and_cost_without_model_arithmetic() -> None:
    payload = {
        "title": "项目偏差分析",
        "subject": {"subjectId": "P-1", "subjectType": "project"},
        "period": {"start": "2026-01-01", "end": "2026-06-30"},
        "asOf": "2026-06-30",
        "dimensions": ["TIME", "CONTENT", "COST"],
        "time": {
            "milestones": [
                {
                    "milestoneId": "M1",
                    "name": "基础交付",
                    "currentBaselineDate": "2026-05-01",
                    "actualDate": "2026-05-11",
                    "critical": True,
                    "evidenceRefs": ["doc:v1:p3"],
                },
                {
                    "milestoneId": "M2",
                    "currentBaselineDate": "2026-06-10",
                    "forecastDate": "2026-06-08",
                    "critical": False,
                },
            ],
            "pv": 100,
            "ev": 80,
        },
        "content": {
            "items": [
                {"itemId": "D1", "status": "ACCEPTED", "weight": 3},
                {"itemId": "D2", "status": "CONDITIONAL", "weight": 1},
            ]
        },
        "cost": {
            "currency": "CNY",
            "originalBAC": 1000,
            "approvedChanges": [
                {"amount": 100, "approved": True},
                {"amount": 50, "approved": False},
            ],
            "eac": 1210,
            "ac": 700,
            "commitments": 200,
            "ev": 630,
        },
    }

    time_result = calculate_time_deviation(payload)
    content_result = compare_content_deviation(payload)
    cost_result = calculate_cost_deviation(payload)

    assert time_result["metrics"]["maximumDelayDays"] == 10
    assert time_result["metrics"]["onTimeRate"] == 0.5
    assert time_result["metrics"]["spi"] == 0.8
    assert content_result["metrics"]["actualCompletionRate"] == 0.875
    assert content_result["metrics"]["contentVarianceRate"] == -0.125
    assert cost_result["metrics"]["currentBAC"] == 1100.0
    assert cost_result["metrics"]["costVariance"] == 110.0
    assert cost_result["metrics"]["cpi"] == 0.9


def test_deviation_golden_fixture_is_reproducible() -> None:
    fixture = json.loads(
        Path("tests/fixtures/business/deviation-analysis-golden.json").read_text(
            encoding="utf-8"
        )
    )
    payload = fixture["payload"]
    expected = fixture["expected"]

    time_result = calculate_time_deviation(payload)
    content_result = compare_content_deviation(payload)
    cost_result = calculate_cost_deviation(payload)

    assert time_result["metrics"]["maximumDelayDays"] == expected["maximumDelayDays"]
    assert time_result["metrics"]["onTimeRate"] == expected["onTimeRate"]
    assert time_result["metrics"]["spi"] == expected["spi"]
    assert (
        content_result["metrics"]["actualCompletionRate"]
        == expected["actualCompletionRate"]
    )
    assert (
        content_result["metrics"]["contentVarianceRate"]
        == expected["contentVarianceRate"]
    )
    assert cost_result["metrics"]["currentBAC"] == expected["currentBAC"]
    assert cost_result["metrics"]["costVariance"] == expected["costVariance"]
    assert cost_result["metrics"]["cpi"] == expected["cpi"]


def test_missing_evm_and_cross_currency_are_not_silently_invented() -> None:
    time_result = calculate_time_deviation(
        {
            "time": {
                "milestones": [
                    {
                        "baselineDate": "2026-01-01",
                        "forecastDate": "2026-01-02",
                    }
                ]
            }
        }
    )
    cost_result = calculate_cost_deviation(
        {
            "cost": {
                "currency": "CNY",
                "currencies": ["CNY", "USD"],
                "originalBAC": 100,
                "eac": 110,
            }
        }
    )

    assert time_result["metrics"]["spi"] is None
    assert time_result["metrics"]["spiUnavailableReason"] == "PV and EV are both required"
    assert cost_result["status"] == "CONFLICTED"


def test_content_equal_weight_and_first_run_trend_are_explicit() -> None:
    content = compare_content_deviation(
        {
            "content": {
                "items": [
                    {"status": "ACCEPTED"},
                    {"status": "PENDING"},
                ]
            }
        }
    )
    trend = build_deviation_trends(
        {
            "subjectId": "P-1",
            "asOf": "2026-06-30",
            "baselineHash": "b1",
            "configurationHash": "c1",
        },
        [],
    )

    assert content["metrics"]["equalWeightFallback"] is True
    assert content["metrics"]["actualCompletionRate"] == 0.625
    assert trend["status"] == "DATA_INSUFFICIENT"


@pytest.mark.asyncio
async def test_deviation_facts_are_adapted_for_consistency_check() -> None:
    result = await deviation_facts_merge(
        {
            "basePayload": {
                "title": "偏差分析",
                "subject": {"subjectId": "P-1"},
                "period": {"start": "2026-01-01", "end": "2026-06-30"},
                "time": {},
                "content": {},
                "cost": {},
            },
            "analyses": {
                "schedule": {
                    "payloadPatch": {},
                    "facts": [
                        {
                            "type": "BASELINE_DATE",
                            "date": "2026-05-01",
                            "documentVersionId": "019f9e22-c73b-777a-a4a5-3bf15e49a3b9",
                        }
                    ],
                    "conflicts": [],
                    "missingEvidence": [],
                }
            },
        },
        "effect-1",
    )

    fact = result["facts"][0]
    assert fact["factId"].startswith("deviation-fact-")
    assert fact["factType"] == "BASELINE_DATE"
    assert fact["confidence"] == 0.8
    assert fact["evidenceRefs"] == ["019f9e22-c73b-777a-a4a5-3bf15e49a3b9"]
    assert isinstance(fact["value"], str)


def test_responsibility_is_proposed_and_finalization_preserves_dimension_status() -> None:
    responsibility = aggregate_responsibility(
        [
            {
                "party": "承包商",
                "scope": "TIME",
                "rationale": "关键设备晚到",
                "confidence": 0.8,
                "evidenceRefs": [
                    "019f9e22-e046-73c6-be7c-5f985cc6dd86 (根因证据包)",
                    "SHA:deadbeef",
                ],
                "status": "CONFIRMED",
            }
        ]
    )
    result = finalize_deviation_result(
        payload={
            "title": "偏差分析",
            "subject": {"subjectId": "P-1"},
            "period": {},
            "asOf": "2026-06-30",
            "dimensions": ["TIME", "CONTENT"],
        },
        dimensions={
            "TIME": {"status": "OK", "metrics": {}, "reasons": [], "evidenceRefs": []},
            "CONTENT": {
                "status": "DATA_INSUFFICIENT",
                "metrics": {},
                "reasons": ["missing"],
                "evidenceRefs": [],
            },
        },
        root_causes=[],
        trends={},
        responsibility=responsibility,
        coverage={"complete": True},
        evidence_review={"reviewRequired": False},
        narrative={"executiveSummary": "摘要"},
        provenance={
            "documentContentHash": "d",
            "attachmentManifestHash": "a",
            "selectionManifestHash": "s",
            "baselineHash": "b",
            "configurationHash": "c",
            "agents": [],
        },
    )

    assert responsibility["proposals"][0]["status"] == "PROPOSED"
    assert responsibility["proposals"][0]["evidenceRefs"] == [
        "019f9e22-e046-73c6-be7c-5f985cc6dd86"
    ]
    assert responsibility["humanConfirmationRequired"] is True
    assert result["reviewRequired"] is True
    assert result["qualityStatus"] == "REVIEW_REQUIRED"
    assert result["dimensions"]["CONTENT"]["status"] == "DATA_INSUFFICIENT"
    assert result["time"]["status"] == "OK"
    assert result["content"]["status"] == "DATA_INSUFFICIENT"
    responsibility_findings = [
        finding
        for finding in result["findings"]
        if finding["code"].startswith("RESPONSIBILITY_PROPOSAL_")
    ]
    assert responsibility_findings[0]["dimension"] == "RESPONSIBILITY"
    Draft202012Validator(
        SCHEMAS["schema://deviation-analysis/result@1"]
    ).validate(result)
    inconsistent = {**result, "time": {**result["time"], "status": "CONFLICTED"}}
    try:
        validate_deviation_result(inconsistent)
    except ValueError as exc:
        assert "must match" in str(exc)
    else:
        raise AssertionError("inconsistent dimension aliases must be rejected")
