from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import suppress
from typing import Any, Protocol

from swarmcore_observability import SwarmMetrics, get_tracer
from temporalio import activity

from agno.models.base import Model

logger = logging.getLogger(__name__)


class StaticModelResolver:
    def __init__(self, models: dict[str, str]) -> None:
        self._models = models

    def resolve(self, reference: str, context: dict[str, Any]) -> Model | str:
        del context
        try:
            return self._models[reference]
        except KeyError as exc:
            raise ValueError(f"model reference is not configured: {reference}") from exc


class AgentAdapter(Protocol):
    async def execute(self, request: dict[str, Any]) -> dict[str, Any]: ...


class AgentActivities:
    def __init__(self, adapter: AgentAdapter, metrics: SwarmMetrics | None = None) -> None:
        self._adapter = adapter
        self._metrics = metrics

    @activity.defn(name="execute_agent")
    async def execute_agent(self, request: dict[str, Any]) -> dict[str, Any]:
        node_key = str(request["node"]["key"])
        model_ref = request["agent"].get("model") or request.get("defaultModel")
        run = request["run"]
        info = activity.info()
        started = time.monotonic()
        if self._metrics is not None and info.attempt > 1:
            self._metrics.activity_retries.add(1, {"category": "agent"})
        activity.heartbeat({"stage": "starting", "nodeKey": node_key})
        logger.info(
            "agent_execution_started %s",
            json.dumps({"nodeKey": node_key, "modelRef": model_ref}, sort_keys=True),
        )
        with get_tracer("worker-agent").start_as_current_span(
            "agent.invoke",
            attributes={
                "tenant.id": str(run["tenantId"]),
                "project.id": str(run["projectId"]),
                "swarm.run.id": str(run["runId"]),
                "swarm.task.id": str(request["taskExecutionId"]),
                "swarm.attempt.id": info.activity_id,
                "swarm.strategy.version": str(run.get("strategyVersionId", "unknown")),
                "agent.definition": str(request["node"]["config"].get("agent", "unknown")),
                "model.logical_name": str(model_ref),
                "retry.attempt": info.attempt,
            },
        ) as span:
            heartbeat_task = asyncio.create_task(self._heartbeat_while_running(node_key))
            try:
                result = await self._adapter.execute(request)
            except Exception as exc:
                span.set_attribute("error.type", type(exc).__name__)
                logger.exception(
                    "agent_execution_failed %s",
                    json.dumps(
                        {
                            "nodeKey": node_key,
                            "modelRef": model_ref,
                            "errorType": type(exc).__name__,
                            "error": str(exc)[:1000],
                        },
                        sort_keys=True,
                    ),
                )
                raise
            finally:
                heartbeat_task.cancel()
                with suppress(asyncio.CancelledError):
                    await heartbeat_task
                if self._metrics is not None:
                    self._metrics.task_duration.record(
                        time.monotonic() - started, {"node_type": "agent"}
                    )
            usage = result.get("metrics", {})
            if isinstance(usage, dict):
                input_tokens = usage.get("input_tokens", usage.get("inputTokens", 0))
                output_tokens = usage.get("output_tokens", usage.get("outputTokens", 0))
                cost_usd = usage.get("cost_usd", usage.get("costUsd", 0))
                span.set_attribute(
                    "token.input", int(input_tokens) if isinstance(input_tokens, int | float) else 0
                )
                span.set_attribute(
                    "token.output",
                    int(output_tokens) if isinstance(output_tokens, int | float) else 0,
                )
                span.set_attribute(
                    "budget.cost_usd",
                    float(cost_usd) if isinstance(cost_usd, int | float) else 0.0,
                )
        activity.heartbeat({"stage": "completed", "nodeKey": node_key})
        logger.info(
            "agent_execution_completed %s",
            json.dumps(
                {
                    "nodeKey": node_key,
                    "model": result.get("model"),
                    "status": result.get("status"),
                    "metrics": result.get("metrics", {}),
                },
                sort_keys=True,
            ),
        )
        return result

    @staticmethod
    async def _heartbeat_while_running(node_key: str) -> None:
        while True:
            await asyncio.sleep(10)
            activity.heartbeat({"stage": "running", "nodeKey": node_key})

    @activity.defn(name="execute_team")
    async def execute_team(self, request: dict[str, Any]) -> dict[str, Any]:
        raise ValueError("opaque Agno Team definitions are not configured in Phase 1")
