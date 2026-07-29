from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

TENANT_ID = "00000000-0000-0000-0000-000000000001"
PROJECT_ID = "00000000-0000-0000-0000-000000000002"
API_URL = os.getenv("SWARMCORE_PUBLIC_REPLAY_API_URL", "http://127.0.0.1:8000").rstrip("/")
ARTIFACT_URL = os.getenv(
    "SWARMCORE_PUBLIC_REPLAY_ARTIFACT_URL", "http://127.0.0.1:8091"
).rstrip("/")
OUTPUT_DIR = Path("output/contract-performance-public-chain")
CONTRACT_URL = (
    "https://www.contractsfinder.service.gov.uk/Notice/Attachment/"
    "45b270f2-647d-4203-835d-4c020fdbfaaf"
)
APRIL_URL = (
    "https://assets.publishing.service.gov.uk/media/66a37d8f49b9c0597fdb0560/"
    "DfE_Spend__25k_April_2024.csv"
)
SEPTEMBER_URL = (
    "https://assets.publishing.service.gov.uk/media/674456951034a5f4a58568bb/"
    "DfE_Spend_Sept_2024_Transparency__25k.csv"
)
SCOPES = (
    "case.create case.read case.assess document.read evidence.submit "
    "plan.review plan.publish approval.respond contract-performance.audit report.read"
)
TERMINAL_RUN_STATUSES = {"SUCCEEDED", "FAILED", "CANCELLED", "TIMED_OUT"}
TERMINAL_PROCESSING_STATUSES = {
    "SUCCEEDED",
    "READY",
    "REVIEW_REQUIRED",
    "FAILED",
    "CANCELLED",
}


class ChainError(RuntimeError):
    pass


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    actor: str = "public-contract-operator",
    idempotency_key: str | None = None,
    if_match: int | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "X-Actor-ID": actor,
        "X-Scopes": SCOPES,
    }
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    if if_match is not None:
        headers["If-Match"] = f'"{if_match}"'
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


def _download_public_file(url: str) -> tuple[bytes, dict[str, Any]]:
    headers = {
        "Accept": "application/pdf,text/csv,*/*",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36"
        ),
    }
    with httpx.Client(headers=headers, follow_redirects=True, timeout=180) as client:
        response = client.get(url)
        response.raise_for_status()
    content = response.content
    return content, {
        "requestedUrl": url,
        "finalUrl": str(response.url),
        "statusCode": response.status_code,
        "mediaType": str(response.headers.get("content-type") or "").split(";", 1)[0],
        "etag": response.headers.get("etag"),
        "lastModified": response.headers.get("last-modified"),
        "contentLength": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "retrievedAt": datetime.now(UTC).isoformat(),
    }


def _wait_for_processing(
    client: httpx.Client,
    document_id: str,
    *,
    timeout_seconds: int = 300,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    latest: dict[str, Any] = {}
    while time.monotonic() < deadline:
        latest = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/documents/{document_id}/processing",
        )
        status = str(latest.get("status") or "")
        if status in TERMINAL_PROCESSING_STATUSES:
            if status in {"FAILED", "CANCELLED"}:
                raise ChainError(f"document processing ended with {status}: {latest}")
            events = _request(
                client,
                "GET",
                f"/v1/projects/{PROJECT_ID}/documents/{document_id}/processing/events",
            )
            result = _request(
                client,
                "GET",
                f"/v1/projects/{PROJECT_ID}/documents/{document_id}/processing-result",
            )
            return latest, events, result
        time.sleep(2)
    raise ChainError(f"document processing did not finish: {latest}")


def _approval_value(operation: str) -> dict[str, Any]:
    if operation == "INITIALIZE":
        return {
            "approved": True,
            "confirmations": [
                "已核对公开合同原文、页码与哈希",
                "仅发布候选履约基线, 不作企业履约结论",
            ],
            "comment": "公开真实数据回放: 发布候选计划用于后续付款候选匹配。",
        }
    return {
        "decision": "REQUEST_EVIDENCE",
        "reason": (
            "公开支出交易参考号不能唯一对应 ESFA-25001; 保持候选关联并要求合同/PO 交叉键。"
        ),
    }


def _wait_for_run(
    client: httpx.Client,
    run_id: str,
    *,
    operation: str,
    timeout_seconds: int = 900,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    deadline = time.monotonic() + timeout_seconds
    approvals: list[dict[str, Any]] = []
    decided: set[str] = set()
    while time.monotonic() < deadline:
        snapshot = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}",
        )
        if str(snapshot["status"]) in TERMINAL_RUN_STATUSES:
            return snapshot, approvals
        pending = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/approvals?runId={run_id}",
        )
        for approval in pending.get("items", []):
            approval_id = str(approval["approvalId"])
            if approval_id in decided:
                continue
            decision = _request(
                client,
                "POST",
                f"/v1/projects/{PROJECT_ID}/approvals/{approval_id}:approve",
                actor="public-contract-reviewer",
                idempotency_key=f"public-chain-approval-{approval_id}",
                json_body={"value": _approval_value(operation)},
            )
            approvals.append({"request": approval, "decision": decision})
            decided.add(approval_id)
        time.sleep(2)
    raise ChainError(f"run {run_id} did not finish in {timeout_seconds} seconds")


def _run_evidence(
    client: httpx.Client,
    *,
    run: dict[str, Any],
    assessment: dict[str, Any],
    approvals: list[dict[str, Any]],
) -> dict[str, Any]:
    run_id = str(run["runId"])
    evaluation_id = str(assessment["evaluationId"])
    return {
        "run": run,
        "approvals": approvals,
        "result": _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/result",
        ),
        "eventHistory": _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/event-history",
        ),
        "artifacts": _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/artifacts",
        ),
        "reports": _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/evaluations/{evaluation_id}/reports",
        ),
    }


def _json_report(run_evidence: dict[str, Any]) -> dict[str, Any]:
    for item in run_evidence["reports"].get("items", []):
        if item.get("format") == "JSON" and isinstance(item.get("content"), dict):
            return dict(item["content"])
    raise ChainError("JSON report was not recorded")


def _assert_public_result(
    initialize_result: dict[str, Any],
    collect_result: dict[str, Any],
) -> dict[str, Any]:
    plan = initialize_result.get("plan") or {}
    contract = plan.get("contract") or {}
    contract_number = str(
        contract.get("contractNumber")
        or contract.get("masterContractNumber")
        or contract.get("number")
        or ""
    )
    if contract_number != "ESFA-25001":
        raise ChainError(f"unexpected contract number: {contract_number!r}")
    obligations = list(plan.get("obligations") or [])
    milestones = list(plan.get("milestones") or [])
    payment_conditions = list(plan.get("paymentConditions") or [])
    acceptance = list(plan.get("acceptanceCriteria") or [])
    service_levels = list(plan.get("serviceLevels") or [])
    if len(obligations) < 10:
        raise ChainError(f"expected at least 10 obligations, received {len(obligations)}")
    if len(milestones) < 3:
        raise ChainError(f"expected at least 3 milestones, received {len(milestones)}")
    if not payment_conditions or not acceptance or not service_levels:
        raise ChainError("payment, acceptance, or service-level candidates are missing")
    evidence_pages: set[int] = set()
    for item in [
        contract,
        *obligations,
        *list(plan.get("deliverables") or []),
        *milestones,
        *acceptance,
        *service_levels,
        *payment_conditions,
    ]:
        if not isinstance(item, dict):
            continue
        for reference in item.get("evidenceRefs") or []:
            if isinstance(reference, dict) and isinstance(reference.get("page"), int):
                evidence_pages.add(int(reference["page"]))
    if not evidence_pages or max(evidence_pages) <= 1:
        raise ChainError("contract plan evidence does not retain real PDF page locators")
    ledger = collect_result.get("evidenceLedger") or {}
    payment_evidence = [
        item
        for item in ledger.get("evidence") or []
        if str(item.get("type") or "").upper() == "PAYMENT"
    ]
    if len(payment_evidence) != 5:
        raise ChainError(
            f"expected five public payment candidates, received {len(payment_evidence)}"
        )
    total = round(sum(float(item.get("amount") or 0) for item in payment_evidence), 2)
    if total != 4_218_003.64:
        raise ChainError(f"unexpected public payment total: {total}")
    links = list(ledger.get("links") or [])
    if collect_result.get("status") != "REVIEW_REQUIRED":
        raise ChainError(
            f"public payment result must require review: {collect_result.get('status')}"
        )
    if any(item.get("matchStatus") == "MATCHED" for item in links):
        raise ChainError("public payment evidence must not be asserted as a stable contract match")
    return {
        "contractNumber": contract_number,
        "obligationCount": len(obligations),
        "milestoneCount": len(milestones),
        "paymentConditionCount": len(payment_conditions),
        "acceptanceCriterionCount": len(acceptance),
        "serviceLevelCount": len(service_levels),
        "evidencePages": sorted(evidence_pages),
        "paymentCandidateCount": len(payment_evidence),
        "paymentCandidateTotalGbp": total,
        "transactionNumbers": sorted(
            str(item.get("sourceRecordId") or "") for item in payment_evidence
        ),
        "status": collect_result.get("status"),
        "resultHash": collect_result.get("resultHash"),
    }


def main() -> int:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    nonce = uuid4().hex[:10]
    evidence: dict[str, Any] = {
        "startedAt": datetime.now(UTC).isoformat(),
        "tenantId": TENANT_ID,
        "projectId": PROJECT_ID,
        "dataClass": "public-real-data",
    }
    contract_content, contract_http = _download_public_file(CONTRACT_URL)
    april_content, april_http = _download_public_file(APRIL_URL)
    september_content, september_http = _download_public_file(SEPTEMBER_URL)
    evidence["publicSources"] = {
        "contract": contract_http,
        "aprilSpend": april_http,
        "septemberSpend": september_http,
    }
    del april_content, september_content

    with httpx.Client(base_url=API_URL, timeout=120) as client:
        health = client.get("/health/live")
        health.raise_for_status()
        evidence["apiHealth"] = health.json()
        packs = _request(client, "GET", f"/v1/projects/{PROJECT_ID}/capability-packs")
        pack = next(
            (
                item
                for item in packs["items"]
                if item["name"] == "contract-performance" and item["version"] == "1.0.16"
            ),
            None,
        )
        if pack is None:
            raise ChainError("trusted contract-performance@1.0.16 pack was not found")
        requirements = pack["manifest"]["spec"]["documents"]["requirements"]
        enabled = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/capability-packs/{pack['versionId']}:enable",
            idempotency_key=f"public-chain-enable-{nonce}",
            json_body={
                "configuration": {
                    "timezone": "Europe/London",
                    "currency": "GBP",
                    "documentRequirements": requirements,
                }
            },
        )
        evidence["capabilityPack"] = enabled

        business_object = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/business-objects",
            idempotency_key=f"public-chain-object-{nonce}",
            json_body={
                "objectType": "contract",
                "canonicalKey": f"ESFA-25001-{nonce}",
                "schemaRef": "schema://contract/facts@1",
                "data": {
                    "contractNumber": "ESFA-25001",
                    "title": "Skills Bootcamps DPS Second Competitions",
                    "supplier": "COGRAMMAR LTD",
                    "amount": 7_000_300,
                    "currency": "GBP",
                    "startDate": "2023-09-01",
                    "endDate": "2024-08-31",
                },
                "provenance": {
                    "source": CONTRACT_URL,
                    "retrievedAt": contract_http["retrievedAt"],
                    "contentHash": contract_http["sha256"],
                    "authorization": "public-contracts-finder",
                },
            },
        )
        evidence["businessObject"] = business_object
        digest = str(contract_http["sha256"])
        initiated = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/documents:initiate",
            idempotency_key=f"public-chain-document-init-{nonce}",
            json_body={
                "name": "DfE and Cogrammar signed Skills Bootcamps contract",
                "category": "MASTER_CONTRACT",
                "tags": ["MASTER_CONTRACT", "CONTRACT", "PUBLIC_REAL_DATA"],
                "filename": "DfE_Cogrammar_ESFA-25001_signed_contract.pdf",
                "mediaType": "application/pdf",
                "sizeBytes": len(contract_content),
                "sha256": digest,
                "businessObjectIds": [business_object["businessObjectId"]],
                "businessWorkKeys": ["contract-performance", "contract-performance-case"],
                "retentionDays": 365,
            },
        )
        with httpx.Client(base_url=ARTIFACT_URL, timeout=120) as artifact_client:
            upload = artifact_client.post(
                initiated["uploadRef"],
                json={
                    "capabilityToken": initiated["capabilityToken"],
                    "contentBase64": base64.b64encode(contract_content).decode(),
                },
            )
            upload.raise_for_status()
            evidence["artifactUpload"] = upload.json()
        document = _request(
            client,
            "POST",
            (
                f"/v1/projects/{PROJECT_ID}/document-uploads/"
                f"{initiated['uploadId']}:complete"
            ),
            idempotency_key=f"public-chain-document-complete-{nonce}",
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
        processing, processing_events, processing_result = _wait_for_processing(
            client,
            str(document["documentId"]),
        )
        evidence["documentProcessing"] = processing
        evidence["documentProcessingEvents"] = processing_events
        evidence["documentProcessingResult"] = processing_result

        subject = {
            "businessObjectId": business_object["businessObjectId"],
            "businessObjectVersionId": business_object["versionId"],
            "role": "PRIMARY",
            "subjectKey": "contract",
        }
        case = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/cases",
            idempotency_key=f"public-chain-case-{nonce}",
            json_body={
                "scenarioType": "contract-performance-case",
                "payload": {
                    "operation": "INITIALIZE",
                    "contractObjectId": business_object["businessObjectId"],
                    "asOf": "2024-09-30",
                    "title": "DfE/Cogrammar public contract performance replay",
                    "contractNumber": "ESFA-25001",
                    "timezone": "Europe/London",
                    "currency": "GBP",
                },
                "subjects": [subject],
                "owner": "public-contract-operator",
            },
        )
        evidence["case"] = case
        initialize_assessment = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}:assess",
            idempotency_key=f"public-chain-initialize-{nonce}",
        )
        initialize_run, initialize_approvals = _wait_for_run(
            client,
            str(initialize_assessment["runId"]),
            operation="INITIALIZE",
        )
        if initialize_run["status"] != "SUCCEEDED":
            raise ChainError(f"initialize run ended with {initialize_run['status']}")
        initialize_evidence = _run_evidence(
            client,
            run=initialize_run,
            assessment=initialize_assessment,
            approvals=initialize_approvals,
        )
        evidence["initialize"] = initialize_evidence
        initialize_result = _json_report(initialize_evidence)

        collection_payload = {
            "operation": "COLLECT",
            "contractObjectId": business_object["businessObjectId"],
            "asOf": "2024-09-30",
            "title": "DfE/Cogrammar public payment candidate collection",
            "contractNumber": "ESFA-25001",
            "timezone": "Europe/London",
            "currency": "GBP",
            "plan": initialize_result["plan"],
            "sources": [
                {
                    "sourceRef": "public://dfe-spend/2024-04",
                    "kind": "PUBLIC_DFE_SPEND_CSV",
                    "url": APRIL_URL,
                    "filters": {
                        "Supplier": "Cogrammar Ltd",
                        "Expense Area": "Apprenticeships and Skills Bootcamps",
                    },
                    "currency": "GBP",
                },
                {
                    "sourceRef": "public://dfe-spend/2024-09",
                    "kind": "PUBLIC_DFE_SPEND_CSV",
                    "url": SEPTEMBER_URL,
                    "filters": {
                        "Supplier": "Cogrammar Ltd",
                        "Expense Area": "Apprenticeships and Skills Bootcamps",
                    },
                    "currency": "GBP",
                },
            ],
        }
        revised = _request(
            client,
            "PATCH",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}",
            idempotency_key=f"public-chain-collect-revision-{nonce}",
            if_match=int(case["revision"]),
            json_body={"payload": collection_payload, "owner": "public-contract-operator"},
        )
        evidence["collectionRevision"] = revised
        collect_assessment = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}:assess",
            idempotency_key=f"public-chain-collect-{nonce}",
        )
        collect_run, collect_approvals = _wait_for_run(
            client,
            str(collect_assessment["runId"]),
            operation="COLLECT",
        )
        if collect_run["status"] != "SUCCEEDED":
            raise ChainError(f"collect run ended with {collect_run['status']}")
        collect_evidence = _run_evidence(
            client,
            run=collect_run,
            assessment=collect_assessment,
            approvals=collect_approvals,
        )
        evidence["collect"] = collect_evidence
        collect_result = _json_report(collect_evidence)
        evidence["acceptance"] = _assert_public_result(initialize_result, collect_result)
        evidence["assessments"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}/assessments",
        )
        evidence["findings"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}/findings",
        )

    evidence["finishedAt"] = datetime.now(UTC).isoformat()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"public-chain-{stamp}-{nonce}.json"
    encoded = json.dumps(evidence, ensure_ascii=False, indent=2, default=str)
    output_path.write_text(encoded, encoding="utf-8")
    (OUTPUT_DIR / "latest.json").write_text(encoded, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "initializeRunId": evidence["initialize"]["run"]["runId"],
                "collectRunId": evidence["collect"]["run"]["runId"],
                "caseId": evidence["case"]["caseId"],
                "acceptance": evidence["acceptance"],
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
        print(f"PUBLIC_CHAIN_FAILED: {exc}", file=sys.stderr, flush=True)
        raise
