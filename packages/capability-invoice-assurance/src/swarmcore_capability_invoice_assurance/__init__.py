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
STRATEGIES = {"strategy://invoice-assurance/assess@2": _load("strategy.json")}
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
