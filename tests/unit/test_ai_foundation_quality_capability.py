from __future__ import annotations

import base64
import hashlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator
from swarmcore_application import StrategyService
from swarmcore_application.capability_tool_executors import EvaluationRecorderExecutor
from swarmcore_application.quality_benchmark import evaluate_quality_benchmark
from swarmcore_capability_ai_foundation_quality import MANIFEST, REFERENCES, SCHEMAS, STRATEGIES
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import Evaluation, Report, WorkItem
from swarmcore_persistence.repositories import canonical_hash
from swarmcore_registry import CapabilityPackManifest, CapabilityReferenceCatalog, builtin_registry
from swarmcore_spec import SwarmStrategy


def test_ai_quality_assets_compile_and_close_dependencies() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    strategy = SwarmStrategy.model_validate(
        STRATEGIES["strategy://ai-foundation-quality/benchmark@1"]
    )
    registry = builtin_registry()

    assert manifest.metadata.name == "ai-foundation-quality"
    assert manifest.metadata.version == "1.0.0"
    assert strategy.spec.agents == {}
    assert all(registry.resolve_tool(ref) is not None for ref in manifest.spec.tools)
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)
    assert set(manifest.spec.references()) <= REFERENCES
    CapabilityReferenceCatalog.from_iterable(REFERENCES)
    _, plan = StrategyService().compile(
        STRATEGIES[manifest.spec.strategies.execute],
        registry_snapshot=registry.snapshot_id,
        policy_revision="test",
    )
    assert set(plan.resolved_tools) == set(manifest.spec.tools)
    review = next(node for node in plan.nodes if node.key == "manual-review")
    assert review.config["requiredRoles"] == ["quality_reviewer", "tenant_admin"]
    assert review.config["requiresDistinctApprover"] is True


def test_quality_benchmark_enforces_threshold_and_critical_failures() -> None:
    result = evaluate_quality_benchmark(
        {
            "benchmarkId": "foundation-regression-2026-08",
            "minimumPassRate": 0.5,
            "samples": [
                {"sampleId": "ok", "expected": {"answer": 1}, "actual": {"answer": 1}},
                {
                    "sampleId": "critical",
                    "expected": {"answer": 2},
                    "actual": {"answer": 3},
                    "critical": True,
                },
            ],
        }
    )

    assert result["passRate"] == 0.5
    assert result["passed"] is False
    assert result["reviewRequired"] is True
    assert result["criticalFailures"] == ["critical"]
    result_hash = result.pop("resultHash")
    assert result_hash == canonical_hash(result)


@pytest.mark.asyncio
async def test_quality_recorder_persists_reports_and_updates_work_item(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import swarmcore_application.capability_tool_executors as executors_module

    tenant_id = uuid4()
    project_id = uuid4()
    evaluation_id = uuid4()
    result = evaluate_quality_benchmark(
        {
            "benchmarkId": "ready",
            "minimumPassRate": 1,
            "samples": [{"sampleId": "one", "expected": 1, "actual": 1}],
        }
    )
    pdf = b"%PDF-test"
    report_payload = {
        "mediaType": "application/pdf",
        "sha256": hashlib.sha256(pdf).hexdigest(),
        "contentBase64": base64.b64encode(pdf).decode("ascii"),
    }
    evaluation = MagicMock(spec=Evaluation)
    evaluation.id = evaluation_id
    evaluation.work_item_id = uuid4()
    evaluation.result = None
    evaluation.status = "RUNNING"
    evaluation.report_template_version = "report://ai-foundation-quality@1"
    evaluation.output_schema_version = "schema://ai-foundation-quality/result@1"
    item = MagicMock(spec=WorkItem)
    item.id = evaluation.work_item_id
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[evaluation, item])

    @asynccontextmanager
    async def fake_transaction(*args: object, **kwargs: object) -> AsyncIterator[MagicMock]:
        del args, kwargs
        yield session

    monkeypatch.setattr(executors_module, "tenant_transaction", fake_transaction)
    monkeypatch.setattr(AuditRepository, "append", AsyncMock())
    receipt = await EvaluationRecorderExecutor(None).execute(  # type: ignore[arg-type]
        {
            "evaluationId": str(evaluation_id),
            "result": result,
            "report": report_payload,
        },
        "effect-quality-record",
        SimpleNamespace(
            tenant_id=str(tenant_id),
            project_id=str(project_id),
            execution_id="execution",
            run_id=str(uuid4()),
        ),
    )

    reports = session.add_all.call_args.args[0]
    assert receipt["recorded"] is True
    assert evaluation.status == "SUCCEEDED"
    assert item.status == "COMPLETED"
    assert [value.format for value in reports if isinstance(value, Report)] == ["JSON", "PDF"]
