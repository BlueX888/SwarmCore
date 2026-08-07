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


MANIFEST_V1_0_4 = _load("manifest.json")
MANIFEST = deepcopy(MANIFEST_V1_0_4)
MANIFEST["metadata"]["version"] = "1.0.5"
MANIFEST["spec"]["case"]["schema"] = "schema://swarm-calibration/case@2"
MANIFEST["spec"]["inputSchema"] = "schema://swarm-calibration/input@2"
MANIFEST["spec"]["strategies"]["execute"] = "strategy://swarm-calibration/assess@5"
_CASE_V1 = _load("case.schema.json")
_CASE_V2 = deepcopy(_CASE_V1)
_CASE_V2["$id"] = "schema://swarm-calibration/case@2"
_CASE_V2["required"].insert(1, "calibrationMode")
_CASE_V2["properties"]["calibrationMode"] = {
    "const": "GITHUB_ENGINEERING_ISSUE"
}
_INPUT_V1 = _load("input.schema.json")
_INPUT_V2 = deepcopy(_INPUT_V1)
_INPUT_V2["$id"] = "schema://swarm-calibration/input@2"
_INPUT_V2["$defs"]["case"]["required"].insert(1, "calibrationMode")
_INPUT_V2["$defs"]["case"]["properties"]["calibrationMode"] = {
    "const": "GITHUB_ENGINEERING_ISSUE"
}
SCHEMAS = {
    "schema://swarm-calibration/case@1": _CASE_V1,
    "schema://swarm-calibration/case@2": _CASE_V2,
    "schema://swarm-calibration/input@1": _INPUT_V1,
    "schema://swarm-calibration/input@2": _INPUT_V2,
    "schema://swarm-calibration/result@1": _load("output.schema.json"),
}
_STRATEGY_V4 = _load("strategy.json")
_STRATEGY_V5 = deepcopy(_STRATEGY_V4)
_STRATEGY_V5["metadata"]["name"] = "swarm-calibration-assess-v5"
_STRATEGY_V5["spec"]["budget"]["maxCostUsd"] = 3
_V5_REVIEW = _STRATEGY_V5["spec"]["graph"]["nodes"]["manual-review"]
_V5_REVIEW["requiredRoles"] = ["calibration_reviewer", "tenant_admin"]
_V5_REVIEW["requiresDistinctApprover"] = True
STRATEGIES = {
    "strategy://swarm-calibration/assess@4": _STRATEGY_V4,
    "strategy://swarm-calibration/assess@5": _STRATEGY_V5,
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
    "MANIFEST_V1_0_4",
    "REFERENCES",
    "SCHEMAS",
    "STRATEGIES",
    "VIEW_DEFINITION",
]
