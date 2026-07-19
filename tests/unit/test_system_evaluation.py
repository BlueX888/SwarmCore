from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def _module() -> ModuleType:
    path = Path(__file__).parents[2] / "scripts" / "system_evaluation" / "evaluate.py"
    spec = importlib.util.spec_from_file_location("system_evaluation", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _finalizer_module() -> ModuleType:
    path = Path(__file__).parents[2] / "scripts" / "system_evaluation" / "finalize_evidence.py"
    spec = importlib.util.spec_from_file_location("system_evaluation_finalizer", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_percentile_uses_nearest_rank_and_reports_sample_sufficiency() -> None:
    module: Any = _module()
    assert module.percentile([], 0.95) is None
    assert module.percentile([1, 2, 3, 4], 0.50) == 2
    assert module.percentile([1, 2, 3, 4], 0.95) == 4
    value = module.distribution(list(range(200)))
    assert value["sampleCount"] == 200
    assert value["p95SampleSufficient"] is True
    assert value["p99SampleSufficient"] is False


def test_event_validator_detects_gap_duplicate_and_multiple_terminal_events() -> None:
    module: Any = _module()
    events = [
        {"seq": 1, "type": "run.accepted"},
        {"seq": 2, "type": "run.validating"},
        {"seq": 4, "type": "run.queued"},
        {"seq": 4, "type": "run.completed"},
        {"seq": 5, "type": "run.failed"},
    ]
    violations = module.validate_event_sequence(events)
    assert "DUPLICATE_EVENT_SEQ" in violations
    assert "EVENT_SEQ_GAP" in violations
    assert "TERMINAL_EVENT_COUNT" in violations


def test_event_validator_accepts_standard_single_agent_run() -> None:
    module: Any = _module()
    events = [
        {"seq": 1, "type": "run.accepted"},
        {"seq": 2, "type": "run.validating"},
        {"seq": 3, "type": "run.queued"},
        {"seq": 4, "type": "run.started"},
        {"seq": 5, "type": "task.started"},
        {"seq": 6, "type": "task.completed"},
        {"seq": 7, "type": "run.completed"},
    ]
    assert module.validate_event_sequence(events) == []


def test_fallback_process_sampler_contains_current_process_on_windows() -> None:
    if os.name != "nt":
        return
    path = (
        Path(__file__).parents[2] / "scripts" / "system_evaluation" / "fallback_resource_sampler.py"
    )
    spec = importlib.util.spec_from_file_location("fallback_resource_sampler", path)
    assert spec is not None and spec.loader is not None
    fallback = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fallback)
    processes = fallback.snapshot_processes()
    selected = fallback.descendants(processes, os.getpid())
    assert any(item["Id"] == os.getpid() for item in selected)
    assert all("CPU" in item for item in selected)


def test_resource_recompute_uses_per_process_deltas_without_inventing_missing_cpu() -> None:
    module: Any = _finalizer_module()
    scenario = {
        "scenario": "E1",
        "level": 1,
        "windowSeconds": 10.0,
        "R5": {},
    }
    samples = [
        {
            "capturedAt": "2026-01-01T00:00:00+00:00",
            "processes": [
                {"RootPid": 1, "Id": 10, "StartTime": "a", "CPU": 1, "WorkingSet64": 100},
                {"RootPid": 1, "Id": 11, "StartTime": "b", "CPU": 10, "WorkingSet64": 200},
            ],
        },
        {
            "capturedAt": "2026-01-01T00:00:10+00:00",
            "processes": [
                {"RootPid": 1, "Id": 10, "StartTime": "a", "CPU": 3, "WorkingSet64": 120}
            ],
        },
    ]
    clients = [
        {
            "scenario": "E1",
            "phase": "sample",
            "tTerminal": "2026-01-01T00:00:05+00:00",
        }
    ]
    module.recompute_resources(scenario, samples, clients, "test")
    assert scenario["R1"]["averageCpuCores"] == 0.2
    assert scenario["R1"]["peakCpuCores"] == 0.2
    assert scenario["R2"]["windowGrowthMiB"] == "NOT_COLLECTED"
    assert scenario["R5"]["cpuCoreSecondsPerCompletedRun"] == 2.0
