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
        STRATEGIES["strategy://procurement-supplier-risk/assess@6"]
    )
    assert manifest.metadata.name == "procurement-supplier-risk"
    assert manifest.metadata.version == "1.0.5"
    assert manifest.case_type == "procurement-supplier-risk-case"
    assert strategy.spec.graph.entrypoint == "read-documents"
    assert set(manifest.spec.references()) <= REFERENCES
    assert VIEW_DEFINITION["spec"]["sections"][0]["key"] == "consistency"
    registry = builtin_registry()
    assert all(registry.resolve_agent(ref) is not None for ref in manifest.spec.agents)
    assert all(registry.resolve_tool(ref) is not None for ref in manifest.spec.tools)
    clause_agent = registry.resolve_agent(
        "agent://procurement/clause-evidence-analyst@4"
    )
    assert clause_agent is not None
    assert clause_agent.tools == ()
    assert clause_agent.output_schema is not None
    assert "clauseFacts" in clause_agent.output_schema["required"]
    mapping_schema = clause_agent.output_schema["properties"]["mappingCandidates"]["items"]
    assert "severity" not in mapping_schema.get("properties", {})
    assert "severity" not in mapping_schema.get("required", [])
    assert "strategy://procurement-supplier-risk/assess@5" in STRATEGIES
    assert strategy.spec.agents["clause-analyst"].ref == (
        "agent://procurement/clause-evidence-analyst@4"
    )
    assert "risk-analyst" not in strategy.spec.agents
    assert "reviewer" not in strategy.spec.agents
    review = strategy.spec.graph.nodes.root["manual-review"]
    assert review.requires_distinct_approver is True
    assert set(review.required_roles) == {
        "procurement_reviewer",
        "legal_reviewer",
        "risk_reviewer",
        "tenant_admin",
    }
    assert "action" in review.input_schema["required"]
    assert "approved" not in review.input_schema.get("properties", {})
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
