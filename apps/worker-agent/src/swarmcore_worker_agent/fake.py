from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

from temporalio import activity
from temporalio.exceptions import ApplicationError


class DeterministicFakeAgentAdapter:
    """Credential-free adapter for local tests and demos.

    It is never selected in production by default.
    """

    async def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        if request["run"].get("input", {}).get("_failOnce") and activity.info().attempt == 1:
            raise ApplicationError("deterministic transient failure", type="WORKER_TRANSIENT")
        delay = request["run"].get("input", {}).get("_delaySeconds", 0)
        if isinstance(delay, int | float) and delay > 0:
            remaining = min(float(delay), 30.0)
            while remaining > 0:
                activity.heartbeat({"remainingSeconds": remaining})
                interval = min(0.25, remaining)
                await asyncio.sleep(interval)
                remaining -= interval
        node = request["node"]
        payload = {
            "input": request["run"].get("input", {}),
            "nodeInput": node.get("config", {}).get("input", {}),
            "dependencyOutputs": request.get("dependencyOutputs", {}),
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return {
            "status": "COMPLETED",
            "content": {
                "node": str(node["key"]),
                "digest": hashlib.sha256(encoded.encode()).hexdigest()[:16],
                "input": payload["input"],
            },
            "runId": str(request["taskExecutionId"]),
            "model": "fake:deterministic",
            "metrics": {"input_tokens": len(encoded.split()), "output_tokens": 8, "costUsd": 0.0},
        }
