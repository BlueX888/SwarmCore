from __future__ import annotations

import argparse
import ctypes
import json
import os
import time
from ctypes import wintypes
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

TH32CS_SNAPPROCESS = 0x00000002
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010
PROCESS_TERMINATE = 0x0001


class ProcessEntry32W(ctypes.Structure):
    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


class ProcessMemoryCounters(ctypes.Structure):
    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def filetime_value(value: wintypes.FILETIME) -> int:
    return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)


def snapshot_processes() -> dict[int, dict[str, Any]]:
    if os.name != "nt":
        raise RuntimeError("fallback process sampler currently requires Windows")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")
    entry = ProcessEntry32W()
    entry.dwSize = ctypes.sizeof(entry)
    values: dict[int, dict[str, Any]] = {}
    try:
        success = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while success:
            pid = int(entry.th32ProcessID)
            values[pid] = {
                "Id": pid,
                "ParentProcessId": int(entry.th32ParentProcessID),
                "ProcessName": entry.szExeFile,
            }
            success = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    for pid, value in values.items():
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, pid
        )
        if not handle:
            continue
        try:
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            if kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                value["CPU"] = (filetime_value(kernel) + filetime_value(user)) / 10_000_000
                value["CreationFileTime"] = filetime_value(creation)
            memory = ProcessMemoryCounters()
            memory.cb = ctypes.sizeof(memory)
            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                value["WorkingSet64"] = int(memory.WorkingSetSize)
                value["PrivateMemorySize64"] = int(memory.PagefileUsage)
        finally:
            kernel32.CloseHandle(handle)
    return values


def descendants(processes: dict[int, dict[str, Any]], root_pid: int) -> list[dict[str, Any]]:
    by_parent: dict[int, list[int]] = {}
    for value in processes.values():
        by_parent.setdefault(int(value["ParentProcessId"]), []).append(int(value["Id"]))
    pending = [root_pid]
    seen: set[int] = set()
    selected = []
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        if current in processes:
            selected.append({"RootPid": root_pid, **processes[current]})
        pending.extend(by_parent.get(current, []))
    return selected


def terminate_process(pid: int, exit_code: int = 1) -> None:
    """Terminate one exact Windows process without recursively killing its descendants."""
    if os.name != "nt":
        raise RuntimeError("native process termination currently requires Windows")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
    if not handle:
        raise OSError(ctypes.get_last_error(), f"OpenProcess({pid}) failed")
    try:
        if not kernel32.TerminateProcess(handle, exit_code):
            raise OSError(ctypes.get_last_error(), f"TerminateProcess({pid}) failed")
    finally:
        kernel32.CloseHandle(handle)


def current_scenario(evidence: Path) -> str:
    path = evidence / "metrics" / "postgresql-samples.jsonl"
    if not path.exists():
        return "UNKNOWN"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return "UNKNOWN"
    try:
        return str(json.loads(lines[-1]).get("scenario", "UNKNOWN"))
    except json.JSONDecodeError:
        return "UNKNOWN"


def sample(evidence: Path) -> dict[str, Any]:
    manifest = json.loads((evidence / "processes.json").read_text(encoding="utf-8"))
    roots = [int(item["pid"]) for item in manifest["active"] if item["exitCode"] is None]
    processes = snapshot_processes()
    selected = [item for root in roots for item in descendants(processes, root)]
    return {
        "capturedAt": datetime.now(UTC).isoformat(),
        "scenario": current_scenario(evidence),
        "source": "Windows Toolhelp32/GetProcessTimes/GetProcessMemoryInfo",
        "processes": selected,
    }


def main(args: argparse.Namespace) -> None:
    evidence = Path(args.evidence).resolve()
    output = evidence / "metrics" / "resource-samples-fallback.jsonl"
    errors = evidence / "metrics" / "resource-fallback-errors.jsonl"
    started = time.monotonic()
    while time.monotonic() - started < args.max_seconds:
        if (evidence / "result-summary.json").exists():
            return
        try:
            value = sample(evidence)
            target = output
        except Exception as exc:
            value = {
                "capturedAt": datetime.now(UTC).isoformat(),
                "error": f"{type(exc).__name__}:{exc}",
            }
            target = errors
        with target.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, separators=(",", ":")) + "\n")
        time.sleep(args.period_seconds)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Supplement Windows process resource sampling")
    value.add_argument("--evidence", required=True)
    value.add_argument("--period-seconds", type=float, default=5.0)
    value.add_argument("--max-seconds", type=float, default=2400.0)
    return value


if __name__ == "__main__":
    main(parser().parse_args())
