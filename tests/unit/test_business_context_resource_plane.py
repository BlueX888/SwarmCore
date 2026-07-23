from pathlib import Path

import pytest
from sqlalchemy import UniqueConstraint
from swarmcore_application import (
    ConnectionService,
    DecisionAssetService,
    FakeConnector,
    execute_decision,
    normalize_decision,
    validate_evidence_ref,
)
from swarmcore_capability_contract_integrity import MANIFEST, MANIFEST_V2, REFERENCES
from swarmcore_persistence.models import Base
from swarmcore_registry import (
    FAKE_FILES_CONNECTOR,
    CapabilityPackManifest,
    CapabilityReferenceCatalog,
    builtin_connector_registry,
    hash_manifest,
    resolve_manifest,
)


def test_v1_and_v2_capability_pack_contracts_are_compatible() -> None:
    v1, _ = resolve_manifest(MANIFEST, CapabilityReferenceCatalog.from_iterable(REFERENCES))
    v2, snapshot = resolve_manifest(
        MANIFEST_V2, CapabilityReferenceCatalog.from_iterable(REFERENCES)
    )

    assert v1.case_type == "contract-case"
    assert v2.case_type == "contract-case"
    assert v1.api_version == "swarmcore.io/v1"
    assert v2.api_version == "swarmcore.io/v2"
    assert v2.spec.case is not None and v2.spec.case.subjects_required
    assert {value.slot for value in v2.spec.decisions} == {"document-checklist"}
    assert {value.slot for value in v2.spec.resources} == {
        "contract-files",
        "report-output",
    }
    assert set(snapshot) == set(v2.spec.references())
    assert hash_manifest(v1) != hash_manifest(v2)


def test_v2_manifest_rejects_duplicate_slots() -> None:
    value = {**MANIFEST_V2, "spec": {**MANIFEST_V2["spec"]}}
    value["spec"]["decisions"] = [
        *MANIFEST_V2["spec"]["decisions"],
        MANIFEST_V2["spec"]["decisions"][0],
    ]
    with pytest.raises(ValueError, match="decision slot keys must be unique"):
        CapabilityPackManifest.model_validate(value)


def test_decision_envelope_tests_gate_publish_contract() -> None:
    definition = {
        "apiVersion": "swarmcore.io/decision/v1",
        "kind": "DecisionAsset",
        "type": "EXPRESSION",
        "engine": "swarmcore.rules.v1",
        "inputSchema": "schema://contract/check-input@1",
        "outputSchema": "schema://contract/check-output@1",
        "definition": {"condition": "amount >= 100"},
        "tests": [
            {"name": "large", "input": {"amount": 101}, "expected": {"matched": True}},
            {"name": "small", "input": {"amount": 1}, "expected": {"matched": False}},
        ],
    }
    envelope = DecisionAssetService().validate(definition)
    assert execute_decision(envelope, {"amount": 100}) == {"matched": True}

    definition["tests"][0]["expected"] = {"matched": False}
    with pytest.raises(ValueError, match="DECISION_TEST_FAILED"):
        DecisionAssetService().validate(definition)


def test_legacy_decision_is_normalized_without_rewriting_source() -> None:
    legacy = {
        "schemaVersion": "schema://contract/checklist-rule@1",
        "match": {"contractType": "purchase"},
        "requirements": [],
    }
    normalized = normalize_decision(legacy)
    assert normalized.type == "CHECKLIST"
    assert normalized.definition == legacy
    assert "apiVersion" not in legacy


def test_connection_configuration_rejects_secret_values() -> None:
    with pytest.raises(ValueError, match="CONNECTION_CONFIGURATION_CONTAINS_SECRET"):
        ConnectionService._validate(
            "connector://test/files@1",
            {"endpoint": "https://example", "apiToken": "x"},
            "vault://test/key",
        )
    with pytest.raises(ValueError, match="CONNECTION_SECRET_UNAVAILABLE"):
        ConnectionService._validate(
            "connector://test/files@1", {"endpoint": "https://example"}, "plain-text"
        )


@pytest.mark.asyncio
async def test_fake_connector_registry_and_health_are_deterministic() -> None:
    definition = builtin_connector_registry().resolve("connector://fake/files@1")
    assert definition == FAKE_FILES_CONNECTOR
    connector = FakeConnector()
    assert await connector.health({}) is True
    assert await connector.health({"unhealthy": True}) is False
    assert await connector.read({"value": {"contract": "C-1"}}) == {"contract": "C-1"}


def test_evidence_ref_requires_stable_hash_and_authorized_reference() -> None:
    validate_evidence_ref(
        {
            "source": {
                "kind": "RESOURCE_SNAPSHOT",
                "ref": "resource-snapshot://test",
                "contentHash": "a" * 64,
            },
            "locator": {"page": 1},
        }
    )
    with pytest.raises(ValueError, match="EVIDENCE_REF_INVALID"):
        validate_evidence_ref(
            {"source": {"kind": "INLINE", "ref": "text://secret", "contentHash": "x"}}
        )


def test_business_context_resource_tables_and_idempotency_constraints_exist() -> None:
    expected = {
        "business_objects",
        "business_object_versions",
        "business_object_relations",
        "work_item_subjects",
        "project_capability_decision_bindings",
        "evaluation_decisions",
        "decision_executions",
        "connections",
        "connection_versions",
        "resource_definitions",
        "capability_resource_bindings",
        "resource_snapshots",
    }
    assert expected <= set(Base.metadata.tables)
    constraints = {
        constraint.name
        for constraint in Base.metadata.tables["resource_snapshots"].constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert "uq_resource_snapshots_key" in constraints


def test_business_context_resource_migration_has_rls_immutability_and_downgrade() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0011_business_context_resources.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0010_pack_version_delete"' in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "swarmcore_reject_immutable_update" in migration
    assert "DROP TABLE IF EXISTS" in migration
