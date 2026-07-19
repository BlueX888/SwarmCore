from __future__ import annotations

# The generated report intentionally contains Chinese full-width punctuation and long Markdown
# table rows; those are artifact content rather than Python source style.
# ruff: noqa: E402, E501, RUF001
import argparse
import asyncio
import hashlib
import json
import math
import os
import platform
import re
import shutil
import socket
import statistics
import subprocess
import sys
import time
from collections import Counter
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

# Keep direct script execution and importlib-based unit loading consistent.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import asyncpg
import grpc
import httpx
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2, metrics_service_pb2_grpc
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2, trace_service_pb2_grpc
from temporalio.api.enums.v1 import TaskQueueType
from temporalio.api.taskqueue.v1 import TaskQueue
from temporalio.api.workflowservice.v1 import DescribeTaskQueueRequest
from temporalio.client import Client

from scripts.system_evaluation.fallback_resource_sampler import (
    descendants,
    snapshot_processes,
    terminate_process,
)

TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "CANCELLED", "TIMED_OUT", "REJECTED"}
TERMINAL_EVENTS = {
    "run.completed": "SUCCEEDED",
    "run.failed": "FAILED",
    "run.cancelled": "CANCELLED",
    "run.timed_out": "TIMED_OUT",
    "run.rejected": "REJECTED",
}
RUN_TRANSITIONS = {
    "run.accepted": {"run.validating", "run.cancelling", "run.failed"},
    "run.validating": {"run.queued", "run.rejected", "run.cancelling"},
    "run.queued": {"run.started", "run.pausing", "run.cancelling"},
    "run.started": {
        "run.waiting_input",
        "run.waiting_approval",
        "run.pausing",
        "run.cancelling",
        "run.completed",
        "run.failed",
        "run.timed_out",
    },
    "run.waiting_input": {"run.started", "run.pausing", "run.cancelling"},
    "run.waiting_approval": {"run.started", "run.pausing", "run.cancelling"},
    "run.pausing": {"run.paused", "run.cancelling"},
    "run.paused": {"run.started", "run.cancelling"},
    "run.cancelling": {"run.cancelled", "run.compensating"},
    "run.compensating": {"run.cancelled", "run.failed"},
}
TENANT_ID = "00000000-0000-0000-0000-000000000001"
PROJECT_ID = "00000000-0000-0000-0000-000000000002"


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_now() -> str:
    return utc_now().isoformat()


def parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def distribution(values: list[float], *, include_max: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "sampleCount": len(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "p95SampleSufficient": len(values) >= 200,
        "p99SampleSufficient": len(values) >= 1000,
    }
    if include_max:
        result["max"] = max(values) if values else None
    return result


def validate_event_sequence(events: list[dict[str, Any]]) -> list[str]:
    violations: list[str] = []
    seqs = [int(item["seq"]) for item in events]
    if len(seqs) != len(set(seqs)):
        violations.append("DUPLICATE_EVENT_SEQ")
    if seqs != sorted(seqs):
        violations.append("OUT_OF_ORDER_EVENT_SEQ")
    if seqs and seqs != list(range(seqs[0], seqs[-1] + 1)):
        violations.append("EVENT_SEQ_GAP")
    if seqs and seqs[0] != 1:
        violations.append("EVENT_SEQ_DOES_NOT_START_AT_1")
    terminals = [item for item in events if item["type"] in TERMINAL_EVENTS]
    if len(terminals) != 1:
        violations.append("TERMINAL_EVENT_COUNT")
    run_events = [item["type"] for item in events if item["type"].startswith("run.")]
    for previous, current in pairwise(run_events):
        if previous in TERMINAL_EVENTS:
            violations.append("EVENT_AFTER_TERMINAL")
        elif current not in RUN_TRANSITIONS.get(previous, set()):
            violations.append(f"ILLEGAL_RUN_TRANSITION:{previous}->{current}")
    return violations


def hash_key(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(type(value).__name__)


def evidence_tree_hash(root: Path, excluded: set[str]) -> str:
    aggregate = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.relative_to(root).as_posix() in excluded:
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        relative = path.relative_to(root).as_posix()
        aggregate.update(f"{digest.hexdigest()}  {relative}\n".encode())
    return aggregate.hexdigest()


class Evidence:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.metrics = root / "metrics"
        self.logs = root / "logs"
        self.events = root / "events"
        self.raw = self.metrics / "raw"
        for path in (root, self.metrics, self.logs, self.events, self.raw):
            path.mkdir(parents=True, exist_ok=True)
        self._locks: dict[Path, asyncio.Lock] = {}

    def write_json(self, relative: str, value: Any) -> None:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(value, indent=2, ensure_ascii=False, default=json_default) + "\n",
            encoding="utf-8",
        )

    async def append_jsonl(self, relative: str, value: Any) -> None:
        target = self.root / relative
        lock = self._locks.setdefault(target, asyncio.Lock())
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=json_default)
        async with lock:
            with target.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded + "\n")


class MetricsReceiver(metrics_service_pb2_grpc.MetricsServiceServicer):
    def __init__(self, evidence: Evidence) -> None:
        self.evidence = evidence
        self.exports = 0

    async def Export(self, request: Any, context: Any) -> Any:
        self.exports += 1
        await self.evidence.append_jsonl(
            "metrics/swarmcore-otel.jsonl",
            {
                "receivedAt": iso_now(),
                "request": MessageToDict(request, preserving_proto_field_name=True),
            },
        )
        return metrics_service_pb2.ExportMetricsServiceResponse()


class TraceReceiver(trace_service_pb2_grpc.TraceServiceServicer):
    def __init__(self, evidence: Evidence) -> None:
        self.evidence = evidence

    async def Export(self, request: Any, context: Any) -> Any:
        spans = sum(
            len(scope.spans)
            for resource in request.resource_spans
            for scope in resource.scope_spans
        )
        await self.evidence.append_jsonl(
            "metrics/swarmcore-trace-export-summary.jsonl",
            {"receivedAt": iso_now(), "spanCount": spans},
        )
        return trace_service_pb2.ExportTraceServiceResponse()


class OtlpServer:
    def __init__(self, evidence: Evidence, port: int) -> None:
        self.server = grpc.aio.server()
        self.metrics = MetricsReceiver(evidence)
        metrics_service_pb2_grpc.add_MetricsServiceServicer_to_server(self.metrics, self.server)
        trace_service_pb2_grpc.add_TraceServiceServicer_to_server(
            TraceReceiver(evidence), self.server
        )
        self.server.add_insecure_port(f"127.0.0.1:{port}")

    async def start(self) -> None:
        await self.server.start()

    async def stop(self) -> None:
        await self.server.stop(grace=2)


@dataclass
class ManagedProcess:
    service: str
    generation: int
    process: subprocess.Popen[bytes]
    stdout: Any
    stderr: Any
    started_at: str
    injected_stops: int = 0


class ProcessManager:
    def __init__(self, root: Path, evidence: Evidence, environment: dict[str, str]) -> None:
        self.root = root
        self.evidence = evidence
        self.environment = environment
        self.processes: dict[str, ManagedProcess] = {}
        self.history: list[dict[str, Any]] = []

    def start(self, service: str, executable: str) -> ManagedProcess:
        previous = self.processes.get(service)
        generation = previous.generation + 1 if previous else 1
        stdout_path = self.evidence.logs / f"{service}-g{generation}.stdout.log"
        stderr_path = self.evidence.logs / f"{service}-g{generation}.stderr.log"
        stdout = stdout_path.open("wb")
        stderr = stderr_path.open("wb")
        executable_path = self.root / ".venv" / "Scripts" / "python.exe"
        modules = {
            "swarmcore-api": "swarmcore_api.main",
            "swarmcore-command-dispatcher": "swarmcore_command_dispatcher.main",
            "swarmcore-worker-control": "swarmcore_worker_control.main",
            "swarmcore-worker-agent": "swarmcore_worker_agent.main",
            "swarmcore-event-publisher": "swarmcore_event_publisher.main",
            "swarmcore-projection-reconciler": "swarmcore_projection_reconciler.main",
        }
        module = modules[executable]
        if not executable_path.exists():
            raise FileNotFoundError(executable_path)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen(
            [str(executable_path), "-c", f"from {module} import run; run()"],
            cwd=self.root,
            env=self.environment,
            stdout=stdout,
            stderr=stderr,
            creationflags=flags,
        )
        managed = ManagedProcess(service, generation, process, stdout, stderr, iso_now())
        self.processes[service] = managed
        self.history.append(
            {
                "service": service,
                "generation": generation,
                "pid": process.pid,
                "startedAt": managed.started_at,
                "executable": str(executable_path),
                "module": module,
            }
        )
        self._write_manifest()
        return managed

    async def inject_agent_fault(self) -> str:
        managed = self.processes["worker-agent"]
        root_pid = managed.process.pid
        target_pid = root_pid
        if os.name == "nt":
            processes = await asyncio.to_thread(snapshot_processes)
            children = descendants(processes, root_pid)
            python_children = [
                item
                for item in children
                if int(item["Id"]) != root_pid
                and str(item.get("ProcessName", "")).lower() == "python.exe"
            ]
            if python_children:
                target_pid = int(max(python_children, key=lambda item: item.get("CPU", 0))["Id"])
        fault = iso_now()
        if os.name == "nt":
            await asyncio.to_thread(terminate_process, target_pid)
        else:
            managed.process.kill()
        try:
            await asyncio.to_thread(managed.process.wait, 10)
        except subprocess.TimeoutExpired:
            managed.process.kill()
            await asyncio.to_thread(managed.process.wait, 10)
        managed.stdout.close()
        managed.stderr.close()
        managed.injected_stops += 1
        history = next(
            item
            for item in reversed(self.history)
            if item["service"] == managed.service and item["generation"] == managed.generation
        )
        history["stoppedAt"] = iso_now()
        history["stopReason"] = "E3_FORCED_TERMINATION"
        history["terminatedPid"] = target_pid
        self._write_manifest()
        return fault

    def unexpected_exits(self) -> list[dict[str, Any]]:
        values = []
        for service, managed in self.processes.items():
            code = managed.process.poll()
            if code is not None:
                values.append(
                    {
                        "service": service,
                        "generation": managed.generation,
                        "pid": managed.process.pid,
                        "exitCode": code,
                    }
                )
        return values

    async def stop_all(self) -> None:
        for managed in reversed(list(self.processes.values())):
            if managed.process.poll() is None:
                if os.name == "nt":
                    await asyncio.to_thread(
                        subprocess.run,
                        ["taskkill", "/PID", str(managed.process.pid), "/T", "/F"],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                else:
                    managed.process.terminate()
        for managed in reversed(list(self.processes.values())):
            if managed.process.poll() is None:
                try:
                    await asyncio.to_thread(managed.process.wait, 10)
                except subprocess.TimeoutExpired:
                    managed.process.kill()
            managed.stdout.close()
            managed.stderr.close()
        self._write_manifest()

    def _write_manifest(self) -> None:
        active = [
            {
                "service": item.service,
                "generation": item.generation,
                "pid": item.process.pid,
                "exitCode": item.process.poll(),
            }
            for item in self.processes.values()
        ]
        self.evidence.write_json("processes.json", {"active": active, "history": self.history})


@dataclass
class ScenarioAccumulator:
    scenario: str
    level: int | str
    started_at: str = field(default_factory=iso_now)
    finished_at: str | None = None
    accepted: int = 0
    succeeded: int = 0
    http_errors: Counter[int] = field(default_factory=Counter)
    client_errors: Counter[str] = field(default_factory=Counter)
    event_violations: int = 0
    state_inconsistencies: int = 0
    illegal_transitions: int = 0
    replay_attempts: int = 0
    replay_matches: int = 0
    api_ms: list[float] = field(default_factory=list)
    queue_ms: list[float] = field(default_factory=list)
    e2e_ms: list[float] = field(default_factory=list)
    sse_ms: list[float] = field(default_factory=list)
    projection_ms: list[float] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)
    window_seconds: float = 0.0
    backlog_recovery_seconds: float | None = None
    backlog_recovered: bool | None = None
    unexpected_exits: list[dict[str, Any]] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def add(self, sample: dict[str, Any], events: list[dict[str, Any]]) -> None:
        async with self._lock:
            status = int(sample["httpStatus"])
            if status == 202 and sample.get("runId"):
                self.accepted += 1
                self.run_ids.append(sample["runId"])
            else:
                self.http_errors[status] += 1
            if sample.get("error"):
                self.client_errors[str(sample["error"])] += 1
            if sample.get("snapshotStatus") == "SUCCEEDED":
                self.succeeded += 1
            for name, target in (
                ("apiLatencyMs", self.api_ms),
                ("queueLatencyMs", self.queue_ms),
                ("endToEndLatencyMs", self.e2e_ms),
                ("projectionLatencyMs", self.projection_ms),
            ):
                value = sample.get(name)
                if isinstance(value, int | float):
                    target.append(float(value))
            for event in events:
                value = event.get("sseLatencyMs")
                if isinstance(value, int | float):
                    self.sse_ms.append(float(value))
            violations = sample.get("eventViolations", [])
            if violations:
                self.event_violations += 1
                self.illegal_transitions += sum(
                    str(item).startswith("ILLEGAL_RUN_TRANSITION") for item in violations
                )
            if sample.get("stateConsistent") is False:
                self.state_inconsistencies += 1
            replay = sample.get("replay")
            if replay:
                self.replay_attempts += 1
                if replay.get("runId") == sample.get("runId") and replay.get("httpStatus") == 202:
                    self.replay_matches += 1

    def summary(self) -> dict[str, Any]:
        c1 = self.succeeded / self.accepted if self.accepted else 0.0
        return {
            "scenario": self.scenario,
            "level": self.level,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "windowSeconds": self.window_seconds,
            "C1": {"value": c1, "sampleCount": self.accepted, "threshold": 1.0},
            "C2": {"value": self.accepted - self.succeeded, "threshold": 0},
            "C3": {
                "value": self.replay_matches / self.replay_attempts
                if self.replay_attempts
                else None,
                "sampleCount": self.replay_attempts,
                "threshold": 1.0,
            },
            "C4": {"value": self.event_violations, "threshold": 0},
            "C5": {"value": self.state_inconsistencies, "threshold": 0},
            "C6": {"value": "PENDING_LOG_AND_OTLP_ANALYSIS", "threshold": 0},
            "C7": {"value": len(self.unexpected_exits), "threshold": 0},
            "P1": distribution(self.api_ms),
            "P2": distribution(self.api_ms),
            "P3": distribution(self.queue_ms),
            "P4": distribution(self.sse_ms),
            "P5": distribution(self.projection_ms),
            "P6": distribution(self.e2e_ms, include_max=True),
            "P7": {
                "completedRunsPerSecond": self.succeeded / self.window_seconds
                if self.window_seconds
                else None,
                "sampleCount": self.succeeded,
            },
            "Q2": {
                "recovered": self.backlog_recovered,
                "recoverySeconds": self.backlog_recovery_seconds,
                "thresholdSeconds": 60,
            },
            "httpErrors": dict(self.http_errors),
            "clientErrors": dict(self.client_errors),
        }


class RunTracker:
    def __init__(
        self,
        evaluator: Evaluator,
        scenario: str,
        level: int | str,
        phase: str,
        request_id: str,
        key: str,
        body: dict[str, Any],
        response: httpx.Response,
        submit_start_wall: datetime,
        submit_start_mono: float,
        accept_wall: datetime,
        accept_mono: float,
    ) -> None:
        self.evaluator = evaluator
        self.scenario = scenario
        self.level = level
        self.phase = phase
        self.request_id = request_id
        self.key = key
        self.body = body
        self.response = response
        self.submit_start_wall = submit_start_wall
        self.submit_start_mono = submit_start_mono
        self.accept_wall = accept_wall
        self.accept_mono = accept_mono
        self.run_id = str(response.json()["runId"]) if response.status_code == 202 else None
        self.sse_received: dict[int, str] = {}
        self.sse_error: str | None = None
        self.snapshot: dict[str, Any] | None = None
        self.snapshot_terminal_at: datetime | None = None
        self._sse_task: asyncio.Task[None] | None = None
        if self.run_id:
            self._sse_task = asyncio.create_task(self._collect_sse())

    async def _collect_sse(self) -> None:
        assert self.run_id is not None
        url = self.evaluator.run_url(self.run_id, "events")
        try:
            async with self.evaluator.client.stream(
                "GET", url, params={"after": 0}, headers=self.evaluator.headers
            ) as response:
                if response.status_code != 200:
                    self.sse_error = f"SSE_HTTP_{response.status_code}"
                    return
                data_lines: list[str] = []
                async for line in response.aiter_lines():
                    if line == "":
                        if data_lines:
                            document = json.loads("\n".join(data_lines))
                            self.sse_received[int(document["seq"])] = iso_now()
                            data_lines.clear()
                            if document["type"] in TERMINAL_EVENTS:
                                return
                        continue
                    if line.startswith("data:"):
                        data_lines.append(line[5:].lstrip())
        except (httpx.HTTPError, asyncio.CancelledError) as exc:
            if not isinstance(exc, asyncio.CancelledError):
                self.sse_error = f"{type(exc).__name__}:{exc}"

    async def wait_for_event(self, event_type: str, timeout: float) -> dict[str, Any]:
        assert self.run_id is not None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            events = await self.evaluator.fetch_events(self.run_id)
            for event in events:
                if event["type"] == event_type:
                    return event
            await asyncio.sleep(0.1)
        raise TimeoutError(f"{self.run_id} did not emit {event_type} within {timeout}s")

    async def finish(self, timeout: float = 60.0, replay: bool = False) -> dict[str, Any]:
        replay_value: dict[str, Any] | None = None
        if replay and self.run_id:
            replay_response = await self.evaluator.client.post(
                self.evaluator.runs_url,
                headers={**self.evaluator.headers, "Idempotency-Key": self.key},
                json=self.body,
            )
            replay_value = {
                "httpStatus": replay_response.status_code,
                "runId": replay_response.json().get("runId")
                if replay_response.headers.get("content-type", "").startswith("application/json")
                else None,
            }
        error: str | None = None
        events: list[dict[str, Any]] = []
        result: dict[str, Any] | None = None
        created_at: datetime | None = None
        try:
            if self.run_id:
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    response = await self.evaluator.client.get(
                        self.evaluator.run_url(self.run_id), headers=self.evaluator.headers
                    )
                    if response.status_code != 200:
                        error = f"SNAPSHOT_HTTP_{response.status_code}"
                        break
                    self.snapshot = response.json()
                    if self.snapshot["status"] in TERMINAL_STATUSES:
                        self.snapshot_terminal_at = utc_now()
                        break
                    await asyncio.sleep(0.1)
                else:
                    error = "TERMINAL_TIMEOUT"
                if self.snapshot_terminal_at:
                    events = await self.evaluator.fetch_events(self.run_id)
                    created_at = await self.evaluator.run_created_at(self.run_id)
                    result_response = await self.evaluator.client.get(
                        self.evaluator.run_url(self.run_id, "result"),
                        headers=self.evaluator.headers,
                    )
                    if result_response.status_code == 200:
                        result = result_response.json()
                    else:
                        error = error or f"RESULT_HTTP_{result_response.status_code}"
        except (httpx.HTTPError, asyncpg.PostgresError, ValueError) as exc:
            error = f"{type(exc).__name__}:{exc}"
        if self._sse_task:
            try:
                await asyncio.wait_for(self._sse_task, timeout=5)
            except (TimeoutError, asyncio.CancelledError):
                self._sse_task.cancel()
        terminal = next((item for item in events if item["type"] in TERMINAL_EVENTS), None)
        started = next((item for item in events if item["type"] == "run.started"), None)
        violations = validate_event_sequence(events)
        snapshot_status = self.snapshot.get("status") if self.snapshot else None
        result_status = result.get("status") if result else None
        expected_status = TERMINAL_EVENTS.get(terminal["type"]) if terminal else None
        state_consistent = (
            snapshot_status is not None
            and snapshot_status == result_status
            and snapshot_status == expected_status
        )
        terminal_at = parse_time(terminal.get("occurredAt")) if terminal else None
        started_at = parse_time(started.get("occurredAt")) if started else None
        queue_ms = (
            (started_at - created_at).total_seconds() * 1000 if started_at and created_at else None
        )
        e2e_ms = (
            (terminal_at - created_at).total_seconds() * 1000
            if terminal_at and created_at
            else None
        )
        projection_ms = (
            max(0.0, (self.snapshot_terminal_at - terminal_at).total_seconds() * 1000)
            if self.snapshot_terminal_at and terminal_at
            else None
        )
        event_rows = []
        for event in events:
            received = parse_time(self.sse_received.get(int(event["seq"])))
            occurred = parse_time(event.get("occurredAt"))
            row = {
                "scenario": self.scenario,
                "level": self.level,
                "phase": self.phase,
                **event,
                "tSseReceive": received.isoformat() if received else None,
                "sseLatencyMs": max(0.0, (received - occurred).total_seconds() * 1000)
                if received and occurred
                else None,
            }
            event_rows.append(row)
            await self.evaluator.evidence.append_jsonl("run-events.jsonl", row)
        sample = {
            "scenario": self.scenario,
            "level": self.level,
            "phase": self.phase,
            "requestId": self.request_id,
            "idempotencyKeyHash": hash_key(self.key),
            "runId": self.run_id,
            "httpStatus": self.response.status_code,
            "tSubmitStart": self.submit_start_wall.isoformat(),
            "tAccept": self.accept_wall.isoformat(),
            "tRunCreated": created_at.isoformat() if created_at else None,
            "tRunStarted": started_at.isoformat() if started_at else None,
            "tTerminal": terminal_at.isoformat() if terminal_at else None,
            "tSnapshotTerminal": self.snapshot_terminal_at.isoformat()
            if self.snapshot_terminal_at
            else None,
            "apiLatencyMs": (self.accept_mono - self.submit_start_mono) * 1000,
            "queueLatencyMs": queue_ms,
            "endToEndLatencyMs": e2e_ms,
            "projectionLatencyMs": projection_ms,
            "snapshotStatus": snapshot_status,
            "resultStatus": result_status,
            "stateConsistent": state_consistent,
            "eventViolations": violations,
            "sseError": self.sse_error,
            "replay": replay_value,
            "error": error,
        }
        await self.evaluator.evidence.append_jsonl("client-samples.jsonl", sample)
        return {"sample": sample, "events": event_rows}


class Evaluator:
    def __init__(self, args: argparse.Namespace, root: Path, evidence: Evidence) -> None:
        self.args = args
        self.root = root
        self.evidence = evidence
        self.api_url = f"http://127.0.0.1:{args.api_port}"
        self.runs_url = f"{self.api_url}/v1/projects/{PROJECT_ID}/runs"
        self.headers = {"X-Tenant-ID": TENANT_ID}
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10, read=None, write=30, pool=30),
            limits=httpx.Limits(max_connections=512, max_keepalive_connections=128),
        )
        self.database_dsn = (
            f"postgresql://swarmcore:swarmcore@127.0.0.1:{args.postgres_port}/swarmcore_eval"
        )
        self.database_url = self.database_dsn.replace("postgresql://", "postgresql+asyncpg://")
        self.db: asyncpg.Pool[Any] | None = None
        self.temporal: Client | None = None
        self.strategy_version_id = ""
        self.plan_hash = ""
        self.current_scenario = "PREPARATION"
        self.stop_metrics = asyncio.Event()
        self.metrics_task: asyncio.Task[None] | None = None
        self.process_manager: ProcessManager | None = None
        self.scenarios: list[ScenarioAccumulator] = []
        self.e3_result: dict[str, Any] = {}
        self.clock_max_offset_ms: float | None = None

    def run_url(self, run_id: str, suffix: str = "") -> str:
        base = f"{self.runs_url}/{run_id}"
        return f"{base}/{suffix}" if suffix else base

    async def close(self) -> None:
        self.stop_metrics.set()
        if self.metrics_task:
            await self.metrics_task
        await self.client.aclose()
        if self.db:
            await self.db.close()

    async def connect(self) -> None:
        self.db = await asyncpg.create_pool(self.database_dsn, min_size=2, max_size=20)
        self.temporal = await Client.connect(
            f"127.0.0.1:{self.args.temporal_port}", namespace="default"
        )

    async def environment_details(self) -> dict[str, Any]:
        assert self.db is not None
        async with self.db.acquire() as connection:
            postgres = await connection.fetchrow(
                "SELECT version() AS version, current_setting('max_connections') AS max_connections"
            )
            counts = {}
            for table in (
                "tenants",
                "projects",
                "strategies",
                "strategy_versions",
                "runs",
                "run_events",
                "outbox_events",
            ):
                counts[table] = await connection.fetchval(f"SELECT count(*) FROM {table}")
        nats = await self.client.get(f"http://127.0.0.1:{self.args.nats_monitor_port}/varz")
        temporal = await self.client.get(
            f"http://127.0.0.1:{self.args.temporal_metrics_port}/metrics"
        )
        build_lines = [
            line
            for line in temporal.text.splitlines()
            if re.search(r"(?i)(build_information|build_info|server_version)", line)
        ]
        return {
            "postgresql": dict(postgres or {}),
            "databaseInitialRowCounts": counts,
            "nats": nats.json() if nats.status_code == 200 else {"status": nats.status_code},
            "temporalBuildMetricLines": build_lines,
        }

    async def create_strategy(self) -> None:
        spec = {
            "apiVersion": "swarmcore.io/v1",
            "kind": "SwarmStrategy",
            "metadata": {"name": "system-evaluation-fake-deterministic-v1"},
            "spec": {
                "inputSchema": {
                    "type": "object",
                    "required": ["payload", "_delaySeconds"],
                    "properties": {
                        "payload": {"type": "string"},
                        "_delaySeconds": {"type": "number", "minimum": 0, "maximum": 30},
                    },
                    "additionalProperties": False,
                },
                "outputSchema": {"type": "object"},
                "defaults": {"model": "model://fake-deterministic@1"},
                "agents": {
                    "worker": {
                        "role": "deterministic-evaluation-worker",
                        "instructions": "Return only the deterministic adapter result.",
                        "model": "model://fake-deterministic@1",
                    }
                },
                "graph": {
                    "entrypoint": "work",
                    "nodes": {"work": {"type": "agent", "agent": "worker"}},
                    "output": {"result": "{{ tasks.work.output }}"},
                },
            },
        }
        strategy = await self.client.post(
            f"{self.api_url}/v1/projects/{PROJECT_ID}/strategies",
            headers=self.headers,
            json={"name": f"system-evaluation-{uuid4().hex[:8]}", "spec": spec},
        )
        strategy.raise_for_status()
        created = strategy.json()
        published = await self.client.post(
            f"{self.api_url}/v1/projects/{PROJECT_ID}/strategies/{created['strategyId']}/publish",
            headers=self.headers,
            json={"draftId": created["draftId"]},
        )
        published.raise_for_status()
        value = published.json()
        self.strategy_version_id = value["strategyVersionId"]
        self.plan_hash = value["planHash"]

    async def submit(self, scenario: str, level: int | str, phase: str, delay: float) -> RunTracker:
        request_id = str(uuid4())
        key = f"system-eval-{scenario}-{level}-{phase}-{request_id}"
        body = {
            "strategyVersionId": self.strategy_version_id,
            "input": {"payload": "swarmcore-system-evaluation-v1", "_delaySeconds": delay},
        }
        submit_wall = utc_now()
        submit_mono = time.perf_counter()
        try:
            response = await self.client.post(
                self.runs_url,
                headers={**self.headers, "Idempotency-Key": key},
                json=body,
            )
        except httpx.HTTPError as exc:
            response = httpx.Response(599, json={"error": f"{type(exc).__name__}:{exc}"})
        accept_mono = time.perf_counter()
        return RunTracker(
            self,
            scenario,
            level,
            phase,
            request_id,
            key,
            body,
            response,
            submit_wall,
            submit_mono,
            utc_now(),
            accept_mono,
        )

    async def execute_one(
        self,
        accumulator: ScenarioAccumulator,
        *,
        phase: str,
        delay: float,
        replay: bool = False,
        timeout: float = 60,
    ) -> dict[str, Any]:
        tracker = await self.submit(accumulator.scenario, accumulator.level, phase, delay)
        result = await tracker.finish(timeout=timeout, replay=replay)
        if phase == "sample":
            await accumulator.add(result["sample"], result["events"])
        return result

    async def fixed_load(
        self,
        accumulator: ScenarioAccumulator,
        count: int,
        concurrency: int,
        *,
        phase: str,
        delay: float,
        replay_count: int = 0,
    ) -> None:
        queue: asyncio.Queue[int] = asyncio.Queue()
        for index in range(count):
            queue.put_nowait(index)

        async def worker() -> None:
            while not queue.empty():
                try:
                    index = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                await self.execute_one(
                    accumulator,
                    phase=phase,
                    delay=delay,
                    replay=phase == "sample" and index < replay_count,
                )
                queue.task_done()

        await asyncio.gather(*(worker() for _ in range(concurrency)))

    async def duration_load(
        self, accumulator: ScenarioAccumulator, concurrency: int, duration: float, minimum: int
    ) -> None:
        started = time.monotonic()
        completed = 0
        stop = False
        lock = asyncio.Lock()

        async def worker() -> None:
            nonlocal completed, stop
            while True:
                async with lock:
                    if stop:
                        return
                await self.execute_one(accumulator, phase="sample", delay=0.2)
                async with lock:
                    completed += 1
                    if completed >= minimum and time.monotonic() - started >= duration:
                        stop = True

        await asyncio.gather(*(worker() for _ in range(concurrency)))
        accumulator.window_seconds = time.monotonic() - started

    async def fetch_events(self, run_id: str) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        after = 0
        while True:
            response = await self.client.get(
                self.run_url(run_id, "event-history"),
                params={"after": after, "limit": 1000},
                headers=self.headers,
            )
            response.raise_for_status()
            page = response.json()["items"]
            values.extend(page)
            if len(page) < 1000:
                return values
            after = int(page[-1]["seq"])

    async def run_created_at(self, run_id: str) -> datetime | None:
        assert self.db is not None
        async with self.db.acquire() as connection:
            return await connection.fetchval(
                "SELECT created_at FROM runs WHERE id = $1", UUID(run_id)
            )

    async def backlog(self) -> dict[str, Any]:
        assert self.db is not None and self.temporal is not None
        async with self.db.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT
                  count(*) FILTER (WHERE status IN ('PENDING','DELIVERING')) AS pending,
                  count(*) FILTER (WHERE status = 'DEAD') AS dead,
                  extract(epoch FROM (now() - min(available_at) FILTER
                    (WHERE status IN ('PENDING','DELIVERING')))) AS oldest_seconds
                FROM outbox_events
                """
            )
        task_queues: dict[str, Any] = {}
        for queue, queue_type in (
            ("swarm-control", TaskQueueType.TASK_QUEUE_TYPE_WORKFLOW),
            ("swarm-control", TaskQueueType.TASK_QUEUE_TYPE_ACTIVITY),
            ("agent-general", TaskQueueType.TASK_QUEUE_TYPE_ACTIVITY),
        ):
            try:
                response = await self.temporal.workflow_service.describe_task_queue(
                    DescribeTaskQueueRequest(
                        namespace="default",
                        task_queue=TaskQueue(name=queue),
                        task_queue_type=queue_type,
                        report_stats=True,
                    )
                )
                task_queues[f"{queue}:{queue_type}"] = MessageToDict(
                    response, preserving_proto_field_name=True
                )
            except Exception as exc:  # Temporal RPC diagnostics must survive the run.
                task_queues[f"{queue}:{queue_type}"] = {"error": f"{type(exc).__name__}:{exc}"}
        return {"capturedAt": iso_now(), "outbox": dict(row or {}), "taskQueues": task_queues}

    async def wait_backlog(
        self, baseline: dict[str, Any], timeout: float = 120
    ) -> tuple[bool, float]:
        started = time.monotonic()
        baseline_pending = int(baseline["outbox"].get("pending") or 0)
        while time.monotonic() - started < timeout:
            value = await self.backlog()
            await self.evidence.append_jsonl("metrics/backlog-recovery.jsonl", value)
            pending = int(value["outbox"].get("pending") or 0)
            queue_clear = all(
                int(item.get("stats", {}).get("approximate_backlog_count", 0) or 0) == 0
                for item in value["taskQueues"].values()
                if not item.get("error")
            )
            if pending <= baseline_pending and queue_clear:
                return True, time.monotonic() - started
            await asyncio.sleep(1)
        return False, time.monotonic() - started

    async def metrics_loop(self) -> None:
        while not self.stop_metrics.is_set():
            started = time.monotonic()
            components = ("postgresql", "temporal", "nats", "resources")
            results = await asyncio.gather(
                self.sample_postgres(),
                self.sample_temporal(),
                self.sample_nats(),
                self.sample_resources(),
                return_exceptions=True,
            )
            for component, result in zip(components, results, strict=True):
                if isinstance(result, BaseException):
                    await self.evidence.append_jsonl(
                        "metrics/collector-errors.jsonl",
                        {
                            "capturedAt": iso_now(),
                            "scenario": self.current_scenario,
                            "component": component,
                            "error": f"{type(result).__name__}:{result}",
                        },
                    )
            remaining = max(0.0, self.args.sample_period - (time.monotonic() - started))
            with suppress(TimeoutError):
                await asyncio.wait_for(self.stop_metrics.wait(), timeout=remaining)

    async def sample_postgres(self) -> None:
        assert self.db is not None
        async with self.db.acquire() as connection:
            started = time.perf_counter()
            await connection.fetchval("SELECT 1")
            probe_ms = (time.perf_counter() - started) * 1000
            database = await connection.fetchrow(
                """
                SELECT numbackends, xact_commit, xact_rollback, blks_read, blks_hit,
                       tup_returned, tup_fetched, tup_inserted, tup_updated, tup_deleted,
                       temp_files, temp_bytes, deadlocks, blk_read_time, blk_write_time
                FROM pg_stat_database WHERE datname = current_database()
                """
            )
            connections = await connection.fetchrow(
                """
                SELECT count(*) AS used,
                       current_setting('max_connections')::int AS configured,
                       count(*) FILTER (WHERE state = 'active') AS active
                FROM pg_stat_activity
                """
            )
            locks = await connection.fetchrow(
                """
                SELECT count(*) FILTER (WHERE NOT granted) AS waiting,
                       coalesce(max(extract(epoch FROM (now() - query_start)))
                         FILTER (WHERE NOT granted), 0) AS longest_wait_seconds
                FROM pg_locks LEFT JOIN pg_stat_activity USING (pid)
                """
            )
            outbox = await connection.fetchrow(
                """
                SELECT count(*) FILTER (WHERE status IN ('PENDING','DELIVERING')) AS pending,
                       count(*) FILTER (WHERE status = 'DEAD') AS dead,
                       extract(epoch FROM (now() - min(available_at) FILTER
                         (WHERE status IN ('PENDING','DELIVERING')))) AS oldest_seconds
                FROM outbox_events
                """
            )
            active_runs = await connection.fetchval(
                "SELECT count(*) FROM runs WHERE status NOT IN ('SUCCEEDED','FAILED','CANCELLED','TIMED_OUT','REJECTED')"
            )
        await self.evidence.append_jsonl(
            "metrics/postgresql-samples.jsonl",
            {
                "capturedAt": iso_now(),
                "scenario": self.current_scenario,
                "probeLatencyMs": probe_ms,
                "database": dict(database or {}),
                "connections": dict(connections or {}),
                "locks": dict(locks or {}),
                "outbox": dict(outbox or {}),
                "activeRuns": active_runs,
            },
        )

    async def sample_temporal(self) -> None:
        url = f"http://127.0.0.1:{self.args.temporal_metrics_port}/metrics"
        response = await self.client.get(url)
        selected = [
            line
            for line in response.text.splitlines()
            if not line.startswith("#")
            and re.search(r"(?i)(schedule_to_start|backlog|task_queue|poller)", line)
        ]
        await self.evidence.append_jsonl(
            "metrics/temporal-samples.jsonl",
            {
                "capturedAt": iso_now(),
                "scenario": self.current_scenario,
                "httpStatus": response.status_code,
                "selectedExpositionLines": selected,
            },
        )

    async def sample_nats(self) -> None:
        base = f"http://127.0.0.1:{self.args.nats_monitor_port}"
        health, jsz = await asyncio.gather(
            self.client.get(f"{base}/healthz"), self.client.get(f"{base}/jsz")
        )
        await self.evidence.append_jsonl(
            "metrics/nats-samples.jsonl",
            {
                "capturedAt": iso_now(),
                "scenario": self.current_scenario,
                "healthStatus": health.status_code,
                "healthBody": health.text,
                "jetstream": jsz.json() if jsz.status_code == 200 else None,
            },
        )

    async def sample_resources(self) -> None:
        processes = self.process_manager.processes if self.process_manager else {}
        pids = [item.process.pid for item in processes.values() if item.process.poll() is None]
        process_values: list[dict[str, Any]] = []
        if pids:
            command = (
                "$OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
                "$parents=@{};Get-CimInstance Win32_Process|ForEach-Object "
                "{$parents[[int]$_.ProcessId]=[int]$_.ParentProcessId};"
                "Get-Process|ForEach-Object {[pscustomobject]@{"
                "Id=$_.Id;ParentProcessId=$parents[[int]$_.Id];ProcessName=$_.ProcessName;"
                "CPU=$_.CPU;WorkingSet64=$_.WorkingSet64;"
                "PrivateMemorySize64=$_.PrivateMemorySize64;StartTime=$_.StartTime}}|"
                "ConvertTo-Json -Compress"
            )
            completed = await asyncio.to_thread(
                subprocess.run,
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            if completed.returncode == 0 and completed.stdout.strip():
                decoded = json.loads(completed.stdout)
                all_processes = decoded if isinstance(decoded, list) else [decoded]
                by_parent: dict[int, list[int]] = {}
                by_pid = {int(item["Id"]): item for item in all_processes}
                for item in all_processes:
                    by_parent.setdefault(int(item.get("ParentProcessId") or 0), []).append(
                        int(item["Id"])
                    )
                for root_pid in pids:
                    pending = [root_pid]
                    seen: set[int] = set()
                    while pending:
                        current = pending.pop()
                        if current in seen:
                            continue
                        seen.add(current)
                        pending.extend(by_parent.get(current, []))
                    for pid in seen:
                        if pid in by_pid:
                            process_values.append({"RootPid": root_pid, **by_pid[pid]})
        project = self.args.compose_project
        containers = await asyncio.to_thread(
            subprocess.run,
            ["docker", "ps", "--filter", f"label=com.docker.compose.project={project}", "-q"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        container_values: list[dict[str, Any]] = []
        ids = containers.stdout.split()
        if ids:
            stats = await asyncio.to_thread(
                subprocess.run,
                ["docker", "stats", "--no-stream", "--format", "{{json .}}", *ids],
                capture_output=True,
                text=True,
                timeout=20,
            )
            container_values = [json.loads(line) for line in stats.stdout.splitlines() if line]
        await self.evidence.append_jsonl(
            "metrics/resource-samples.jsonl",
            {
                "capturedAt": iso_now(),
                "scenario": self.current_scenario,
                "processes": process_values,
                "containers": container_values,
            },
        )

    async def snapshot_pg_stat_statements(self, name: str) -> None:
        assert self.db is not None
        async with self.db.acquire() as connection:
            try:
                rows = await connection.fetch(
                    """
                    SELECT queryid, calls, total_exec_time, min_exec_time, max_exec_time,
                           mean_exec_time, stddev_exec_time, rows, shared_blks_hit,
                           shared_blks_read, temp_blks_written
                    FROM pg_stat_statements
                    ORDER BY total_exec_time DESC LIMIT 500
                    """
                )
                value: Any = [dict(row) for row in rows]
            except Exception as exc:
                value = {"error": f"{type(exc).__name__}:{exc}"}
        self.evidence.write_json(f"metrics/raw/pg-stat-statements-{name}.json", value)

    async def run_e0(self) -> dict[str, Any]:
        self.current_scenario = "E0"
        baseline = await self.backlog()
        accumulator = ScenarioAccumulator("E0", "warmup")
        await self.fixed_load(accumulator, 20, 1, phase="warmup", delay=0.2)
        # Warm-up is excluded from formal metrics, so count its actual terminal states directly.
        assert self.db is not None
        async with self.db.acquire() as connection:
            warmup = await connection.fetchrow(
                """
                SELECT count(*) AS total, count(*) FILTER (WHERE status='SUCCEEDED') AS succeeded
                FROM runs WHERE strategy_version_id=$1
                """,
                self.strategy_version_id,
            )
        await asyncio.sleep(31)
        api_health, nats_health, temporal_metrics = await asyncio.gather(
            self.client.get(f"{self.api_url}/health/live"),
            self.client.get(f"http://127.0.0.1:{self.args.nats_monitor_port}/healthz"),
            self.client.get(f"http://127.0.0.1:{self.args.temporal_metrics_port}/metrics"),
        )
        task_queue_errors = [
            name for name, value in baseline["taskQueues"].items() if value.get("error")
        ]
        unexpected_exits = self.process_manager.unexpected_exits() if self.process_manager else []
        checks = {
            "apiHealthy": api_health.status_code == 200,
            "postgresHealthy": True,
            "temporalHealthy": temporal_metrics.status_code == 200,
            "natsHealthy": nats_health.status_code == 200,
            "workersHealthy": not task_queue_errors and not unexpected_exits,
            "clockWithin100Ms": self.clock_max_offset_ms is not None
            and self.clock_max_offset_ms <= 100,
            "swarmcoreMetricsCollected": self.args.otlp_receiver.metrics.exports > 0,
        }
        result = {
            "scenario": "E0",
            "baseline": baseline,
            "warmup": dict(warmup or {}),
            "swarmcoreOtlpExports": self.args.otlp_receiver.metrics.exports,
            "checks": checks,
            "taskQueueErrors": task_queue_errors,
            "unexpectedExits": unexpected_exits,
            "status": "PASS"
            if warmup
            and warmup["total"] == 20
            and warmup["succeeded"] == 20
            and all(checks.values())
            else "FAIL",
        }
        self.evidence.write_json("events/e0-result.json", result)
        return result

    async def run_e1(self) -> ScenarioAccumulator:
        self.current_scenario = "E1-c1"
        accumulator = ScenarioAccumulator("E1", 1)
        baseline = await self.backlog()
        started = time.monotonic()
        await self.fixed_load(accumulator, 200, 1, phase="sample", delay=0.2, replay_count=20)
        accumulator.window_seconds = time.monotonic() - started
        accumulator.finished_at = iso_now()
        accumulator.unexpected_exits = (
            self.process_manager.unexpected_exits() if self.process_manager else []
        )
        recovered, seconds = await self.wait_backlog(baseline)
        accumulator.backlog_recovered = recovered
        accumulator.backlog_recovery_seconds = seconds
        self.scenarios.append(accumulator)
        await self.snapshot_pg_stat_statements("e1-end")
        return accumulator

    async def run_e2_level(self, level: int) -> ScenarioAccumulator:
        self.current_scenario = f"E2-c{level}-warmup"
        warmup = ScenarioAccumulator("E2", level)
        await self.fixed_load(warmup, 20, level, phase="warmup", delay=0.2)
        baseline = await self.backlog()
        accumulator = ScenarioAccumulator("E2", level)
        self.current_scenario = f"E2-c{level}-sample"
        await self.duration_load(
            accumulator, level, self.args.e2_min_seconds, self.args.e2_min_runs
        )
        accumulator.finished_at = iso_now()
        accumulator.unexpected_exits = (
            self.process_manager.unexpected_exits() if self.process_manager else []
        )
        self.current_scenario = f"E2-c{level}-drain"
        recovered, seconds = await self.wait_backlog(baseline)
        accumulator.backlog_recovered = recovered
        accumulator.backlog_recovery_seconds = seconds
        self.scenarios.append(accumulator)
        await self.snapshot_pg_stat_statements(f"e2-c{level}-end")
        return accumulator

    async def temporal_history(self, run_id: str) -> list[dict[str, Any]]:
        assert self.temporal is not None
        handle = self.temporal.get_workflow_handle(f"swarm:{TENANT_ID}:{run_id}")
        values = []
        async for event in handle.fetch_history_events():
            values.append(MessageToDict(event, preserving_proto_field_name=True))
        return values

    async def run_e3(self) -> dict[str, Any]:
        rounds = []
        all_recovery_seconds: list[float] = []
        total_succeeded = 0
        total_violations = 0
        for round_index in range(1, 4):
            self.current_scenario = f"E3-round-{round_index}"
            trackers = [await self.submit("E3", round_index, "fault", 30.0) for _ in range(10)]
            started_events = await asyncio.gather(
                *(tracker.wait_for_event("task.started", 60) for tracker in trackers)
            )
            assert all(started_events)
            assert self.process_manager is not None
            t_fault_text = await self.process_manager.inject_agent_fault()
            t_fault = parse_time(t_fault_text)
            assert t_fault is not None
            await asyncio.sleep(10)
            self.process_manager.start("worker-agent", "swarmcore-worker-agent")
            finished = await asyncio.gather(*(tracker.finish(timeout=150) for tracker in trackers))
            histories = await asyncio.gather(
                *(self.temporal_history(str(tracker.run_id)) for tracker in trackers)
            )
            recoveries: list[dict[str, Any]] = []
            for tracker, result, history in zip(trackers, finished, histories, strict=True):
                recovery_time: datetime | None = None
                attempts = 0
                for event in history:
                    attributes = event.get("activity_task_started_event_attributes")
                    if attributes:
                        attempts += 1
                        event_time = parse_time(event.get("event_time"))
                        if event_time and event_time >= t_fault and recovery_time is None:
                            recovery_time = event_time
                seconds = (recovery_time - t_fault).total_seconds() if recovery_time else None
                if seconds is not None:
                    all_recovery_seconds.append(seconds)
                sample = result["sample"]
                if sample.get("snapshotStatus") == "SUCCEEDED":
                    total_succeeded += 1
                total_violations += bool(sample.get("eventViolations")) or not bool(
                    sample.get("stateConsistent")
                )
                recoveries.append(
                    {
                        "runId": tracker.run_id,
                        "tFault": t_fault_text,
                        "tRecovered": recovery_time.isoformat() if recovery_time else None,
                        "recoverySeconds": seconds,
                        "activityTaskStartedCount": attempts,
                        "terminalStatus": sample.get("snapshotStatus"),
                        "eventViolations": sample.get("eventViolations"),
                        "stateConsistent": sample.get("stateConsistent"),
                    }
                )
                await self.evidence.append_jsonl(
                    "events/temporal-history.jsonl",
                    {"round": round_index, "runId": tracker.run_id, "history": history},
                )
            round_value = {
                "round": round_index,
                "tFault": t_fault_text,
                "runs": recoveries,
                "maxRecoverySeconds": max(
                    (
                        item["recoverySeconds"]
                        for item in recoveries
                        if item["recoverySeconds"] is not None
                    ),
                    default=None,
                ),
            }
            rounds.append(round_value)
            self.evidence.write_json(f"events/e3-round-{round_index}.json", round_value)
        result = {
            "rounds": rounds,
            "F1": {
                "sampleCount": len(all_recovery_seconds),
                "maxRecoverySeconds": max(all_recovery_seconds) if all_recovery_seconds else None,
                "thresholdSeconds": 60,
            },
            "F2": {"value": total_succeeded / 30, "sampleCount": 30, "threshold": 1.0},
            "F3": {"value": total_violations, "threshold": 0},
            "F4": {
                "extraActivityAttempts": sum(
                    max(0, item["activityTaskStartedCount"] - 1)
                    for round_value in rounds
                    for item in round_value["runs"]
                ),
                "explanation": "forced worker termination followed by heartbeat timeout and Temporal retry",
            },
        }
        self.e3_result = result
        return result


def run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    log: Path,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        f"COMMAND: {subprocess.list2cmdline(command)}\nEXIT: {completed.returncode}\n"
        f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}\n",
        encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {command}")
    return completed


async def clock_offsets(project: str) -> dict[str, Any]:
    container_ids = subprocess.run(
        ["docker", "ps", "--filter", f"label=com.docker.compose.project={project}", "-q"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    async def one(container_id: str) -> dict[str, Any]:
        started = time.time()
        completed = await asyncio.to_thread(
            subprocess.run,
            [
                "docker",
                "exec",
                container_id,
                "sh",
                "-c",
                "touch /tmp/swarmcore-eval-clock && stat -c %y /tmp/swarmcore-eval-clock",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        finished = time.time()
        midpoint_ms = (started + finished) * 500
        container_time = datetime.fromisoformat(completed.stdout.strip())
        container_ms = container_time.timestamp() * 1000
        return {
            "containerId": container_id,
            "offsetMs": container_ms - midpoint_ms,
            "roundTripMs": (finished - started) * 1000,
            "exitCode": completed.returncode,
        }

    values = await asyncio.gather(*(one(value) for value in container_ids))
    return {
        "capturedAt": iso_now(),
        "method": "container touch/stat timestamp minus host request midpoint",
        "samples": values,
        "maxAbsoluteOffsetMs": max((abs(item["offsetMs"]) for item in values), default=None),
    }


def git_metadata(root: Path) -> dict[str, Any]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    diff = subprocess.run(
        ["git", "diff", "--binary", "HEAD"], cwd=root, capture_output=True, check=True
    ).stdout
    untracked = sorted(
        line[3:]
        for line in status.splitlines()
        if line.startswith("?? ") and not line[3:].startswith(".tmp/")
    )
    return {
        "commit": head,
        "shortCommit": head[:8],
        "branch": subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip(),
        "dirty": bool(status.strip()),
        "status": status.splitlines(),
        "trackedDiffSha256": hashlib.sha256(diff).hexdigest(),
        "untrackedFiles": untracked,
    }


def host_metadata(root: Path) -> dict[str, Any]:
    disk = shutil.disk_usage(root)
    powershell = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "$cpu=Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors;"
            "$system=Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory;"
            "[pscustomobject]@{cpu=$cpu;system=$system}|ConvertTo-Json -Compress -Depth 4",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    windows_hardware = (
        json.loads(powershell.stdout) if powershell.returncode == 0 and powershell.stdout else None
    )
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version,
        "logicalCpuCount": os.cpu_count(),
        "machine": platform.machine(),
        "windowsHardware": windows_hardware,
        "workspaceDisk": {
            "totalBytes": disk.total,
            "usedBytes": disk.used,
            "freeBytes": disk.free,
        },
    }


def assess_scenario(summary: dict[str, Any]) -> tuple[str, list[str]]:
    failures = []
    if summary["C1"]["value"] != 1.0:
        failures.append("C1")
    if summary["C2"]["value"] != 0:
        failures.append("C2")
    if summary["C3"]["sampleCount"] and summary["C3"]["value"] != 1.0:
        failures.append("C3")
    if summary["C4"]["value"] != 0:
        failures.append("C4")
    if summary["C5"]["value"] != 0:
        failures.append("C5")
    if isinstance(summary["C6"]["value"], int) and summary["C6"]["value"] != 0:
        failures.append("C6")
    if summary["C7"]["value"] != 0:
        failures.append("C7")
    for metric, threshold in (("P1", 150), ("P2", 300), ("P3", 5000), ("P4", 1000)):
        value = summary[metric]["p95"]
        if value is None or value >= threshold:
            failures.append(metric)
    p5 = summary["P5"]
    if p5["p95"] is None or p5["p95"] >= 1000 or p5["p99"] is None or p5["p99"] >= 5000:
        failures.append("P5")
    if summary["Q2"]["recovered"] is not True or (
        summary["Q2"]["recoverySeconds"] is not None and summary["Q2"]["recoverySeconds"] > 60
    ):
        failures.append("Q2/Q3")
    if summary["httpErrors"] or summary["clientErrors"]:
        failures.append("HTTP_OR_CLIENT_ERRORS")
    if (
        summary.get("R3", {}).get("peakUsageRatio") is not None
        and summary["R3"]["peakUsageRatio"] >= 0.8
    ):
        failures.append("R3")
    return ("FAIL" if failures else "PASS", failures)


def apply_retry_evidence(evidence: Evidence, scenarios: list[dict[str, Any]]) -> None:
    starts: list[datetime] = []
    for path in evidence.logs.glob("worker-agent-g*.stderr.log"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                document = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "agent_execution_started" not in str(document.get("message", "")):
                continue
            timestamp = parse_time(document.get("timestamp"))
            if timestamp is not None:
                starts.append(timestamp)
    for scenario in scenarios:
        started = parse_time(scenario.get("startedAt"))
        finished = parse_time(scenario.get("finishedAt"))
        expected = int(scenario["C1"]["sampleCount"])
        observed = sum(
            started is not None and finished is not None and started <= timestamp <= finished
            for timestamp in starts
        )
        scenario["C6"] = {
            "value": observed - expected if observed >= expected else "NOT_COLLECTED",
            "agentActivityStarts": observed,
            "expectedAgentActivities": expected,
            "threshold": 0,
            "evidence": "logs/worker-agent-g*.stderr.log",
        }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    values = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            values.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return values


def apply_infrastructure_metrics(evidence: Evidence, scenarios: list[dict[str, Any]]) -> None:
    postgres = read_jsonl(evidence.metrics / "postgresql-samples.jsonl")
    resources = read_jsonl(evidence.metrics / "resource-samples.jsonl")
    temporal = read_jsonl(evidence.metrics / "temporal-samples.jsonl")
    for scenario in scenarios:
        label = "E1-c1" if scenario["scenario"] == "E1" else f"E2-c{scenario['level']}-sample"
        pg = [item for item in postgres if item.get("scenario") == label]
        resource = [item for item in resources if item.get("scenario") == label]
        temporal_values = [item for item in temporal if item.get("scenario") == label]
        active = [float(item.get("activeRuns") or 0) for item in pg]
        scenario["Q1"] = {
            "sampleCount": len(active),
            "average": statistics.fmean(active) if active else None,
            "peak": max(active) if active else None,
            "source": "metrics/postgresql-samples.jsonl",
        }
        backlog_values = []
        schedule_lines = 0
        for item in temporal_values:
            for line in item.get("selectedExpositionLines", []):
                if "schedule_to_start" in line.lower():
                    schedule_lines += 1
                if "backlog" not in line.lower():
                    continue
                match = re.search(r"\s([-+0-9.eE]+)$", line)
                if match:
                    backlog_values.append(float(match.group(1)))
        scenario["Q3"] = {
            "sampleCount": len(backlog_values),
            "maxApproximateBacklog": max(backlog_values) if backlog_values else None,
            "scheduleToStartExpositionLineCount": schedule_lines,
            "drained": scenario["Q2"]["recovered"],
            "status": "COLLECTED" if backlog_values or schedule_lines else "NOT_COLLECTED",
            "source": "metrics/temporal-samples.jsonl",
        }
        cpu_points = []
        memory_mib = []
        for item in resource:
            timestamp = parse_time(item.get("capturedAt"))
            processes = item.get("processes", [])
            cpu_total = sum(float(process.get("CPU") or 0) for process in processes)
            memory_total = sum(float(process.get("WorkingSet64") or 0) for process in processes) / (
                1024 * 1024
            )
            if timestamp:
                cpu_points.append((timestamp, cpu_total))
            memory_mib.append(memory_total)
        core_samples = []
        for previous, current in pairwise(cpu_points):
            elapsed = (current[0] - previous[0]).total_seconds()
            if elapsed > 0:
                core_samples.append(max(0.0, current[1] - previous[1]) / elapsed)
        cpu_core_seconds = (
            max(0.0, cpu_points[-1][1] - cpu_points[0][1]) if len(cpu_points) >= 2 else None
        )
        scenario["R1"] = {
            "sampleCount": len(core_samples),
            "averageCpuCores": statistics.fmean(core_samples) if core_samples else None,
            "peakCpuCores": max(core_samples) if core_samples else None,
            "resourceLimit": "NOT_CONFIGURED",
            "source": "metrics/resource-samples.jsonl",
        }
        scenario["R2"] = {
            "sampleCount": len(memory_mib),
            "peakWorkingSetMiB": max(memory_mib) if memory_mib else None,
            "windowGrowthMiB": memory_mib[-1] - memory_mib[0] if len(memory_mib) >= 2 else None,
            "resourceLimit": "NOT_CONFIGURED",
            "source": "metrics/resource-samples.jsonl",
        }
        connection_ratios = [
            float(item["connections"]["used"]) / float(item["connections"]["configured"])
            for item in pg
            if item.get("connections", {}).get("configured")
        ]
        scenario["R3"] = {
            "sampleCount": len(connection_ratios),
            "peakUsageRatio": max(connection_ratios) if connection_ratios else None,
            "threshold": 0.8,
            "source": "metrics/postgresql-samples.jsonl",
        }
        probes = [float(item["probeLatencyMs"]) for item in pg if "probeLatencyMs" in item]
        lock_waits = [float(item["locks"].get("waiting") or 0) for item in pg]
        scenario["R4"] = {
            "businessQueryLatencyPercentiles": "NOT_COLLECTED",
            "selectOneProbeLatencyMs": distribution(probes),
            "lockWaitSampleCount": len(lock_waits),
            "peakWaitingLocks": max(lock_waits) if lock_waits else None,
            "source": "metrics/postgresql-samples.jsonl and metrics/raw/pg-stat-statements-*.json",
        }
        database_delta: dict[str, float] = {}
        if len(pg) >= 2:
            for key in (
                "xact_commit",
                "xact_rollback",
                "tup_inserted",
                "tup_updated",
                "tup_deleted",
                "blks_read",
                "blks_hit",
            ):
                database_delta[key] = float(pg[-1]["database"][key]) - float(pg[0]["database"][key])
        completed = int(scenario["C1"]["sampleCount"])
        scenario["R5"] = {
            "cpuCoreSecondsPerCompletedRun": cpu_core_seconds / completed
            if cpu_core_seconds is not None and completed
            else None,
            "databaseCounterDelta": database_delta,
            "databaseOperationsPerCompletedRun": {
                key: value / completed for key, value in database_delta.items()
            }
            if completed
            else {},
            "measurementOverheadIncluded": True,
        }


def build_report(
    evidence: Evidence,
    metadata: dict[str, Any],
    e0: dict[str, Any],
    scenarios: list[ScenarioAccumulator],
    e3: dict[str, Any],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    scenario_values = []
    stable = []
    first_unstable: dict[str, Any] | None = None
    for scenario in scenarios:
        summary = scenario.summary()
        scenario_values.append(summary)
    apply_retry_evidence(evidence, scenario_values)
    apply_infrastructure_metrics(evidence, scenario_values)
    for summary in scenario_values:
        status, failures = assess_scenario(summary)
        summary["status"] = status
        summary["failedCriteria"] = failures
        if summary["scenario"] == "E2":
            if status == "PASS":
                stable.append(summary)
            elif first_unstable is None:
                first_unstable = {"level": summary["level"], "reasons": failures}
    f1 = e3.get("F1", {})
    e3_pass = (
        f1.get("sampleCount") == 30
        and f1.get("maxRecoverySeconds") is not None
        and f1["maxRecoverySeconds"] <= 60
        and e3.get("F2", {}).get("value") == 1.0
        and e3.get("F3", {}).get("value") == 0
    )
    invalid_reasons = []
    if metadata["git"]["dirty"]:
        invalid_reasons.append("工作树不干净，评测对象未绑定不可变提交")
    invalid_reasons.append(
        "R4 PostgreSQL 全体业务查询 p50/p95/p99 无原始逐查询时延数据；pg_stat_statements 仅提供聚合统计"
    )
    if e0.get("swarmcoreOtlpExports", 0) == 0:
        invalid_reasons.append("SwarmCore OTLP 指标未收到导出")
    if any(value["C6"]["value"] == "NOT_COLLECTED" for value in scenario_values):
        invalid_reasons.append("至少一个场景无法从 Agent Worker 原始日志核对 Activity retry")
    if any(value["Q3"]["status"] == "NOT_COLLECTED" for value in scenario_values):
        invalid_reasons.append("至少一个场景未采集到 Temporal backlog/schedule-to-start 指标")
    if errors:
        invalid_reasons.append("执行期间存在工具或环境错误")
    any_fail = (
        e0.get("status") == "FAIL"
        or any(value["status"] == "FAIL" for value in scenario_values)
        or not e3_pass
    )
    overall = "INVALID" if invalid_reasons else "FAIL" if any_fail else "PASS"
    stable_top = stable[-1] if stable else None
    result = {
        "evaluationId": metadata["evaluationId"],
        "evidenceLocation": str(evidence.root),
        "rawEvidenceSha256": metadata.get("rawEvidenceSha256"),
        "overallStatus": overall,
        "technicalFailureObserved": any_fail,
        "invalidReasons": invalid_reasons,
        "E0": e0,
        "scenarios": scenario_values,
        "E3": {**e3, "status": "PASS" if e3_pass else "FAIL"},
        "stableConcurrencyLowerBound": stable_top["level"] if stable_top else None,
        "stableConcurrencyThroughputRunsPerSecond": stable_top["P7"]["completedRunsPerSecond"]
        if stable_top
        else None,
        "firstUnstableLevel": first_unstable or "NOT_REACHED",
        "notCollected": [
            {
                "metric": "R4 query latency p50/p95/p99",
                "reason": "PostgreSQL exporter/pg_stat_statements does not retain raw per-query latency samples",
            }
        ],
        "errors": errors,
    }
    evidence.write_json("result-summary.json", result)
    rows = []
    for value in scenario_values:
        for metric in (
            "C1",
            "C2",
            "C3",
            "C4",
            "C5",
            "C6",
            "C7",
            "P1",
            "P2",
            "P3",
            "P4",
            "P5",
            "P6",
            "P7",
            "Q1",
            "Q2",
            "Q3",
            "R1",
            "R2",
            "R3",
            "R4",
            "R5",
        ):
            rows.append(
                f"| {metric} | {value['scenario']}/并发 {value['level']} | "
                f"`{json.dumps(value[metric], ensure_ascii=False)}` | {value['status']} |"
            )
    report = f"""# SwarmCore 首版最小系统运行评测报告

## 总结

| 项目 | 结果 |
|---|---|
| 评测编号 | `{metadata["evaluationId"]}` |
| 总体状态 | **{overall}** |
| 技术失败是否出现 | {any_fail} |
| 已验证稳定并发下界 | {result["stableConcurrencyLowerBound"] if result["stableConcurrencyLowerBound"] is not None else "NOT_ESTABLISHED"} |
| 对应完成吞吐量 | {result["stableConcurrencyThroughputRunsPerSecond"] if result["stableConcurrencyThroughputRunsPerSecond"] is not None else "NOT_ESTABLISHED"} Run/s |
| 首个不稳定档位 | `{json.dumps(result["firstUnstableLevel"], ensure_ascii=False)}` |
| Worker 恢复 | `{json.dumps(result["E3"], ensure_ascii=False)}` |
| 证据位置 | `{evidence.root}` |
| 原始证据内容 SHA-256 | `{metadata.get("rawEvidenceSha256", "NOT_AVAILABLE")}` |

本次总体为 `{overall}`。工作树在开始时不干净，按评测方案只能形成探索证据，不能提升为正式回归基线。另有 R4 全体 PostgreSQL 查询 p50/p95/p99 原始样本无法由当前观测链路获取，已明确标为 `NOT_COLLECTED`，没有估算为 0。

## E0-E3 结论

- E0：`{e0.get("status")}`；20 个预热 Run `{e0.get("warmup", {}).get("succeeded")}/{e0.get("warmup", {}).get("total")}` 成功，OTLP 导出批次 `{e0.get("swarmcoreOtlpExports")}`。
- E1/E2：逐档结果见下表；所有失败样本均保留在 `client-samples.jsonl` 与 `run-events.jsonl`。
- E3：`{"PASS" if e3_pass else "FAIL"}`；30 个受影响 Task 的最大恢复时间 `{f1.get("maxRecoverySeconds")}` 秒，成功结算率 `{e3.get("F2", {}).get("value")}`，事件/状态违规 `{e3.get("F3", {}).get("value")}`。

## 指标结果

| ID | 场景/档位 | 实测值与样本数 | 场景状态 |
|---|---|---|---|
{chr(10).join(rows)}

Q1、Q2、Q3、R1、R2、R3、R4、R5 的 5 秒原始时序分别保存在 `metrics/postgresql-samples.jsonl`、`metrics/temporal-samples.jsonl`、`metrics/resource-samples.jsonl` 和 `metrics/raw/pg-stat-statements-*.json`。Q4 见总结中的稳定并发下界。

## 主要瓶颈与限制

主要瓶颈按首个不稳定档位的失败指标判定；若为 `NOT_REACHED`，本轮没有在 32 并发内观测到首个不稳定档位，不能推断系统最大容量。R4 百分位缺失是观测链路限制，不用日志印象替代。工作树未绑定不可变 commit 是本轮成为正式基线的另一硬阻塞。

## 未执行或未采集

- `R4 PostgreSQL 查询延迟 p50/p95/p99`: `NOT_COLLECTED`；保留 pg_stat_statements 聚合与 5 秒 SELECT 1 探针，但两者都不冒充全体业务查询原始百分位。
- 月度可用性、HA、RPO/RTO、真实模型、外部 Tool 和业务能力包：不在本方案范围内，未执行。

## 后续动作

1. 在干净提交上从空环境重跑同一工具，并绑定构建镜像 digest，才能形成正式回归基线。
2. 为 PostgreSQL 接入可导出原始/直方图查询时延的 exporter 或数据库观测方案，再关闭 R4 `NOT_COLLECTED`。
3. 若出现不稳定档位，优先按该档位的 API、Outbox、Temporal Queue、Worker、PostgreSQL和事件链路原始样本定位，不通过修改产品行为重跑掩盖现场。

## 证据索引

- `metadata.json`：环境、Git、镜像、时钟与时间范围。
- `workload.json`：固定 Strategy、闭环模型、轮询、SSE 和档位参数。
- `client-samples.jsonl`：逐 Run 客户端原始样本。
- `run-events.jsonl`：逐 Run 完整事件序列及 SSE 接收时间。
- `events/temporal-history.jsonl`：E3 Temporal History。
- `metrics/`：OTLP、Temporal、PostgreSQL、NATS、进程与容器资源原始数据。
- `logs/`：评测窗口内各进程和基础设施日志。
- `result-summary.json`：机器可读公式结果、阈值和状态。
"""
    (evidence.root / "report.md").write_text(report, encoding="utf-8")
    return result


async def async_main(args: argparse.Namespace) -> int:
    root = Path(__file__).resolve().parents[2]
    git = git_metadata(root)
    evaluation_id = (
        args.evaluation_id or f"{utc_now().strftime('%Y%m%d-%H%M')}-{git['shortCommit']}"
    )
    evidence_root = root / ".tmp" / "system-evaluation" / evaluation_id
    if evidence_root.exists():
        raise FileExistsError(f"evidence directory already exists: {evidence_root}")
    evidence = Evidence(evidence_root)
    args.compose_project = f"swarmcore-eval-{evaluation_id.lower()}".replace("_", "-")
    args.otlp_receiver = None
    environment = os.environ.copy()
    environment.update(
        {
            "EVAL_POSTGRES_PORT": str(args.postgres_port),
            "EVAL_TEMPORAL_PORT": str(args.temporal_port),
            "EVAL_TEMPORAL_METRICS_PORT": str(args.temporal_metrics_port),
            "EVAL_NATS_PORT": str(args.nats_port),
            "EVAL_NATS_MONITOR_PORT": str(args.nats_monitor_port),
            "SWARMCORE_DATABASE_URL": f"postgresql+asyncpg://swarmcore:swarmcore@127.0.0.1:{args.postgres_port}/swarmcore_eval",
            "SWARMCORE_TEMPORAL_ADDRESS": f"127.0.0.1:{args.temporal_port}",
            "SWARMCORE_TEMPORAL_NAMESPACE": "default",
            "SWARMCORE_NATS_URL": f"nats://127.0.0.1:{args.nats_port}",
            "SWARMCORE_API_HOST": "127.0.0.1",
            "SWARMCORE_API_PORT": str(args.api_port),
            "SWARMCORE_OTLP_ENDPOINT": f"http://127.0.0.1:{args.otlp_port}",
            "SWARMCORE_TELEMETRY_ENABLED": "true",
            "SWARMCORE_USE_FAKE_AGENT": "true",
            "SWARMCORE_DEPLOYMENT_MODE": "local",
            "SWARMCORE_AUTH_MODE": "local",
            "SWARMCORE_POLICY_MODE": "local",
        }
    )
    metadata: dict[str, Any] = {
        "evaluationId": evaluation_id,
        "startedAt": iso_now(),
        "executor": "Codex local evaluation harness",
        "git": git,
        "host": host_metadata(root),
        "environmentName": args.compose_project,
        "ports": {
            "api": args.api_port,
            "postgres": args.postgres_port,
            "temporal": args.temporal_port,
            "temporalMetrics": args.temporal_metrics_port,
            "nats": args.nats_port,
            "natsMonitor": args.nats_monitor_port,
            "otlp": args.otlp_port,
        },
        "metricSamplePeriodSeconds": args.sample_period,
        "fakeAgentRequired": True,
        "fakeAgentConfigured": environment["SWARMCORE_USE_FAKE_AGENT"] == "true",
    }
    evidence.write_json("metadata.json", metadata)
    evidence.write_json(
        "workload.json",
        {
            "schemaVersion": "1.0",
            "model": "model://fake-deterministic@1",
            "strategy": "single agent node; no tool, approval, artifact, external network or business pack",
            "normalDelaySeconds": 0.2,
            "recoveryDelaySeconds": 30,
            "sseAfter": 0,
            "snapshotPollIntervalSeconds": 0.1,
            "trafficModel": "closed-loop",
            "E0": {"warmupRuns": 20},
            "E1": {"concurrency": 1, "runs": 200, "idempotencyReplays": 20},
            "E2": {
                "levels": [4, 8, 16, 32],
                "warmupRunsPerLevel": 20,
                "minimumSecondsPerLevel": args.e2_min_seconds,
                "minimumCompletedRunsPerLevel": args.e2_min_runs,
                "drainTimeoutSeconds": 120,
            },
            "E3": {"rounds": 3, "runsPerRound": 10, "workerStoppedSeconds": 10},
        },
    )
    errors: list[dict[str, Any]] = []
    evaluator = Evaluator(args, root, evidence)
    otlp = OtlpServer(evidence, args.otlp_port)
    args.otlp_receiver = otlp
    manager = ProcessManager(root, evidence, environment)
    evaluator.process_manager = manager
    compose_file = root / "scripts" / "system_evaluation" / "compose.evaluation.yaml"
    compose_base = [
        "docker",
        "compose",
        "-p",
        args.compose_project,
        "-f",
        str(compose_file),
    ]
    e0: dict[str, Any] = {"status": "INVALID", "reason": "not started"}
    try:
        await otlp.start()
        run_command(
            [*compose_base, "up", "-d", "--wait"],
            cwd=root,
            env=environment,
            log=evidence.logs / "compose-up.log",
            timeout=360,
        )
        run_command(
            [
                *compose_base,
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "swarmcore",
                "-d",
                "swarmcore_eval",
                "-c",
                "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;",
            ],
            cwd=root,
            env=environment,
            log=evidence.logs / "postgres-extension.log",
        )
        run_command(
            ["uv", "run", "alembic", "-c", "packages/persistence/alembic.ini", "upgrade", "head"],
            cwd=root,
            env=environment,
            log=evidence.logs / "migrations.log",
        )
        run_command(
            ["uv", "run", "swarmcore-seed"],
            cwd=root,
            env=environment,
            log=evidence.logs / "seed.log",
        )
        for service, executable in (
            ("api", "swarmcore-api"),
            ("command-dispatcher", "swarmcore-command-dispatcher"),
            ("worker-control", "swarmcore-worker-control"),
            ("worker-agent", "swarmcore-worker-agent"),
            ("event-publisher", "swarmcore-event-publisher"),
            ("projection-reconciler", "swarmcore-projection-reconciler"),
        ):
            manager.start(service, executable)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                response = await evaluator.client.get(f"{evaluator.api_url}/health/live")
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.25)
        else:
            raise TimeoutError("API did not become healthy")
        await evaluator.connect()
        metadata["infrastructure"] = await evaluator.environment_details()
        await evaluator.create_strategy()
        metadata["strategyVersionId"] = evaluator.strategy_version_id
        metadata["planHash"] = evaluator.plan_hash
        metadata["clock"] = await clock_offsets(args.compose_project)
        evaluator.clock_max_offset_ms = metadata["clock"]["maxAbsoluteOffsetMs"]
        images = run_command(
            [*compose_base, "images", "--format", "json"],
            cwd=root,
            env=environment,
            log=evidence.logs / "compose-images.log",
        )
        metadata["imagesRaw"] = images.stdout.splitlines()
        metadata["topology"] = {
            "apiReplicas": 1,
            "dispatcherReplicas": 1,
            "controlWorkerReplicas": 1,
            "agentWorkerReplicas": 1,
            "eventPublisherReplicas": 1,
            "projectionReconcilerReplicas": 1,
            "resourceLimits": "NOT_CONFIGURED; absolute CPU cores and MiB collected",
        }
        evidence.write_json("metadata.json", metadata)
        evaluator.metrics_task = asyncio.create_task(evaluator.metrics_loop())
        await evaluator.snapshot_pg_stat_statements("initial")
        e0 = await evaluator.run_e0()
        if not args.only_e3:
            await evaluator.run_e1()
            for level in (4, 8, 16, 32):
                scenario = await evaluator.run_e2_level(level)
                status, failures = assess_scenario(scenario.summary())
                if status == "FAIL":
                    errors.append(
                        {
                            "stage": f"E2-c{level}",
                            "type": "FIRST_UNSTABLE_LEVEL",
                            "details": failures,
                        }
                    )
                    break
        evaluator.current_scenario = "E3"
        await evaluator.run_e3()
    except Exception as exc:
        errors.append(
            {
                "stage": evaluator.current_scenario,
                "type": type(exc).__name__,
                "message": str(exc),
                "capturedAt": iso_now(),
            }
        )
        evidence.write_json("execution-errors.json", errors)
    finally:
        metadata["endedAt"] = iso_now()
        try:
            metadata["clockEnd"] = await clock_offsets(args.compose_project)
        except Exception as exc:
            metadata["clockEnd"] = {"error": f"{type(exc).__name__}:{exc}"}
        evidence.write_json("metadata.json", metadata)
        await evaluator.close()
        await manager.stop_all()
        await otlp.stop()
        try:
            completed = subprocess.run(
                [*compose_base, "logs", "--no-color", "--timestamps"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            (evidence.logs / "infrastructure.log").write_text(
                completed.stdout + completed.stderr, encoding="utf-8"
            )
        except Exception as exc:
            errors.append(
                {"stage": "cleanup-logs", "type": type(exc).__name__, "message": str(exc)}
            )
        if not args.keep_infrastructure:
            try:
                run_command(
                    [*compose_base, "down", "--volumes", "--remove-orphans"],
                    cwd=root,
                    env=environment,
                    log=evidence.logs / "compose-down.log",
                    timeout=180,
                )
            except Exception as exc:
                errors.append({"stage": "cleanup", "type": type(exc).__name__, "message": str(exc)})
    generated = {"metadata.json", "result-summary.json", "report.md", "evidence-sha256.txt"}
    metadata["rawEvidenceHashScope"] = "all files except metadata/report/summary/hash manifest"
    metadata["rawEvidenceSha256"] = evidence_tree_hash(evidence.root, generated)
    evidence.write_json("metadata.json", metadata)
    result = build_report(evidence, metadata, e0, evaluator.scenarios, evaluator.e3_result, errors)
    manifest_lines = []
    for path in sorted(evidence.root.rglob("*")):
        if path.is_file() and path.name != "evidence-sha256.txt":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_lines.append(f"{digest}  {path.relative_to(evidence.root).as_posix()}")
    (evidence.root / "evidence-sha256.txt").write_text(
        f"RAW_EVIDENCE_SHA256  {metadata['rawEvidenceSha256']}\n"
        + "\n".join(manifest_lines)
        + "\n",
        encoding="ascii",
    )
    print(json.dumps({"evidence": str(evidence.root), "result": result}, ensure_ascii=False))
    return 0 if result["overallStatus"] in {"PASS", "INVALID"} else 1


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Run the SwarmCore minimal system evaluation E0-E3")
    value.add_argument("--evaluation-id", default="")
    value.add_argument("--api-port", type=int, default=18080)
    value.add_argument("--postgres-port", type=int, default=25433)
    value.add_argument("--temporal-port", type=int, default=27233)
    value.add_argument("--temporal-metrics-port", type=int, default=28000)
    value.add_argument("--nats-port", type=int, default=24222)
    value.add_argument("--nats-monitor-port", type=int, default=28222)
    value.add_argument("--otlp-port", type=int, default=24317)
    value.add_argument("--sample-period", type=float, default=5.0)
    value.add_argument("--e2-min-seconds", type=float, default=300.0)
    value.add_argument("--e2-min-runs", type=int, default=200)
    value.add_argument("--keep-infrastructure", action="store_true")
    value.add_argument(
        "--only-e3",
        action="store_true",
        help="run E0 preflight followed by E3 only, for recovery reruns",
    )
    return value


if __name__ == "__main__":
    arguments = parser().parse_args()
    if arguments.e2_min_seconds < 300 or arguments.e2_min_runs < 200:
        raise SystemExit("formal evaluation requires E2 >= 300 seconds and >= 200 completed runs")
    raise SystemExit(asyncio.run(async_main(arguments)))
