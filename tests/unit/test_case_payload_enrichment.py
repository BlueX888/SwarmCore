from uuid import uuid4

from swarmcore_application.cases import CaseSubjectInput, _enrich_case_payload


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


def test_enrich_ignores_unrelated_scenario_types() -> None:
    payload = {"title": "发票一致性校验"}
    subjects = [
        CaseSubjectInput(
            business_object_id=uuid4(),
            business_object_version_id=uuid4(),
            role="PRIMARY",
            subject_key="invoice",
        )
    ]

    assert _enrich_case_payload("invoice-assurance-case", payload, subjects) is payload
