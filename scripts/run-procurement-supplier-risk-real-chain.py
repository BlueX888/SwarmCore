from __future__ import annotations

# ruff: noqa: RUF001
import base64
import hashlib
import html
import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.etree import ElementTree
from zipfile import ZipFile

import httpx

TENANT_ID = "00000000-0000-0000-0000-000000000001"
PROJECT_ID = "00000000-0000-0000-0000-000000000002"
API_URL = os.getenv("SWARMCORE_REAL_CHAIN_API_URL", "http://127.0.0.1:8000")
ARTIFACT_URL = os.getenv(
    "SWARMCORE_REAL_CHAIN_ARTIFACT_URL", "http://127.0.0.1:8091"
)
OUTPUT_DIR = Path("output/procurement-supplier-risk-real-chain")

AWARD_URL = (
    "https://www.ccgp.gov.cn/cggg/zygg/zbgg/202606/"
    "t20260622_26787153.htm"
)
TENDER_URL = (
    "https://download.ccgp.gov.cn/oss/download"
    "?uuid=869FB06B509D37B0D6B74EFA5BC38C"
)
RISK_URL = "https://www.ccgp.gov.cn/cr/list"
PROJECT_NAME = "泛血管全栈数智基座与智能体项目"
PROJECT_NO = "招案2026-1952"
SUPPLIER_NAME = "上海龙田数码科技有限公司"
SUPPLIER_CREDIT_CODE = "91310116740594799B"


class ChainError(RuntimeError):
    pass


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del attrs
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        elif self._ignored_depth == 0 and tag in {
            "br",
            "p",
            "div",
            "tr",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
        }:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)
        elif self._ignored_depth == 0 and tag in {
            "p",
            "div",
            "tr",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
        }:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth == 0:
            self.parts.append(data)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _normalize_text(value: str) -> str:
    lines = []
    for raw_line in html.unescape(value).replace("\xa0", " ").splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _html_text(content: bytes) -> str:
    parser = _VisibleTextParser()
    parser.feed(content.decode("utf-8", errors="replace"))
    return _normalize_text("".join(parser.parts))


def _docx_lines(content: bytes) -> list[str]:
    with ZipFile(BytesIO(content)) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    lines: list[str] = []
    for paragraph in root.iter(namespace + "p"):
        text = "".join(
            node.text or "" for node in paragraph.iter(namespace + "t")
        ).strip()
        if text:
            lines.append(_normalize_text(text))
    return lines


def _source_header(
    *,
    title: str,
    source_url: str,
    source_sha256: str,
    acquired_at: str,
    note: str,
) -> str:
    return "\n".join(
        (
            f"资料名称：{title}",
            f"来源URL：{source_url}",
            f"来源SHA-256：{source_sha256}",
            f"获取时间：{acquired_at}",
            f"资料说明：{note}",
            "",
        )
    )


def _fetch_public_documents() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    acquired_at = datetime.now(UTC).isoformat()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/137 Safari/537.36"
        )
    }
    with httpx.Client(
        timeout=60,
        follow_redirects=True,
        headers=headers,
    ) as source_client:
        award_response = source_client.get(AWARD_URL)
        award_response.raise_for_status()
        tender_response: httpx.Response | None = None
        for attempt in range(3):
            tender_response = source_client.get(
                TENDER_URL,
                headers={
                    "Referer": AWARD_URL,
                    "Accept": (
                        "application/vnd.openxmlformats-officedocument."
                        "wordprocessingml.document,application/octet-stream,*/*"
                    ),
                },
            )
            if tender_response.status_code == 200:
                break
            if attempt < 2:
                time.sleep(1)
                source_client.get(AWARD_URL).raise_for_status()
        if tender_response is None:
            raise ChainError("official tender download returned no response")
        tender_response.raise_for_status()

    tender_bytes = tender_response.content
    award_bytes = award_response.content
    if not tender_bytes.startswith(b"PK"):
        raise ChainError("official tender response is not a DOCX archive")
    tender_lines = _docx_lines(tender_bytes)
    tender_text = "\n".join(tender_lines)
    award_text = _html_text(award_bytes)
    for expected in (
        PROJECT_NAME,
        PROJECT_NO,
        "人民币393万元整",
        "第四部分 合同条款",
    ):
        if expected not in tender_text:
            raise ChainError(f"official tender is missing expected text: {expected}")
    for expected in (
        PROJECT_NAME,
        PROJECT_NO,
        SUPPLIER_NAME,
        "388.5000000",
        "92.30",
    ):
        if expected not in award_text:
            raise ChainError(f"official award notice is missing expected text: {expected}")

    try:
        contract_start = next(
            index
            for index, line in enumerate(tender_lines)
            if index > 100 and line == "合同条款"
        )
        contract_end = next(
            index
            for index, line in enumerate(tender_lines)
            if index > contract_start and line == "第五部分 评标办法"
        )
    except StopIteration as exc:
        raise ChainError("official tender contract section could not be isolated") from exc
    contract_text = "\n".join(tender_lines[contract_start:contract_end])
    if len(contract_text) < 1000:
        raise ChainError("official tender contract section is unexpectedly short")

    tender_sha = _sha256(tender_bytes)
    award_sha = _sha256(award_bytes)
    winning_bid_text = "\n".join(
        (
            "公开中标响应事实摘录",
            "本资料不是供应商投标文件原件；投标原件未在公告中公开。",
            f"项目名称：{PROJECT_NAME}",
            f"项目编号：{PROJECT_NO}",
            f"中标供应商：{SUPPLIER_NAME}",
            "中标金额：人民币388.5000000万元",
            "综合得分：92.30，排名第一",
            (
                "主要标的：影像AI存储、文件归档存储、全闪热存储、"
                "大数据中间件服务器、大数据治理节点服务器、"
                "国产服务器操作系统、泛血管智能体应用软件"
            ),
            (
                "交付时间：合同签订后3个月内完成硬件和成品软件供货，"
                "8个月完成定制化软件开发（包含1个月试运行）"
            ),
            "保修（维保）期：3年",
            f"事实来源：{AWARD_URL}",
            f"来源SHA-256：{award_sha}",
            "证据限制：公开公告未提供中标供应商完整投标响应原件，需人工复核。",
        )
    )
    documents = [
        {
            "name": f"{PROJECT_NO}公开招标文件文本提取",
            "category": "TENDER_DOCUMENT",
            "labels": ["TENDER_DOCUMENT", "PROCUREMENT_DOCUMENT"],
            "filename": "tender-document.txt",
            "content": (
                _source_header(
                    title=f"{PROJECT_NO}公开招标文件",
                    source_url=TENDER_URL,
                    source_sha256=tender_sha,
                    acquired_at=acquired_at,
                    note="从中国政府采购网公开DOCX原件确定性提取全部文本。",
                )
                + tender_text
            ),
        },
        {
            "name": f"{PROJECT_NO}公开中标响应事实摘录",
            "category": "WINNING_BID",
            "labels": ["WINNING_BID", "BID_RESPONSE"],
            "filename": "winning-bid-public-facts.txt",
            "content": (
                _source_header(
                    title="公开中标响应事实摘录",
                    source_url=AWARD_URL,
                    source_sha256=award_sha,
                    acquired_at=acquired_at,
                    note="由官方中标公告逐项摘录；不是未公开的投标响应原件。",
                )
                + winning_bid_text
            ),
        },
        {
            "name": f"{PROJECT_NO}中标结果公告",
            "category": "AWARD_NOTICE",
            "labels": ["AWARD_NOTICE"],
            "filename": "award-notice.txt",
            "content": (
                _source_header(
                    title=f"{PROJECT_NAME}中标结果公告",
                    source_url=AWARD_URL,
                    source_sha256=award_sha,
                    acquired_at=acquired_at,
                    note="中国政府采购网公开中标公告的可见文本。",
                )
                + award_text
            ),
        },
        {
            "name": f"{PROJECT_NO}待签合同条款模板",
            "category": "MASTER_CONTRACT",
            "labels": ["MASTER_CONTRACT", "CONTRACT"],
            "filename": "contract-template.txt",
            "content": (
                _source_header(
                    title=f"{PROJECT_NO}待签合同条款模板",
                    source_url=TENDER_URL,
                    source_sha256=tender_sha,
                    acquired_at=acquired_at,
                    note=(
                        "从官方招标原件第四部分合同条款提取；"
                        "属于真实待签合同模板，不是已签合同。"
                    ),
                )
                + contract_text
            ),
        },
    ]
    source_evidence = {
        "acquiredAt": acquired_at,
        "projectName": PROJECT_NAME,
        "projectNo": PROJECT_NO,
        "tender": {
            "url": TENDER_URL,
            "sha256": tender_sha,
            "sizeBytes": len(tender_bytes),
            "extractedLineCount": len(tender_lines),
        },
        "awardNotice": {
            "url": AWARD_URL,
            "sha256": award_sha,
            "sizeBytes": len(award_bytes),
        },
        "derivedDocuments": [
            {
                "name": item["name"],
                "category": item["category"],
                "sha256": _sha256(str(item["content"]).encode("utf-8")),
                "sizeBytes": len(str(item["content"]).encode("utf-8")),
            }
            for item in documents
        ],
        "limitations": [
            "中标供应商完整投标响应原件未公开，WINNING_BID资料为官方公告事实摘录。",
            "合同资料为官方招标原件中的待签合同条款模板，不是已签合同。",
            "未取得供应商ERP履约数据，绩效节点必须输出INSUFFICIENT_DATA。",
        ],
    }
    return documents, source_evidence


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    actor: str = "procurement-risk-operator",
    idempotency_key: str | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "X-Actor-ID": actor,
        "X-Scopes": (
            "case.create case.read case.assess document.read evidence.submit "
            "supplier-risk.read supplier-risk.refresh supplier-risk.review "
            "supplier-risk.work-order approval.respond report.read "
            "procurement-risk.audit audit.read"
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


def _upload_document(
    client: httpx.Client,
    *,
    artifact_client: httpx.Client,
    business_object_id: str,
    document: dict[str, Any],
    nonce: str,
) -> dict[str, Any]:
    content = str(document["content"]).encode("utf-8")
    digest = _sha256(content)
    initiated = _request(
        client,
        "POST",
        f"/v1/projects/{PROJECT_ID}/documents:initiate",
        idempotency_key=f"procurement-real-document-init-{document['category']}-{nonce}",
        json_body={
            "name": document["name"],
            "category": document["category"],
            "tags": [*document["labels"], "REAL_PUBLIC_SOURCE"],
            "filename": document["filename"],
            "mediaType": "text/plain",
            "sizeBytes": len(content),
            "sha256": digest,
            "businessObjectIds": [business_object_id],
            "businessWorkKeys": [
                "procurement-supplier-risk",
                "procurement-supplier-risk-case",
            ],
            "retentionDays": 365,
        },
    )
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
    completed = _request(
        client,
        "POST",
        (
            f"/v1/projects/{PROJECT_ID}/document-uploads/"
            f"{initiated['uploadId']}:complete"
        ),
        idempotency_key=(
            f"procurement-real-document-complete-{document['category']}-{nonce}"
        ),
        json_body={
            "sha256": digest,
            "profileRef": "document-profile://business-default@1",
            "extractionSchemaRef": "schema://document/generic-text@1",
            "classificationLabels": [
                {"label": label, "source": "human"}
                for label in document["labels"]
            ],
        },
    )
    return {
        **completed,
        "contentSha256": digest,
        "sourceCategory": document["category"],
        "artifactUpload": upload.json(),
    }


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
                actor="procurement-risk-reviewer",
                idempotency_key=f"procurement-real-approve-{approval_id}",
                json_body={
                    "value": {
                        "approved": True,
                        "decision": "CONFIRM_BLOCK",
                        "comment": (
                            "真实链路验收：确认官方禁入证据与信用代码精确匹配；"
                            "确认公开资料缺少投标原件和ERP绩效，保留证据缺口，"
                            "不覆盖硬门禁。"
                        ),
                        "assignee": "procurement-risk-reviewer",
                    }
                },
            )
            approvals.append({"request": approval, "decision": decision})
            approved_ids.add(approval_id)
            print(f"approved {approval_id} with CONFIRM_BLOCK", flush=True)
        time.sleep(2)
    raise ChainError(f"run {run_id} did not finish in {timeout_seconds} seconds")


def main() -> int:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    nonce = uuid4().hex[:10]
    public_documents, public_sources = _fetch_public_documents()
    evidence: dict[str, Any] = {
        "startedAt": datetime.now(UTC).isoformat(),
        "tenantId": TENANT_ID,
        "projectId": PROJECT_ID,
        "dataClass": "real-public-procurement-and-live-official-risk",
        "publicSources": public_sources,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_dir = OUTPUT_DIR / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)
    for document in public_documents:
        source_path = source_dir / str(document["filename"])
        source_path.write_text(str(document["content"]), encoding="utf-8")

    with httpx.Client(base_url=API_URL, timeout=60) as client:
        health = client.get("/health/live")
        health.raise_for_status()
        evidence["apiHealth"] = health.json()

        packs = _request(
            client, "GET", f"/v1/projects/{PROJECT_ID}/capability-packs"
        )
        risk_pack = next(
            (
                item
                for item in packs["items"]
                if item["name"] == "procurement-supplier-risk"
                and item["version"] == "1.0.4"
            ),
            None,
        )
        if risk_pack is None:
            raise ChainError(
                "trusted procurement-supplier-risk@1.0.4 pack was not found"
            )
        requirements = risk_pack["manifest"]["spec"]["documents"]["requirements"]
        enabled = _request(
            client,
            "POST",
            (
                f"/v1/projects/{PROJECT_ID}/capability-packs/"
                f"{risk_pack['versionId']}:enable"
            ),
            idempotency_key=f"procurement-real-enable-{nonce}",
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
            "contentHash": risk_pack["contentHash"],
        }
        if enabled["bindingStatus"] not in {"ENABLED", "READY"} or enabled["blockers"]:
            raise ChainError(
                f"capability pack is not ready: {enabled['bindingStatus']} "
                f"{enabled['blockers']}"
            )

        procurement_object = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/business-objects",
            idempotency_key=f"procurement-real-object-{nonce}",
            json_body={
                "objectType": "procurement",
                "canonicalKey": f"{PROJECT_NO}-{nonce}",
                "schemaRef": "schema://procurement/facts@1",
                "data": {
                    "projectNo": PROJECT_NO,
                    "title": PROJECT_NAME,
                    "buyer": "复旦大学附属中山医院",
                    "budgetAmount": 3930000,
                    "awardAmount": 3885000,
                    "currency": "CNY",
                },
                "provenance": {
                    "source": AWARD_URL,
                    "dataClass": "real-public",
                    "sourceSha256": public_sources["awardNotice"]["sha256"],
                },
            },
        )
        supplier_object = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/business-objects",
            idempotency_key=f"supplier-real-object-{nonce}",
            json_body={
                "objectType": "supplier",
                "canonicalKey": f"{SUPPLIER_CREDIT_CODE}-{nonce}",
                "schemaRef": "schema://supplier/identity@1",
                "data": {
                    "name": SUPPLIER_NAME,
                    "creditCode": SUPPLIER_CREDIT_CODE,
                },
                "provenance": {
                    "source": AWARD_URL,
                    "dataClass": "real-public",
                },
            },
        )
        evidence["businessObjects"] = {
            "procurement": procurement_object,
            "supplier": supplier_object,
        }

        documents: list[dict[str, Any]] = []
        with httpx.Client(base_url=ARTIFACT_URL, timeout=60) as artifact_client:
            for public_document in public_documents:
                uploaded = _upload_document(
                    client,
                    artifact_client=artifact_client,
                    business_object_id=procurement_object["businessObjectId"],
                    document=public_document,
                    nonce=nonce,
                )
                documents.append(uploaded)
                print(
                    f"uploaded {uploaded['sourceCategory']}: "
                    f"{uploaded['documentId']}",
                    flush=True,
                )
        evidence["documents"] = documents

        payload = {
            "title": f"{PROJECT_NAME}一致性与供应商风险复核",
            "projectNo": PROJECT_NO,
            "lotNo": "NO-LOT",
            "procurementType": "GOVERNMENT_GOODS",
            "asOf": "2026-07-28",
            "supplier": {
                "name": SUPPLIER_NAME,
                "creditCode": SUPPLIER_CREDIT_CODE,
                "aliases": [],
            },
            "riskSources": [
                {
                    "kind": "CCGP_SERIOUS_ILLEGAL",
                    "sourceRef": "official://ccgp/serious-illegal",
                    "endpoint": RISK_URL,
                }
            ],
            "performance": {
                "periodStart": "2026-01-01",
                "periodEnd": "2026-07-28",
                "minimumSampleSize": 3,
                "records": [],
            },
            "clauses": {},
            "semanticProposals": [],
            "approvedExceptionKeys": [],
            "previousSnapshot": None,
        }
        subjects = [
            {
                "businessObjectId": procurement_object["businessObjectId"],
                "businessObjectVersionId": procurement_object["versionId"],
                "role": "PRIMARY",
                "subjectKey": "procurement",
            },
            {
                "businessObjectId": supplier_object["businessObjectId"],
                "businessObjectVersionId": supplier_object["versionId"],
                "role": "RELATED",
                "subjectKey": "supplier",
            },
        ]
        case = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/cases",
            idempotency_key=f"procurement-real-case-{nonce}",
            json_body={
                "scenarioType": "procurement-supplier-risk-case",
                "payload": payload,
                "subjects": subjects,
                "owner": "procurement-risk-operator",
            },
        )
        evidence["case"] = case
        monitor = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/procurement-supplier-risk/monitors",
            idempotency_key=f"procurement-real-monitor-{nonce}",
            json_body={
                "caseId": case["caseId"],
                "supplierName": SUPPLIER_NAME,
                "supplierCreditCode": SUPPLIER_CREDIT_CODE,
                "cadence": "DAILY",
                "sources": payload["riskSources"],
            },
        )
        evidence["monitor"] = monitor

        accepted = _request(
            client,
            "POST",
            (
                f"/v1/projects/{PROJECT_ID}/procurement-supplier-risk/"
                f"monitors/{monitor['monitorId']}:refresh"
            ),
            idempotency_key=f"procurement-real-refresh-{nonce}",
        )
        evidence["assessmentAccepted"] = accepted
        run_id = str(accepted["runId"])
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
        evidence["assessments"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}/assessments",
        )
        evidence["reports"] = _request(
            client,
            "GET",
            (
                f"/v1/projects/{PROJECT_ID}/evaluations/"
                f"{accepted['evaluationId']}/reports"
            ),
        )
        evidence["findings"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}/findings",
        )
        evidence["history"] = _request(
            client,
            "GET",
            (
                f"/v1/projects/{PROJECT_ID}/procurement-supplier-risk/"
                f"monitors/{monitor['monitorId']}/history"
            ),
        )
        alerts = _request(
            client,
            "GET",
            (
                f"/v1/projects/{PROJECT_ID}/procurement-supplier-risk/"
                f"alerts?monitorId={monitor['monitorId']}"
            ),
        )
        evidence["alerts"] = alerts
        if not alerts.get("items"):
            raise ChainError("successful blocked assessment did not create any alert")
        hard_gate_alert = next(
            (
                item
                for item in alerts["items"]
                if item["alertType"] == "HARD_GATE"
            ),
            alerts["items"][0],
        )
        work_order = _request(
            client,
            "POST",
            (
                f"/v1/projects/{PROJECT_ID}/procurement-supplier-risk/"
                f"alerts/{hard_gate_alert['alertId']}/work-orders"
            ),
            idempotency_key=f"procurement-real-work-order-{nonce}",
            json_body={
                "priority": "CRITICAL",
                "assignee": "procurement-risk-reviewer",
            },
        )
        started = _request(
            client,
            "PATCH",
            (
                f"/v1/projects/{PROJECT_ID}/procurement-supplier-risk/"
                f"work-orders/{work_order['workOrderId']}"
            ),
            idempotency_key=f"procurement-real-work-order-start-{nonce}",
            json_body={
                "status": "IN_PROGRESS",
                "assignee": "procurement-risk-reviewer",
                "comment": "已核验财政部公开处罚记录和统一社会信用代码。",
            },
        )
        closed = _request(
            client,
            "PATCH",
            (
                f"/v1/projects/{PROJECT_ID}/procurement-supplier-risk/"
                f"work-orders/{work_order['workOrderId']}"
            ),
            idempotency_key=f"procurement-real-work-order-close-{nonce}",
            json_body={
                "status": "CLOSED",
                "assignee": "procurement-risk-reviewer",
                "resolution": {
                    "decision": "CONFIRM_BLOCK",
                    "reason": "评估时点处于政府采购禁入有效期，停止准入。",
                    "evidenceRecordId": "2c8382ba9e61ca97019f83cfaaa205a6",
                },
                "comment": "硬门禁不可由人工审批覆盖，工单按阻断结论关闭。",
            },
        )
        evidence["workOrderLifecycle"] = {
            "created": work_order,
            "started": started,
            "closed": closed,
        }
        evidence["workOrders"] = _request(
            client,
            "GET",
            (
                f"/v1/projects/{PROJECT_ID}/procurement-supplier-risk/"
                f"work-orders?monitorId={monitor['monitorId']}"
            ),
        )
        evidence["auditLogs"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/audit-logs?runId={run_id}&limit=1000",
        )

    assessment_items = evidence["assessments"].get("items", [])
    assessment = next(
        (
            item
            for item in assessment_items
            if item.get("runId") == evidence["run"]["runId"]
        ),
        None,
    )
    if not isinstance(assessment, dict) or not isinstance(assessment.get("result"), dict):
        raise ChainError("successful run did not persist its business assessment result")
    result = assessment["result"]
    decision = result.get("decision")
    hard_gate_records = result.get("risk", {}).get("hardGates", [])
    hard_gates = [
        str(item.get("code"))
        for item in hard_gate_records
        if isinstance(item, dict) and item.get("code")
    ]
    if decision != "BLOCK":
        raise ChainError(f"expected BLOCK decision, received {decision!r}")
    if "GOVERNMENT_PROCUREMENT_BAN" not in hard_gates:
        raise ChainError(f"expected government procurement ban, received {hard_gates!r}")
    if not evidence["reports"].get("items"):
        raise ChainError("no persisted report was returned")
    if not evidence["history"].get("items"):
        raise ChainError("no immutable supplier risk snapshot was returned")
    if evidence["workOrderLifecycle"]["closed"]["status"] != "CLOSED":
        raise ChainError("risk work order did not reach CLOSED")

    evidence["verification"] = {
        "runSucceeded": True,
        "decision": decision,
        "hardGates": hard_gates,
        "documentCategories": [
            item["sourceCategory"] for item in evidence["documents"]
        ],
        "agentAndToolEventsVisible": bool(
            evidence["eventHistory"].get("events")
            or evidence["eventHistory"].get("items")
        ),
        "reportCount": len(evidence["reports"].get("items", [])),
        "findingCount": len(evidence["findings"].get("items", [])),
        "snapshotCount": len(evidence["history"].get("items", [])),
        "alertCount": len(evidence["alerts"].get("items", [])),
        "workOrderClosed": True,
        "auditCount": len(evidence["auditLogs"].get("items", [])),
    }
    evidence["finishedAt"] = datetime.now(UTC).isoformat()
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
                "monitorId": evidence["monitor"]["monitorId"],
                "decision": decision,
                "hardGates": hard_gates,
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
