from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PRODUCTION_GATES = (
    "postgresql",
    "temporal",
    "nats",
    "s3Kms",
    "vaultWorkloadIdentity",
    "opa",
    "clamav",
    "mtls",
    "rls",
    "sandbox",
    "secretRotation",
    "observability",
    "rollback",
    "ha",
)


def _is_sha256(value: Any, *, prefix: bool = False) -> bool:
    if not isinstance(value, str):
        return False
    digest = value.removeprefix("sha256:") if prefix else value
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def _object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _array(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _result(status: str, reasons: list[str], evidence: dict[str, Any]) -> dict[str, Any]:
    return {"status": status, "reasons": reasons, "evidence": evidence}


def audit_model(document: dict[str, Any]) -> dict[str, Any]:
    run = _object(document.get("run"))
    run_result = _object(document.get("runResult"))
    output = _object(run_result.get("output"))
    usage = _object(run_result.get("usage"))
    sandbox = _object(output.get("sandbox"))
    reasons: list[str] = []
    if run.get("status") != "SUCCEEDED" or run_result.get("status") != "SUCCEEDED":
        reasons.append("MODEL_RUN_NOT_SUCCEEDED")
    if output.get("status") not in {"COMPLETED", "COMPLETED_DEGRADED"}:
        reasons.append("MODEL_RESULT_NOT_TERMINAL")
    if not _is_sha256(output.get("resultHash")):
        reasons.append("MODEL_RESULT_HASH_INVALID")
    if float(usage.get("inputTokens") or 0) <= 0 or float(usage.get("outputTokens") or 0) <= 0:
        reasons.append("MODEL_USAGE_MISSING")
    if sandbox.get("status") != "PASSED":
        reasons.append("MODEL_SANDBOX_NOT_PASSED")
    evidence = {
        "runId": run.get("runId"),
        "runStatus": run.get("status"),
        "resultStatus": output.get("status"),
        "resultHash": output.get("resultHash"),
        "inputTokens": usage.get("inputTokens"),
        "outputTokens": usage.get("outputTokens"),
        "sandboxStatus": sandbox.get("status"),
    }
    return _result("PASSED" if not reasons else "FAILED", reasons, evidence)


def audit_ocr(document: dict[str, Any]) -> dict[str, Any]:
    run = _object(document.get("run"))
    processing = _object(document.get("processing"))
    processing_result = _object(document.get("processingResult"))
    result = _object(processing_result.get("result"))
    content = _object(result.get("content"))
    layout = _object(content.get("layout"))
    pages = _array(content.get("pages"))
    artifacts = _object(document.get("runArtifacts"))
    published = _object(document.get("publishedPackage"))
    reasons: list[str] = []
    if run.get("status") != "SUCCEEDED":
        reasons.append("OCR_CHAIN_RUN_NOT_SUCCEEDED")
    if processing.get("status") not in {"READY", "REVIEW_REQUIRED"}:
        reasons.append("OCR_PROCESSING_NOT_TERMINAL")
    if layout.get("ocrProvider") in {None, "", "ocr://unconfigured@1"}:
        reasons.append("OCR_PROVIDER_MISSING")
    if not any(isinstance(page, dict) and page.get("sourceKind") == "OCR" for page in pages):
        reasons.append("OCR_PAGE_EVIDENCE_MISSING")
    if "OCR_APPLIED" not in set(content.get("warnings") or []):
        reasons.append("OCR_APPLIED_MARKER_MISSING")
    if int(artifacts.get("total") or 0) < 1:
        reasons.append("OCR_ARTIFACTS_MISSING")
    if published.get("status") != "READY":
        reasons.append("OCR_PACKAGE_NOT_PUBLISHED")
    evidence = {
        "documentId": _object(document.get("document")).get("documentId"),
        "processingStatus": processing.get("status"),
        "ocrProvider": layout.get("ocrProvider"),
        "ocrPageCount": sum(
            1 for page in pages if isinstance(page, dict) and page.get("sourceKind") == "OCR"
        ),
        "runId": run.get("runId"),
        "runStatus": run.get("status"),
        "artifactCount": artifacts.get("total"),
        "publishedStatus": published.get("status"),
    }
    return _result("PASSED" if not reasons else "FAILED", reasons, evidence)


def audit_authorized_source(document: dict[str, Any] | None) -> dict[str, Any]:
    if document is None:
        return _result("MISSING", ["AUTHORIZED_SOURCE_EVIDENCE_MISSING"], {})
    authorization = _object(document.get("authorization"))
    source = _object(document.get("source"))
    run = _object(document.get("run"))
    reasons: list[str] = []
    if not str(authorization.get("authorizedBy") or "").strip():
        reasons.append("AUTHORIZED_BY_MISSING")
    if not str(authorization.get("scope") or "").strip():
        reasons.append("AUTHORIZATION_SCOPE_MISSING")
    connector_ref = str(source.get("connectorRef") or "")
    if not connector_ref.startswith("connector://") or connector_ref.startswith(
        "connector://fake/"
    ):
        reasons.append("AUTHORIZED_CONNECTOR_INVALID")
    if not str(source.get("sourceSystem") or "").strip():
        reasons.append("SOURCE_SYSTEM_MISSING")
    if not str(source.get("sourceRecordId") or "").strip():
        reasons.append("SOURCE_RECORD_ID_MISSING")
    if not _is_sha256(source.get("contentHash")):
        reasons.append("SOURCE_CONTENT_HASH_INVALID")
    if source.get("healthStatus") != "PASSED":
        reasons.append("SOURCE_HEALTH_NOT_PASSED")
    if run.get("status") != "SUCCEEDED":
        reasons.append("AUTHORIZED_SOURCE_RUN_NOT_SUCCEEDED")
    evidence = {
        "authorizedBy": authorization.get("authorizedBy"),
        "scope": authorization.get("scope"),
        "connectorRef": source.get("connectorRef"),
        "sourceSystem": source.get("sourceSystem"),
        "sourceRecordId": source.get("sourceRecordId"),
        "contentHash": source.get("contentHash"),
        "healthStatus": source.get("healthStatus"),
        "runId": run.get("runId"),
        "runStatus": run.get("status"),
    }
    return _result("PASSED" if not reasons else "FAILED", reasons, evidence)


def audit_production(document: dict[str, Any] | None) -> dict[str, Any]:
    if document is None:
        return _result("MISSING", ["PRODUCTION_EVIDENCE_MISSING"], {})
    gates = _object(document.get("gates"))
    reasons: list[str] = []
    if document.get("environment") != "STAGING":
        reasons.append("PRODUCTION_ENVIRONMENT_NOT_STAGING")
    if document.get("status") != "PASSED":
        reasons.append("PRODUCTION_STATUS_NOT_PASSED")
    if not _is_sha256(document.get("imageDigest"), prefix=True):
        reasons.append("PRODUCTION_IMAGE_DIGEST_INVALID")
    if not str(document.get("evidenceRef") or "").strip():
        reasons.append("PRODUCTION_EVIDENCE_REF_MISSING")
    failed_gates = [gate for gate in PRODUCTION_GATES if gates.get(gate) != "PASSED"]
    reasons.extend(f"PRODUCTION_GATE_NOT_PASSED:{gate}" for gate in failed_gates)
    evidence = {
        "environment": document.get("environment"),
        "cluster": document.get("cluster"),
        "imageDigest": document.get("imageDigest"),
        "evidenceRef": document.get("evidenceRef"),
        "gates": {gate: gates.get(gate) for gate in PRODUCTION_GATES},
    }
    return _result("PASSED" if not reasons else "FAILED", reasons, evidence)


def _load(path: Path, *, optional: bool = False) -> dict[str, Any] | None:
    if not path.is_file():
        if optional:
            return None
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"evidence must be a JSON object: {path}")
    return value


def build_report(
    *,
    model_evidence: dict[str, Any],
    ocr_evidence: dict[str, Any],
    authorized_source_evidence: dict[str, Any] | None,
    production_evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    checks = {
        "realModel": audit_model(model_evidence),
        "realOcr": audit_ocr(ocr_evidence),
        "authorizedBusinessSource": audit_authorized_source(authorized_source_evidence),
        "productionQualification": audit_production(production_evidence),
    }
    return {
        "schemaVersion": "schema://swarmcore/qualification-audit@1",
        "generatedAt": datetime.now(UTC).isoformat(),
        "status": (
            "PASSED"
            if all(check["status"] == "PASSED" for check in checks.values())
            else "INCOMPLETE"
        ),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit SwarmCore qualification evidence.")
    parser.add_argument(
        "--model-evidence",
        type=Path,
        default=Path("output/swarm-calibration-real-chain/latest.json"),
    )
    parser.add_argument(
        "--ocr-evidence",
        type=Path,
        default=Path("output/document-structuring-real-chain/latest.json"),
    )
    parser.add_argument(
        "--authorized-source-evidence",
        type=Path,
        default=Path("output/authorized-business-source/latest.json"),
    )
    parser.add_argument(
        "--production-evidence",
        type=Path,
        default=Path("output/production-qualification/latest.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/qualification-audit/latest.json"),
    )
    args = parser.parse_args()
    report = build_report(
        model_evidence=_load(args.model_evidence) or {},
        ocr_evidence=_load(args.ocr_evidence) or {},
        authorized_source_evidence=_load(args.authorized_source_evidence, optional=True),
        production_evidence=_load(args.production_evidence, optional=True),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "PASSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
