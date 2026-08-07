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


MANIFEST_V1_0_5 = _load("manifest.json")
MANIFEST = deepcopy(MANIFEST_V1_0_5)
MANIFEST["metadata"]["version"] = "1.0.6"
MANIFEST["spec"]["inputSchema"] = "schema://deviation-analysis/input@2"
MANIFEST["spec"]["outputSchema"] = "schema://deviation-analysis/result@2"
MANIFEST["spec"]["strategies"]["execute"] = "strategy://deviation-analysis/execute@7"
_ACCEPTED_MEDIA_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "application/json",
    "text/plain",
    "text/markdown",
]
for _requirement in MANIFEST["spec"]["documents"]["requirements"]:
    _requirement.setdefault("acceptedMediaTypes", list(_ACCEPTED_MEDIA_TYPES))
_INPUT_V1 = _load("input.schema.json")
_INPUT_V2 = deepcopy(_INPUT_V1)
_INPUT_V2["$id"] = "schema://deviation-analysis/input@2"
_INPUT_V2["properties"]["upstreamEvaluations"] = {
    "type": "array",
    "items": {"type": "object"},
}
_RESULT_V1 = _load("output.schema.json")
_RESULT_V2 = deepcopy(_RESULT_V1)
_RESULT_V2["$id"] = "schema://deviation-analysis/result@2"
_RESULT_V2["properties"]["schemaVersion"]["const"] = (
    "schema://deviation-analysis/result@2"
)
_RESULT_V2["required"].append("approvals")
_RESULT_V2["properties"]["approvals"] = {
    "type": "array",
    "items": {"type": "object"},
}
SCHEMAS = {
    "schema://deviation-analysis/case@1": _load("case.schema.json"),
    "schema://deviation-analysis/input@1": _INPUT_V1,
    "schema://deviation-analysis/input@2": _INPUT_V2,
    "schema://deviation-analysis/result@1": _RESULT_V1,
    "schema://deviation-analysis/result@2": _RESULT_V2,
}
_STRATEGY_V6 = _load("strategy.json")
_STRATEGY_V7 = deepcopy(_STRATEGY_V6)
_STRATEGY_V7["metadata"]["name"] = "deviation-analysis-execute-v7"
_NODES_V7 = _STRATEGY_V7["spec"]["graph"]["nodes"]
for _key in ("analyze-schedule-scope", "analyze-cost-change"):
    _NODES_V7[_key]["input"]["upstreamEvaluations"] = "{{ input.upstreamEvaluations }}"
_NODES_V7["merge-facts"]["input"]["upstreamEvaluations"] = (
    "{{ input.upstreamEvaluations }}"
)
_NODES_V7["finalize"]["dependsOn"] = [
    *_NODES_V7["finalize"]["dependsOn"],
    "manual-review",
    "auto-continue",
]
_NODES_V7["finalize"]["input"]["schemaVersion"] = (
    "schema://deviation-analysis/result@2"
)
_NODES_V7["finalize"]["input"]["approvals"] = [
    "{{ tasks.manual-review.output }}"
]
STRATEGIES = {
    "strategy://deviation-analysis/execute@6": _STRATEGY_V6,
    "strategy://deviation-analysis/execute@7": _STRATEGY_V7,
}
VIEW_DEFINITION = _load("view-definition.json")
REFERENCES = frozenset(
    {
        *SCHEMAS,
        *STRATEGIES,
        *MANIFEST["spec"]["agents"],
        *MANIFEST["spec"]["tools"],
        MANIFEST["spec"]["report"]["template"],
        MANIFEST["spec"]["ui"]["viewDefinition"],
    }
)

__all__ = [
    "MANIFEST",
    "MANIFEST_V1_0_5",
    "REFERENCES",
    "SCHEMAS",
    "STRATEGIES",
    "VIEW_DEFINITION",
]
