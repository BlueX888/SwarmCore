from __future__ import annotations

from jsonschema import Draft202012Validator
from swarmcore_application import StrategyService
from swarmcore_capability_deviation_analysis import MANIFEST, REFERENCES, SCHEMAS, STRATEGIES
from swarmcore_registry import (
    CapabilityPackManifest,
    CapabilityReferenceCatalog,
    builtin_registry,
    resolve_manifest,
)
from swarmcore_spec import SwarmStrategy


def test_deviation_capability_assets_and_references_are_valid() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    strategy = SwarmStrategy.model_validate(
        STRATEGIES["strategy://deviation-analysis/execute@7"]
    )
    registry = builtin_registry()

    assert manifest.metadata.name == "deviation-analysis"
    assert manifest.metadata.version == "1.0.6"
    assert strategy.spec.budget.max_agents == 6
    assert strategy.spec.budget.max_parallelism == 4
    assert set(manifest.spec.agents) <= REFERENCES
    assert set(manifest.spec.tools) <= REFERENCES
    assert all(registry.resolve_agent(ref) is not None for ref in manifest.spec.agents)
    assert all(registry.resolve_tool(ref) is not None for ref in manifest.spec.tools)
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)
    resolved, snapshot = resolve_manifest(
        MANIFEST, CapabilityReferenceCatalog.from_iterable(REFERENCES)
    )
    assert set(snapshot) == set(resolved.spec.references())
    _, plan = StrategyService().compile(
        STRATEGIES[resolved.spec.strategies.execute],
        registry_snapshot=registry.snapshot_id,
        policy_revision="test",
    )
    assert set(plan.resolved_tools) == set(manifest.spec.tools)
    merge_facts = strategy.spec.graph.nodes.root["merge-facts"]
    assert merge_facts.input["upstreamEvaluations"] == "{{ input.upstreamEvaluations }}"
    finalize = strategy.spec.graph.nodes.root["finalize"]
    assert finalize.input["schemaVersion"] == "schema://deviation-analysis/result@2"
    assert finalize.input["approvals"] == ["{{ tasks.manual-review.output }}"]
