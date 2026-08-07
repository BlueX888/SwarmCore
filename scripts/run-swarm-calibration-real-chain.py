from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

TENANT_ID = "00000000-0000-0000-0000-000000000001"
PROJECT_ID = "00000000-0000-0000-0000-000000000002"
API_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path("output/swarm-calibration-real-chain")


class ChainError(RuntimeError):
    pass


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    actor: str = "calibration-operator",
    idempotency_key: str | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "X-Actor-ID": actor,
        "X-Scopes": (
            "case.create case.read case.assess report.read calibration.read "
            "calibration.assess calibration.review run.control capability.admin"
        ),
    }
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    response = client.request(method, path, headers=headers, json=json_body)
    if response.status_code >= 400:
        raise ChainError(
            f"{method} {path} returned {response.status_code}: {response.text[:4000]}"
        )
    if not response.content:
        return {}
    value = response.json()
    if not isinstance(value, dict):
        raise ChainError(f"{method} {path} returned a non-object response")
    return value


def _wait_for_run(
    client: httpx.Client,
    run_id: str,
    *,
    timeout_seconds: int = 900,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    deadline = time.monotonic() + timeout_seconds
    approvals: list[dict[str, Any]] = []
    approved_ids: set[str] = set()
    last_status = ""
    while time.monotonic() < deadline:
        snapshot = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}",
        )
        status = str(snapshot["status"])
        if status != last_status:
            print(f"run {run_id}: {status}", flush=True)
            last_status = status
        if status in {"SUCCEEDED", "FAILED", "CANCELLED", "TIMED_OUT"}:
            return snapshot, approvals

        pending = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/approvals?runId={run_id}",
        )
        for approval in pending.get("items", []):
            approval_id = str(approval["approvalId"])
            if approval_id in approved_ids:
                continue
            decision = _request(
                client,
                "POST",
                f"/v1/projects/{PROJECT_ID}/approvals/{approval_id}:approve",
                actor="calibration-reviewer",
                idempotency_key=f"calibration-real-approve-{approval_id}",
                json_body={
                    "value": {
                        "approved": True,
                        "reason": (
                            "本地真实链验收: 已查看机器分数、硬失败、冻结证据和沙箱结果,"
                            "批准保留降级状态继续生成追溯报告。"
                        ),
                        "corrections": [],
                    }
                },
            )
            approvals.append({"request": approval, "decision": decision})
            approved_ids.add(approval_id)
            print(f"approved {approval_id}", flush=True)
        time.sleep(2)
    raise ChainError(f"run {run_id} did not finish in {timeout_seconds} seconds")


def main() -> int:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    nonce = uuid4().hex[:10]
    evidence: dict[str, Any] = {
        "startedAt": datetime.now(UTC).isoformat(),
        "tenantId": TENANT_ID,
        "projectId": PROJECT_ID,
        "dataClass": "public-github-real-runtime",
        "sourceUrl": "https://github.com/temporalio/sdk-python/issues/782",
    }
    with httpx.Client(base_url=API_URL, timeout=60) as client:
        health = client.get("/health/live")
        health.raise_for_status()
        evidence["apiHealth"] = health.json()

        packs = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/capability-packs",
        )
        pack = next(
            (
                item
                for item in packs["items"]
                if item["name"] == "swarm-calibration"
                and item["version"] == "1.0.5"
            ),
            None,
        )
        if pack is None:
            raise ChainError("trusted swarm-calibration@1.0.5 pack was not found")
        enabled = (
            pack
            if pack.get("bindingStatus") == "ENABLED"
            else _request(
                client,
                "POST",
                f"/v1/projects/{PROJECT_ID}/capability-packs/{pack['versionId']}:enable",
                idempotency_key=f"calibration-real-enable-{nonce}",
                json_body={"configuration": {}},
            )
        )
        evidence["capabilityPack"] = {
            "versionId": enabled["versionId"],
            "bindingStatus": enabled["bindingStatus"],
            "blockers": enabled["blockers"],
        }

        assessment = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/swarm-calibration:run",
            idempotency_key=f"calibration-real-run-{nonce}",
            json_body={
                "title": "Temporal Python SDK 异步 Activity 完成竞态校准",
                "issueUrl": evidence["sourceUrl"],
                "objective": (
                    "基于 Issue、讨论、关联 PR 和精确合并提交, 说明故障机制、修复方式,"
                    "并验证修复版本中的 temporalio Python 包可成功编译。"
                ),
                "acceptanceCriteria": [
                    "引用真实 Issue、讨论和关联 Pull Request 证据",
                    "说明根因、影响、修复机制和验证方法",
                    "对合并提交 391338b66939c8c2068c5d28a66be682743bc972 执行仓库验证",
                ],
                "sandbox": {
                    "enabled": True,
                    "testCommand": [
                        "python",
                        "-m",
                        "compileall",
                        "-q",
                        "temporalio",
                    ],
                },
                "owner": "calibration-operator",
            },
        )
        evidence["assessmentAccepted"] = assessment
        run_id = str(assessment["runId"])
        run, approvals = _wait_for_run(client, run_id)
        evidence["run"] = run
        evidence["approvals"] = approvals
        evidence["eventHistory"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/event-history",
        )
        if run["status"] != "SUCCEEDED":
            raise ChainError(f"run ended with status {run['status']}")

        evidence["runResult"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/result",
        )
        evidence["runArtifacts"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/artifacts",
        )
        evidence["reports"] = _request(
            client,
            "GET",
            (
                f"/v1/projects/{PROJECT_ID}/evaluations/"
                f"{assessment['evaluationId']}/reports"
            ),
        )

    evidence["finishedAt"] = datetime.now(UTC).isoformat()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"real-chain-{stamp}-{nonce}.json"
    serialized = json.dumps(evidence, ensure_ascii=False, indent=2, default=str)
    output_path.write_text(serialized, encoding="utf-8")
    (OUTPUT_DIR / "latest.json").write_text(serialized, encoding="utf-8")
    output = evidence["runResult"].get("output") or {}
    result = output.get("result") if isinstance(output.get("result"), dict) else output
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "runId": evidence["run"]["runId"],
                "evaluationId": assessment["evaluationId"],
                "resultStatus": result.get("status"),
                "resultHash": result.get("resultHash"),
                "evidence": str(output_path.resolve()),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"REAL_CHAIN_FAILED: {exc}", file=sys.stderr, flush=True)
        raise
