from swarmcore_application import CapabilityCatalogService, IntegrityRuleDocument, StrategyService
from swarmcore_capability_contract_integrity import (
    DEFAULT_RULES,
    MANIFEST,
    MANIFEST_V2_1,
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


def test_contract_integrity_pack_is_self_consistent() -> None:
    manifest, snapshot = resolve_manifest(
        MANIFEST, CapabilityReferenceCatalog.from_iterable(REFERENCES)
    )
    assert isinstance(manifest, CapabilityPackManifest)
    assert set(snapshot) == set(manifest.spec.references())
    assert manifest.spec.work_item_schema in SCHEMAS
    assert IntegrityRuleDocument.model_validate(DEFAULT_RULES).match == {
        "contractType": "purchase"
    }
    assert VIEW_DEFINITION["kind"] == "ViewDefinition"


def test_capability_catalog_discovers_the_business_pack() -> None:
    catalog = CapabilityCatalogService((MANIFEST,)).get()
    assert [item.model_dump(mode="json", by_alias=True) for item in catalog.capability_packs] == [
        {
            "name": "contract-integrity",
            "version": "1.2.0",
            "workItemType": "contract-case",
            "inputSchema": "schema://contract/validation-input@1",
            "outputSchema": "schema://contract/validation-result@1",
            "viewDefinition": "view://contract-integrity/work-item@1",
        }
    ]


def test_contract_pack_agents_and_tools_are_registered_runtime_capabilities() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    registry = builtin_registry()
    catalog = CapabilityCatalogService((MANIFEST,)).get()

    assert set(manifest.spec.agents) <= {item.ref for item in registry.agents}
    assert set(manifest.spec.tools) <= {item.ref for item in registry.tools}
    assert set(manifest.spec.agents) <= {item.id for item in catalog.agents}
    assert set(manifest.spec.tools) <= {item.ref for item in catalog.tools}


def test_contract_pack_strategy_uses_exactly_its_declared_runtime_dependencies() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    registry = builtin_registry()
    _, plan = StrategyService().compile(
        STRATEGIES[manifest.spec.strategies.execute],
        registry_snapshot=registry.snapshot_id,
        policy_revision="test",
    )

    actual_agents = {
        str(value["registryRef"])
        for value in plan.resolved_agents.values()
        if value.get("registryRef") is not None
    }
    assert actual_agents == set(manifest.spec.agents)
    assert set(plan.resolved_tools) == set(manifest.spec.tools)
    assert "model://fake-deterministic@1" not in plan.resolved_models


def test_document_processing_pack_strategy_dependencies_match_manifest() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST_V2_1)
    registry = builtin_registry()
    _, plan = StrategyService().compile(
        STRATEGIES[manifest.spec.strategies.execute],
        registry_snapshot=registry.snapshot_id,
        policy_revision="test",
    )

    actual_agents = {
        str(value["registryRef"])
        for value in plan.resolved_agents.values()
        if value.get("registryRef") is not None
    }
    assert actual_agents == set(manifest.spec.agents)
    assert set(plan.resolved_tools) == set(manifest.spec.tools)
