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
MANIFEST["spec"]["strategies"]["execute"] = (
    "strategy://procurement-supplier-risk/assess@6"
)
_ACCEPTED_MEDIA_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/json",
    "text/csv",
    "text/plain",
]
for _requirement in MANIFEST["spec"]["documents"]["requirements"]:
    _requirement.setdefault("acceptedMediaTypes", list(_ACCEPTED_MEDIA_TYPES))

SCHEMAS = {
    "schema://procurement-supplier-risk/case@1": _load("case.schema.json"),
    "schema://procurement-supplier-risk/input@1": _load("input.schema.json"),
    "schema://procurement-supplier-risk/result@1": _load("output.schema.json"),
}
_STRATEGY_V5 = _load("strategy.json")
_STRATEGY_V6 = deepcopy(_STRATEGY_V5)
_STRATEGY_V6["metadata"]["name"] = "procurement-supplier-risk-assess-v6"
_V6_REVIEW = _STRATEGY_V6["spec"]["graph"]["nodes"]["manual-review"]
_V6_REVIEW["requiredRoles"] = [
    "procurement_reviewer",
    "legal_reviewer",
    "risk_reviewer",
    "tenant_admin",
]
_V6_REVIEW["requiresDistinctApprover"] = True
_STRATEGY_V6["spec"]["graph"]["nodes"]["finalize"]["input"]["provenance"][
    "strategy"
] = "strategy://procurement-supplier-risk/assess@6"
STRATEGIES = {
    "strategy://procurement-supplier-risk/assess@5": _STRATEGY_V5,
    "strategy://procurement-supplier-risk/assess@6": _STRATEGY_V6,
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
