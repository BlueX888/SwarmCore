from __future__ import annotations

from copy import deepcopy
from typing import Any

_CASE_PROPERTIES: dict[str, Any] = {
    "title": {"type": "string", "minLength": 1},
    "benchmarkId": {"type": "string", "minLength": 1},
    "minimumPassRate": {"type": "number", "minimum": 0, "maximum": 1},
    "samples": {
        "type": "array",
        "minItems": 1,
        "items": {
            "type": "object",
            "required": ["sampleId", "expected", "actual"],
            "properties": {
                "sampleId": {"type": "string", "minLength": 1},
                "expected": {},
                "actual": {},
                "critical": {"type": "boolean", "default": False},
                "weight": {"type": "number", "exclusiveMinimum": 0, "default": 1},
            },
            "additionalProperties": False,
        },
    },
}

CASE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "schema://ai-foundation-quality/case@1",
    "type": "object",
    "required": ["title", "benchmarkId", "minimumPassRate", "samples"],
    "properties": deepcopy(_CASE_PROPERTIES),
    "additionalProperties": False,
}
INPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "schema://ai-foundation-quality/input@1",
    "type": "object",
    "required": [
        "workItemId",
        "workItemRevisionId",
        "evaluationId",
        "payload",
        "subjects",
        "documents",
        "attachments",
        "attachmentManifestHash",
        "selectionManifestHash",
        "baselineHash",
        "configurationHash",
        "configuration",
    ],
    "properties": {
        "workItemId": {"type": "string", "format": "uuid"},
        "workItemRevisionId": {"type": "string", "format": "uuid"},
        "evaluationId": {"type": "string", "format": "uuid"},
        "payload": {
            "type": "object",
            "required": ["title", "benchmarkId", "minimumPassRate", "samples"],
            "properties": deepcopy(_CASE_PROPERTIES),
            "additionalProperties": False,
        },
        "subjects": {"type": "array", "items": {"type": "object"}},
        "documents": {"type": "array", "items": {"type": "object"}},
        "attachments": {"type": "array", "items": {"type": "object"}},
        "attachmentManifestHash": {"type": "string", "minLength": 1},
        "selectionManifestHash": {"type": "string", "minLength": 1},
        "baselineHash": {"type": "string", "minLength": 1},
        "configurationHash": {"type": "string", "minLength": 1},
        "configuration": {"type": "object"},
    },
    "additionalProperties": False,
}
RESULT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "schema://ai-foundation-quality/result@1",
    "type": "object",
    "required": [
        "schemaVersion",
        "benchmarkId",
        "qualityStatus",
        "reviewRequired",
        "passed",
        "sampleCount",
        "passedCount",
        "passRate",
        "minimumPassRate",
        "criticalFailures",
        "samples",
        "provenance",
        "resultHash",
    ],
    "properties": {
        "schemaVersion": {"const": "schema://ai-foundation-quality/result@1"},
        "benchmarkId": {"type": "string"},
        "qualityStatus": {"enum": ["READY", "REVIEW_REQUIRED"]},
        "reviewRequired": {"type": "boolean"},
        "passed": {"type": "boolean"},
        "sampleCount": {"type": "integer", "minimum": 1},
        "passedCount": {"type": "integer", "minimum": 0},
        "passRate": {"type": "number", "minimum": 0, "maximum": 1},
        "minimumPassRate": {"type": "number", "minimum": 0, "maximum": 1},
        "criticalFailures": {"type": "array", "items": {"type": "string"}},
        "samples": {"type": "array", "items": {"type": "object"}},
        "approval": {"type": ["object", "null"]},
        "provenance": {"type": "object"},
        "resultHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    },
    "additionalProperties": False,
}

STRATEGY: dict[str, Any] = {
    "apiVersion": "swarmcore.io/v1",
    "kind": "SwarmStrategy",
    "metadata": {"name": "ai-foundation-quality-benchmark-v1"},
    "spec": {
        "inputSchema": {"type": "object"},
        "outputSchema": {"type": "object"},
        "defaults": {},
        "budget": {
            "maxDuration": "PT15M",
            "maxTokens": 1,
            "maxCostUsd": 0.01,
            "maxAgents": 1,
            "maxParallelism": 1,
            "onExhausted": "fail",
        },
        "agents": {},
        "graph": {
            "entrypoint": "benchmark",
            "nodes": {
                "benchmark": {
                    "type": "tool",
                    "tool": "tool://ai/quality-benchmark@1",
                    "input": {"payload": "{{ input.payload }}"},
                },
                "review-router": {
                    "type": "router",
                    "dependsOn": ["benchmark"],
                    "routes": [
                        {
                            "when": "tasks.benchmark.output.content.reviewRequired == true",
                            "target": "manual-review",
                        }
                    ],
                    "default": "auto-continue",
                },
                "manual-review": {
                    "type": "approval",
                    "dependsOn": ["review-router"],
                    "prompt": "质量基准未达到门槛或存在关键样本失败，请质量负责人复核。",
                    "requiredRoles": ["quality_reviewer", "tenant_admin"],
                    "requiresDistinctApprover": True,
                    "inputSchema": {
                        "type": "object",
                        "required": ["approved", "reason"],
                        "properties": {
                            "approved": {"type": "boolean"},
                            "reason": {"type": "string", "minLength": 1},
                        },
                        "additionalProperties": False,
                    },
                },
                "auto-continue": {
                    "type": "join",
                    "strategy": "all",
                    "dependsOn": ["review-router"],
                },
                "finalize": {
                    "type": "tool",
                    "tool": "tool://ai/quality-finalize@1",
                    "dependsOn": ["manual-review", "auto-continue"],
                    "input": {
                        "payload": "{{ input.payload }}",
                        "approval": "{{ tasks.manual-review.output }}",
                    },
                },
                "report": {
                    "type": "tool",
                    "tool": "tool://report/render-ai-quality@1",
                    "dependsOn": ["finalize"],
                    "input": {"result": "{{ tasks.finalize.output.content }}"},
                },
                "record": {
                    "type": "tool",
                    "tool": "tool://workbench/record-ai-quality@1",
                    "dependsOn": ["finalize", "report"],
                    "input": {
                        "evaluationId": "{{ input.evaluationId }}",
                        "result": "{{ tasks.finalize.output.content }}",
                        "report": "{{ tasks.report.output.content }}",
                    },
                },
            },
            "output": {"result": "{{ tasks.finalize.output.content }}"},
        },
        "$defs": {},
    },
}

MANIFEST: dict[str, Any] = {
    "apiVersion": "swarmcore.io/v2",
    "kind": "CapabilityPack",
    "metadata": {"name": "ai-foundation-quality", "version": "1.0.0"},
    "spec": {
        "case": {
            "type": "ai-quality-benchmark-case",
            "schema": "schema://ai-foundation-quality/case@1",
            "subjectsRequired": False,
            "subjectRoles": [],
        },
        "inputSchema": "schema://ai-foundation-quality/input@1",
        "outputSchema": "schema://ai-foundation-quality/result@1",
        "strategies": {"execute": "strategy://ai-foundation-quality/benchmark@1"},
        "agents": [],
        "tools": [
            "tool://ai/quality-benchmark@1",
            "tool://ai/quality-finalize@1",
            "tool://report/render-ai-quality@1",
            "tool://workbench/record-ai-quality@1",
        ],
        "report": {"template": "report://ai-foundation-quality@1"},
        "permissions": ["case.read", "case.assess", "report.read", "approval.respond"],
        "events": {"namespace": "capability.ai-foundation-quality"},
        "ui": {"viewDefinition": "view://ai-foundation-quality/case@1"},
    },
}

SCHEMAS: dict[str, dict[str, Any]] = {
    str(value["$id"]): value for value in (CASE_SCHEMA, INPUT_SCHEMA, RESULT_SCHEMA)
}
STRATEGIES: dict[str, dict[str, Any]] = {
    "strategy://ai-foundation-quality/benchmark@1": STRATEGY
}
REFERENCES = frozenset(
    {
        *SCHEMAS,
        *STRATEGIES,
        *MANIFEST["spec"]["tools"],
        MANIFEST["spec"]["report"]["template"],
        MANIFEST["spec"]["ui"]["viewDefinition"],
    }
)

__all__ = ["MANIFEST", "REFERENCES", "SCHEMAS", "STRATEGIES"]
