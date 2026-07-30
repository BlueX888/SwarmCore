from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from swarmcore_application import (
    BUSINESS_WORK_DEFINITIONS,
    BusinessWorkService,
    CapabilityPackService,
    CaseService,
    document_binding_keys,
    pack_name_for_work_key,
    work_key_for_pack_name,
)
from swarmcore_capability_contract_integrity import MANIFEST, MANIFEST_V2_1, REFERENCES
from swarmcore_capability_contract_post_evaluation import MANIFEST as POST_EVALUATION_MANIFEST
from swarmcore_persistence.models import CapabilityPackVersion
from swarmcore_registry import CapabilityReferenceCatalog


class MissingCapabilities:
    async def list(self, **_: Any):
        return ()


def _version(manifest: dict[str, Any] | None = None) -> MagicMock:
    version = MagicMock(spec=CapabilityPackVersion)
    version.id = uuid4()
    version.pack_id = uuid4()
    version.version = str(manifest["metadata"]["version"]) if manifest else "1.0.0"
    version.manifest = manifest or MANIFEST
    version.content_hash = "a" * 64
    version.dependency_snapshot = {}
    return version


def _service() -> BusinessWorkService:
    packs = CapabilityPackService(CapabilityReferenceCatalog.from_iterable(REFERENCES))
    workbench = MagicMock()
    cases = MagicMock(spec=CaseService)
    documents = MagicMock()
    documents.current_versions_for_work = AsyncMock(return_value=[])
    return BusinessWorkService(packs, workbench, cases, documents=documents)


def test_central_mapping_covers_implemented_packs() -> None:
    assert pack_name_for_work_key("ai-foundation-quality") == "swarm-calibration"
    assert pack_name_for_work_key("document-integrity") == "contract-integrity"
    assert pack_name_for_work_key("contract-post-evaluation") == "contract-post-evaluation"
    assert pack_name_for_work_key("deviation-analysis") == "deviation-analysis"
    assert pack_name_for_work_key("invoice-assurance") == "invoice-assurance"
    assert pack_name_for_work_key("report-generation") == "contract-post-evaluation"
    assert work_key_for_pack_name("contract-integrity") == "document-integrity"
    assert work_key_for_pack_name("contract-post-evaluation") == "contract-post-evaluation"
    assert work_key_for_pack_name("deviation-analysis") == "deviation-analysis"
    assert work_key_for_pack_name("invoice-assurance") == "invoice-assurance"
    keys = document_binding_keys("contract-post-evaluation", "contract-post-evaluation-case")
    assert keys == ("contract-post-evaluation", "contract-post-evaluation-case")
    deviation_keys = document_binding_keys("deviation-analysis", "deviation-analysis-case")
    assert "performance-plan-collection" in deviation_keys
    assert "invoice-assurance" in deviation_keys
    invoice_keys = document_binding_keys("invoice-assurance", "invoice-assurance-case")
    assert invoice_keys == ("invoice-assurance", "invoice-assurance-case", "invoice-assurance")


@pytest.mark.asyncio
async def test_list_works_marks_unconfigured_and_maps_pack_status() -> None:
    service = _service()
    session = AsyncMock()
    pack = MagicMock()
    pack.name = "contract-integrity"
    version = _version(MANIFEST)
    binding = MagicMock()
    binding.status = "ENABLED"
    binding.configuration = {"threshold": 0.8}
    service._capability_packs.ensure_trusted = AsyncMock()  # type: ignore[method-assign]
    service._capability_packs.list_project = AsyncMock(  # type: ignore[method-assign]
        return_value=[(pack, version, binding)]
    )
    service._capability_packs.blockers_for_version = AsyncMock(return_value=[])  # type: ignore[method-assign]

    items = await service.list_works(session, tenant_id=uuid4(), project_id=uuid4())

    assert len(items) == len(BUSINESS_WORK_DEFINITIONS)
    by_key = {item.work_key: item for item in items}
    assert by_key["invoice-assurance"].status == "not_configured"
    assert by_key["report-generation"].status == "not_configured"
    assert by_key["document-integrity"].status == "runnable"
    assert by_key["document-integrity"].pack_name == "contract-integrity"
    assert by_key["document-integrity"].configuration == {"threshold": 0.8}
    assert by_key["contract-post-evaluation"].status == "not_configured"


@pytest.mark.asyncio
async def test_report_generation_reuses_runnable_post_evaluation_pack() -> None:
    service = _service()
    session = AsyncMock()
    pack = MagicMock()
    pack.name = "contract-post-evaluation"
    version = _version(POST_EVALUATION_MANIFEST)
    binding = MagicMock()
    binding.status = "ENABLED"
    binding.configuration = {}
    service._capability_packs.ensure_trusted = AsyncMock()  # type: ignore[method-assign]
    service._capability_packs.list_project = AsyncMock(  # type: ignore[method-assign]
        return_value=[(pack, version, binding)]
    )
    service._capability_packs.blockers_for_version = AsyncMock(return_value=[])  # type: ignore[method-assign]
    cast(AsyncMock, service._documents.current_versions_for_work).return_value = [
        (MagicMock(category="CONTRACT"), MagicMock(), MagicMock()),
        (MagicMock(category="ACCEPTANCE"), MagicMock(), MagicMock()),
    ]

    summary = await service.get_work(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        work_key="report-generation",
    )

    assert summary.status == "runnable"
    assert summary.pack_name == "contract-post-evaluation"
    assert summary.work_item_type == "contract-post-evaluation-case"
    assert summary.case_based is True


@pytest.mark.asyncio
async def test_business_work_exposes_decision_slot_contract() -> None:
    service = _service()
    session = AsyncMock()
    pack = MagicMock()
    pack.name = "contract-integrity"
    version = _version(MANIFEST_V2_1)
    binding = MagicMock()
    binding.status = "ENABLED"
    binding.configuration = {}
    service._capability_packs.ensure_trusted = AsyncMock()  # type: ignore[method-assign]
    service._capability_packs.list_project = AsyncMock(  # type: ignore[method-assign]
        return_value=[(pack, version, binding)]
    )
    service._capability_packs.blockers_for_version = AsyncMock(return_value=[])  # type: ignore[method-assign]
    cast(AsyncMock, service._documents.current_versions_for_work).return_value = [
        (MagicMock(category="CONTRACT"), MagicMock(), MagicMock())
    ]

    summary = await service.get_work(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        work_key="document-integrity",
    )

    assert summary.decision_slots == (
        {
            "slot": "document-checklist",
            "required": True,
            "inputSchema": "schema://contract/validation-input@2",
            "outputSchema": "schema://contract/validation-result@1",
            "allowedTypes": ["CHECKLIST", "DECISION_TABLE"],
        },
    )


@pytest.mark.asyncio
async def test_incomplete_when_document_bindings_missing() -> None:
    service = _service()
    session = AsyncMock()
    pack = MagicMock()
    pack.name = "contract-post-evaluation"
    version = _version(POST_EVALUATION_MANIFEST)
    binding = MagicMock()
    binding.status = "ENABLED"
    binding.configuration = {}
    service._capability_packs.ensure_trusted = AsyncMock()  # type: ignore[method-assign]
    service._capability_packs.list_project = AsyncMock(  # type: ignore[method-assign]
        return_value=[(pack, version, binding)]
    )
    service._capability_packs.blockers_for_version = AsyncMock(return_value=[])  # type: ignore[method-assign]
    cast(AsyncMock, service._documents.current_versions_for_work).return_value = []

    summary = await service.get_work(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        work_key="contract-post-evaluation",
    )

    assert summary.status == "incomplete"
    assert any(item.code == "DOCUMENT_BINDING_MISSING" for item in summary.blockers)


@pytest.mark.asyncio
async def test_disabled_pack_is_unavailable_and_blocks_new_assessment() -> None:
    service = _service()
    session = AsyncMock()
    pack = MagicMock()
    pack.name = "contract-integrity"
    version = _version(MANIFEST)
    binding = MagicMock()
    binding.status = "DISABLED"
    binding.configuration = {}
    service._capability_packs.ensure_trusted = AsyncMock()  # type: ignore[method-assign]
    service._capability_packs.list_project = AsyncMock(  # type: ignore[method-assign]
        return_value=[(pack, version, binding)]
    )
    service._capability_packs.blockers_for_version = AsyncMock(return_value=[])  # type: ignore[method-assign]

    summary = await service.get_work(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        work_key="document-integrity",
    )
    assert summary.status == "unavailable"

    with pytest.raises(ValueError, match="BUSINESS_WORK_UNAVAILABLE"):
        await service.start_assessment(
            session,
            tenant_id=uuid4(),
            project_id=uuid4(),
            work_key="document-integrity",
            case_id=uuid4(),
            idempotency_key="assess-1",
            actor="tester",
        )


@pytest.mark.asyncio
async def test_get_assessment_scopes_to_tenant_project() -> None:
    service = _service()
    session = AsyncMock()
    evaluation = MagicMock()
    evaluation.id = uuid4()
    evaluation.work_item_id = uuid4()
    evaluation.work_item_revision_id = uuid4()
    evaluation.tenant_id = uuid4()
    evaluation.project_id = uuid4()
    session.scalar = AsyncMock(side_effect=[evaluation, None, None])

    found, item, revision = await service.get_assessment(
        session,
        tenant_id=evaluation.tenant_id,
        project_id=evaluation.project_id,
        assessment_id=evaluation.id,
    )
    assert found is evaluation
    assert item is None
    assert revision is None
    assert session.scalar.await_count == 3


def test_next_pack_version_bumps_patch() -> None:
    assert BusinessWorkService._next_pack_version(["1.6.0", "1.5.9"]) == "1.6.1"
    assert BusinessWorkService._next_pack_version([]) == "0.0.1"


def test_select_pack_template_prefers_document_requirements() -> None:
    pack = MagicMock()
    pack.name = "contract-post-evaluation"
    legacy = _version(
        {
            **POST_EVALUATION_MANIFEST,
            "metadata": {**POST_EVALUATION_MANIFEST["metadata"], "version": "1.6.2"},
            "spec": {**POST_EVALUATION_MANIFEST["spec"], "documents": []},
        }
    )
    complete = _version(POST_EVALUATION_MANIFEST)
    enabled = MagicMock()
    enabled.status = "ENABLED"
    selected = BusinessWorkService._select_pack_template(
        [(pack, legacy, enabled), (pack, complete, None)]
    )
    assert selected is not None
    assert selected[1] is complete


def test_manifest_for_strategy_rewrites_execute_agents_and_tools() -> None:
    strategy_id = uuid4()
    manifest = BusinessWorkService._manifest_for_strategy(
        template=POST_EVALUATION_MANIFEST,
        pack_name="contract-post-evaluation",
        pack_version="1.6.1",
        strategy_id=strategy_id,
        strategy_version_number=8,
        agents=["agent://custom@1"],
        tools=["tool://custom@1"],
    )
    assert manifest["metadata"]["version"] == "1.6.1"
    assert manifest["spec"]["strategies"]["execute"] == f"strategy://project/{strategy_id}@8"
    assert manifest["spec"]["agents"] == ["agent://custom@1"]
    assert manifest["spec"]["tools"] == ["tool://custom@1"]
    assert manifest["spec"]["documents"] == POST_EVALUATION_MANIFEST["spec"]["documents"]


@pytest.mark.asyncio
async def test_bind_strategy_publishes_and_enables_new_pack_version() -> None:
    service = _service()
    session = AsyncMock()
    tenant_id = uuid4()
    project_id = uuid4()
    strategy_id = uuid4()
    strategy_version_id = uuid4()
    pack = MagicMock()
    pack.name = "contract-post-evaluation"
    template = _version(POST_EVALUATION_MANIFEST)
    template.dependency_snapshot = {"strategy": {"strategyVersionId": str(uuid4())}}
    binding = MagicMock()
    binding.status = "ENABLED"
    binding.configuration = {"timeoutSeconds": 30}
    binding.pack_version_id = template.id
    published = _version(
        {
            **POST_EVALUATION_MANIFEST,
            "metadata": {**POST_EVALUATION_MANIFEST["metadata"], "version": "2.0.6"},
        }
    )
    published.dependency_snapshot = {
        "strategy": {
            "strategyVersionId": str(strategy_version_id),
            "ref": f"strategy://project/{strategy_id}@8",
        }
    }

    strategy = MagicMock()
    strategy.id = strategy_id
    strategy.name = "后评价执行策略"
    strategy_version = MagicMock()
    strategy_version.id = strategy_version_id
    strategy_version.version = 8
    strategy_version.plan = {
        "resolved_agents": {"analyst": {"registryRef": "agent://contract/post-evaluation-analyst@1"}},
        "resolved_models": {},
        "resolved_tools": {
            "tool://document/read-versions@1": {},
            "tool://contract/post-evaluation@1": {},
            "tool://report/render-post-evaluation@1": {},
            "tool://workbench/record-post-evaluation@1": {},
        },
        "spec_hash": "s" * 64,
        "registry_snapshot": "registry",
    }
    strategy_version.plan_hash = "p" * 64

    service._capability_packs.ensure_trusted = AsyncMock()  # type: ignore[method-assign]
    service._capability_packs.list_project = AsyncMock(  # type: ignore[method-assign]
        side_effect=[
            [(pack, template, binding)],
            [(pack, published, binding)],
        ]
    )
    service._capability_packs.publish = AsyncMock(return_value=published)  # type: ignore[method-assign]
    service._capability_packs.enable = AsyncMock(return_value=binding)  # type: ignore[method-assign]
    service._capability_packs.blockers_for_version = AsyncMock(return_value=[])  # type: ignore[method-assign]
    cast(AsyncMock, service._documents.current_versions_for_work).return_value = [
        (MagicMock(category="CONTRACT"), MagicMock(), MagicMock()),
        (MagicMock(category="ACCEPTANCE"), MagicMock(), MagicMock()),
    ]

    result_row = MagicMock()
    result_row.one_or_none = MagicMock(return_value=(strategy_version, strategy))
    session.execute = AsyncMock(return_value=result_row)

    summary = await service.bind_strategy(
        session,
        tenant_id=tenant_id,
        project_id=project_id,
        work_key="contract-post-evaluation",
        strategy_version_id=strategy_version_id,
        idempotency_key="bind-1",
        actor="tester",
    )

    cast(AsyncMock, service._capability_packs.publish).assert_awaited_once()
    publish_kwargs = cast(AsyncMock, service._capability_packs.publish).await_args.kwargs
    assert publish_kwargs["strategy_version_id"] == strategy_version_id
    assert publish_kwargs["manifest"]["metadata"]["version"] == "2.0.7"
    assert (
        publish_kwargs["manifest"]["spec"]["strategies"]["execute"]
        == f"strategy://project/{strategy_id}@8"
    )
    cast(AsyncMock, service._capability_packs.enable).assert_awaited_once()
    assert cast(AsyncMock, service._capability_packs.enable).await_args.kwargs[
        "version_id"
    ] == published.id
    assert summary.bound_strategy_version_id == strategy_version_id
    assert summary.bound_strategy_name == "后评价执行策略"
    assert summary.bound_strategy_version == 8
    assert summary.status == "runnable"
