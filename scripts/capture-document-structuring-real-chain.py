from __future__ import annotations

import hashlib
import json
import runpy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

chain = runpy.run_path("scripts/run-document-structuring-real-chain.py")
API_URL = cast(str, chain["API_URL"])
PROJECT_ID = chain["PROJECT_ID"]
TENANT_ID = chain["TENANT_ID"]
SOURCE_PATH = cast(Path, chain["SOURCE_PATH"])
OUTPUT_DIR = cast(Path, chain["OUTPUT_DIR"])
request = chain["_request"]
headers = chain["_headers"]

DOCUMENT_ID = "019fa704-bad2-7976-b181-99a51e806689"
CASE_ID = "019fa711-c20f-752e-85ec-15bada703930"
EVALUATION_ID = "019fa711-c26c-77f2-ab1d-bb38b953d60c"
RUN_ID = "019fa711-c272-75e1-8a18-783c5ce315a7"


def main() -> None:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_dir = OUTPUT_DIR / f"{stamp}-completed"
    artifact_dir = output_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    source = SOURCE_PATH.read_bytes()
    evidence: dict[str, Any] = {
        "startedAt": datetime.now(UTC).isoformat(),
        "tenantId": str(TENANT_ID),
        "projectId": str(PROJECT_ID),
        "documentId": DOCUMENT_ID,
        "caseId": CASE_ID,
        "evaluationId": EVALUATION_ID,
        "runId": RUN_ID,
        "source": {
            "path": str(SOURCE_PATH.resolve()),
            "filename": SOURCE_PATH.name,
            "sizeBytes": len(source),
            "sha256": hashlib.sha256(source).hexdigest(),
            "origin": "GOV.UK Digital Outcomes and Specialists 4 call-off contract",
            "dataClass": "public-real-document",
        },
    }
    with httpx.Client(base_url=API_URL, timeout=90) as client:
        evidence["processing"] = request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/documents/{DOCUMENT_ID}/processing",
        )
        evidence["processingEvents"] = request(
            client,
            "GET",
            (
                f"/v1/projects/{PROJECT_ID}/documents/{DOCUMENT_ID}"
                "/processing/events?limit=500"
            ),
        )
        evidence["processingResult"] = request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/documents/{DOCUMENT_ID}/processing-result",
        )
        evidence["run"] = request(
            client, "GET", f"/v1/projects/{PROJECT_ID}/runs/{RUN_ID}"
        )
        evidence["eventHistory"] = request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{RUN_ID}/event-history",
        )
        evidence["runResult"] = request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{RUN_ID}/result",
        )
        evidence["assessment"] = request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/assessments/{EVALUATION_ID}",
        )
        evidence["approvals"] = request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/approvals?runId={RUN_ID}",
        )
        evidence["structuredPackageBeforePublish"] = request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/documents/{DOCUMENT_ID}/structured-package",
        )
        evidence["publishedPackage"] = request(
            client,
            "POST",
            f"/v1/projects/{PROJECT_ID}/documents/{DOCUMENT_ID}:publish",
            actor="document-chain-reviewer",
            idempotency_key="document-final-8110-formal-publish",
        )
        artifacts = request(
            client,
            "GET",
            f"/v1/projects/{PROJECT_ID}/runs/{RUN_ID}/artifacts",
        )
        evidence["runArtifacts"] = artifacts
        downloaded: list[dict[str, Any]] = []
        for artifact in artifacts.get("items", []):
            artifact_id = str(artifact["artifactId"])
            grant = request(
                client,
                "POST",
                f"/v1/projects/{PROJECT_ID}/artifacts/{artifact_id}:download",
            )
            response = client.get(str(grant["downloadRef"]), headers=headers())
            response.raise_for_status()
            target = artifact_dir / Path(str(artifact["filename"])).name
            target.write_bytes(response.content)
            downloaded.append(
                {
                    **artifact,
                    "downloadedPath": str(target.resolve()),
                    "downloadedSha256": hashlib.sha256(response.content).hexdigest(),
                }
            )
        evidence["downloadedArtifacts"] = downloaded

    evidence["finishedAt"] = datetime.now(UTC).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "evidence.json"
    serialized = json.dumps(evidence, ensure_ascii=False, indent=2, default=str)
    output_path.write_text(serialized, encoding="utf-8")
    (OUTPUT_DIR / "latest.json").write_text(serialized, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": evidence["run"]["status"],
                "documentStatus": evidence["publishedPackage"]["status"],
                "artifactCount": evidence["runArtifacts"]["total"],
                "evidence": str(output_path.resolve()),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
