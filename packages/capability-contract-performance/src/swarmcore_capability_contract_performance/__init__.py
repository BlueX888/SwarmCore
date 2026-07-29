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
    "text/csv",
    "application/json",
    "text/plain",
    "message/rfc822",
    "image/jpeg",
    "image/png",
]
for _requirement in MANIFEST["spec"]["documents"]["requirements"]:
    _requirement.setdefault("acceptedMediaTypes", list(_ACCEPTED_MEDIA_TYPES))
SCHEMAS = {
    "schema://contract-performance/case@1": _load("case.schema.json"),
    "schema://contract-performance/input@1": _load("input.schema.json"),
    "schema://contract-performance/plan@1": _load("plan.schema.json"),
    "schema://contract-performance/result@1": _load("output.schema.json"),
}
STRATEGIES = {
    "strategy://contract-performance/initialize@13": _load("strategy-initialize.json"),
    "strategy://contract-performance/collect@10": _load("strategy-collect.json"),
}
VIEW_DEFINITION = _load("view-definition.json")
MODELS = frozenset(
    {
        "model://general@1",
        "model://document-vision-fallback@1",
    }
)
_COLLECT_REFERENCES = frozenset(
    {
        "agent://contract-performance/execution-evidence-analyst@4",
        "tool://contract-performance/source-collect@1",
        "tool://document/parse@1",
        "tool://document/ocr@1",
        "tool://contract-performance/evidence-match@1",
        "tool://contract-performance/status-calculate@2",
    }
)
REFERENCES = frozenset(
    {
        *SCHEMAS,
        *STRATEGIES,
        *MANIFEST["spec"]["agents"],
        *MANIFEST["spec"]["tools"],
        *MODELS,
        *_COLLECT_REFERENCES,
        MANIFEST["spec"]["report"]["template"],
        MANIFEST["spec"]["ui"]["viewDefinition"],
    }
)

__all__ = ["MANIFEST", "MODELS", "REFERENCES", "SCHEMAS", "STRATEGIES", "VIEW_DEFINITION"]
