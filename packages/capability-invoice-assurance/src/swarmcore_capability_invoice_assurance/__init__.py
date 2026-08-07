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


MANIFEST_V1_1 = _load("manifest.json")
MANIFEST = deepcopy(MANIFEST_V1_1)
MANIFEST["metadata"]["version"] = "1.1.1"
MANIFEST["spec"]["strategies"]["execute"] = "strategy://invoice-assurance/assess@3"
_ACCEPTED_MEDIA_TYPES = [
    "application/xml",
    "text/xml",
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/json",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
]
for _requirement in MANIFEST["spec"]["documents"]["requirements"]:
    _requirement.setdefault("acceptedMediaTypes", list(_ACCEPTED_MEDIA_TYPES))
SCHEMAS = {
    "schema://invoice-assurance/case@1": _load("case.schema.json"),
    "schema://invoice-assurance/input@1": _load("input.schema.json"),
    "schema://invoice-assurance/result@1": _load("output.schema.json"),
}
_STRATEGY_V2 = _load("strategy.json")
_STRATEGY_V3 = deepcopy(_STRATEGY_V2)
_STRATEGY_V3["metadata"]["name"] = "invoice-assurance-assess-v3"
_STRATEGY_V3["spec"]["graph"]["nodes"]["finalize"]["input"]["approvals"] = {
    "manual-review": "{{ tasks.manual-review.output }}"
}
STRATEGIES = {
    "strategy://invoice-assurance/assess@2": _STRATEGY_V2,
    "strategy://invoice-assurance/assess@3": _STRATEGY_V3,
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
    "MANIFEST_V1_1",
    "REFERENCES",
    "SCHEMAS",
    "STRATEGIES",
    "VIEW_DEFINITION",
]
