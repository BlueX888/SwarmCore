from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def _load(name: str) -> dict[str, Any]:
    value = json.loads(files(__package__).joinpath(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"capability asset must be an object: {name}")
    return value


MANIFEST = _load("manifest.json")
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
STRATEGIES = {"strategy://procurement-supplier-risk/assess@5": _load("strategy.json")}
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

__all__ = ["MANIFEST", "REFERENCES", "SCHEMAS", "STRATEGIES", "VIEW_DEFINITION"]
