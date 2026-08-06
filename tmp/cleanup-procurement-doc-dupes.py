"""One-shot: unbind duplicate procurement-supplier-risk documents; keep newest per category+name."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections import defaultdict
from typing import Any

TENANT_ID = "00000000-0000-0000-0000-000000000001"
PROJECT_ID = "00000000-0000-0000-0000-000000000002"
API_URL = "http://127.0.0.1:8000"
WORK_KEY = "procurement-supplier-risk"


def _request(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{API_URL}{path}",
        data=data,
        method=method,
        headers={
            "X-Tenant-ID": TENANT_ID,
            "X-Actor-ID": "cleanup-operator",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> {exc.code}: {detail}") from exc


def main() -> None:
    payload = _request("GET", f"/v1/projects/{PROJECT_ID}/documents")
    items = [
        doc
        for doc in payload["items"]
        if WORK_KEY in doc.get("businessWorkKeys", [])
    ]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for doc in items:
        grouped[(doc["category"], doc["name"])].append(doc)

    print(f"bound documents: {len(items)}")
    kept = 0
    unbound = 0
    for (category, name), docs in sorted(grouped.items()):
        docs = sorted(docs, key=lambda item: item["updatedAt"], reverse=True)
        keep = docs[0]
        drop = docs[1:]
        print(
            f"{len(docs):2d}  {category}  {name}  "
            f"keep={keep['documentId']}  drop={len(drop)}"
        )
        kept += 1
        for doc in drop:
            object_ids = list(doc.get("businessObjectIds") or [])
            remaining_keys = [
                key
                for key in doc.get("businessWorkKeys", [])
                if key not in {WORK_KEY, f"{WORK_KEY}-case"}
            ]
            _request(
                "PUT",
                f"/v1/projects/{PROJECT_ID}/documents/{doc['documentId']}/bindings",
                {
                    "businessObjectIds": object_ids,
                    "businessWorkKeys": remaining_keys,
                },
            )
            unbound += 1
            print(f"  unbound {doc['documentId']}")

    print(f"done: kept_groups={kept} unbound={unbound}")


if __name__ == "__main__":
    main()
