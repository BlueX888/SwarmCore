from __future__ import annotations

# ruff: noqa: RUF001
import base64
import hashlib
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
ARTIFACT_URL = "http://127.0.0.1:8091"
OUTPUT_DIR = Path("output/contract-performance-real-chain")

CONTRACT_TEXT = """\
智慧仓储系统采购与实施合同

合同编号：SC-REAL-2026-0728
甲方：上海示范供应链有限公司
乙方：北京示范智能科技有限公司
签署日期：2026-07-01
合同总额：人民币 1,200,000 元（含税）。

一、合同范围
乙方负责提供智慧仓储软件平台、20 台手持终端、接口集成、部署、培训和
三个月上线保障服务。乙方应提交需求规格说明书、部署方案、测试报告、
培训材料和运维手册。

二、里程碑与依赖
M1 需求确认：2026-07-10 前完成，双方签署需求确认单。
M2 测试环境部署：2026-07-25 前完成，依赖 M1。
M3 用户验收测试：2026-08-15 前完成，依赖 M2；通过标准为 80 个测试用例
中至少 76 个通过，且不存在严重级别缺陷。
M4 生产上线：2026-08-31 前完成，依赖 M3。

三、服务水平
生产上线后的三个月保障期内，严重故障应在 30 分钟内响应、4 小时内恢复；
一般故障应在 4 小时内响应、2 个工作日内解决。月度可用性不低于 99.5%。

四、验收
乙方提交验收申请、测试报告及完整交付物后，甲方应在 5 个工作日内组织验收。
验收以双方签署的验收单为准；沉默或系统使用不构成验收。

五、付款条件
合同签署后支付 20%，前提是收到合规发票；
M2 完成并经双方确认后支付 30%；
M3 验收通过并签署验收单后支付 40%；
保障期结束且不存在未解决严重故障后支付 10%。

六、变更控制
任何范围、价款或工期变更必须由双方授权代表书面批准后生效。2026-07-18
双方批准变更单 CR-001：新增 ERP 库存接口，M3 截止日期调整为 2026-08-20，
新增费用人民币 80,000 元，其他条款不变。
"""


class ChainError(RuntimeError):
    pass


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    actor: str = "contract-operator",
    idempotency_key: str | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "X-Actor-ID": actor,
        "X-Scopes": (
            "case.create case.read case.assess document.read evidence.submit "
            "plan.review plan.publish approval.respond contract-performance.audit report.read"
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
    timeout_seconds: int = 600,
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
                (
                    f"/v1/projects/{PROJECT_ID}/approvals/"
                    f"{approval_id}:approve"
                ),
                actor="contract-reviewer",
                idempotency_key=f"real-chain-approve-{approval_id}",
                json_body={
                    "value": {
                        "approved": True,
                        "confirmations": [
                            "已核对合同原文证据定位",
                            "已核对里程碑、验收、SLA 与付款条件",
                        ],
                        "comment": "真实链路本地验收：批准发布候选履约基线。",
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
        "dataClass": "synthetic-contract-real-runtime",
    }
    with httpx.Client(base_url=API_URL, timeout=60) as client:
        health = client.get("/health/live")
        health.raise_for_status()
        evidence["apiHealth"] = health.json()

        packs = _request(
            client, "GET", f"/v1/projects/{PROJECT_ID}/capability-packs"
        )
        contract_pack = next(
            (
                item
                for item in packs["items"]
                if item["name"] == "contract-performance"
                and item["version"] == "1.0.16"
            ),
            None,
        )
        if contract_pack is None:
            raise ChainError("trusted contract-performance@1.0.16 pack was not found")
        requirements = contract_pack["manifest"]["spec"]["documents"]["requirements"]
        enabled = _request(
            client,
            "POST",
            (
                f"/v1/projects/{PROJECT_ID}/capability-packs/"
                f"{contract_pack['versionId']}:enable"
            ),
            idempotency_key=f"real-chain-enable-{nonce}",
            json_body={
                "configuration": {
                    "timezone": "Asia/Shanghai",
                    "currency": "CNY",
                    "documentRequirements": requirements,
                }
            },
        )
        evidence["capabilityPack"] = {
            "versionId": enabled["versionId"],
            "bindingStatus": enabled["bindingStatus"],
            "blockers": enabled["blockers"],
        }

        business_object = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/business-objects",
            idempotency_key=f"real-chain-object-{nonce}",
            json_body={
                "objectType": "contract",
                "canonicalKey": f"SC-REAL-2026-0728-{nonce}",
                "schemaRef": "schema://contract/facts@1",
                "data": {
                    "contractNumber": "SC-REAL-2026-0728",
                    "title": "智慧仓储系统采购与实施合同",
                    "amount": 1200000,
                    "currency": "CNY",
                },
                "provenance": {
                    "source": "real-chain-verification",
                    "dataClass": "synthetic",
                },
            },
        )
        evidence["businessObject"] = business_object

        content = CONTRACT_TEXT.encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        initiated = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/documents:initiate",
            idempotency_key=f"real-chain-document-init-{nonce}",
            json_body={
                "name": "智慧仓储系统采购与实施合同",
                "category": "MASTER_CONTRACT",
                "tags": ["MASTER_CONTRACT", "CONTRACT", "REAL_CHAIN_SYNTHETIC"],
                "filename": f"contract-{stamp}.txt",
                "mediaType": "text/plain",
                "sizeBytes": len(content),
                "sha256": digest,
                "businessObjectIds": [business_object["businessObjectId"]],
                "businessWorkKeys": [
                    "contract-performance",
                    "contract-performance-case",
                    "performance-plan-collection",
                ],
                "retentionDays": 365,
            },
        )
        with httpx.Client(base_url=ARTIFACT_URL, timeout=60) as artifact_client:
            upload = artifact_client.post(
                initiated["uploadRef"],
                json={
                    "capabilityToken": initiated["capabilityToken"],
                    "contentBase64": base64.b64encode(content).decode(),
                },
            )
            if upload.status_code >= 400:
                raise ChainError(
                    f"artifact upload returned {upload.status_code}: {upload.text[:4000]}"
                )
            evidence["artifactUpload"] = upload.json()
        document = _request(
            client,
            "POST",
            (
                f"/v1/projects/{PROJECT_ID}/document-uploads/"
                f"{initiated['uploadId']}:complete"
            ),
            idempotency_key=f"real-chain-document-complete-{nonce}",
            json_body={
                "sha256": digest,
                "profileRef": "document-profile://business-default@1",
                "extractionSchemaRef": "schema://document/generic-text@1",
                "classificationLabels": [
                    {"label": "MASTER_CONTRACT", "source": "human"},
                    {"label": "CONTRACT", "source": "human"},
                ],
            },
        )
        evidence["document"] = document

        case = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/cases",
            idempotency_key=f"real-chain-case-{nonce}",
            json_body={
                "scenarioType": "contract-performance-case",
                "payload": {
                    "contractObjectId": business_object["businessObjectId"],
                    "timezone": "Asia/Shanghai",
                    "currency": "CNY",
                    "operation": "INITIALIZE",
                    "asOf": "2026-07-28",
                    "title": "智慧仓储合同履约基线初始化",
                    "contractNumber": "SC-REAL-2026-0728",
                },
                "subjects": [
                    {
                        "businessObjectId": business_object["businessObjectId"],
                        "businessObjectVersionId": business_object["versionId"],
                        "role": "PRIMARY",
                        "subjectKey": "contract",
                    }
                ],
                "owner": "contract-operator",
            },
        )
        evidence["case"] = case

        assessment = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}:assess",
            idempotency_key=f"real-chain-assess-{nonce}",
        )
        evidence["assessmentAccepted"] = assessment
        run_id = str(assessment["runId"])
        run, approvals = _wait_for_run(client, run_id)
        evidence["run"] = run
        evidence["approvals"] = approvals
        if run["status"] != "SUCCEEDED":
            evidence["eventHistory"] = _request(
                client,
                "GET",
                f"/v1/projects/{PROJECT_ID}/runs/{run_id}/event-history",
            )
            raise ChainError(f"run ended with status {run['status']}")

        evidence["runResult"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/result",
        )
        evidence["eventHistory"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/event-history",
        )
        evidence["runArtifacts"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/artifacts",
        )
        evidence["assessments"] = _request(
            client,
            "GET",
            (
                f"/v1/projects/{PROJECT_ID}/cases/"
                f"{case['caseId']}/assessments"
            ),
        )
        evidence["reports"] = _request(
            client,
            "GET",
            (
                f"/v1/projects/{PROJECT_ID}/evaluations/"
                f"{assessment['evaluationId']}/reports"
            ),
        )
        evidence["findings"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}/findings",
        )

    evidence["finishedAt"] = datetime.now(UTC).isoformat()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"real-chain-{stamp}-{nonce}.json"
    output_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    latest_path = OUTPUT_DIR / "latest.json"
    latest_path.write_text(output_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "runId": evidence["run"]["runId"],
                "caseId": evidence["case"]["caseId"],
                "documentId": evidence["document"]["documentId"],
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
