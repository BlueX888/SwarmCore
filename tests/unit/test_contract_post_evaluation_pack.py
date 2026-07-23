from __future__ import annotations

from jsonschema import Draft202012Validator
from swarmcore_application import (
    CapabilityCatalogService,
    PostEvaluationPayload,
    StrategyService,
    evaluate_post_evaluation,
)
from swarmcore_application.post_evaluation import assemble_post_evaluation_payload
from swarmcore_capability_contract_post_evaluation import (
    MANIFEST,
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


def _payload() -> PostEvaluationPayload:
    return PostEvaluationPayload.model_validate(
        {
            "title": "供应合同年度后评价",
            "evaluationPeriod": {"start": "2026-01-01", "end": "2026-06-30"},
            "contract": {
                "contractId": "contract-001",
                "contractName": "设备供应合同",
                "contractAmount": 100,
                "actualCost": 105,
            },
            "documents": [
                {"documentId": "doc-1", "category": "合同", "status": "VALID"},
                {"documentId": "doc-2", "category": "验收单", "status": "MISSING"},
            ],
            "obligations": [
                {
                    "obligationId": "obligation-1",
                    "category": "交付",
                    "timeliness": "ON_TIME",
                    "quality": "ACCEPTED",
                },
                {
                    "obligationId": "obligation-2",
                    "category": "安装",
                    "timeliness": "LATE",
                    "quality": "REJECTED",
                },
            ],
            "deviations": [
                {
                    "deviationId": "deviation-1",
                    "category": "进度",
                    "severity": "HIGH",
                    "status": "OPEN",
                },
                {
                    "deviationId": "deviation-2",
                    "category": "内容",
                    "severity": "LOW",
                    "status": "CLOSED",
                },
            ],
            "invoices": [
                {
                    "invoiceId": "invoice-1",
                    "amount": 60,
                    "contractMatched": True,
                    "acceptanceMatched": True,
                    "taxValid": True,
                },
                {
                    "invoiceId": "invoice-2",
                    "amount": 40,
                    "contractMatched": True,
                    "acceptanceMatched": False,
                    "taxValid": True,
                },
            ],
            "risks": [
                {
                    "riskId": "risk-1",
                    "category": "供应",
                    "level": "HIGH",
                    "status": "OPEN",
                    "actionOverdue": True,
                },
                {
                    "riskId": "risk-2",
                    "category": "质量",
                    "level": "LOW",
                    "status": "CLOSED",
                },
            ],
        }
    )


def test_post_evaluation_pack_is_self_consistent_and_runnable() -> None:
    manifest, snapshot = resolve_manifest(
        MANIFEST, CapabilityReferenceCatalog.from_iterable(REFERENCES)
    )
    assert isinstance(manifest, CapabilityPackManifest)
    assert manifest.case_type == "contract-post-evaluation-case"
    assert set(snapshot) == set(manifest.spec.references())
    assert manifest.spec.resources == ()
    assert [(value.category, value.required) for value in manifest.spec.documents] == [
        ("CONTRACT", True)
    ]
    assert VIEW_DEFINITION["detail"]["sections"][2] == "seven-dimensions"
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)

    registry = builtin_registry()
    _, plan = StrategyService().compile(
        STRATEGIES[manifest.spec.strategies.execute],
        registry_snapshot=registry.snapshot_id,
        policy_revision="test",
    )
    assert {item["registryRef"] for item in plan.resolved_agents.values()} == {
        "agent://contract/post-evaluation-analyst@1"
    }
    assert set(plan.resolved_tools) == set(manifest.spec.tools)
    assemble_tool = next(
        item for item in registry.tools if item.ref == "tool://contract/post-evaluation/assemble@1"
    )
    assemble_output = assemble_tool.output_schema
    assert "evidenceAvailability" in assemble_output["properties"]
    assert STRATEGIES[manifest.spec.strategies.execute]["spec"]["graph"]["nodes"]["record"][
        "input"
    ]["report"] == "{{ tasks.report.output.content }}"

    catalog = CapabilityCatalogService((MANIFEST,)).get()
    assert [item.name for item in catalog.capability_packs] == ["contract-post-evaluation"]


def test_post_evaluation_generates_exactly_seven_deterministic_dimensions() -> None:
    result = evaluate_post_evaluation(_payload())

    assert [item.code for item in result.dimensions] == [
        "DOCUMENT_COMPLETENESS",
        "DELIVERY_TIMELINESS",
        "DELIVERY_QUALITY",
        "COST_CONTROL",
        "INVOICE_COMPLIANCE",
        "DEVIATION_GOVERNANCE",
        "RISK_GOVERNANCE",
    ]
    assert [item.score for item in result.dimensions] == [50, 75, 50, 75, 60, 41, 38]
    assert result.overall_score == 57.55
    assert result.grade == "不合格"
    assert result.risk_level == "CRITICAL"
    assert result.passed is False
    Draft202012Validator(SCHEMAS["schema://contract/post-evaluation-result@1"]).validate(
        result.model_dump(mode="json", by_alias=True)
    )


def test_post_evaluation_flags_missing_evidence_for_review() -> None:
    value = _payload().model_dump(mode="json", by_alias=True)
    value["documents"] = []
    value["obligations"] = []
    value["contract"]["actualCost"] = None

    result = evaluate_post_evaluation(PostEvaluationPayload.model_validate(value))

    assert result.review_required is True
    assert [item.status for item in result.dimensions[:4]] == [
        "DATA_INSUFFICIENT",
        "DATA_INSUFFICIENT",
        "DATA_INSUFFICIENT",
        "DATA_INSUFFICIENT",
    ]
    assert {item.code for item in result.findings} >= {"DATA_INSUFFICIENT"}


def test_post_evaluation_does_not_treat_unavailable_registers_as_perfect() -> None:
    payload = assemble_post_evaluation_payload(
        _payload().model_dump(mode="json", by_alias=True),
        [
            {
                "slot": "invoice-data",
                "data": {"invoices": [], "evidenceStatus": "NOT_PUBLICLY_AVAILABLE"},
            },
            {
                "slot": "deviation-data",
                "data": {"deviations": [], "evidenceStatus": "NOT_PUBLICLY_AVAILABLE"},
            },
            {
                "slot": "risk-data",
                "data": {"risks": [], "evidenceStatus": "NOT_PUBLICLY_AVAILABLE"},
            },
        ],
    )

    result = evaluate_post_evaluation(payload)
    dimensions = {item.code: item for item in result.dimensions}

    assert dimensions["INVOICE_COMPLIANCE"].status == "DATA_INSUFFICIENT"
    assert dimensions["DEVIATION_GOVERNANCE"].status == "DATA_INSUFFICIENT"
    assert dimensions["RISK_GOVERNANCE"].status == "DATA_INSUFFICIENT"
    assert result.overall_score == 38.75
    assert result.review_required is True
    assert result.passed is False
