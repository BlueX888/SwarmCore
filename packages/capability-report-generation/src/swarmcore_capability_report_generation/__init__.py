from __future__ import annotations

from copy import deepcopy
from typing import Any

_CASE_PROPERTIES: dict[str, Any] = {
    "title": {"type": "string", "minLength": 1},
    "sourceEvaluationId": {"type": "string", "format": "uuid"},
    "format": {"enum": ["JSON", "PDF"], "default": "PDF"},
}
CASE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "schema://report-generation/case@1",
    "type": "object",
    "required": ["title", "sourceEvaluationId", "format"],
    "properties": deepcopy(_CASE_PROPERTIES),
    "additionalProperties": False,
}
INPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "schema://report-generation/input@1",
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
            "required": ["title", "sourceEvaluationId", "format"],
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
    "$id": "schema://report-generation/result@1",
    "type": "object",
    "required": [
        "schemaVersion",
        "sourceEvaluationId",
        "reportId",
        "format",
        "contentHash",
        "sourceResultHash",
        "status",
        "qualityStatus",
        "reviewRequired",
        "passed",
        "generated",
        "provenance",
        "resultHash",
    ],
    "properties": {
        "schemaVersion": {"const": "schema://report-generation/result@1"},
        "sourceEvaluationId": {"type": "string", "format": "uuid"},
        "reportId": {"type": "string", "format": "uuid"},
        "format": {"enum": ["JSON", "PDF"]},
        "contentHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "sourceResultHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "status": {"const": "READY"},
        "qualityStatus": {"const": "READY"},
        "reviewRequired": {"const": False},
        "passed": {"const": True},
        "generated": {"type": "boolean"},
        "provenance": {"type": "object"},
        "resultHash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    },
    "additionalProperties": False,
}
STRATEGY: dict[str, Any] = {
    "apiVersion": "swarmcore.io/v1",
    "kind": "SwarmStrategy",
    "metadata": {"name": "report-generation-confirmed-v1"},
    "spec": {
        "inputSchema": {"type": "object"},
        "outputSchema": {"type": "object"},
        "defaults": {},
        "budget": {
            "maxDuration": "PT10M",
            "maxTokens": 1,
            "maxCostUsd": 0.01,
            "maxAgents": 1,
            "maxParallelism": 1,
            "onExhausted": "fail",
        },
        "agents": {},
        "graph": {
            "entrypoint": "generate",
            "nodes": {
                "generate": {
                    "type": "tool",
                    "tool": "tool://report/generate-confirmed@1",
                    "input": {
                        "sourceEvaluationId": "{{ input.payload.sourceEvaluationId }}",
                        "title": "{{ input.payload.title }}",
                        "format": "{{ input.payload.format }}",
                    },
                },
                "record": {
                    "type": "tool",
                    "tool": "tool://workbench/record-evaluation@1",
                    "dependsOn": ["generate"],
                    "input": {
                        "evaluationId": "{{ input.evaluationId }}",
                        "result": "{{ tasks.generate.output.content }}",
                    },
                },
            },
            "output": {"result": "{{ tasks.generate.output.content }}"},
        },
        "$defs": {},
    },
}
MANIFEST: dict[str, Any] = {
    "apiVersion": "swarmcore.io/v2",
    "kind": "CapabilityPack",
    "metadata": {"name": "report-generation", "version": "1.0.0"},
    "spec": {
        "case": {
            "type": "report-generation-case",
            "schema": "schema://report-generation/case@1",
            "subjectsRequired": False,
            "subjectRoles": [],
        },
        "inputSchema": "schema://report-generation/input@1",
        "outputSchema": "schema://report-generation/result@1",
        "strategies": {"execute": "strategy://report-generation/confirmed@1"},
        "agents": [],
        "tools": [
            "tool://report/generate-confirmed@1",
            "tool://workbench/record-evaluation@1",
        ],
        "report": {"template": "report://confirmed-evaluation@1"},
        "permissions": ["case.read", "case.assess", "report.read", "evaluation.read"],
        "events": {"namespace": "capability.report-generation"},
        "ui": {"viewDefinition": "view://report-generation/case@1"},
    },
}
SCHEMAS: dict[str, dict[str, Any]] = {
    str(value["$id"]): value for value in (CASE_SCHEMA, INPUT_SCHEMA, RESULT_SCHEMA)
}
STRATEGIES: dict[str, dict[str, Any]] = {
    "strategy://report-generation/confirmed@1": STRATEGY
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
