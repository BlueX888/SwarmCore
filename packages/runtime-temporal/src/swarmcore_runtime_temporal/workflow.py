from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any, cast

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.workflow import ActivityCancellationType

from .scheduler import NodeState, blocked_by_failure, ready_nodes

_CONTROL_QUEUE = "swarm-control"
_AGENT_QUEUE = "agent-general"
_TOOL_QUEUE = "tool-trusted"


@workflow.defn(name="SwarmRunWorkflow")
class SwarmRunWorkflow:
    """Deterministic execution interpreter with durable, ordered human-control commands."""

    def __init__(self) -> None:
        self._run_input: dict[str, Any] = {}
        self._nodes: list[dict[str, Any]] = []
        self._states: dict[str, NodeState] = {}
        self._outputs: dict[str, Any] = {}
        self._last_applied_command_seq = 0
        self._command_results: dict[int, dict[str, Any]] = {}
        self._request_results: dict[str, dict[str, Any]] = {}
        self._cancel_requested = False
        self._pause_requested = False
        self._paused = False
        self._failure_wait = False
        self._human_requests: dict[str, dict[str, Any]] = {}
        self._in_flight: set[asyncio.Task[dict[str, Any]]] = set()

    @workflow.run
    async def run(self, run_input: dict[str, Any]) -> dict[str, Any]:
        self._run_input = run_input
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
            task_queue=_CONTROL_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=0),
            result_type=dict[str, Any],
        )
        self._nodes = list(plan["nodes"])
        self._states = {str(node["key"]): NodeState.PENDING for node in self._nodes}
        await self._project("run.validating", {})
        await self._project("run.queued", {})
        await self._project("run.started", {})

        max_parallelism = int(plan["budget"]["maxParallelism"])
        while True:
            if self._cancel_requested:
                await self._cancel_run()
                return {"status": "CANCELLED", "outputs": self._outputs}
            await self._pause_barrier()
            if self._cancel_requested:
                continue

            for key in blocked_by_failure(self._nodes, self._states):
                self._states[key] = NodeState.SKIPPED
                await self._project("task.skipped", {"nodeKey": key})

            if self._all_terminal():
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

            batch = ready_nodes(self._nodes, self._states, max_parallelism=max_parallelism)
            if not batch:
                await self._project("run.failed", {"code": "GRAPH_DEADLOCK"})
                await workflow.wait_condition(workflow.all_handlers_finished)
                return {"status": "FAILED", "code": "GRAPH_DEADLOCK"}

            by_key = {str(node["key"]): node for node in self._nodes}
            tasks = {
                key: asyncio.create_task(
                    self._execute_node(
                        by_key[key],
                        plan.get("resolved_agents", {}),
                        plan.get("defaults", {}).get("model"),
                    )
                )
                for key in batch
            }
            self._in_flight.update(tasks.values())
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            self._in_flight.difference_update(tasks.values())
            for key, outcome in zip(tasks, results, strict=True):
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
                    await self._project("task.completed", {"nodeKey": key, "output": outcome})

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
            for task in self._in_flight:
                task.cancel()
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
                if state == NodeState.SKIPPED:
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
    ) -> dict[str, Any]:
        key = str(node["key"])
        self._states[key] = NodeState.RUNNING
        await self._project(
            "task.started",
            {
                "nodeKey": key,
                "nodeType": node["type"],
                "dependencies": node.get("dependencies", []),
            },
        )
        if node["type"] in {"approval", "input"}:
            return await self._wait_for_human(node)
        activity_name, queue = self._activity_for(str(node["type"]))
        payload: dict[str, Any] = {
            "run": self._run_input,
            "node": node,
            "taskExecutionId": str(workflow.uuid4()),
            "agentInstanceId": str(workflow.uuid4()),
            "dependencyOutputs": {
                dependency: self._outputs[dependency] for dependency in node.get("dependencies", [])
            },
        }
        if node["type"] == "agent":
            payload["agent"] = resolved_agents[node["config"]["agent"]]
            payload["defaultModel"] = default_model
        result = await workflow.execute_activity(
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
        return cast(dict[str, Any], result)

    async def _wait_for_human(self, node: dict[str, Any]) -> dict[str, Any]:
        request_id = str(workflow.uuid4())
        kind = str(node["type"])
        request = {
            "kind": kind,
            "nodeKey": str(node["key"]),
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

    async def _project(self, event_type: str, data: dict[str, Any]) -> None:
        await workflow.execute_activity(
            "project_transition",
            {
                "run": self._run_input,
                "transitionId": str(workflow.uuid4()),
                "type": event_type,
                "data": data,
            },
            task_queue=_CONTROL_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=0),
        )

    async def _cancel_run(self) -> None:
        for key, state in self._states.items():
            if state in {NodeState.PENDING, NodeState.RUNNING}:
                self._states[key] = NodeState.CANCELLED
                await self._project("task.cancelled", {"nodeKey": key})
        await self._project("run.cancelling", {})
        await self._project("run.cancelled", {})

    def _all_terminal(self) -> bool:
        terminal = {
            NodeState.SUCCEEDED,
            NodeState.FAILED,
            NodeState.CANCELLED,
            NodeState.SKIPPED,
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

    @staticmethod
    def _activity_for(node_type: str) -> tuple[str, str]:
        if node_type == "agent":
            return "execute_agent", _AGENT_QUEUE
        if node_type == "team":
            return "execute_team", _AGENT_QUEUE
        if node_type == "tool":
            return "execute_tool", _TOOL_QUEUE
        return "execute_control_node", _CONTROL_QUEUE

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
