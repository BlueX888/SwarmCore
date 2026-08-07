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
MANIFEST_V1 = _load("manifest-v1.json")
SCHEMAS = {
    "schema://document-structuring/case@1": _load("case.schema.json"),
    "schema://document-structuring/input@1": _load("input.schema.json"),
    "schema://document-structuring/package@1": _load("output.schema.json"),
}
STRATEGIES = {
    "strategy://document-structuring/execute@1": _load("strategy-v1.json"),
    "strategy://document-structuring/execute@2": _load("strategy.json"),
}
VIEW_DEFINITION = _load("view-definition.json")
MODELS = frozenset(
    {
        "model://document-layout-ocr@1",
        "model://document-nlp@1",
    }
)
REFERENCES = frozenset(
    {
        *SCHEMAS,
        *STRATEGIES,
        *MANIFEST["spec"]["agents"],
        *MANIFEST["spec"]["tools"],
        *MODELS,
        MANIFEST["spec"]["report"]["template"],
        MANIFEST["spec"]["ui"]["viewDefinition"],
    }
)

__all__ = [
    "MANIFEST",
    "MANIFEST_V1",
    "MODELS",
    "REFERENCES",
    "SCHEMAS",
    "STRATEGIES",
    "VIEW_DEFINITION",
]
