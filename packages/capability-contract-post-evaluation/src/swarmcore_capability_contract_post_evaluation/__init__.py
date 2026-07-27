from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files
from typing import Any


def _load(name: str) -> dict[str, Any]:
    value = json.loads(files(__package__).joinpath(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"capability asset must be an object: {name}")
    return value


LEGACY_MANIFEST = _load("manifest.json")
MANIFEST_V2_0 = _load("manifest-v2.json")
SCHEMAS = {
    "schema://contract/post-evaluation-case@1": _load("case.schema.json"),
    "schema://contract/post-evaluation-input@2": _load("input.schema.json"),
    "schema://contract/post-evaluation-input@3": _load("input-v3.schema.json"),
    "schema://contract/post-evaluation-result@1": _load("output.schema.json"),
    "schema://contract/post-evaluation-result@2": _load("output-v2.schema.json"),
    "schema://contract/post-evaluation-result@3": _load("output-v3.schema.json"),
    "schema://contract/evidence-fact@1": _load("evidence-fact.schema.json"),
    "schema://contract/domain-analysis@1": _load("domain-analysis.schema.json"),
}
VIEW_DEFINITION = _load("view-definition.json")
_STRATEGY_V8 = _load("strategy-v8.json")
_STRATEGY_V9 = deepcopy(_STRATEGY_V8)
_STRATEGY_V9["metadata"]["name"] = "contract-post-evaluation-generate-v9"
for _agent in ("baseline", "performance", "finance", "governance"):
    _ref = str(_STRATEGY_V9["spec"]["agents"][_agent]["ref"])
    _STRATEGY_V9["spec"]["agents"][_agent]["ref"] = f"{_ref.rsplit('@', 1)[0]}@2"
for _node in _STRATEGY_V9["spec"]["graph"]["nodes"].values():
    _input = _node.get("input")
    if not isinstance(_input, dict):
        continue
    _provenance = _input.get("provenance")
    if not isinstance(_provenance, dict):
        continue
    _agents = _provenance.get("agents")
    if isinstance(_agents, list):
        _provenance["agents"] = [
            f"{value.rsplit('@', 1)[0]}@2"
            if any(
                name in value
                for name in (
                    "baseline-analyst",
                    "performance-quality-analyst",
                    "finance-invoice-analyst",
                    "deviation-risk-analyst",
                )
            )
            else value
            for value in _agents
        ]
_STRATEGY_V10 = deepcopy(_STRATEGY_V9)
_STRATEGY_V10["metadata"]["name"] = "contract-post-evaluation-generate-v10"
_STRATEGY_V10["spec"]["budget"]["maxTokens"] = 240_000
_DOMAIN_SEARCH_DEPENDENCIES = [
    "coverage-check",
    "search-contract",
    "search-performance",
    "search-finance",
    "search-governance",
]
for _node_key in (
    "analyze-baseline",
    "analyze-performance",
    "analyze-finance",
    "analyze-governance",
):
    _STRATEGY_V10["spec"]["graph"]["nodes"][_node_key]["dependsOn"] = list(
        _DOMAIN_SEARCH_DEPENDENCIES
    )
_STRATEGY_V11 = deepcopy(_STRATEGY_V10)
_STRATEGY_V11["metadata"]["name"] = "contract-post-evaluation-generate-v11"
_STRATEGY_V11["spec"]["budget"]["maxTokens"] = 500_000
for _node_key in (
    "search-contract",
    "search-performance",
    "search-finance",
    "search-governance",
):
    _STRATEGY_V11["spec"]["graph"]["nodes"][_node_key]["input"]["maxHits"] = 6
_STRATEGY_V12 = deepcopy(_STRATEGY_V11)
_STRATEGY_V12["metadata"]["name"] = "contract-post-evaluation-generate-v12"
for _node_key in (
    "analyze-baseline",
    "analyze-performance",
    "analyze-finance",
    "analyze-governance",
    "evidence-review",
    "report-narrative",
):
    _STRATEGY_V12["spec"]["graph"]["nodes"][_node_key]["input"]["_contextMode"] = (
        "node_only"
    )
_STRATEGY_V13 = deepcopy(_STRATEGY_V12)
_STRATEGY_V13["metadata"]["name"] = "contract-post-evaluation-generate-v13"
_STRATEGY_V13["spec"]["graph"]["nodes"]["report"]["tool"] = (
    "tool://report/render-post-evaluation@3"
)
_STRATEGY_V14 = deepcopy(_STRATEGY_V13)
_STRATEGY_V14["metadata"]["name"] = "contract-post-evaluation-generate-v14"
_STRATEGY_V14["spec"]["budget"]["maxAgents"] = 9
_STRATEGY_V14["spec"]["budget"]["maxTokens"] = 750_000
_STRATEGY_V14["spec"]["agents"]["narrator"]["ref"] = (
    "agent://contract/report-narrator@2"
)
_STRATEGY_V14["spec"]["agents"].update(
    {
        "performance_writer": {
            "ref": "agent://contract/performance-report-writer@1"
        },
        "governance_writer": {
            "ref": "agent://contract/governance-report-writer@1"
        },
        "quality_reviewer": {
            "ref": "agent://contract/report-quality-reviewer@1"
        },
    }
)
_V14_NODES = _STRATEGY_V14["spec"]["graph"]["nodes"]
_V14_NODES["readability-gate"] = {
    "type": "tool",
    "tool": "tool://document/readability-gate@1",
    "dependsOn": ["coverage-check"],
    "input": {
        "coverage": "{{ tasks.coverage-check.output.content }}",
        "formalThreshold": 0.8,
    },
}
_V14_NODES["write-performance-report"] = {
    "type": "agent",
    "agent": "performance_writer",
    "dependsOn": [
        "evaluate",
        "readability-gate",
        "timeline-check",
    ],
    "input": {
        "result": "{{ tasks.evaluate.output.content }}",
        "diagnostics": {
            "timeline": "{{ tasks.timeline-check.output.content }}",
        },
        "readability": "{{ tasks.readability-gate.output.content }}",
        "_contextMode": "node_only",
    },
}
_V14_NODES["write-governance-report"] = {
    "type": "agent",
    "agent": "governance_writer",
    "dependsOn": [
        "evaluate",
        "readability-gate",
        "amount-check",
        "invoice-check",
        "deviation-check",
        "risk-check",
    ],
    "input": {
        "result": "{{ tasks.evaluate.output.content }}",
        "diagnostics": {
            "amounts": "{{ tasks.amount-check.output.content }}",
            "invoices": "{{ tasks.invoice-check.output.content }}",
            "deviations": "{{ tasks.deviation-check.output.content }}",
            "risks": "{{ tasks.risk-check.output.content }}",
        },
        "readability": "{{ tasks.readability-gate.output.content }}",
        "_contextMode": "node_only",
    },
}
_V14_NODES["report-narrative"]["agent"] = "narrator"
_V14_NODES["report-narrative"]["dependsOn"].extend(
    ["write-performance-report", "write-governance-report", "readability-gate"]
)
_V14_NODES["report-narrative"]["input"].update(
    {
        "sectionDrafts": {
            "performance": "{{ tasks.write-performance-report.output.content }}",
            "governance": "{{ tasks.write-governance-report.output.content }}",
        },
        "readability": "{{ tasks.readability-gate.output.content }}",
        "_contextMode": "node_only",
    }
)
_V14_PROVENANCE_AGENTS = [
    "agent://contract/baseline-analyst@2",
    "agent://contract/performance-quality-analyst@2",
    "agent://contract/finance-invoice-analyst@2",
    "agent://contract/deviation-risk-analyst@2",
    "agent://contract/evidence-reviewer@1",
    "agent://contract/performance-report-writer@1",
    "agent://contract/governance-report-writer@1",
    "agent://contract/report-narrator@2",
    "agent://contract/report-quality-reviewer@1",
]
_V14_NODES["finalize"]["input"]["provenance"]["agents"] = list(
    _V14_PROVENANCE_AGENTS
)
_V14_NODES["compose-report"] = {
    "type": "tool",
    "tool": "tool://report/compose-post-evaluation@1",
    "dependsOn": [
        "finalize",
        "readability-gate",
        "write-performance-report",
        "write-governance-report",
        "manual-review",
        "auto-continue",
    ],
    "input": {
        "title": "{{ input.payload.title }}",
        "result": "{{ tasks.finalize.output.content }}",
        "readability": "{{ tasks.readability-gate.output.content }}",
        "sectionDrafts": {
            "performance": "{{ tasks.write-performance-report.output.content }}",
            "governance": "{{ tasks.write-governance-report.output.content }}",
        },
        "editorial": "{{ tasks.report-narrative.output.content }}",
        "review": "{{ tasks.evidence-review.output.content }}",
        "coverage": "{{ tasks.coverage-check.output.content }}",
        "consistency": "{{ tasks.consistency-check.output.content }}",
        "diagnostics": {
            "timeline": "{{ tasks.timeline-check.output.content }}",
            "amounts": "{{ tasks.amount-check.output.content }}",
            "invoices": "{{ tasks.invoice-check.output.content }}",
            "deviations": "{{ tasks.deviation-check.output.content }}",
            "risks": "{{ tasks.risk-check.output.content }}",
        },
        "approval": "{{ tasks.manual-review.output }}",
    },
}
_V14_NODES["verify-report-citations"] = {
    "type": "tool",
    "tool": "tool://report/verify-post-evaluation-citations@1",
    "dependsOn": ["compose-report", "finalize"],
    "input": {
        "reportDocument": "{{ tasks.compose-report.output.content }}",
        "sourceResult": "{{ tasks.finalize.output.content }}",
    },
}
_V14_NODES["review-report-quality"] = {
    "type": "agent",
    "agent": "quality_reviewer",
    "dependsOn": [
        "compose-report",
        "verify-report-citations",
        "readability-gate",
    ],
    "input": {
        "reportDocument": "{{ tasks.compose-report.output.content }}",
        "sourceResult": "{{ tasks.finalize.output.content }}",
        "citationCheck": "{{ tasks.verify-report-citations.output.content }}",
        "readability": "{{ tasks.readability-gate.output.content }}",
        "_contextMode": "node_only",
    },
}
_V14_NODES["quality-gate"] = {
    "type": "tool",
    "tool": "tool://report/check-post-evaluation-quality@1",
    "dependsOn": [
        "finalize",
        "compose-report",
        "verify-report-citations",
        "review-report-quality",
        "readability-gate",
    ],
    "input": {
        "sourceResult": "{{ tasks.finalize.output.content }}",
        "reportDocument": "{{ tasks.compose-report.output.content }}",
        "citationCheck": "{{ tasks.verify-report-citations.output.content }}",
        "modelReview": "{{ tasks.review-report-quality.output.content }}",
        "readability": "{{ tasks.readability-gate.output.content }}",
    },
}
_V14_NODES["report"] = {
    "type": "tool",
    "tool": "tool://report/render-post-evaluation@4",
    "dependsOn": ["quality-gate"],
    "input": {"result": "{{ tasks.quality-gate.output.content }}"},
}
_V14_NODES["record"] = {
    "type": "tool",
    "tool": "tool://workbench/record-post-evaluation@3",
    "dependsOn": ["quality-gate", "report"],
    "input": {
        "evaluationId": "{{ input.evaluationId }}",
        "result": "{{ tasks.quality-gate.output.content }}",
        "report": "{{ tasks.report.output.content }}",
    },
}
_STRATEGY_V14["spec"]["graph"]["output"] = {
    "result": "{{ tasks.quality-gate.output.content }}"
}
STRATEGIES = {
    "strategy://contract-post-evaluation/generate@7": _load("strategy.json"),
    "strategy://contract-post-evaluation/generate@8": _STRATEGY_V8,
    "strategy://contract-post-evaluation/generate@9": _STRATEGY_V9,
    "strategy://contract-post-evaluation/generate@10": _STRATEGY_V10,
    "strategy://contract-post-evaluation/generate@11": _STRATEGY_V11,
    "strategy://contract-post-evaluation/generate@12": _STRATEGY_V12,
    "strategy://contract-post-evaluation/generate@13": _STRATEGY_V13,
    "strategy://contract-post-evaluation/generate@14": _STRATEGY_V14,
}
MANIFEST_V2_1 = deepcopy(MANIFEST_V2_0)
MANIFEST_V2_1["metadata"]["version"] = "2.0.1"
MANIFEST_V2_1["spec"]["strategies"]["execute"] = (
    "strategy://contract-post-evaluation/generate@9"
)
MANIFEST_V2_1["spec"]["agents"] = [
    f"{value.rsplit('@', 1)[0]}@2"
    if any(
        name in value
        for name in (
            "baseline-analyst",
            "performance-quality-analyst",
            "finance-invoice-analyst",
            "deviation-risk-analyst",
        )
    )
    else value
    for value in MANIFEST_V2_1["spec"]["agents"]
]
MANIFEST_V2_2 = deepcopy(MANIFEST_V2_1)
MANIFEST_V2_2["metadata"]["version"] = "2.0.2"
MANIFEST_V2_2["spec"]["strategies"]["execute"] = (
    "strategy://contract-post-evaluation/generate@10"
)
MANIFEST_V2_3 = deepcopy(MANIFEST_V2_2)
MANIFEST_V2_3["metadata"]["version"] = "2.0.3"
MANIFEST_V2_3["spec"]["strategies"]["execute"] = (
    "strategy://contract-post-evaluation/generate@11"
)
MANIFEST_V2_4 = deepcopy(MANIFEST_V2_3)
MANIFEST_V2_4["metadata"]["version"] = "2.0.4"
MANIFEST_V2_4["spec"]["strategies"]["execute"] = (
    "strategy://contract-post-evaluation/generate@12"
)
MANIFEST_V2_5 = deepcopy(MANIFEST_V2_4)
MANIFEST_V2_5["metadata"]["version"] = "2.0.5"
MANIFEST_V2_5["spec"]["strategies"]["execute"] = (
    "strategy://contract-post-evaluation/generate@13"
)
MANIFEST_V2_5["spec"]["tools"] = [
    "tool://report/render-post-evaluation@3"
    if value == "tool://report/render-post-evaluation@2"
    else value
    for value in MANIFEST_V2_5["spec"]["tools"]
]
MANIFEST = deepcopy(MANIFEST_V2_5)
MANIFEST["metadata"]["version"] = "2.0.6"
MANIFEST["spec"]["outputSchema"] = "schema://contract/post-evaluation-result@3"
MANIFEST["spec"]["strategies"]["execute"] = "strategy://contract-post-evaluation/generate@14"
MANIFEST["spec"]["agents"] = list(_V14_PROVENANCE_AGENTS)
MANIFEST["spec"]["tools"] = [
    "tool://report/render-post-evaluation@4"
    if value == "tool://report/render-post-evaluation@3"
    else "tool://workbench/record-post-evaluation@3"
    if value == "tool://workbench/record-post-evaluation@2"
    else value
    for value in MANIFEST["spec"]["tools"]
]
MANIFEST["spec"]["tools"].extend(
    [
        "tool://document/readability-gate@1",
        "tool://report/compose-post-evaluation@1",
        "tool://report/verify-post-evaluation-citations@1",
        "tool://report/check-post-evaluation-quality@1",
    ]
)
MANIFESTS = (
    LEGACY_MANIFEST,
    MANIFEST_V2_0,
    MANIFEST_V2_1,
    MANIFEST_V2_2,
    MANIFEST_V2_3,
    MANIFEST_V2_4,
    MANIFEST_V2_5,
    MANIFEST,
)
REFERENCES = frozenset(
    {
        *SCHEMAS,
        *STRATEGIES,
        "agent://contract/post-evaluation-analyst@1",
        "agent://contract/baseline-analyst@1",
        "agent://contract/baseline-analyst@2",
        "agent://contract/performance-quality-analyst@1",
        "agent://contract/performance-quality-analyst@2",
        "agent://contract/finance-invoice-analyst@1",
        "agent://contract/finance-invoice-analyst@2",
        "agent://contract/deviation-risk-analyst@1",
        "agent://contract/deviation-risk-analyst@2",
        "agent://contract/evidence-reviewer@1",
        "agent://contract/report-narrator@1",
        "agent://contract/performance-report-writer@1",
        "agent://contract/governance-report-writer@1",
        "agent://contract/report-narrator@2",
        "agent://contract/report-quality-reviewer@1",
        "tool://document/read-versions@1",
        "tool://evidence/search@1",
        "tool://document/coverage-check@1",
        "tool://contract/post-evaluation/merge-domains@1",
        "tool://contract/timeline-calculate@1",
        "tool://finance/amount-reconcile@1",
        "tool://invoice/assurance@1",
        "tool://deviation/aggregate@1",
        "tool://risk/aggregate@1",
        "tool://evidence/consistency-check@1",
        "tool://contract/post-evaluation@1",
        "tool://contract/post-evaluation/finalize@2",
        "tool://report/render-post-evaluation@1",
        "tool://report/render-post-evaluation@2",
        "tool://report/render-post-evaluation@3",
        "tool://document/readability-gate@1",
        "tool://report/compose-post-evaluation@1",
        "tool://report/verify-post-evaluation-citations@1",
        "tool://report/check-post-evaluation-quality@1",
        "tool://report/render-post-evaluation@4",
        "tool://workbench/record-post-evaluation@1",
        "tool://workbench/record-post-evaluation@2",
        "tool://workbench/record-post-evaluation@3",
        "report://contract/post-evaluation@1",
        "view://contract-post-evaluation/case@1",
    }
)

__all__ = [
    "LEGACY_MANIFEST",
    "MANIFEST",
    "MANIFESTS",
    "MANIFEST_V2_0",
    "MANIFEST_V2_1",
    "MANIFEST_V2_2",
    "MANIFEST_V2_3",
    "MANIFEST_V2_4",
    "MANIFEST_V2_5",
    "REFERENCES",
    "SCHEMAS",
    "STRATEGIES",
    "VIEW_DEFINITION",
]
