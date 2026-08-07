from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from swarmcore_application.cases import CaseService, CaseSubjectInput, _enrich_case_payload
from swarmcore_capability_document_structuring import MANIFEST
from swarmcore_registry import CapabilityPackManifest


def test_enrich_contract_performance_payload_injects_contract_object_id() -> None:
    contract_id = uuid4()
    subjects = [
        CaseSubjectInput(
            business_object_id=contract_id,
            business_object_version_id=uuid4(),
            role="PRIMARY",
            subject_key="contract",
        )
    ]
    payload = {
        "title": "合同履约计划与采集",
        "operation": "INITIALIZE",
        "currency": "CNY",
        "timezone": "Asia/Shanghai",
    }

    enriched = _enrich_case_payload("contract-performance-case", payload, subjects)

    assert enriched["contractObjectId"] == str(contract_id)
    assert enriched["operation"] == "INITIALIZE"


def test_enrich_keeps_explicit_contract_object_id() -> None:
    existing = str(uuid4())
    subjects = [
        CaseSubjectInput(
            business_object_id=uuid4(),
            business_object_version_id=uuid4(),
            role="PRIMARY",
            subject_key="contract",
        )
    ]

    enriched = _enrich_case_payload(
        "contract-performance-case",
        {"contractObjectId": existing, "currency": "CNY"},
        subjects,
    )

    assert enriched["contractObjectId"] == existing


def test_enrich_invoice_payload_materializes_optional_strategy_inputs() -> None:
    payload = {"title": "发票一致性校验"}
    subjects = [
        CaseSubjectInput(
            business_object_id=uuid4(),
            business_object_version_id=uuid4(),
            role="PRIMARY",
            subject_key="invoice",
        )
    ]

    enriched = _enrich_case_payload("invoice-assurance-case", payload, subjects)

    assert enriched == {
        "title": "发票一致性校验",
        "fieldConfirmations": [],
        "humanVerification": {},
        "enterprisePublicStatusEvidence": {},
    }
    assert payload == {"title": "发票一致性校验"}


def test_enrich_ignores_unrelated_scenario_types() -> None:
    payload = {"title": "采购合同检查"}

    assert _enrich_case_payload("contract-case", payload, []) is payload


@pytest.mark.asyncio
async def test_create_case_persists_business_work_identity_without_leaking_it_to_pack_lookup(
) -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    item = MagicMock(id=uuid4())
    revision = MagicMock(id=uuid4())
    packs = MagicMock()
    packs.resolve_enabled = AsyncMock(
        return_value=(
            MagicMock(),
            CapabilityPackManifest.model_validate(MANIFEST),
            MagicMock(),
        )
    )
    workbench = MagicMock()
    workbench.create_work_item = AsyncMock(return_value=(item, revision))
    session = MagicMock()
    session.scalars = AsyncMock(return_value=[])
    session.flush = AsyncMock()
    service = CaseService(workbench, packs)

    created_item, created_revision, subjects = await service.create(
        session,
        tenant_id=tenant_id,
        project_id=project_id,
        scenario_type="document-structuring-case",
        business_work_key="document-structuring",
        payload={"title": "OCR qualification"},
        subjects=[],
        owner="operator",
        idempotency_key="case-identity",
        actor="operator",
    )

    assert (created_item, created_revision, subjects) == (item, revision, [])
    packs.resolve_enabled.assert_awaited_once_with(
        session,
        tenant_id=tenant_id,
        project_id=project_id,
        work_item_type="document-structuring-case",
    )
    workbench.create_work_item.assert_awaited_once_with(
        session,
        tenant_id=tenant_id,
        project_id=project_id,
        work_item_type="document-structuring-case",
        business_work_key="document-structuring",
        payload={"title": "OCR qualification"},
        owner="operator",
        idempotency_key="case-identity",
        actor="operator",
    )
