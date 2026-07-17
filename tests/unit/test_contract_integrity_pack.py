from swarmcore_application import CapabilityCatalogService, IntegrityRuleDocument
from swarmcore_capability_contract_integrity import (
    DEFAULT_RULES,
    MANIFEST,
    REFERENCES,
    SCHEMAS,
    VIEW_DEFINITION,
)
from swarmcore_registry import (
    CapabilityPackManifest,
    CapabilityReferenceCatalog,
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
            "version": "1.0.0",
            "workItemType": "contract-case",
            "inputSchema": "schema://contract/validation-input@1",
            "outputSchema": "schema://contract/validation-result@1",
            "viewDefinition": "view://contract-integrity/work-item@1",
        }
    ]
