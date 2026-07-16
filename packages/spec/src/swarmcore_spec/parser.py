from __future__ import annotations

import json
from typing import Any

import yaml
from pydantic import ValidationError

from .models import SwarmStrategy


class DuplicateKeyError(ValueError):
    pass


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> Any:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)  # type: ignore[no-untyped-call]
        if key in mapping:
            raise DuplicateKeyError(
                f"duplicate key: {key!r} at line {key_node.start_mark.line + 1}"
            )
        mapping[key] = loader.construct_object(  # type: ignore[no-untyped-call]
            value_node, deep=deep
        )
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def parse_spec(document: str | bytes, *, content_type: str | None = None) -> SwarmStrategy:
    """Parse JSON/YAML and validate it as a strict SwarmSpec v1 document."""
    if isinstance(document, bytes):
        document = document.decode("utf-8")
    if len(document.encode("utf-8")) > 1024 * 1024:
        raise ValueError("spec exceeds the 1 MiB limit")

    use_json = content_type == "application/json" or (
        content_type is None and document.lstrip().startswith(("{", "["))
    )
    try:
        raw = json.loads(document) if use_json else yaml.load(document, Loader=_UniqueKeyLoader)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid spec document: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("spec document must be an object")
    try:
        return SwarmStrategy.model_validate(raw)
    except ValidationError:
        raise
