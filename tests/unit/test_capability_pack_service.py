from copy import deepcopy
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from swarmcore_application import (
    CapabilityCenterService,
    CapabilityPackDeleteError,
    CapabilityPackDependencyError,
    CapabilityPackReadinessError,
    CapabilityPackService,
)
from swarmcore_capability_contract_integrity import MANIFEST, REFERENCES, STRATEGIES
from swarmcore_capability_contract_performance import (
    MANIFEST as CONTRACT_PERFORMANCE_MANIFEST,
)
from swarmcore_capability_contract_performance import (
    REFERENCES as CONTRACT_PERFORMANCE_REFERENCES,
)
from swarmcore_capability_contract_performance import (
    STRATEGIES as CONTRACT_PERFORMANCE_STRATEGIES,
)
from swarmcore_capability_contract_post_evaluation import MANIFEST as POST_EVALUATION_MANIFEST
from swarmcore_persistence.models import CapabilityPackVersion
from swarmcore_registry import CapabilityReferenceCatalog


class MissingCapabilities:
    async def list(self, **_: Any):
        return ()


class TrackingCapabilities:
    def __init__(self, items: tuple[Any, ...] = ()) -> None:
        self.items = items
        self.kwargs: dict[str, Any] | None = None

    async def list(self, **kwargs: Any):
        self.kwargs = kwargs
        return self.items


def _ready_summary(ref: str) -> MagicMock:
    readiness = MagicMock()
    readiness.status.value = "READY"
    readiness.reasons = ()
    summary = MagicMock()
    summary.ref = ref
    summary.readiness = readiness
    return summary


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
    assert "project_capability_bindings.pack_version_id = capability_pack_versions.id" in sql
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
async def test_document_requirements_do_not_require_legacy_resource_bindings() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(()))
    version = _version()
    version.manifest = POST_EVALUATION_MANIFEST
    session = MagicMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()

    blockers = await service.blockers_for_version(
        tenant_id=uuid4(), project_id=uuid4(), version=version, session=session
    )

    session.scalar.assert_not_awaited()
    session.scalars.assert_not_awaited()
    assert not any(item["reasons"] == ["RESOURCE_BINDING_MISSING"] for item in blockers)


@pytest.mark.asyncio
async def test_blockers_for_version_forwards_session_to_capability_center() -> None:
    tracker = TrackingCapabilities()
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(REFERENCES))
    service.attach_readiness(
        cast(CapabilityCenterService, tracker), environment="development"
    )
    session = MagicMock()
    tenant_id = uuid4()
    project_id = uuid4()

    await service.blockers_for_version(
        tenant_id=tenant_id,
        project_id=project_id,
        version=_version(),
        session=session,
    )

    assert tracker.kwargs is not None
    assert tracker.kwargs["session"] is session
    assert tracker.kwargs["tenant_id"] == tenant_id
    assert tracker.kwargs["project_id"] == project_id
    assert tracker.kwargs["environment"] == "development"


@pytest.mark.asyncio
async def test_blockers_for_version_clears_when_session_scoped_readiness_is_ready() -> None:
    required = (*MANIFEST["spec"]["agents"], *MANIFEST["spec"]["tools"])
    tracker = TrackingCapabilities(tuple(_ready_summary(ref) for ref in required))
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(REFERENCES))
    service.attach_readiness(
        cast(CapabilityCenterService, tracker), environment="development"
    )

    blockers = await service.blockers_for_version(
        tenant_id=uuid4(),
        project_id=uuid4(),
        version=_version(),
        session=MagicMock(),
    )

    assert blockers == []
    assert tracker.kwargs is not None
    assert tracker.kwargs["session"] is not None


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
async def test_publish_freezes_every_operation_strategy_and_dependency_union() -> None:
    service = CapabilityPackService(
        CapabilityReferenceCatalog.from_iterable(CONTRACT_PERFORMANCE_REFERENCES),
        trusted_strategies=CONTRACT_PERFORMANCE_STRATEGIES,
    )
    initialize_version = MagicMock(id=uuid4())
    collect_version = MagicMock(id=uuid4())
    ensure = AsyncMock(side_effect=[initialize_version, collect_version])
    service._strategies.ensure_trusted_version = ensure  # type: ignore[method-assign]
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[None, None])
    session.flush = AsyncMock()

    saved = await service.publish(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        manifest=CONTRACT_PERFORMANCE_MANIFEST,
        actor="test",
    )

    assert saved.dependency_snapshot["strategy"]["ref"] == (
        "strategy://contract-performance/initialize@13"
    )
    assert saved.dependency_snapshot["strategies"]["INITIALIZE"]["strategyVersionId"] == str(
        initialize_version.id
    )
    assert saved.dependency_snapshot["strategies"]["COLLECT"]["strategyVersionId"] == str(
        collect_version.id
    )
    assert [call.kwargs["reference"] for call in ensure.await_args_list] == [
        "strategy://contract-performance/initialize@13",
        "strategy://contract-performance/collect@10",
    ]


@pytest.mark.asyncio
async def test_publish_binds_an_existing_published_strategy_version() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(REFERENCES))
    manifest = deepcopy(MANIFEST)
    manifest["metadata"] = {"name": "custom-contract-review", "version": "1.0.0"}
    manifest["spec"]["strategies"] = {"execute": "strategy://project/strategy-id@2"}
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
    assert saved.dependency_snapshot["strategy"]["ref"] == ("strategy://project/strategy-id@2")
    assert saved.dependency_snapshot["strategy"]["strategyVersionId"] == str(selected.id)
    added_types = {type(call.args[0]).__name__ for call in session.add.call_args_list}
    assert "CapabilityPackVersion" in added_types
    assert "StrategyVersion" not in added_types


@pytest.mark.asyncio
async def test_delete_version_rejects_missing_version() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(()))
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[uuid4(), None])

    with pytest.raises(LookupError, match="能力包版本不存在或已被删除"):
        await service.delete_version(
            session,
            tenant_id=uuid4(),
            project_id=uuid4(),
            version_id=uuid4(),
            actor="test",
        )


@pytest.mark.asyncio
async def test_delete_version_rejects_enabled_binding() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(()))
    version = _version()
    pack = MagicMock()
    pack.id = version.pack_id
    pack.name = "custom-pack"
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[uuid4(), version, pack, uuid4(), None])
    session.execute = AsyncMock()
    session.flush = AsyncMock()

    with pytest.raises(CapabilityPackDeleteError) as captured:
        await service.delete_version(
            session,
            tenant_id=uuid4(),
            project_id=uuid4(),
            version_id=version.id,
            actor="test",
        )

    assert captured.value.code == "CAPABILITY_PACK_ENABLED"
    session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_version_rejects_historical_evaluations() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(()))
    version = _version()
    pack = MagicMock()
    pack.id = version.pack_id
    pack.name = "custom-pack"
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[uuid4(), version, pack, None, uuid4()])
    session.execute = AsyncMock()
    session.flush = AsyncMock()

    with pytest.raises(CapabilityPackDeleteError) as captured:
        await service.delete_version(
            session,
            tenant_id=uuid4(),
            project_id=uuid4(),
            version_id=version.id,
            actor="test",
        )

    assert captured.value.code == "CAPABILITY_PACK_HAS_EVALUATIONS"
    session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_version_allows_unused_trusted_manifest() -> None:
    service = CapabilityPackService(
        CapabilityReferenceCatalog.from_iterable(()),
        trusted_manifests=(MANIFEST,),
    )
    version = _version()
    metadata = MANIFEST["metadata"]
    assert isinstance(metadata, dict)
    version.version = str(metadata["version"])
    pack = MagicMock()
    pack.id = version.pack_id
    pack.name = str(metadata["name"])
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[uuid4(), version, pack, None, None, 0, pack])
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()

    await service.delete_version(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        version_id=version.id,
        actor="test",
    )

    assert session.delete.await_count == 2
    assert session.delete.await_args_list[0].args[0] is version


def test_deletion_blocker_prioritizes_enabled_over_evaluations() -> None:
    service = CapabilityPackService(
        CapabilityReferenceCatalog.from_iterable(()),
        trusted_manifests=(MANIFEST,),
    )
    metadata = MANIFEST["metadata"]
    assert isinstance(metadata, dict)

    blocker = service.deletion_blocker(
        pack_name=str(metadata["name"]),
        version=str(metadata["version"]),
        enabled=True,
        has_evaluations=True,
    )

    assert blocker == (
        "CAPABILITY_PACK_ENABLED",
        "能力包版本仍处于启用状态。请先停用后再删除。",
    )


@pytest.mark.asyncio
async def test_ensure_trusted_skips_deleted_manifest_versions() -> None:
    service = CapabilityPackService(
        CapabilityReferenceCatalog.from_iterable(()),
        trusted_manifests=(MANIFEST,),
    )
    metadata = MANIFEST["metadata"]
    assert isinstance(metadata, dict)
    session = MagicMock()
    session.scalar = AsyncMock(return_value=uuid4())
    existing_rows = MagicMock()
    existing_rows.tuples.return_value = []
    deleted_rows = MagicMock()
    deleted_rows.__iter__.return_value = iter([
        ({"name": metadata["name"], "version": metadata["version"]},)
    ])
    session.execute = AsyncMock(side_effect=[existing_rows, deleted_rows])
    service.publish = AsyncMock()  # type: ignore[method-assign]

    published = await service.ensure_trusted(
        session, tenant_id=uuid4(), project_id=uuid4()
    )

    assert published == []
    service.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_trusted_batches_existing_versions_and_publishes_only_missing() -> None:
    missing_manifest = deepcopy(MANIFEST)
    missing_metadata = missing_manifest["metadata"]
    assert isinstance(missing_metadata, dict)
    missing_metadata["version"] = "9.9.9"
    service = CapabilityPackService(
        CapabilityReferenceCatalog.from_iterable(()),
        trusted_manifests=(MANIFEST, missing_manifest),
    )
    metadata = MANIFEST["metadata"]
    assert isinstance(metadata, dict)
    existing_version = _version()
    session = MagicMock()
    session.scalar = AsyncMock(return_value=uuid4())
    existing_rows = MagicMock()
    existing_rows.tuples.return_value = [
        (metadata["name"], metadata["version"], existing_version)
    ]
    deleted_rows = MagicMock()
    deleted_rows.__iter__.return_value = iter([])
    session.execute = AsyncMock(side_effect=[existing_rows, deleted_rows])
    missing_version = _version()
    missing_version.version = "9.9.9"
    service.publish = AsyncMock(return_value=missing_version)  # type: ignore[method-assign]

    published = await service.ensure_trusted(
        session, tenant_id=uuid4(), project_id=uuid4()
    )

    assert published == [existing_version, missing_version]
    service.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_version_removes_unused_version_and_empty_pack() -> None:
    service = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(()))
    version = _version()
    version.version = "9.9.9"
    pack = MagicMock()
    pack.id = version.pack_id
    pack.name = "custom-pack"
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[uuid4(), version, pack, None, None, 0, pack])
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()

    await service.delete_version(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        version_id=version.id,
        actor="test",
    )

    assert session.execute.await_count >= 2
    allow_sql = str(session.execute.await_args_list[1].args[0])
    assert "app.allow_capability_pack_version_delete" in allow_sql
    assert session.delete.await_count == 2
    assert session.delete.await_args_list[0].args[0] is version
    assert session.delete.await_args_list[1].args[0] is pack
