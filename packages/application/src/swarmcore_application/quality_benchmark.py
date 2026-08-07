from __future__ import annotations

from copy import deepcopy
from typing import Any

from swarmcore_persistence.repositories import canonical_hash

SCHEMA_VERSION = "schema://ai-foundation-quality/result@1"


def evaluate_quality_benchmark(
    payload: dict[str, Any], approval: dict[str, Any] | None = None
) -> dict[str, Any]:
    samples = [dict(value) for value in payload.get("samples", []) if isinstance(value, dict)]
    if not samples:
        raise ValueError("quality benchmark requires at least one sample")
    outcomes: list[dict[str, Any]] = []
    total_weight = 0.0
    passed_weight = 0.0
    critical_failures: list[str] = []
    for index, sample in enumerate(samples, start=1):
        sample_id = str(sample.get("sampleId") or f"sample-{index}")
        weight = float(sample.get("weight", 1))
        if weight <= 0:
            raise ValueError("benchmark sample weight must be positive")
        passed = canonical_hash(sample.get("expected")) == canonical_hash(sample.get("actual"))
        total_weight += weight
        if passed:
            passed_weight += weight
        elif sample.get("critical") is True:
            critical_failures.append(sample_id)
        outcomes.append(
            {
                "sampleId": sample_id,
                "passed": passed,
                "critical": bool(sample.get("critical", False)),
                "weight": weight,
                "expectedHash": canonical_hash(sample.get("expected")),
                "actualHash": canonical_hash(sample.get("actual")),
            }
        )
    pass_rate = round(passed_weight / total_weight, 4)
    threshold = float(payload.get("minimumPassRate", 0.9))
    passed = pass_rate >= threshold and not critical_failures
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "benchmarkId": str(payload.get("benchmarkId") or "default"),
        "qualityStatus": "READY" if passed else "REVIEW_REQUIRED",
        "reviewRequired": not passed,
        "passed": passed,
        "sampleCount": len(outcomes),
        "passedCount": sum(value["passed"] for value in outcomes),
        "passRate": pass_rate,
        "minimumPassRate": threshold,
        "criticalFailures": critical_failures,
        "samples": outcomes,
        "approval": deepcopy(approval) if approval else None,
        "provenance": {
            "benchmarkHash": canonical_hash(samples),
            "evaluator": "tool://ai/quality-benchmark@1",
        },
    }
    result["resultHash"] = canonical_hash(result)
    return result


def quality_benchmark_report_lines(result: dict[str, Any]) -> list[str]:
    return [
        "基础 AI 能力质量评测报告",
        f"基准集: {result['benchmarkId']}",
        f"样本数: {result['sampleCount']}",
        f"通过数: {result['passedCount']}",
        f"加权通过率: {result['passRate']:.2%}",
        f"门槛: {result['minimumPassRate']:.2%}",
        f"结论: {'通过' if result['passed'] else '需复核'}",
    ]


__all__ = ["evaluate_quality_benchmark", "quality_benchmark_report_lines"]
