from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any, cast

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError
from temporalio.workflow import ActivityCancellationType

from .scheduler import NodeState, blocked_by_failure, ready_nodes

_CONTROL_QUEUE = "swarm-control"
_AGENT_QUEUE = "agent-general"
_TOOL_QUEUE = "tool-trusted"


@workflow.defn(name="SwarmRunWorkflow")
class SwarmRunWorkflow:
    def __init__(self) -> None:
        self._run_input: dict[str, Any] = {}
        self._states: dict[str, NodeState] = {}
        self._outputs: dict[str, Any] = {}
        self._last_applied_command_seq = 0
        self._command_results: dict[int, dict[str, Any]] = {}
        self._cancel_requested = False
        self._in_flight: set[asyncio.Task[dict[str, Any]]] = set()

    @workflow.run
    async def run(self, run_input: dict[str, Any]) -> dict[str, Any]:
        self._run_input = run_input
        start_command = run_input.get("startCommand")
        if start_command:
            sequence = int(start_command["commandSeq"])
            self._last_applied_command_seq = sequence
            self._command_results[sequence] = {"status": "APPLIED"}
        plan = await workflow.execute_activity(
            "load_execution_plan",
            run_input,
            task_queue=_CONTROL_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=0),
            result_type=dict[str, Any],
        )
        nodes = list(plan["nodes"])
        self._states = {str(node["key"]): NodeState.PENDING for node in nodes}
        await self._project("run.validating", {})
        await self._project("run.queued", {})
        await self._project("run.started", {})

        max_parallelism = int(plan["budget"]["maxParallelism"])
        while not self._all_terminal():
            if self._cancel_requested:
                await self._cancel_run()
                return {"status": "CANCELLED", "outputs": self._outputs}

            for key in blocked_by_failure(nodes, self._states):
                self._states[key] = NodeState.SKIPPED
                await self._project("task.skipped", {"nodeKey": key})

            batch = ready_nodes(nodes, self._states, max_parallelism=max_parallelism)
            if not batch:
                if self._all_terminal():
                    break
                await self._project("run.failed", {"code": "GRAPH_DEADLOCK"})
                return {"status": "FAILED", "code": "GRAPH_DEADLOCK"}

            by_key = {str(node["key"]): node for node in nodes}
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
            for key, result in zip(tasks, results, strict=True):
                if isinstance(result, asyncio.CancelledError):
                    self._states[key] = NodeState.CANCELLED
                elif isinstance(result, BaseException):
                    self._states[key] = NodeState.FAILED
                    await self._project(
                        "task.failed", {"nodeKey": key, "error": self._safe_error(result)}
                    )
                else:
                    self._states[key] = NodeState.SUCCEEDED
                    self._outputs[key] = result
                    await self._project("task.completed", {"nodeKey": key, "output": result})

        if any(state == NodeState.FAILED for state in self._states.values()):
            await self._project("run.failed", {"code": "TASK_FAILED"})
            return {"status": "FAILED", "outputs": self._outputs}

        result = self._render_result(plan, nodes)
        await self._project("run.completed", {"result": result})
        return {"status": "SUCCEEDED", "result": result, "outputs": self._outputs}

    @workflow.update(name="apply_command")
    async def apply_command(self, command: dict[str, Any]) -> dict[str, Any]:
        sequence = int(command["commandSeq"])
        if sequence <= self._last_applied_command_seq:
            return self._command_results[sequence]
        if sequence != self._last_applied_command_seq + 1:
            return {
                "status": "REJECTED",
                "code": "COMMAND_OUT_OF_ORDER",
                "lastAppliedCommandSeq": self._last_applied_command_seq,
            }
        command_type = str(command["type"])
        if command_type == "start":
            result = {"status": "APPLIED"}
        elif command_type == "cancel":
            self._cancel_requested = True
            for task in self._in_flight:
                task.cancel()
            result = {"status": "APPLIED"}
        else:
            result = {"status": "REJECTED", "code": "COMMAND_NOT_SUPPORTED_IN_PHASE_1"}
        self._last_applied_command_seq = sequence
        self._command_results[sequence] = result
        return result

    @workflow.query(name="engine_state")
    def engine_state(self) -> dict[str, Any]:
        return {
            "states": {key: value.value for key, value in self._states.items()},
            "lastAppliedCommandSeq": self._last_applied_command_seq,
            "cancelRequested": self._cancel_requested,
            "inFlightCount": len(self._in_flight),
        }

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
        await self._project("run.cancelling", {})
        for key, state in self._states.items():
            if state in {NodeState.PENDING, NodeState.RUNNING}:
                self._states[key] = NodeState.CANCELLED
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
            last_reducer = sorted(reducers)[-1]
            return self._outputs.get(last_reducer)
        if not self._outputs:
            return None
        depended_on = {
            dependency for node in nodes for dependency in node.get("dependencies", [])
        }
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
    def _safe_error(error: BaseException) -> dict[str, str]:
        if isinstance(error, ActivityError):
            return {"type": "ActivityError", "message": str(error.cause or error)}
        return {"type": type(error).__name__, "message": str(error)}
