import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from swarmcore_capability_contract_integrity import MANIFEST
from swarmcore_registry import (
    CapabilityPackManifest,
    CapabilityReferenceCatalog,
    hash_manifest,
    normalize_manifest,
    resolve_manifest,
)

FIXTURE = Path("tests/fixtures/business/contract-integrity-pack.json")


def _manifest() -> dict[str, object]:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_manifest_normalization_and_hash_are_deterministic() -> None:
    raw = _manifest()
    reordered = dict(reversed(list(raw.items())))
    assert normalize_manifest(raw) == normalize_manifest(reordered)
    assert hash_manifest(raw) == hash_manifest(reordered)
    assert len(hash_manifest(raw)) == 64


def test_v1_hash_does_not_include_v2_default_slots() -> None:
    normalized = normalize_manifest(MANIFEST)

    assert "case" not in normalized["spec"]
    assert "decisions" not in normalized["spec"]
    assert "resources" not in normalized["spec"]
    assert hash_manifest(MANIFEST) == (
        "c632917f20ddcde51cc4831e9df6cafc2c320bb5687e835457cc5ec3de8c47a2"
    )


def test_manifest_rejects_mutable_refs_and_code_entrypoints() -> None:
    raw = _manifest()
    spec = raw["spec"]
    assert isinstance(spec, dict)
    spec["inputSchema"] = "schema://contract/validation-input"
    with pytest.raises(ValidationError, match="immutable"):
        CapabilityPackManifest.model_validate(raw)

    raw = _manifest()
    spec = raw["spec"]
    assert isinstance(spec, dict)
    spec["module"] = "unsafe.py"
    with pytest.raises(ValidationError):
        CapabilityPackManifest.model_validate(raw)


def test_manifest_requires_all_references_to_resolve() -> None:
    manifest = CapabilityPackManifest.model_validate(_manifest())
    catalog = CapabilityReferenceCatalog.from_iterable(manifest.spec.references()[:-1])
    with pytest.raises(ValueError, match="CAPABILITY_REFERENCE_MISSING"):
        resolve_manifest(manifest, catalog)

    complete = CapabilityReferenceCatalog.from_iterable(manifest.spec.references())
    _, snapshot = resolve_manifest(manifest, complete)
    assert set(snapshot) == set(manifest.spec.references())
