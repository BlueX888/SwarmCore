from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator
from swarmcore_application import StrategyService
from swarmcore_application.capability_tool_executors import ConfirmedEvaluationReportGenerator
from swarmcore_capability_report_generation import MANIFEST, REFERENCES, SCHEMAS, STRATEGIES
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import Evaluation, Report
from swarmcore_registry import CapabilityPackManifest, builtin_registry
from swarmcore_spec import SwarmStrategy


def test_report_generation_assets_compile_and_close_dependencies() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    strategy = SwarmStrategy.model_validate(
        STRATEGIES["strategy://report-generation/confirmed@1"]
    )
    registry = builtin_registry()

    assert manifest.metadata.name == "report-generation"
    assert manifest.metadata.version == "1.0.0"
    assert strategy.spec.agents == {}
    assert all(registry.resolve_tool(ref) is not None for ref in manifest.spec.tools)
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)
    assert set(manifest.spec.references()) <= REFERENCES
    _, plan = StrategyService().compile(
        STRATEGIES[manifest.spec.strategies.execute],
        registry_snapshot=registry.snapshot_id,
        policy_revision="test",
    )
    assert set(plan.resolved_tools) == set(manifest.spec.tools)


def test_report_generation_source_gate_rejects_unconfirmed_results() -> None:
    assert ConfirmedEvaluationReportGenerator._confirmed(None) is False
    assert ConfirmedEvaluationReportGenerator._confirmed({"reviewRequired": True}) is False
    assert ConfirmedEvaluationReportGenerator._confirmed({"passed": False}) is False
    assert ConfirmedEvaluationReportGenerator._confirmed({"passed": True}) is True
    assert ConfirmedEvaluationReportGenerator._confirmed(
        {"reportQuality": {"passed": True}}
    ) is True


@pytest.mark.asyncio
async def test_report_generation_creates_report_for_confirmed_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import swarmcore_application.capability_tool_executors as executors_module

    tenant_id = uuid4()
    project_id = uuid4()
    source = MagicMock(spec=Evaluation)
    source.id = uuid4()
    source.work_item_id = uuid4()
    source.status = "SUCCEEDED"
    source.result = {"passed": True, "reviewRequired": False}
    source.output_schema_version = "schema://source/result@1"
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[source, None])

    async def flush() -> None:
        added = session.add.call_args.args[0]
        if isinstance(added, Report) and added.id is None:
            added.id = uuid4()

    session.flush = flush

    @asynccontextmanager
    async def fake_transaction(*args: object, **kwargs: object) -> AsyncIterator[MagicMock]:
        del args, kwargs
        yield session

    monkeypatch.setattr(executors_module, "tenant_transaction", fake_transaction)
    monkeypatch.setattr(AuditRepository, "append", AsyncMock())
    result = await ConfirmedEvaluationReportGenerator(None).execute(  # type: ignore[arg-type]
        {
            "sourceEvaluationId": str(source.id),
            "title": "确认评价报告",
            "format": "PDF",
        },
        "effect-generate",
        SimpleNamespace(
            tenant_id=str(tenant_id),
            project_id=str(project_id),
            execution_id="execution",
            run_id=str(uuid4()),
        ),
    )

    assert result["generated"] is True
    assert result["sourceEvaluationId"] == str(source.id)
    assert result["format"] == "PDF"
    assert result["reviewRequired"] is False
