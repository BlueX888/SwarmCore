from __future__ import annotations

from jsonschema import Draft202012Validator
from swarmcore_application import StrategyService
from swarmcore_capability_procurement_supplier_risk import (
    MANIFEST,
    REFERENCES,
    SCHEMAS,
    STRATEGIES,
    VIEW_DEFINITION,
)
from swarmcore_registry import (
    CapabilityPackManifest,
    CapabilityReferenceCatalog,
    builtin_registry,
    resolve_manifest,
)
from swarmcore_spec import SwarmStrategy


def test_procurement_supplier_risk_capability_assets_are_valid() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    strategy = SwarmStrategy.model_validate(
        STRATEGIES["strategy://procurement-supplier-risk/assess@5"]
    )
    assert manifest.metadata.name == "procurement-supplier-risk"
    assert manifest.case_type == "procurement-supplier-risk-case"
    assert strategy.spec.graph.entrypoint == "read-documents"
    assert set(manifest.spec.references()) <= REFERENCES
    assert VIEW_DEFINITION["spec"]["sections"][0]["key"] == "consistency"
    registry = builtin_registry()
    assert all(registry.resolve_agent(ref) is not None for ref in manifest.spec.agents)
    assert all(registry.resolve_tool(ref) is not None for ref in manifest.spec.tools)
    clause_agent = registry.resolve_agent(
        "agent://procurement/clause-evidence-analyst@3"
    )
    assert clause_agent is not None
    assert clause_agent.tools == ()
    assert clause_agent.output_schema is not None
    clause_schema = clause_agent.output_schema["properties"]["clauses"]["properties"][
        "TENDER"
    ]["items"]
    assert "category" in clause_schema["required"]
    assert "matchKey" in clause_schema["required"]
    assert "evidenceRefs" in clause_schema["required"]
    assert clause_schema["properties"]["evidenceRefs"]["minItems"] == 1
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
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)


def test_procurement_supplier_risk_pack_requires_real_four_way_documents() -> None:
    requirements = {
        item["key"]: item for item in MANIFEST["spec"]["documents"]["requirements"]
    }
    assert requirements["tender-document"]["required"] is True
    assert requirements["winning-bid"]["required"] is True
    assert requirements["award-notice"]["required"] is True
    assert requirements["contract"]["required"] is True
