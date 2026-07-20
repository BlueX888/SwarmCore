from copy import deepcopy
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from swarmcore_application import (
    CapabilityCenterService,
    CapabilityPackDependencyError,
    CapabilityPackReadinessError,
    CapabilityPackService,
)
from swarmcore_capability_contract_integrity import MANIFEST, REFERENCES, STRATEGIES
from swarmcore_persistence.models import CapabilityPackVersion
from swarmcore_registry import CapabilityReferenceCatalog


class MissingCapabilities:
    async def list(self, **_: Any):
        return ()


def _version() -> MagicMock:
    version = MagicMock(spec=CapabilityPackVersion)
    version.id = uuid4()
    version.pack_id = uuid4()
    version.manifest = MANIFEST
    version.content_hash = "a" * 64
    return version


@pytest.mark.asyncio
async def test_list_project_matches_binding_to_the_bound_version() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(()))
    session = AsyncMock()
    result = MagicMock()
    result.tuples.return_value = []
    session.execute.return_value = result

    await service.list_project(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
    )

    statement = session.execute.await_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert (
        "project_capability_bindings.pack_version_id = capability_pack_versions.id" in sql
    )
    assert "project_capability_bindings.tenant_id" in sql
    assert "project_capability_bindings.project_id" in sql


@pytest.mark.asyncio
async def test_enable_rejects_every_missing_runtime_dependency_before_binding() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(REFERENCES))
    service.attach_readiness(
        cast(CapabilityCenterService, MissingCapabilities()), environment="development"
    )
    session = MagicMock()
    session.scalar = AsyncMock(return_value=_version())
    session.get = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    with pytest.raises(CapabilityPackReadinessError) as captured:
        await service.enable(
            session,
            tenant_id=uuid4(),
            project_id=uuid4(),
            version_id=uuid4(),
            configuration={},
            idempotency_key="enable",
            actor="test",
        )

    expected = {
        *MANIFEST["spec"]["agents"],
        *MANIFEST["spec"]["tools"],
    }
    assert {item["ref"] for item in captured.value.blockers} == expected
    assert all(item["reasons"] == ["DEPENDENCY_NOT_READY"] for item in captured.value.blockers)
    added_types = {type(call.args[0]).__name__ for call in session.add.call_args_list}
    assert "ProjectCapabilityBinding" not in added_types


@pytest.mark.asyncio
async def test_enabled_pack_is_marked_degraded_without_switching_version() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(REFERENCES))
    service.attach_readiness(
        cast(CapabilityCenterService, MissingCapabilities()), environment="development"
    )
    version = _version()
    binding = MagicMock()
    binding.status = "ENABLED"
    binding.pack_version_id = version.id
    pack = MagicMock()
    result = MagicMock()
    result.tuples.return_value = [(pack, version, binding)]
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    session.flush = AsyncMock()

    await service.list_project(session, tenant_id=uuid4(), project_id=uuid4())

    assert binding.status == "DEGRADED"
    assert binding.pack_version_id == version.id


@pytest.mark.asyncio
async def test_publish_rejects_manifest_dependencies_that_differ_from_strategy_plan() -> None:
    service = CapabilityPackService(
        CapabilityReferenceCatalog.from_iterable(REFERENCES),
        trusted_strategies=STRATEGIES,
    )
    invalid_manifest = deepcopy(MANIFEST)
    invalid_manifest["spec"]["tools"].remove("tool://report/render@1")

    with pytest.raises(CapabilityPackDependencyError) as captured:
        await service.publish(
            AsyncMock(),
            tenant_id=uuid4(),
            project_id=uuid4(),
            manifest=invalid_manifest,
            actor="test",
        )

    assert captured.value.actual_tools == set(MANIFEST["spec"]["tools"])
    assert captured.value.declared_tools == set(invalid_manifest["spec"]["tools"])


@pytest.mark.asyncio
async def test_publish_binds_an_existing_published_strategy_version() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(REFERENCES))
    manifest = deepcopy(MANIFEST)
    manifest["metadata"] = {"name": "custom-contract-review", "version": "1.0.0"}
    manifest["spec"]["strategies"] = {
        "execute": "strategy://project/strategy-id@2"
    }
    manifest["spec"]["events"] = {"namespace": "capability.custom-contract-review"}
    selected = MagicMock()
    selected.id = uuid4()
    selected.version = 2
    selected.plan_hash = "b" * 64
    selected.plan = {
        "spec_hash": "a" * 64,
        "registry_snapshot": "registry",
        "resolved_agents": {
            "classify": {"registryRef": "agent://contract/document-classifier@1"},
            "extract": {"registryRef": "agent://contract/field-extractor@1"},
        },
        "resolved_models": {},
        "resolved_tools": {reference: {} for reference in MANIFEST["spec"]["tools"]},
    }
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[selected, None, None])
    session.flush = AsyncMock()

    saved = await service.publish(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        manifest=manifest,
        strategy_version_id=selected.id,
        actor="test",
    )

    assert saved.manifest["metadata"] == {
        "name": "custom-contract-review",
        "version": "1.0.0",
    }
    assert saved.dependency_snapshot["strategy"]["ref"] == (
        "strategy://project/strategy-id@2"
    )
    assert saved.dependency_snapshot["strategy"]["strategyVersionId"] == str(selected.id)
    added_types = {type(call.args[0]).__name__ for call in session.add.call_args_list}
    assert "CapabilityPackVersion" in added_types
    assert "StrategyVersion" not in added_types
