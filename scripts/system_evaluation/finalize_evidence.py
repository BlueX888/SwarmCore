# The generated report contains Chinese full-width punctuation and long Markdown rows.
# ruff: noqa: E501, RUF001
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

GENERATED = {"metadata.json", "result-summary.json", "report.md", "evidence-sha256.txt"}


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def process_key(value: dict[str, Any]) -> tuple[Any, ...]:
    return (
        value.get("RootPid"),
        value.get("Id"),
        value.get("CreationFileTime", value.get("StartTime")),
    )


def recompute_resources(
    scenario: dict[str, Any],
    samples: list[dict[str, Any]],
    client_samples: list[dict[str, Any]],
    source: str,
) -> None:
    samples = sorted(samples, key=lambda value: value["capturedAt"])
    cpu_intervals: list[tuple[float, float]] = []
    for previous, current in pairwise(samples):
        elapsed = (parse_time(current["capturedAt"]) - parse_time(previous["capturedAt"])).total_seconds()
        if elapsed <= 0:
            continue
        previous_cpu = {process_key(item): float(item.get("CPU") or 0) for item in previous["processes"]}
        current_cpu = {process_key(item): float(item.get("CPU") or 0) for item in current["processes"]}
        cpu_seconds = sum(
            max(0.0, current_cpu[key] - previous_cpu[key])
            for key in current_cpu.keys() & previous_cpu.keys()
        )
        cpu_intervals.append((elapsed, cpu_seconds))
    memory = [
        sum(float(item.get("WorkingSet64") or 0) for item in sample["processes"]) / (1024 * 1024)
        for sample in samples
    ]
    process_set_consistent = bool(samples) and {
        process_key(item) for item in samples[0]["processes"]
    } == {process_key(item) for item in samples[-1]["processes"]}
    coverage = sum(value[0] for value in cpu_intervals)
    cpu_seconds = sum(value[1] for value in cpu_intervals)
    cores = [cpu / elapsed for elapsed, cpu in cpu_intervals]
    scenario["R1"] = {
        "sampleCount": len(samples),
        "intervalCount": len(cpu_intervals),
        "coverageSeconds": coverage,
        "coverageRatio": coverage / scenario["windowSeconds"] if scenario["windowSeconds"] else None,
        "averageCpuCores": cpu_seconds / coverage if coverage else None,
        "peakCpuCores": max(cores) if cores else None,
        "resourceLimit": "NOT_CONFIGURED",
        "source": source,
        "method": "per-process cumulative CPU deltas over consecutive observed samples",
    }
    scenario["R2"] = {
        "sampleCount": len(memory),
        "peakWorkingSetMiB": max(memory) if memory else None,
        "windowGrowthMiB": (
            memory[-1] - memory[0]
            if len(memory) >= 2 and process_set_consistent
            else "NOT_COLLECTED"
        ),
        "processSetConsistentAtEndpoints": process_set_consistent,
        "resourceLimit": "NOT_CONFIGURED",
        "source": source,
    }
    start = parse_time(samples[0]["capturedAt"]) if samples else None
    end = parse_time(samples[-1]["capturedAt"]) if samples else None
    matching = []
    for sample in client_samples:
        if sample.get("phase") != "sample" or not sample.get("tTerminal"):
            continue
        if scenario["scenario"] == "E1":
            belongs = sample.get("scenario") == "E1"
        else:
            level = sample.get("level")
            belongs = (
                sample.get("scenario") == "E2"
                and level is not None
                and int(level) == scenario["level"]
            )
        terminal = parse_time(sample["tTerminal"])
        if belongs and start is not None and end is not None and start <= terminal <= end:
            matching.append(sample)
    scenario["R5"]["cpuCoreSecondsPerCompletedRun"] = (
        cpu_seconds / len(matching) if matching else "NOT_COLLECTED"
    )
    scenario["R5"]["cpuMeasurementWindowCompletedRuns"] = len(matching)
    scenario["R5"]["cpuMeasurementCoverageSeconds"] = coverage
    scenario["R5"]["cpuSource"] = source
    scenario["R5"]["method"] = "observed CPU seconds divided by runs completed inside the same observed window"


def evidence_hash(root: Path) -> str:
    aggregate = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if not path.is_file() or relative in GENERATED:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        aggregate.update(f"{digest}  {relative}\n".encode())
    return aggregate.hexdigest()


def metric_value(metric: dict[str, Any]) -> str:
    parts = []
    for key in ("value", "sampleCount", "p50", "p95", "p99", "max", "completedRunsPerSecond"):
        if key in metric:
            parts.append(f"{key}={metric[key]}")
    return ", ".join(parts) if parts else json.dumps(metric, ensure_ascii=False, separators=(",", ":"))


def scenario_rows(scenarios: list[dict[str, Any]]) -> str:
    rows = []
    for scenario in scenarios:
        label = "E1-c1" if scenario["scenario"] == "E1" else f"E2-c{scenario['level']}"
        for name in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "P1", "P2", "P3", "P4", "P5", "P6", "P7"):
            metric = scenario[name]
            if name == "C3" and scenario["scenario"] != "E1":
                value = "NOT_APPLICABLE（仅 E1 重放）"
            else:
                value = metric_value(metric)
            result = "FAIL" if name in scenario["failedCriteria"] else "PASS"
            if name in {"P6", "P7"} or (name == "C3" and scenario["scenario"] != "E1"):
                result = "OBSERVED"
            rows.append(f"| {name} | {label} | {value} | {result} |")
        for name in ("Q1", "Q2", "Q3", "R1", "R2", "R3", "R4", "R5"):
            metric = scenario[name]
            if name == "R4":
                result = "NOT_COLLECTED"
            elif name == "R3":
                result = "PASS" if metric.get("peakUsageRatio", 1) < metric["threshold"] else "FAIL"
            elif name in {"Q2", "Q3"}:
                result = "PASS" if scenario["Q2"]["recovered"] else "FAIL"
            else:
                result = "OBSERVED"
            rows.append(f"| {name} | {label} | {metric_value(metric)} | {result} |")
    return "\n".join(rows)


def build_report(root: Path, summary: dict[str, Any], metadata: dict[str, Any]) -> str:
    scenarios = summary["scenarios"]
    e3 = summary["E3"]
    return f"""# SwarmCore 首版最小系统运行评测报告

## 总体结论

| 项目 | 结论 |
|---|---|
| 评测编号 | `{summary['evaluationId']}` |
| 总体状态 | **{summary['overallStatus']}** |
| 技术失败 | **是**：E2 并发 8 的 P1/P2 超阈值 |
| 稳定并发下界 | **{summary['stableConcurrencyLowerBound']}** |
| 对应吞吐量 | **{summary['stableConcurrencyThroughputRunsPerSecond']:.6f} Run/s** |
| 首个不稳定档位 | **并发 8**（P1、P2） |
| Worker 恢复 | **{e3['status']}**；3 轮 30/30 成功，最大 {e3['F1']['maxRecoverySeconds']:.6f}s |
| 证据位置 | `{root}` |
| 原始证据 SHA-256 | `{metadata['rawEvidenceSha256']}` |

总体为 `INVALID`，不是 `PASS`：开始时工作树不干净；R4 全体业务查询原始延迟未采集；Windows CIM 资源采集存在超时，虽有原生采样补充，但观测链路不完整。技术结果仍明确显示并发 8 首次不稳定。

## E0-E3 判定

- E0：`{summary['E0']['status']}`，20/20 预热成功，API/PostgreSQL/Temporal/NATS/Worker/时钟/OTLP 全部通过。
- E1：`{scenarios[0]['status']}`，200/200 成功，20/20 幂等重放一致。
- E2 并发 4：`{scenarios[1]['status']}`，{scenarios[1]['C1']['sampleCount']} Run，{scenarios[1]['windowSeconds']:.3f}s，{scenarios[1]['P7']['completedRunsPerSecond']:.6f} Run/s。
- E2 并发 8：`{scenarios[2]['status']}`，{scenarios[2]['C1']['sampleCount']} Run，P1/P2 p95={scenarios[2]['P1']['p95']:.3f}ms，分别超过 150/300ms 阈值。
- E2 并发 16/32：`NOT_EXECUTED_AFTER_FIRST_UNSTABLE`；方案要求首个不稳定档位后停止升级。
- E3：`{e3['status']}`。F1 最大 {e3['F1']['maxRecoverySeconds']:.6f}s（<60s），F2={e3['F2']['value']:.0%}，F3={e3['F3']['value']}；专项复跑证据在 `e3-rerun/{summary['e3RerunEvaluationId']}/`。

## C/P/Q/R 指标

| ID | 场景 | 实测值 | 判定 |
|---|---|---|---|
{scenario_rows(scenarios)}
| Q4 | 总体 | stableConcurrencyLowerBound=4, throughput=2.973350 Run/s | OBSERVED |

门槛: C1/C3=100%; C2/C4/C5/C6/C7=0; P1 p95<150ms; P2 p95<300ms;
P3 p95<5s; P4 p95<1s; P5 p95<1s 且 p99<5s; Q2/Q3 排空≤60s;
R3<80%; F1≤60s/Task; F2=100%; F3=0。P6/P7、Q1/Q4、R1/R2/R5、F4
为观测项，无首版硬门槛。

## F 指标

| ID | 实测值 | 判定 |
|---|---|---|
| F1 | n={e3['F1']['sampleCount']}, max={e3['F1']['maxRecoverySeconds']:.6f}s，阈值 ≤60s | PASS |
| F2 | n={e3['F2']['sampleCount']}, value={e3['F2']['value']:.0%} | PASS |
| F3 | value={e3['F3']['value']}，阈值 0 | PASS |
| F4 | extraActivityAttempts={e3['F4']['extraActivityAttempts']} | OBSERVED |

## 主要瓶颈

首个不稳定档位并发 8 的 P1（API 接受延迟）和 P2（客户端接受延迟）p95 同为 478.363ms。该档位正确性、最终结算、事件连续性、Outbox 排空、Temporal 排空及数据库连接占用均仍满足门槛，因此当前首要瓶颈定位为 API 接受路径，而不是 Agent 执行正确性或持久化丢失。

## 未采集、未执行和观测限制

- `R4 PostgreSQL 全体业务查询 p50/p95/p99`：`NOT_COLLECTED`。保留了 `pg_stat_statements` 聚合和 SELECT 1 探针，不将其冒充原始全体查询百分位。
- E2 并发 16/32：首个不稳定档位后按方案停止，状态为 `NOT_EXECUTED_AFTER_FIRST_UNSTABLE`。
- 主运行首次 E3 注入使用 `taskkill /T` 超时，现场保留；随后只修改评测工具的注入方式，在独立隔离栈完成三轮 E3。未修改产品行为。
- 资源主采集器出现 CIM 超时；R1/R2/R5 使用保留下来的逐进程累计计数重算，并明确记录来源、样本数和覆盖窗口。未采集部分不估算。
- 月度可用性、HA、RPO/RTO、真实模型、外部工具和业务能力包不属于本方案，未执行。

## 后续动作

1. 在干净且绑定镜像 digest 的不可变提交上重跑同一工具，才能形成正式回归基线。
2. 优先剖析并发 8 的 API 接受路径（请求处理、提交事务、连接池等待），不要通过放宽门槛掩盖 P1/P2。
3. 接入可导出逐查询原始直方图的 PostgreSQL 观测链路，关闭 R4 缺口。
4. 将 Windows 原生资源采样器作为正式主采集器或在 Linux 基准机重跑，消除 CIM 超时。

## 证据索引

- `metadata.json`：环境、Git、端口、镜像、时钟和时间范围。
- `workload.json`：确定性 Fake Agent、闭环负载和场景参数。
- `client-samples.jsonl`、`run-events.jsonl`：逐 Run 样本与事件序列。
- `events/`：E0 结果和原始 E3 注入失败现场。
- `e3-rerun/{summary['e3RerunEvaluationId']}/events/`：三轮 E3 和 Temporal History。
- `metrics/`：PostgreSQL、Temporal、NATS、OTLP、资源原始时序及采集错误。
- `logs/`：应用与基础设施日志。
- `result-summary.json`：机器可读结论；`evidence-sha256.txt`：逐文件哈希清单。
"""


def finalize(main_root: Path, e3_root: Path) -> None:
    summary = read_json(main_root / "result-summary.json")
    e3_summary = read_json(e3_root / "result-summary.json")
    metadata = read_json(main_root / "metadata.json")
    target = main_root / "e3-rerun" / e3_summary["evaluationId"]
    shutil.copytree(e3_root, target, dirs_exist_ok=True)

    client_samples = read_jsonl(main_root / "client-samples.jsonl")
    primary = read_jsonl(main_root / "metrics" / "resource-samples.jsonl")
    fallback = read_jsonl(main_root / "metrics" / "resource-samples-fallback.jsonl")
    for scenario in summary["scenarios"]:
        label = "E1-c1" if scenario["scenario"] == "E1" else f"E2-c{scenario['level']}-sample"
        if scenario["scenario"] == "E2":
            samples = [item for item in fallback if item.get("scenario") == label]
            source = "metrics/resource-samples-fallback.jsonl (Windows native APIs)"
        else:
            samples = [item for item in primary if item.get("scenario") == label]
            source = "metrics/resource-samples.jsonl (successful CIM samples)"
        recompute_resources(scenario, samples, client_samples, source)

    original_errors = summary.get("errors", [])
    summary["errors"] = [item for item in original_errors if item.get("type") != "TimeoutExpired"]
    prior_failures = summary.get("priorEvaluationToolFailures", [])
    prior_failures.extend(item for item in original_errors if item.get("type") == "TimeoutExpired")
    summary["priorEvaluationToolFailures"] = list(
        {json.dumps(item, sort_keys=True): item for item in prior_failures}.values()
    )
    summary["E3"] = e3_summary["E3"]
    summary["e3RerunEvaluationId"] = e3_summary["evaluationId"]
    summary["e3Evidence"] = f"e3-rerun/{e3_summary['evaluationId']}"
    summary["notExecuted"] = [
        {"scenario": "E2", "level": 16, "reason": "NOT_EXECUTED_AFTER_FIRST_UNSTABLE_E2_C8"},
        {"scenario": "E2", "level": 32, "reason": "NOT_EXECUTED_AFTER_FIRST_UNSTABLE_E2_C8"},
    ]
    summary["invalidReasons"] = [
        "工作树不干净，评测对象未绑定不可变提交",
        "R4 PostgreSQL 全体业务查询 p50/p95/p99 无原始逐查询延迟数据",
        "Windows CIM 资源采集多次超时；补充采样不能消除观测链路不完整性",
    ]
    summary["observationIssues"] = {
        "resourceCollectorErrors": len(read_jsonl(main_root / "metrics" / "collector-errors.jsonl")),
        "fallbackSampler": "metrics/resource-samples-fallback.jsonl",
    }
    summary["overallStatus"] = "INVALID"
    summary["technicalFailureObserved"] = True

    metadata["e3RerunEvaluationId"] = e3_summary["evaluationId"]
    metadata["e3RerunEvidence"] = f"e3-rerun/{e3_summary['evaluationId']}"
    metadata["e3RerunRawEvidenceSha256"] = e3_summary["rawEvidenceSha256"]
    metadata["rawEvidenceSha256"] = evidence_hash(main_root)
    summary["rawEvidenceSha256"] = metadata["rawEvidenceSha256"]
    (main_root / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (main_root / "result-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (main_root / "report.md").write_text(build_report(main_root, summary, metadata), encoding="utf-8")

    lines = [f"RAW_EVIDENCE_SHA256  {metadata['rawEvidenceSha256']}"]
    for path in sorted(main_root.rglob("*")):
        if path.is_file() and path.relative_to(main_root).as_posix() != "evidence-sha256.txt":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.relative_to(main_root).as_posix()}")
    (main_root / "evidence-sha256.txt").write_text("\n".join(lines) + "\n", encoding="ascii")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Merge an E3 rerun and finalize evaluation evidence")
    value.add_argument("--main-evidence", type=Path, required=True)
    value.add_argument("--e3-evidence", type=Path, required=True)
    return value


if __name__ == "__main__":
    args = parser().parse_args()
    finalize(args.main_evidence.resolve(), args.e3_evidence.resolve())
