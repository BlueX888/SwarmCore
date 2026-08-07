from __future__ import annotations

from jsonschema import Draft202012Validator
from swarmcore_application import StrategyService
from swarmcore_capability_invoice_assurance import MANIFEST, REFERENCES, SCHEMAS, STRATEGIES
from swarmcore_registry import (
    CapabilityPackManifest,
    CapabilityReferenceCatalog,
    builtin_registry,
    resolve_manifest,
)
from swarmcore_spec import SwarmStrategy


def test_invoice_assurance_capability_assets_and_references_are_valid() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    strategy = SwarmStrategy.model_validate(STRATEGIES["strategy://invoice-assurance/assess@3"])
    registry = builtin_registry()

    assert manifest.metadata.name == "invoice-assurance"
    assert manifest.metadata.version == "1.1.1"
    assert strategy.spec.budget.max_agents == 3
    assert strategy.spec.budget.max_parallelism == 3
    assert set(manifest.spec.agents) <= REFERENCES
    assert set(manifest.spec.tools) <= REFERENCES
    assert all(registry.resolve_agent(ref) is not None for ref in manifest.spec.agents)
    assert all(registry.resolve_tool(ref) is not None for ref in manifest.spec.tools)
    finalize_registration = registry.resolve_tool("tool://invoice/finalize@1")
    assert finalize_registration is not None
    assert "enterprisePublicStatus" in finalize_registration.input_schema["properties"]
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
    review_router = next(node for node in plan.nodes if node.key == "review-router")
    router_conditions = [
        route["when"] for route in review_router.config["routes"]
    ]
    assert (
        'tasks.payment-gate.output.content.status == "PAYMENT_BLOCKED"'
        in router_conditions
    )
    assert (
        'tasks.payment-gate.output.content.status == "REVIEW_REQUIRED"'
        in router_conditions
    )
    finalize = next(node for node in plan.nodes if node.key == "finalize")
    assert finalize.config["input"]["approvals"] == {
        "manual-review": "{{ tasks.manual-review.output }}"
    }
