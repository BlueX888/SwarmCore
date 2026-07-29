from __future__ import annotations

import pytest
from jsonschema import Draft202012Validator
from swarmcore_application import StrategyService, WorkbenchService
from swarmcore_capability_contract_performance import (
    MANIFEST,
    MODELS,
    REFERENCES,
    SCHEMAS,
    STRATEGIES,
)
from swarmcore_registry import CapabilityPackManifest, builtin_registry
from swarmcore_spec import SwarmStrategy


def test_contract_performance_capability_assets_are_valid() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    initialize = SwarmStrategy.model_validate(
        STRATEGIES["strategy://contract-performance/initialize@13"]
    )
    collect = SwarmStrategy.model_validate(
        STRATEGIES["strategy://contract-performance/collect@10"]
    )

    assert manifest.metadata.name == "contract-performance"
    assert manifest.metadata.version == "1.0.17"
    assert len(initialize.spec.agents) == 1
    assert len(collect.spec.agents) == 1
    assert initialize.spec.budget.max_agents == 4
    assert collect.spec.budget.max_agents == 5
    assert collect.spec.budget.max_parallelism == 5
    assert collect.spec.budget.on_exhausted == "partial_result"
    assert manifest.spec.strategies.execute in REFERENCES
    assert manifest.spec.strategies.operations == {
        "INITIALIZE": "strategy://contract-performance/initialize@13",
        "COLLECT": "strategy://contract-performance/collect@10",
    }
    assert "strategy://contract-performance/collect@10" in REFERENCES
    assert set(manifest.spec.agents) <= REFERENCES
    assert set(manifest.spec.tools) <= REFERENCES
    registry = builtin_registry()
    assert all(registry.resolve_agent(ref) is not None for ref in manifest.spec.agents)
    assert all(registry.resolve_model(ref) is not None for ref in MODELS)
    assert all(registry.resolve_tool(ref) is not None for ref in manifest.spec.tools)
    plans = [
        StrategyService().compile(
            STRATEGIES[reference],
            registry_snapshot=registry.snapshot_id,
            policy_revision="test",
        )[1]
        for reference in manifest.spec.strategies.references()
    ]
    actual_agents = {
        str(value["registryRef"])
        for plan in plans
        for value in plan.resolved_agents.values()
        if value.get("registryRef") is not None
    }
    actual_tools = {reference for plan in plans for reference in plan.resolved_tools}
    assert actual_agents == set(manifest.spec.agents)
    assert actual_tools == set(manifest.spec.tools)
    collect_schedule = collect.spec.graph.nodes.root["build-schedule"]
    assert collect_schedule.input["actuals"] == "{{ tasks.calculate-status.output.content }}"
    collect_ledger = collect.spec.graph.nodes.root["finalize"].input["evidenceLedger"]
    assert collect_ledger["sourceResults"] == (
        "{{ tasks.source-collect.output.content.sourceResults }}"
    )
    assert collect_ledger["cursors"] == "{{ tasks.source-collect.output.content.nextCursors }}"

    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)


def test_contract_performance_pack_has_single_primary_contract_and_all_document_slots() -> None:
    case = MANIFEST["spec"]["case"]
    primary = [item for item in case["subjectRoles"] if item["role"] == "PRIMARY"]
    assert len(primary) == 1
    assert primary[0]["min"] == primary[0]["max"] == 1

    requirements = {item["key"]: item for item in MANIFEST["spec"]["documents"]["requirements"]}
    assert requirements["master-contract"]["required"] is True
    assert {
        "dispatch-logistics",
        "receipt-arrival",
        "delivery-acceptance",
        "payment-evidence",
        "progress-service",
        "meeting-correspondence",
    } <= requirements.keys()


def test_contract_performance_operation_selects_frozen_collect_strategy() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    initialize = {
        "ref": "strategy://contract-performance/initialize@13",
        "strategyVersionId": "00000000-0000-0000-0000-000000000001",
    }
    collect = {
        "ref": "strategy://contract-performance/collect@10",
        "strategyVersionId": "00000000-0000-0000-0000-000000000002",
    }
    dependency_snapshot = {
        "strategy": initialize,
        "strategies": {"INITIALIZE": initialize, "COLLECT": collect},
    }

    selected = WorkbenchService._select_strategy_snapshot(
        manifest,
        dependency_snapshot,
        {"operation": "collect"},
    )

    assert selected == collect
    with pytest.raises(ValueError, match="CAPABILITY_OPERATION_UNSUPPORTED"):
        WorkbenchService._select_strategy_snapshot(
            manifest,
            dependency_snapshot,
            {"operation": "UNSUPPORTED"},
        )


def test_contract_performance_agents_cannot_write_business_systems() -> None:
    tools = set(MANIFEST["spec"]["tools"])
    forbidden = {
        "tool://payment/create@1",
        "tool://acceptance/sign@1",
        "tool://contract/change-write@1",
        "tool://message/send@1",
    }
    assert tools.isdisjoint(forbidden)


def test_contract_performance_agents_publish_strict_business_schemas() -> None:
    registry = builtin_registry()
    extractor = registry.resolve_agent("agent://contract-performance/plan-extractor@5")
    analyst = registry.resolve_agent("agent://contract-performance/execution-evidence-analyst@4")

    assert extractor is not None
    assert analyst is not None
    assert extractor.model == "model://general@1"
    assert analyst.model == "model://general@1"
    search = registry.resolve_tool("tool://evidence/search@3")
    assert search is not None
    assert search.input_schema["properties"]["domain"]["type"] == "string"
    assert "execution" in search.input_schema["properties"]["domain"]["enum"]
    assert extractor.output_schema is not None
    assert analyst.output_schema is not None
    Draft202012Validator.check_schema(extractor.output_schema)
    Draft202012Validator.check_schema(analyst.output_schema)
    assert extractor.output_schema["additionalProperties"] is False
    assert {
        "contract",
        "obligations",
        "milestones",
        "acceptanceCriteria",
        "serviceLevels",
        "paymentConditions",
        "changes",
    } <= set(extractor.output_schema["required"])
    milestone = extractor.output_schema["properties"]["milestones"]["items"]
    assert {"title", "dueDate", "dependencies", "evidenceRefs"} <= set(milestone["required"])
    acceptance = extractor.output_schema["properties"]["acceptanceCriteria"]["items"]
    service_level = extractor.output_schema["properties"]["serviceLevels"]["items"]
    assert "boolean" in acceptance["properties"]["target"]["type"]
    assert "boolean" in service_level["properties"]["target"]["type"]
    assert analyst.output_schema["additionalProperties"] is False
    assert {"facts", "links", "ambiguities", "summary"} == set(analyst.output_schema["required"])
