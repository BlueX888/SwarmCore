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
        content = self._calibration_content(request, payload)
        if content is None:
            content = {
                "node": str(node["key"]),
                "digest": hashlib.sha256(encoded.encode()).hexdigest()[:16],
                "input": payload["input"],
            }
        return {
            "status": "COMPLETED",
            "content": content,
            "runId": str(request["taskExecutionId"]),
            "model": "fake:deterministic",
            "metrics": {"input_tokens": len(encoded.split()), "output_tokens": 8, "costUsd": 0.0},
        }

    @staticmethod
    def _calibration_content(
        request: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        agent = request.get("agent")
        if not isinstance(agent, dict):
            return None
        role = str(agent.get("role") or "")
        node_input = payload["nodeInput"]
        if not isinstance(node_input, dict):
            return None
        if role == "scheduling-calibration-supervisor":
            return {
                "recommendedRoute": "PRIMARY",
                "reasonCodes": ["PRIMARY_READY"],
                "budgetAllocation": {"diagnosisAttempts": 2, "qualityReviews": 2},
                "risks": [],
            }
        if role in {
            "primary-engineering-diagnostician",
            "standby-engineering-diagnostician",
        }:
            task = node_input.get("task")
            evidence = node_input.get("evidence")
            task = task if isinstance(task, dict) else {}
            evidence = evidence if isinstance(evidence, dict) else {}
            evidence_index = evidence.get("evidenceIndex")
            evidence_items = evidence_index if isinstance(evidence_index, list) else []
            evidence_refs = [
                str(item["evidenceId"])
                for item in evidence_items
                if isinstance(item, dict) and isinstance(item.get("evidenceId"), str)
            ]
            cited = evidence_refs[:1] or ["ev-001"]
            criteria = task.get("acceptanceCriteria")
            acceptance_criteria = criteria if isinstance(criteria, list) else []
            return {
                "summary": "基于冻结问题、讨论、拉取请求和提交证据完成工程诊断。",
                "rootCause": "冻结证据显示问题由相关实现路径的行为不一致导致。",
                "impact": "该问题会影响任务描述中的目标行为和验收结果。",
                "fixMechanism": "采用冻结拉取请求对应提交中的实现修复, 并以隔离测试验证。",
                "verificationPlan": [
                    "校验证据清单哈希和完整提交 SHA。",
                    "在禁网隔离环境对固定提交执行声明的测试命令。",
                ],
                "claims": [
                    {
                        "claim": "诊断仅依据本次运行冻结的真实 GitHub 证据。",
                        "material": True,
                        "evidenceRefs": cited,
                    }
                ],
                "acceptanceMapping": [
                    {
                        "criterion": str(criterion),
                        "status": "MET",
                        "evidenceRefs": cited,
                    }
                    for criterion in acceptance_criteria
                ],
                "confidence": 0.8,
            }
        if role == "calibration-quality-supervisor":
            return {
                "decision": "PASS",
                "evidenceConsistent": True,
                "defects": [],
                "reviewRequired": False,
            }
        return None
