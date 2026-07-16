from __future__ import annotations

import hashlib
from typing import Any

from .gateway import ToolExecutor


async def search(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    del effect_id
    return {"items": [{"title": str(input_value["query"]), "source": "controlled-index"}]}


async def publish_report(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
    publication_id = hashlib.sha256(effect_id.encode()).hexdigest()[:16]
    return {"publicationId": publication_id, "reports": input_value["reports"]}


def builtin_executors() -> dict[str, ToolExecutor]:
    return {
        "builtin.search": search,
        "builtin.publish_report": publish_report,
    }
