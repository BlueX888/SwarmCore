from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import timedelta
from typing import Any, cast

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.workflow import ActivityCancellationType

with workflow.unsafe.imports_passed_through():
    from swarmcore_spec import evaluate_condition, render_templates

from .scheduler import NodeState, propagate_failure_blocks, ready_nodes

_CONTROL_QUEUE = "swarm-control"
_AGENT_QUEUE = "agent-general"
_TOOL_QUEUE = "tool-trusted"
_INITIAL_RUN_EVENT_TYPES = ("run.validating", "run.queued", "run.started")


@workflow.defn(name="SwarmRunWorkflow")
class SwarmRunWorkflow:
    """Deterministic execution interpreter with durable, ordered human-control commands."""

    def __init__(self) -> None:
        self._run_input: dict[str, Any] = {}
        self._nodes: list[dict[str, Any]] = []
        self._states: dict[str, NodeState] = {}
        self._outputs: dict[str, Any] = {}
        self._plan: dict[str, Any] = {}
        self._loop_body_keys: set[str] = set()
        self._current_iteration: int | None = None
        self._last_applied_command_seq = 0
        self._command_results: dict[int, dict[str, Any]] = {}
        self._request_results: dict[str, dict[str, Any]] = {}
        self._cancel_requested = False
        self._pause_requested = False
        self._paused = False
        self._failure_wait = False
        self._human_requests: dict[str, dict[str, Any]] = {}
        self._in_flight: set[asyncio.Task[dict[str, Any]]] = set()
        self._activity_handles: set[asyncio.Task[dict[str, Any]]] = set()
        self._used_tokens = 0
        self._used_cost_usd = 0.0
        self._budget_warned = False
        self._compensation_stack: list[dict[str, Any]] = []
        self._control_queue = _CONTROL_QUEUE
        self._agent_queue = _AGENT_QUEUE
        self._tool_queue = _TOOL_QUEUE

    @workflow.run
    async def run(self, run_input: dict[str, Any]) -> dict[str, Any]:
        self._run_input = run_input
        self._control_queue = str(run_input.get("controlTaskQueue") or _CONTROL_QUEUE)
        self._agent_queue = str(run_input.get("agentTaskQueue") or _AGENT_QUEUE)
        self._tool_queue = str(run_input.get("toolTaskQueue") or _TOOL_QUEUE)
        start_command = run_input.get("startCommand")
        if start_command:
            sequence = int(start_command["commandSeq"])
            start_result = {"status": "APPLIED"}
            self._last_applied_command_seq = sequence
            self._command_results[sequence] = start_result
            self._request_results[str(start_command.get("requestId", f"seq:{sequence}"))] = (
                start_result
            )
        plan = await workflow.execute_activity(
            "load_execution_plan",
            run_input,
            task_queue=self._control_queue,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=0),
            result_type=dict[str, Any],
        )
        self._plan = plan
        self._nodes = list(plan["nodes"])
        self._states = {str(node["key"]): NodeState.PENDING for node in self._nodes}
        self._loop_body_keys = {
            str(body_key)
            for node in self._nodes
            if node["type"] == "loop"
            for body_key in node["config"]["body"]
        }
        for body_key in self._loop_body_keys:
            self._states[body_key] = NodeState.SKIPPED
        initial_events = (
            self._initial_run_event_payloads(run_input, plan)
            if workflow.patched("initial-run-event-metadata-v1")
            else {event_type: {} for event_type in _INITIAL_RUN_EVENT_TYPES}
        )
        for event_type, data in initial_events.items():
            await self._project(event_type, data)

        max_parallelism = int(plan["budget"]["maxParallelism"])
        by_key = {str(node["key"]): node for node in self._nodes}
        running: dict[asyncio.Task[dict[str, Any]], str] = {}
        while True:
            if self._cancel_requested:
                for task in running:
                    task.cancel()
                if running:
                    await asyncio.gather(*running, return_exceptions=True)
                    self._in_flight.difference_update(running)
                    running.clear()
                await self._cancel_run()
                await workflow.wait_condition(workflow.all_handlers_finished)
                return {"status": "CANCELLED", "outputs": self._outputs}
            if not running:
                await self._pause_barrier()
            if self._cancel_requested:
                continue
            if not running and self._budget_exhausted():
                terminal = await self._handle_budget_exhaustion()
                if terminal is not None:
                    await workflow.wait_condition(workflow.all_handlers_finished)
                    return terminal

            blocked_state = (
                NodeState.BLOCKED
                if workflow.patched("transitive-failure-blocking-v1")
                else NodeState.SKIPPED
            )
            for key in propagate_failure_blocks(
                self._nodes, self._states, blocked_state=blocked_state
            ):
                await self._project("task.skipped", {"nodeKey": key})

            if not running and self._all_terminal():
                if any(state == NodeState.FAILED for state in self._states.values()):
                    if not self._failure_wait:
                        self._failure_wait = True
                        await self._project(
                            "run.failed", {"code": "TASK_FAILED", "retryable": True}
                        )
                    await workflow.wait_condition(
                        lambda: not self._failure_wait or self._cancel_requested
                    )
                    continue
                result = self._render_result(plan, self._nodes)
                await self._project("run.completed", {"result": result})
                await workflow.wait_condition(workflow.all_handlers_finished)
                return {"status": "SUCCEEDED", "result": result, "outputs": self._outputs}

            scheduling_allowed = not self._pause_requested and not self._budget_exhausted()
            available_slots = max_parallelism - len(running)
            batch = (
                ready_nodes(
                    self._nodes,
                    self._states,
                    max_parallelism=available_slots,
                )
                if scheduling_allowed and available_slots > 0
                else []
            )
            for key in batch:
                task = asyncio.create_task(
                    self._execute_node(
                        by_key[key],
                        plan.get("resolved_agents", {}),
                        plan.get("defaults", {}).get("model"),
                        plan.get("resolved_tools", {}),
                    )
                )
                running[task] = key
                self._in_flight.add(task)

            if not running:
                await self._compensate_effects()
                await self._project("run.failed", {"code": "GRAPH_DEADLOCK"})
                await workflow.wait_condition(workflow.all_handlers_finished)
                return {"status": "FAILED", "code": "GRAPH_DEADLOCK"}

            done, _ = await workflow.wait(running, return_when=asyncio.FIRST_COMPLETED)
            completed = sorted((running.pop(task), task) for task in done)
            self._in_flight.difference_update(done)
            for key, task in completed:
                try:
                    outcome: dict[str, Any] | BaseException = task.result()
                except BaseException as exc:
                    outcome = exc
                if isinstance(outcome, asyncio.CancelledError):
                    self._states[key] = NodeState.CANCELLED
                elif isinstance(outcome, BaseException):
                    self._states[key] = NodeState.FAILED
                    await self._project(
                        "task.failed", {"nodeKey": key, "error": self._safe_error(outcome)}
                    )
                else:
                    self._states[key] = NodeState.SUCCEEDED
                    self._outputs[key] = outcome
                    await self._record_usage(outcome)
                    if by_key[key]["type"] == "router":
                        await self._apply_router_selection(by_key[key], outcome)
                    await self._project("task.completed", {"nodeKey": key, "output": outcome})

    async def _record_usage(self, outcome: dict[str, Any]) -> None:
        metrics = outcome.get("metrics")
        if not isinstance(metrics, dict):
            return
        input_tokens = metrics.get("input_tokens", metrics.get("inputTokens", 0))
        output_tokens = metrics.get("output_tokens", metrics.get("outputTokens", 0))
        cost = metrics.get("cost_usd", metrics.get("costUsd", 0))
        if isinstance(input_tokens, int) and not isinstance(input_tokens, bool):
            self._used_tokens += max(0, input_tokens)
        if isinstance(output_tokens, int) and not isinstance(output_tokens, bool):
            self._used_tokens += max(0, output_tokens)
        if isinstance(cost, int | float) and not isinstance(cost, bool):
            self._used_cost_usd += max(0.0, float(cost))
        budget = self._plan["budget"]
        ratio = max(
            self._used_tokens / int(budget["maxTokens"]),
            self._used_cost_usd / float(budget["maxCostUsd"]),
        )
        usage = {"tokens": self._used_tokens, "costUsd": self._used_cost_usd}
        if ratio >= 1:
            await self._project("budget.exhausted", usage)
        elif ratio >= 0.8 and not self._budget_warned:
            self._budget_warned = True
            await self._project("budget.warning", usage)

    def _budget_exhausted(self) -> bool:
        budget = self._plan.get("budget", {})
        return self._used_tokens >= int(budget.get("maxTokens", 1_000_000)) or (
            self._used_cost_usd >= float(budget.get("maxCostUsd", 25))
        )

    async def _handle_budget_exhaustion(self) -> dict[str, Any] | None:
        budget = self._plan["budget"]
        behavior = str(budget.get("onExhausted", "fail"))
        if behavior == "partial_result":
            result = {"partial": True, "outputs": self._outputs}
            await self._project("run.completed", {"result": result, "reason": "budget"})
            return {"status": "SUCCEEDED", "result": result, "outputs": self._outputs}
        if behavior == "wait_for_budget_approval":
            approval = {
                "key": "budget",
                "type": "approval",
                "config": {
                    "prompt": "Approve a Run budget increase",
                    "inputSchema": {
                        "type": "object",
                        "required": ["maxTokens", "maxCostUsd"],
                        "properties": {
                            "maxTokens": {"type": "integer", "minimum": self._used_tokens + 1},
                            "maxCostUsd": {
                                "type": "number",
                                "exclusiveMinimum": self._used_cost_usd,
                            },
                        },
                        "additionalProperties": False,
                    },
                },
            }
            value = await self._wait_for_human(
                approval,
                task_instance_key="budget",
                kind_override="approval",
                governance={
                    "policyRevision": self._plan["policy_revision"],
                    "requestedBy": self._run_input.get("initiatedBy", "workflow"),
                },
            )
            budget["maxTokens"] = int(value["maxTokens"])
            budget["maxCostUsd"] = float(value["maxCostUsd"])
            await self._project(
                "budget.increased",
                {"maxTokens": budget["maxTokens"], "maxCostUsd": budget["maxCostUsd"]},
            )
            return None
        await self._project(
            "run.failed",
            {
                "code": "BUDGET_EXCEEDED",
                "tokens": self._used_tokens,
                "costUsd": self._used_cost_usd,
            },
        )
        await self._compensate_effects()
        return {"status": "FAILED", "code": "BUDGET_EXCEEDED", "outputs": self._outputs}

    @workflow.update(name="apply_command")
    async def apply_command(self, command: dict[str, Any]) -> dict[str, Any]:
        sequence = int(command["commandSeq"])
        request_id = str(command.get("requestId", f"seq:{sequence}"))
        if request_id in self._request_results:
            return self._request_results[request_id]
        if sequence <= self._last_applied_command_seq:
            return self._command_results.get(
                sequence, {"status": "REJECTED", "code": "COMMAND_SEQUENCE_REUSED"}
            )
        if sequence != self._last_applied_command_seq + 1:
            return {
                "status": "REJECTED",
                "code": "COMMAND_OUT_OF_ORDER",
                "lastAppliedCommandSeq": self._last_applied_command_seq,
            }

        command_type = str(command["type"])
        data = dict(command.get("data", {}))
        result = await self._apply(command_type, data)
        self._last_applied_command_seq = sequence
        self._command_results[sequence] = result
        self._request_results[request_id] = result
        return result

    async def _apply(self, command_type: str, data: dict[str, Any]) -> dict[str, Any]:
        if command_type == "start":
            return {"status": "APPLIED"}
        if command_type == "cancel":
            if self._cancel_requested:
                return {"status": "APPLIED"}
            self._cancel_requested = True
            self._pause_requested = False
            for request in self._human_requests.values():
                if request["status"] == "PENDING":
                    request["status"] = "CANCELLED"
            for handle in self._activity_handles:
                handle.cancel()
            return {"status": "APPLIED"}
        if self._cancel_requested:
            return {"status": "REJECTED", "code": "RUN_CANCELLING"}
        if command_type == "pause":
            if self._pause_requested or self._paused:
                return {"status": "REJECTED", "code": "RUN_ALREADY_PAUSED"}
            self._pause_requested = True
            await self._project("run.pause_requested", {})
            await self._project("run.pausing", {})
            return {"status": "APPLIED"}
        if command_type == "resume":
            if not (self._pause_requested or self._paused):
                return {"status": "REJECTED", "code": "RUN_NOT_PAUSED"}
            self._pause_requested = False
            self._paused = False
            await self._project("run.resume_requested", {})
            await self._project("run.resumed", {})
            return {"status": "APPLIED"}
        if command_type in {"approve", "reject", "provide_input"}:
            return await self._resolve_human_request(command_type, data)
        if command_type == "retry_task":
            node_key = str(data.get("nodeKey", ""))
            if self._states.get(node_key) != NodeState.FAILED:
                return {"status": "REJECTED", "code": "TASK_NOT_RETRYABLE"}
            self._states[node_key] = NodeState.PENDING
            self._outputs.pop(node_key, None)
            for key, state in tuple(self._states.items()):
                if state in {NodeState.SKIPPED, NodeState.BLOCKED}:
                    self._states[key] = NodeState.PENDING
            self._failure_wait = False
            await self._project("task.retry_requested", {"nodeKey": node_key})
            await self._project("task.retry_started", {"nodeKey": node_key})
            await self._project("run.resumed", {"reason": "task_retry"})
            return {"status": "APPLIED", "nodeKey": node_key}
        return {"status": "REJECTED", "code": "COMMAND_NOT_SUPPORTED"}

    async def _resolve_human_request(
        self, command_type: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        request_id = str(data.get("requestId", ""))
        pending = self._human_requests.get(request_id)
        if pending is None:
            return {"status": "REJECTED", "code": "REQUEST_NOT_FOUND"}
        if pending["status"] != "PENDING":
            return {"status": "REJECTED", "code": "REQUEST_ALREADY_HANDLED"}
        expected = "input" if command_type == "provide_input" else "approval"
        if pending["kind"] != expected:
            return {"status": "REJECTED", "code": "REQUEST_TYPE_MISMATCH"}
        value = data.get("value", {})
        if command_type != "reject" and not self._valid_schema(value, pending["schema"]):
            return {"status": "REJECTED", "code": "INPUT_SCHEMA_INVALID"}
        pending["status"] = "REJECTED" if command_type == "reject" else "RESOLVED"
        pending["value"] = value
        event_type = {
            "approve": "approval.approved",
            "reject": "approval.rejected",
            "provide_input": "input.received",
        }[command_type]
        await self._project(
            event_type,
            {"requestId": request_id, "nodeKey": pending["nodeKey"], "value": value},
        )
        return {"status": "APPLIED", "requestId": request_id}

    @workflow.query(name="engine_state")
    def engine_state(self) -> dict[str, Any]:
        return {
            "states": {key: value.value for key, value in self._states.items()},
            "lastAppliedCommandSeq": self._last_applied_command_seq,
            "cancelRequested": self._cancel_requested,
            "pauseRequested": self._pause_requested,
            "paused": self._paused,
            "pendingHumanRequests": sum(
                item["status"] == "PENDING" for item in self._human_requests.values()
            ),
            "humanRequests": {
                key: {
                    "kind": item["kind"],
                    "nodeKey": item["nodeKey"],
                    "status": item["status"],
                }
                for key, item in self._human_requests.items()
            },
            "inFlightCount": len(self._in_flight),
        }

    async def _pause_barrier(self) -> None:
        if not self._pause_requested:
            return
        if not self._paused:
            self._paused = True
            await self._project("run.pausing", {})
            await self._project("run.paused", {})
        await workflow.wait_condition(lambda: not self._pause_requested or self._cancel_requested)

    async def _execute_node(
        self,
        node: dict[str, Any],
        resolved_agents: dict[str, Any],
        default_model: str | None,
        resolved_tools: dict[str, Any],
        *,
        task_instance_key: str | None = None,
        iteration_no: int | None = None,
    ) -> dict[str, Any]:
        key = str(node["key"])
        instance_key = task_instance_key or key
        self._states[key] = NodeState.RUNNING
        await self._project(
            "task.started",
            {
                "nodeKey": key,
                "taskInstanceKey": instance_key,
                "nodeType": node["type"],
                "dependencies": node.get("dependencies", []),
                "iterationNo": iteration_no,
            },
        )
        if self._cancel_requested:
            raise asyncio.CancelledError
        if node["type"] in {"approval", "input"}:
            return await self._wait_for_human(node, task_instance_key=instance_key)
        if node["type"] == "router":
            return self._route(node)
        if node["type"] == "loop":
            return await self._execute_loop(node, resolved_agents, default_model, resolved_tools)
        activity_name, queue, payload = await self._prepare_activity(
            node,
            resolved_agents,
            default_model,
            resolved_tools,
            instance_key=instance_key,
        )
        try:
            result = await self._run_activity(
                node,
                activity_name,
                queue,
                payload,
                instance_key=instance_key,
            )
            fallback_agent = node.get("config", {}).get("fallbackAgent")
            if node["type"] == "agent" and isinstance(fallback_agent, str):
                return {
                    **result,
                    "fallback": {
                        "used": False,
                        "primaryAgent": node["config"]["agent"],
                        "fallbackAgent": fallback_agent,
                        "reason": None,
                    },
                }
            return result
        except Exception as primary_error:
            fallback_agent = node.get("config", {}).get("fallbackAgent")
            if node["type"] != "agent" or not isinstance(fallback_agent, str):
                raise
            fallback_node = {
                **node,
                "config": {
                    **node["config"],
                    "agent": fallback_agent,
                    "fallbackAgent": None,
                },
            }
            fallback_instance_key = f"{instance_key}:fallback"
            await self._project(
                "agent.fallback.selected",
                {
                    "nodeKey": key,
                    "taskInstanceKey": fallback_instance_key,
                    "primaryAgent": node["config"]["agent"],
                    "fallbackAgent": fallback_agent,
                    "error": self._safe_error(primary_error),
                },
            )
            fallback_activity, fallback_queue, fallback_payload = await self._prepare_activity(
                fallback_node,
                resolved_agents,
                default_model,
                resolved_tools,
                instance_key=fallback_instance_key,
            )
            result = await self._run_activity(
                fallback_node,
                fallback_activity,
                fallback_queue,
                fallback_payload,
                instance_key=fallback_instance_key,
            )
            return {
                **result,
                "fallback": {
                    "used": True,
                    "primaryAgent": node["config"]["agent"],
                    "fallbackAgent": fallback_agent,
                    "reason": self._safe_error(primary_error),
                },
            }

    async def _prepare_activity(
        self,
        node: dict[str, Any],
        resolved_agents: dict[str, Any],
        default_model: str | None,
        resolved_tools: dict[str, Any],
        *,
        instance_key: str,
    ) -> tuple[str, str, dict[str, Any]]:
        key = str(node["key"])
        activity_name, queue = self._activity_for(str(node["type"]))
        execution_id = str(workflow.uuid4())
        rendered_node = self._render_node(node)
        payload: dict[str, Any] = {
            "run": self._run_input,
            "node": rendered_node,
            "taskExecutionId": execution_id,
            "agentInstanceId": str(workflow.uuid4()),
            "dependencyOutputs": {
                dependency: self._outputs[dependency]
                for dependency in node.get("dependencies", [])
                if dependency in self._outputs
            },
        }
        if node["type"] == "agent":
            payload["agent"] = resolved_agents[node["config"]["agent"]]
            payload["defaultModel"] = default_model
            model_ref = payload["agent"].get("model") or default_model
            payload["modelRegistration"] = self._plan.get("resolved_models", {}).get(
                model_ref, {}
            )
            payload["toolCapabilities"] = await self._agent_tool_capabilities(
                node, payload["agent"], execution_id, resolved_tools, instance_key
            )
        elif node["type"] == "tool":
            tool_ref = str(node["config"]["tool"])
            registration = resolved_tools[tool_ref]
            effect_id = execution_id
            tool_input = dict(rendered_node["config"].get("input", {}))
            input_hash = self._canonical_hash(tool_input)
            approved = await self._approve_tool_if_required(
                registration,
                instance_key=instance_key,
                tool_input_hash=input_hash,
                execution_id=execution_id,
            )
            payload["capabilityToken"] = await self._issue_tool_capability(
                node_key=instance_key,
                tool_ref=tool_ref,
                execution_id=execution_id,
                effect_id=effect_id,
                approved=approved,
                canonical_input_hash=input_hash if approved else None,
            )
            payload["effectId"] = effect_id
            payload["input"] = tool_input
            await self._project(
                "tool.requested",
                {
                    "nodeKey": key,
                    "taskInstanceKey": instance_key,
                    "toolRef": registration["ref"],
                    "effectId": effect_id,
                },
            )
            await self._project(
                "tool.started",
                {
                    "nodeKey": key,
                    "taskInstanceKey": instance_key,
                    "toolRef": registration["ref"],
                    "effectId": effect_id,
                },
            )
        return activity_name, queue, payload

    async def _run_activity(
        self,
        node: dict[str, Any],
        activity_name: str,
        queue: str,
        payload: dict[str, Any],
        *,
        instance_key: str,
    ) -> dict[str, Any]:
        key = str(node["key"])
        handle = workflow.start_activity(
            activity_name,
            payload,
            task_queue=queue,
            start_to_close_timeout=timedelta(minutes=15),
            heartbeat_timeout=timedelta(seconds=30),
            cancellation_type=ActivityCancellationType.TRY_CANCEL,
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2,
                maximum_interval=timedelta(minutes=1),
                maximum_attempts=3,
            ),
            result_type=dict[str, Any],
        )
        self._activity_handles.add(handle)
        if self._cancel_requested:
            handle.cancel()
        try:
            result = await handle
        except BaseException as exc:
            if node["type"] == "tool":
                await self._project(
                    "tool.failed",
                    {
                        "nodeKey": key,
                        "taskInstanceKey": instance_key,
                        "toolRef": node["config"]["tool"],
                        "effectId": payload["effectId"],
                        "error": self._safe_error(exc),
                    },
                )
            raise
        finally:
            self._activity_handles.discard(handle)
        if node["type"] == "tool":
            await self._project(
                "tool.completed",
                {
                    "nodeKey": key,
                    "taskInstanceKey": instance_key,
                    "toolRef": result.get("tool"),
                    "effectId": result.get("effectId"),
                    "metrics": result.get("metrics", {}),
                },
            )
            registration = self._plan.get("resolved_tools", {}).get(
                node["config"]["tool"], {}
            )
            if registration.get("sideEffecting"):
                self._compensation_stack.append(
                    {
                        "nodeKey": instance_key,
                        "toolRef": registration["ref"],
                        "effectId": result.get("effectId"),
                        "input": payload.get("input", {}),
                        "recoveryPolicy": registration["recoveryPolicy"],
                    }
                )
        elif node["type"] == "agent":
            registration = payload.get("modelRegistration", {})
            await self._project(
                "model.usage",
                {
                    "nodeKey": key,
                    "taskInstanceKey": instance_key,
                    "requestId": result.get("runId") or payload["taskExecutionId"],
                    "logicalModel": payload["agent"].get("model")
                    or payload.get("defaultModel"),
                    "providerModel": registration.get("providerModel", result.get("model")),
                    "modelVersion": registration.get("version", "unknown"),
                    "metrics": result.get("metrics", {}),
                },
            )
        return cast(dict[str, Any], result)

    async def _wait_for_human(
        self,
        node: dict[str, Any],
        *,
        task_instance_key: str | None = None,
        kind_override: str | None = None,
        governance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_id = str(workflow.uuid4())
        kind = kind_override or str(node["type"])
        node_key = task_instance_key or str(node["key"])
        request = {
            "kind": kind,
            "nodeKey": node_key,
            "schema": dict(node["config"].get("inputSchema", {"type": "object"})),
            "status": "PENDING",
            "value": {},
        }
        self._human_requests[request_id] = request
        prefix = "approval" if kind == "approval" else "input"
        await self._project(
            f"{prefix}.requested",
            {
                "requestId": request_id,
                "nodeKey": request["nodeKey"],
                "prompt": node["config"]["prompt"],
                "inputSchema": request["schema"],
                **(governance or {}),
            },
        )
        await self._project(
            "run.waiting_approval" if kind == "approval" else "run.waiting_input",
            {"requestId": request_id, "nodeKey": request["nodeKey"]},
        )
        await workflow.wait_condition(
            lambda: request["status"] != "PENDING" or self._cancel_requested
        )
        if request["status"] == "REJECTED":
            raise ValueError("approval rejected")
        if self._cancel_requested:
            raise asyncio.CancelledError
        await self._project("run.resumed", {"reason": f"{prefix}_resolved"})
        return cast(dict[str, Any], request["value"])

    async def _approve_tool_if_required(
        self,
        registration: dict[str, Any],
        *,
        instance_key: str,
        tool_input_hash: str | None,
        execution_id: str,
    ) -> bool:
        if registration["risk"] not in {"HIGH", "CRITICAL"}:
            return False
        approval_node = {
            "key": instance_key,
            "type": "approval",
            "config": {
                "prompt": f"Approve {registration['ref']} execution",
                "inputSchema": {"type": "object"},
            },
        }
        await self._wait_for_human(
            approval_node,
            task_instance_key=instance_key,
            kind_override="approval",
            governance={
                "taskExecutionId": execution_id,
                "toolRef": registration["ref"],
                "toolVersion": registration["version"],
                "canonicalInputHash": tool_input_hash,
                "policyRevision": self._plan["policy_revision"],
                "expiresAt": (workflow.now() + timedelta(minutes=15)).isoformat(),
                "requiresDistinctApprover": registration["risk"] == "CRITICAL",
                "requestedBy": self._run_input.get("initiatedBy", "workflow"),
            },
        )
        return True

    async def _issue_tool_capability(
        self,
        *,
        node_key: str,
        tool_ref: str,
        execution_id: str,
        effect_id: str | None,
        approved: bool,
        canonical_input_hash: str | None = None,
        action: str = "tool.execute",
    ) -> str:
        result = await workflow.execute_activity(
            "issue_tool_capability",
            {
                "run": self._run_input,
                "nodeKey": node_key,
                "toolRef": tool_ref,
                "executionId": execution_id,
                "effectId": effect_id,
                "approved": approved,
                "canonicalInputHash": canonical_input_hash,
                "policyRevision": self._plan["policy_revision"],
                "action": action,
            },
            task_queue=self._control_queue,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
            result_type=str,
        )
        return str(result)

    async def _agent_tool_capabilities(
        self,
        node: dict[str, Any],
        agent: dict[str, Any],
        execution_id: str,
        resolved_tools: dict[str, Any],
        instance_key: str,
    ) -> dict[str, str]:
        capabilities: dict[str, str] = {}
        for tool_ref in agent.get("tools", []):
            registration = resolved_tools[tool_ref]
            if registration["risk"] in {"HIGH", "CRITICAL"}:
                raise ValueError(
                    "high-risk Agent tools require a separately bound Tool node"
                )
            approved = False
            capabilities[tool_ref] = await self._issue_tool_capability(
                node_key=str(node["key"]),
                tool_ref=tool_ref,
                execution_id=execution_id,
                effect_id=None,
                approved=approved,
            )
        return capabilities

    @staticmethod
    def _canonical_hash(value: dict[str, Any]) -> str:
        encoded = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _route(self, node: dict[str, Any]) -> dict[str, Any]:
        context = self._expression_context()
        for route in node["config"]["routes"]:
            if evaluate_condition(str(route["when"]), context):
                return {"selected": str(route["target"])}
        default = node["config"].get("default")
        if default is None:
            raise ValueError("router did not match and has no default")
        return {"selected": str(default)}

    async def _apply_router_selection(self, node: dict[str, Any], outcome: dict[str, Any]) -> None:
        selected = str(outcome["selected"])
        targets = {str(route["target"]) for route in node["config"]["routes"]}
        default = node["config"].get("default")
        if default:
            targets.add(str(default))
        for target in sorted(targets - {selected}):
            if self._states.get(target) == NodeState.PENDING:
                self._states[target] = NodeState.SKIPPED
                if workflow.patched("router-skipped-output-v1"):
                    self._outputs[target] = {}
                await self._project("task.skipped", {"nodeKey": target, "route": node["key"]})

    async def _execute_loop(
        self,
        node: dict[str, Any],
        resolved_agents: dict[str, Any],
        default_model: str | None,
        resolved_tools: dict[str, Any],
    ) -> dict[str, Any]:
        by_key = {str(item["key"]): item for item in self._nodes}
        iterations: list[dict[str, Any]] = []
        for iteration in range(1, int(node["config"]["maxIterations"]) + 1):
            self._current_iteration = iteration
            current: dict[str, Any] = {}
            for body_key in node["config"]["body"]:
                body_node = by_key[str(body_key)]
                instance_key = f"{body_key}#{iteration}"
                try:
                    output = await self._execute_node(
                        body_node,
                        resolved_agents,
                        default_model,
                        resolved_tools,
                        task_instance_key=instance_key,
                        iteration_no=iteration,
                    )
                except BaseException as exc:
                    self._states[str(body_key)] = NodeState.FAILED
                    await self._project(
                        "task.failed",
                        {
                            "nodeKey": body_key,
                            "taskInstanceKey": instance_key,
                            "error": self._safe_error(exc),
                        },
                    )
                    raise
                self._states[str(body_key)] = NodeState.SUCCEEDED
                self._outputs[str(body_key)] = output
                current[str(body_key)] = output
                await self._project(
                    "task.completed",
                    {
                        "nodeKey": body_key,
                        "taskInstanceKey": instance_key,
                        "output": output,
                    },
                )
            last = current[str(node["config"]["body"][-1])]
            iterations.append(current)
            context = self._expression_context()
            context.update({"iteration": iteration, "output": last})
            if evaluate_condition(str(node["config"]["until"]), context):
                self._current_iteration = None
                return {"iterations": iterations, "last": last}
        self._current_iteration = None
        raise ValueError("LOOP_MAX_ITERATIONS_EXCEEDED")

    def _render_node(self, node: dict[str, Any]) -> dict[str, Any]:
        rendered = dict(node)
        rendered["config"] = dict(node["config"])
        rendered["config"]["input"] = render_templates(
            node["config"].get("input", {}), self._expression_context()
        )
        return rendered

    def _expression_context(self) -> dict[str, Any]:
        context = {
            "input": self._run_input.get("input", {}),
            "tasks": {key: {"output": value} for key, value in self._outputs.items()},
        }
        if self._current_iteration is not None:
            context["iteration"] = self._current_iteration
        return context

    async def _project(self, event_type: str, data: dict[str, Any]) -> None:
        await workflow.execute_activity(
            "project_transition",
            {
                "run": self._run_input,
                "transitionId": str(workflow.uuid4()),
                "type": event_type,
                "data": data,
            },
            task_queue=self._control_queue,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=0),
        )

    @staticmethod
    def _initial_run_event_payloads(
        run_input: dict[str, Any], plan: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        budget = plan["budget"]
        validating: dict[str, Any] = {"planHash": str(run_input["planHash"])}
        optional_validation_fields = {
            "strategyVersionId": run_input.get("strategyVersionId"),
            "planVersion": plan.get("plan_version"),
            "policyRevision": run_input.get("policyRevision") or plan.get("policy_revision"),
            "registrySnapshot": plan.get("registry_snapshot"),
        }
        validating.update(
            {key: value for key, value in optional_validation_fields.items() if value is not None}
        )

        queued: dict[str, Any] = {
            "taskQueue": str(run_input.get("controlTaskQueue") or _CONTROL_QUEUE),
            "nodeCount": len(plan["nodes"]),
            "maxParallelism": int(budget["maxParallelism"]),
        }
        if plan.get("entrypoint") is not None:
            queued["entrypoint"] = plan["entrypoint"]

        started: dict[str, Any] = {
            "nodeCount": len(plan["nodes"]),
            "maxParallelism": int(budget["maxParallelism"]),
        }
        if plan.get("runtime_version") is not None:
            started["runtimeVersion"] = plan["runtime_version"]

        return {
            "run.validating": validating,
            "run.queued": queued,
            "run.started": started,
        }

    async def _cancel_run(self) -> None:
        for key, state in self._states.items():
            if state in {NodeState.PENDING, NodeState.RUNNING}:
                self._states[key] = NodeState.CANCELLED
                await self._project("task.cancelled", {"nodeKey": key})
        await self._project("run.cancelling", {})
        await self._compensate_effects()
        await self._project("run.cancelled", {})

    async def _compensate_effects(self) -> None:
        while self._compensation_stack:
            entry = self._compensation_stack.pop()
            if entry["recoveryPolicy"] == "idempotent":
                continue
            if entry["recoveryPolicy"] == "manual":
                await self._project("compensation.manual_required", entry)
                continue
            token = await self._issue_tool_capability(
                node_key=str(entry["nodeKey"]),
                tool_ref=str(entry["toolRef"]),
                execution_id=str(workflow.uuid4()),
                effect_id=str(entry["effectId"]),
                approved=True,
                action="tool.compensate",
            )
            try:
                result = await workflow.execute_activity(
                    "compensate_tool",
                    {
                        "capabilityToken": token,
                        "effectId": entry["effectId"],
                        "input": entry["input"],
                    },
                    task_queue=self._tool_queue,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                    result_type=dict[str, Any],
                )
            except BaseException as exc:
                await self._project(
                    "compensation.failed",
                    {**entry, "error": self._safe_error(exc)},
                )
            else:
                await self._project(
                    "compensation.completed",
                    {**entry, "result": result},
                )

    def _all_terminal(self) -> bool:
        terminal = {
            NodeState.SUCCEEDED,
            NodeState.FAILED,
            NodeState.CANCELLED,
            NodeState.SKIPPED,
            NodeState.BLOCKED,
        }
        return bool(self._states) and all(state in terminal for state in self._states.values())

    def _render_result(self, plan: dict[str, Any], nodes: list[dict[str, Any]]) -> Any:
        reducers = plan.get("result_reducer", {})
        if reducers:
            return self._outputs.get(sorted(reducers)[-1])
        if not self._outputs:
            return None
        depended_on = {dependency for node in nodes for dependency in node.get("dependencies", [])}
        sinks = [str(node["key"]) for node in nodes if str(node["key"]) not in depended_on]
        for key in reversed(sinks):
            if key in self._outputs:
                return self._outputs[key]
        return self._outputs[next(reversed(self._outputs))]

    def _activity_for(self, node_type: str) -> tuple[str, str]:
        if node_type == "agent":
            return "execute_agent", self._agent_queue
        if node_type == "team":
            return "execute_team", self._agent_queue
        if node_type == "tool":
            return "execute_tool", self._tool_queue
        return "execute_control_node", self._control_queue

    @staticmethod
    def _valid_schema(value: Any, schema: dict[str, Any]) -> bool:
        expected = schema.get("type")
        if expected == "object":
            if not isinstance(value, dict):
                return False
            if any(key not in value for key in schema.get("required", [])):
                return False
            properties = schema.get("properties", {})
            return all(
                key not in properties or SwarmRunWorkflow._valid_schema(item, properties[key])
                for key, item in value.items()
            )
        if expected == "array":
            return isinstance(value, list) and all(
                SwarmRunWorkflow._valid_schema(item, schema.get("items", {})) for item in value
            )
        if expected == "string":
            return isinstance(value, str)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "number":
            return isinstance(value, int | float) and not isinstance(value, bool)
        if expected == "boolean":
            return isinstance(value, bool)
        return True

    @staticmethod
    def _safe_error(error: BaseException) -> dict[str, str]:
        cause = getattr(error, "cause", None)
        return {
            "type": type(error).__name__,
            "message": str(cause or error)[:2000],
        }
