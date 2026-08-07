from __future__ import annotations

# ruff: noqa: RUF001
import asyncio
import base64
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text
from swarmcore_api.settings import Settings
from swarmcore_persistence import Database
from swarmcore_persistence.models import Project, Tenant

API_URL = os.getenv("SWARMCORE_QUALIFICATION_API_URL", "http://127.0.0.1:8110")
ARTIFACT_URL = os.getenv(
    "SWARMCORE_QUALIFICATION_ARTIFACT_URL", "http://127.0.0.1:8091"
)
SOURCE_PATH = Path(
    os.getenv(
        "SWARMCORE_QUALIFICATION_DOCUMENT_PATH",
        ".tmp/document-structuring-demo/dos-4-call-off-contract.odt",
    )
)
SOURCE_MEDIA_TYPE = os.getenv(
    "SWARMCORE_QUALIFICATION_DOCUMENT_MEDIA_TYPE",
    "application/vnd.oasis.opendocument.text",
)
SOURCE_ORIGIN = os.getenv(
    "SWARMCORE_QUALIFICATION_DOCUMENT_ORIGIN",
    "GOV.UK Digital Outcomes and Specialists 4 call-off contract",
)
SOURCE_DATA_CLASS = os.getenv(
    "SWARMCORE_QUALIFICATION_DOCUMENT_DATA_CLASS", "public-real-document"
)
SOURCE_TAGS = [
    value.strip()
    for value in os.getenv(
        "SWARMCORE_QUALIFICATION_DOCUMENT_TAGS", "CONTRACT,ODF,PUBLIC_REAL_CHAIN"
    ).split(",")
    if value.strip()
]
SOURCE_CASE_TITLE = os.getenv(
    "SWARMCORE_QUALIFICATION_DOCUMENT_CASE_TITLE",
    "GOV.UK DOS 4 合同真实文件结构化",
)
SOURCE_NOTES = os.getenv(
    "SWARMCORE_QUALIFICATION_DOCUMENT_NOTES",
    "使用公开真实 ODT，验证解析、NLP、工具、人工确认和发布。",
)
OUTPUT_DIR = Path("output/document-structuring-real-chain")
TENANT_ID = UUID("1813c340-7bdc-42ed-b12d-cb9c91bf1fb3")
PROJECT_ID = UUID("38c74291-3e6b-4fbe-822a-964d5ee43b1a")
TERMINAL_RUN_STATUSES = {"SUCCEEDED", "FAILED", "CANCELLED", "TIMED_OUT"}
TERMINAL_PROCESSING_STATUSES = {"READY", "REVIEW_REQUIRED", "FAILED", "CANCELLED"}


class ChainError(RuntimeError):
    pass


async def _bootstrap_scope() -> None:
    """Create an isolated verification scope without changing existing demo data."""
    database = Database(Settings().database_url)
    try:
        async with database.sessions() as session, session.begin():
            tenant = await session.get(Tenant, TENANT_ID)
            if tenant is None:
                session.add(
                    Tenant(
                        id=TENANT_ID,
                        name="Document Structuring Real Chain Final Isolation",
                        status="ACTIVE",
                    )
                )
                await session.flush()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": str(TENANT_ID)},
            )
            await session.execute(
                text("SELECT set_config('app.project_id', :project, true)"),
                {"project": str(PROJECT_ID)},
            )
            project = await session.get(Project, PROJECT_ID)
            if project is None:
                session.add(
                    Project(
                        id=PROJECT_ID,
                        tenant_id=TENANT_ID,
                        name="Document Structuring Verification",
                    )
                )
    finally:
        await database.dispose()


def _headers(
    *,
    actor: str = "document-chain-operator",
    idempotency_key: str | None = None,
) -> dict[str, str]:
    value = {
        "X-Tenant-ID": str(TENANT_ID),
        "X-Actor-ID": actor,
        "X-Scopes": (
            "capability.read capability.manage case.create case.read case.assess "
            "document.read document.review document.publish approval.read "
            "approval.respond approval.decide report.read run.read artifact.read"
        ),
    }
    if idempotency_key is not None:
        value["Idempotency-Key"] = idempotency_key
    return value


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    actor: str = "document-chain-operator",
    idempotency_key: str | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = client.request(
        method,
        path,
        headers=_headers(actor=actor, idempotency_key=idempotency_key),
        json=json_body,
    )
    if response.status_code >= 400:
        raise ChainError(
            f"{method} {path} returned {response.status_code}: {response.text[:5000]}"
        )
    if not response.content:
        return {}
    value = response.json()
    if not isinstance(value, dict):
        raise ChainError(f"{method} {path} returned a non-object response")
    return value


def _wait_for_processing(
    client: httpx.Client,
    document_id: str,
    *,
    timeout_seconds: int = 300,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    deadline = time.monotonic() + timeout_seconds
    last_status = ""
    while time.monotonic() < deadline:
        processing = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/documents/{document_id}/processing",
        )
        status = str(processing["status"])
        if status != last_status:
            print(
                f"document {document_id}: {status}/{processing['currentStage']}",
                flush=True,
            )
            last_status = status
        if status in TERMINAL_PROCESSING_STATUSES:
            events = _request(
                client,
                "GET",
                (
                    f"/v1/projects/{PROJECT_ID}/documents/{document_id}"
                    "/processing/events?limit=500"
                ),
            )
            result = (
                _request(
                    client,
                    "GET",
                    (
                        f"/v1/projects/{PROJECT_ID}/documents/{document_id}"
                        "/processing-result"
                    ),
                )
                if status in {"READY", "REVIEW_REQUIRED"}
                else {}
            )
            return processing, events, result
        time.sleep(1)
    raise ChainError(f"document processing did not finish in {timeout_seconds} seconds")


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
        if status in TERMINAL_RUN_STATUSES:
            return snapshot, approvals
        pending = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/approvals?runId={run_id}",
        )
        for request in pending.get("items", []):
            approval_id = str(request["approvalId"])
            if approval_id in approved_ids:
                continue
            decision = _request(
                client,
                "POST",
                f"/v1/projects/{PROJECT_ID}/approvals/{approval_id}:approve",
                actor="document-chain-reviewer",
                idempotency_key=f"document-chain-approve-{approval_id}",
                json_body={
                    "value": {
                        "decision": "CONFIRM",
                        "reason": (
                            "已核对真实 ODF 原文、字段证据、表格与质量标记，"
                            "确认进入结构化发布。"
                        ),
                        "fieldCorrections": [],
                    }
                },
            )
            approvals.append({"request": request, "decision": decision})
            approved_ids.add(approval_id)
            print(f"approved {approval_id}", flush=True)
        time.sleep(2)
    raise ChainError(f"run {run_id} did not finish in {timeout_seconds} seconds")


def _download_artifacts(
    client: httpx.Client,
    run_id: str,
    target_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    listing = _request(
        client,
        "GET",
        f"/v1/projects/{PROJECT_ID}/runs/{run_id}/artifacts",
    )
    downloaded: list[dict[str, Any]] = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for artifact in listing.get("items", []):
        artifact_id = str(artifact["artifactId"])
        grant = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/artifacts/{artifact_id}:download",
        )
        response = client.get(
            str(grant["downloadRef"]),
            headers=_headers(),
        )
        if response.status_code >= 400:
            raise ChainError(
                f"artifact download returned {response.status_code}: {response.text[:1000]}"
            )
        filename = str(artifact["filename"])
        destination = target_dir / filename
        destination.write_bytes(response.content)
        downloaded.append(
            {
                **artifact,
                "downloadedPath": str(destination.resolve()),
                "downloadedSha256": hashlib.sha256(response.content).hexdigest(),
            }
        )
    return listing, downloaded


def main() -> int:
    if not SOURCE_PATH.is_file():
        raise ChainError(f"real source document is missing: {SOURCE_PATH}")
    asyncio.run(_bootstrap_scope())
    source = SOURCE_PATH.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    nonce = uuid4().hex[:10]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    evidence: dict[str, Any] = {
        "startedAt": datetime.now(UTC).isoformat(),
        "tenantId": str(TENANT_ID),
        "projectId": str(PROJECT_ID),
        "source": {
            "path": str(SOURCE_PATH.resolve()),
            "filename": SOURCE_PATH.name,
            "mediaType": SOURCE_MEDIA_TYPE,
            "sizeBytes": len(source),
            "sha256": digest,
            "dataClass": SOURCE_DATA_CLASS,
            "origin": SOURCE_ORIGIN,
        },
    }
    with httpx.Client(base_url=API_URL, timeout=90) as client:
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
                if item["name"] == "document-structuring"
                and item["version"] == "1.0.0"
            ),
            None,
        )
        if pack is None:
            raise ChainError("trusted document-structuring@1.0.0 pack was not found")
        enabled = _request(
            client,
            "POST",
            (
                f"/v1/projects/{PROJECT_ID}/capability-packs/"
                f"{pack['versionId']}:enable"
            ),
            idempotency_key=f"document-chain-enable-{nonce}",
            json_body={
                "configuration": {
                    "language": "en-GB",
                    "reviewThreshold": 0.85,
                    "chunkSize": 1200,
                    "chunkOverlap": 120,
                }
            },
        )
        evidence["capabilityPack"] = enabled
        work = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/business-works/document-structuring",
        )
        evidence["businessWorkBeforeUpload"] = work

        batch = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/upload-batches",
            idempotency_key=f"document-chain-batch-{nonce}",
            json_body={
                "source": "public-real-chain",
                "context": {
                    "origin": evidence["source"]["origin"],
                    "sourceSha256": digest,
                },
            },
        )
        evidence["uploadBatch"] = batch
        initiated = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/documents:initiate",
            idempotency_key=f"document-chain-init-{nonce}",
            json_body={
                "name": SOURCE_PATH.stem,
                "category": "SOURCE_DOCUMENT",
                "tags": SOURCE_TAGS,
                "filename": SOURCE_PATH.name,
                "mediaType": evidence["source"]["mediaType"],
                "sizeBytes": len(source),
                "sha256": digest,
                "businessWorkKeys": ["document-structuring"],
                "retentionDays": 365,
            },
        )
        with httpx.Client(base_url=ARTIFACT_URL, timeout=90) as artifact_client:
            upload = artifact_client.post(
                str(initiated["uploadRef"]),
                json={
                    "capabilityToken": initiated["capabilityToken"],
                    "contentBase64": base64.b64encode(source).decode(),
                },
            )
            if upload.status_code >= 400:
                raise ChainError(
                    f"artifact upload returned {upload.status_code}: {upload.text[:3000]}"
                )
            evidence["artifactUpload"] = upload.json()
        document = _request(
            client,
            "POST",
            (
                f"/v1/projects/{PROJECT_ID}/document-uploads/"
                f"{initiated['uploadId']}:complete"
            ),
            idempotency_key=f"document-chain-complete-{nonce}",
            json_body={
                "sha256": digest,
                "uploadBatchId": batch["batchId"],
                "profileRef": "document-profile://business-structuring@1",
                "extractionSchemaRef": "schema://document/contract-structure@1",
                "classificationLabels": [
                    {"label": "CONTRACT", "source": "human"}
                ],
            },
        )
        evidence["document"] = document
        document_id = str(document["documentId"])
        processing, events, processing_result = _wait_for_processing(
            client,
            document_id,
        )
        evidence["processing"] = processing
        evidence["processingEvents"] = events
        evidence["processingResult"] = processing_result
        if processing["status"] in {"FAILED", "CANCELLED"}:
            raise ChainError(
                f"document preprocessing ended with {processing['status']}: "
                f"{processing.get('errorCode')} {processing.get('errorDetail')}"
            )
        work = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/business-works/document-structuring",
        )
        evidence["businessWorkAfterProcessing"] = work
        if work["status"] != "runnable":
            raise ChainError(f"document-structuring work is not runnable: {work['blockers']}")

        case = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/cases",
            idempotency_key=f"document-chain-case-{nonce}",
            json_body={
                "scenarioType": "document-structuring-case",
                "businessWorkKey": "document-structuring",
                "documentIds": [document_id],
                "payload": {
                    "title": SOURCE_CASE_TITLE,
                    "language": "en-GB",
                    "notes": SOURCE_NOTES,
                },
                "subjects": [],
                "owner": "document-chain-operator",
            },
        )
        evidence["case"] = case
        assessment = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/cases/{case['caseId']}:assess",
            idempotency_key=f"document-chain-assess-{nonce}",
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
            raise ChainError(f"capability run ended with {run['status']}")
        evidence["runResult"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{run_id}/result",
        )
        evidence["assessment"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/assessments/{assessment['evaluationId']}",
        )
        evidence["structuredPackageBeforePublish"] = _request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/documents/{document_id}/structured-package",
        )
        published = _request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/documents/{document_id}:publish",
            actor="document-chain-reviewer",
            idempotency_key=f"document-chain-publish-{nonce}",
        )
        evidence["publishedPackage"] = published
        artifacts, downloaded = _download_artifacts(
            client,
            run_id,
            OUTPUT_DIR / f"{stamp}-{nonce}" / "artifacts",
        )
        evidence["runArtifacts"] = artifacts
        evidence["downloadedArtifacts"] = downloaded

    evidence["finishedAt"] = datetime.now(UTC).isoformat()
    output_dir = OUTPUT_DIR / f"{stamp}-{nonce}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "evidence.json"
    output_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "latest.json").write_text(
        output_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "documentId": evidence["document"]["documentId"],
                "caseId": evidence["case"]["caseId"],
                "runId": evidence["run"]["runId"],
                "artifactCount": evidence["runArtifacts"]["total"],
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
        print(f"DOCUMENT_REAL_CHAIN_FAILED: {exc}", file=sys.stderr, flush=True)
        raise
