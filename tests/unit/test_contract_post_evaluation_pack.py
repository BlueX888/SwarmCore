from __future__ import annotations

import json
from pathlib import Path

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

DEMO_PAYLOAD_PATH = (
    Path(__file__).parents[1] / "fixtures" / "business" / "report-generation-demo-payload.json"
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
    assert manifest.metadata.version == "2.0.7"
    assert manifest.spec.input_schema == "schema://contract/post-evaluation-input@4"
    assert manifest.case_type == "contract-post-evaluation-case"
    assert set(snapshot) == set(manifest.spec.references())
    assert manifest.spec.resources == ()
    assert [
        (value.category, value.required) for value in manifest.spec.document_requirements()
    ] == [
        ("CONTRACT", True),
        ("ACCEPTANCE", True),
        ("PERFORMANCE", False),
        ("INVOICE", False),
        ("DEVIATION", False),
        ("RISK", False),
        ("PROCUREMENT", False),
        ("SUPPLEMENTAL_FACTS", False),
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
        "agent://contract/baseline-analyst@2",
        "agent://contract/performance-quality-analyst@2",
        "agent://contract/finance-invoice-analyst@2",
        "agent://contract/deviation-risk-analyst@2",
        "agent://contract/evidence-reviewer@1",
        "agent://contract/performance-report-writer@1",
        "agent://contract/governance-report-writer@1",
        "agent://contract/report-narrator@2",
        "agent://contract/report-quality-reviewer@1",
    }
    assert len(plan.nodes) == 33
    assert plan.budget["maxParallelism"] == 4
    assert plan.budget["maxAgents"] == 9
    assert plan.budget["maxTokens"] == 750_000
    assert len(manifest.spec.tools) == 18
    assert set(plan.resolved_tools) == set(manifest.spec.tools)
    assemble_tool = next(
        item for item in registry.tools if item.ref == "tool://contract/post-evaluation/assemble@1"
    )
    assemble_output = assemble_tool.output_schema
    assert "evidenceAvailability" in assemble_output["properties"]
    strategy_nodes = STRATEGIES[manifest.spec.strategies.execute]["spec"]["graph"]["nodes"]
    expected_search_dependencies = {
        "coverage-check",
        "search-contract",
        "search-performance",
        "search-finance",
        "search-governance",
    }
    for node_key in (
        "analyze-baseline",
        "analyze-performance",
        "analyze-finance",
        "analyze-governance",
    ):
        assert set(strategy_nodes[node_key]["dependsOn"]) == expected_search_dependencies
    for node_key in (
        "search-contract",
        "search-performance",
        "search-finance",
        "search-governance",
    ):
        assert strategy_nodes[node_key]["input"]["maxHits"] == 6
    for node_key in (
        "analyze-baseline",
        "analyze-performance",
        "analyze-finance",
        "analyze-governance",
        "evidence-review",
        "write-performance-report",
        "write-governance-report",
        "report-narrative",
        "review-report-quality",
    ):
        assert strategy_nodes[node_key]["input"]["_contextMode"] == "node_only"
    assert strategy_nodes["record"]["input"]["report"] == "{{ tasks.report.output.content }}"
    assert strategy_nodes["report"]["tool"] == "tool://report/render-post-evaluation@4"
    assert (
        strategy_nodes["record"]["tool"]
        == "tool://workbench/record-post-evaluation@3"
    )
    assert strategy_nodes["quality-gate"]["input"]["modelReview"] == (
        "{{ tasks.review-report-quality.output.content }}"
    )
    assert strategy_nodes["review-router"]["default"] == "auto-continue"
    assert strategy_nodes["manual-review"]["type"] == "approval"
    assert strategy_nodes["merge-domains"]["input"]["upstreamEvaluations"] == (
        "{{ input.upstreamEvaluations }}"
    )
    assert strategy_nodes["finalize"]["input"]["provenance"][
        "upstreamEvaluations"
    ] == "{{ tasks.merge-domains.output.content.upstreamEvaluationRefs }}"

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


def test_report_generation_demo_payload_matches_agent_schema_and_scoring() -> None:
    value = json.loads(DEMO_PAYLOAD_PATH.read_text(encoding="utf-8"))
    analyst = next(
        item
        for item in builtin_registry().agents
        if item.ref == "agent://contract/post-evaluation-analyst@1"
    )

    Draft202012Validator(analyst.output_schema).validate(value)
    payload = PostEvaluationPayload.model_validate(value)
    result = evaluate_post_evaluation(payload)

    assert sum(item.document_id.startswith("PUBLIC-CORE:") for item in payload.documents) == 4
    assert (
        sum(item.document_id.startswith("DEMO-SUPPLEMENT:") for item in payload.documents)
        == 3
    )
    assert not any(
        item.document_id.startswith("CROSS-PROJECT-SAMPLE:")
        for item in payload.documents
    )
    assert all(
        item.invoice_id.startswith("DEMO-SUPPLEMENT:") for item in payload.invoices
    )
    assert all(
        item.deviation_id.startswith("DEMO-SUPPLEMENT:") for item in payload.deviations
    )
    assert all(item.risk_id.startswith("DEMO-SUPPLEMENT:") for item in payload.risks)
    assert payload.evidence_availability == {
        "contract-files": "PUBLIC_CORE_EVIDENCE",
        "performance-data": "MIXED_PUBLIC_AND_DEMO",
        "cost-data": "DEMO_SUPPLEMENT",
        "deviation-data": "DEMO_SUPPLEMENT",
        "invoice-data": "DEMO_SUPPLEMENT",
        "risk-data": "DEMO_SUPPLEMENT",
    }
    assert [item.score for item in result.dimensions] == [
        87.5,
        87.5,
        92.5,
        93.33,
        88.89,
        68.1,
        68.57,
    ]
    assert result.overall_score == 84.55
    assert result.grade == "良好"
    assert result.risk_level == "LOW"
    assert {item.dimension for item in result.findings} == {
        "DEVIATION_GOVERNANCE",
        "RISK_GOVERNANCE",
    }
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
