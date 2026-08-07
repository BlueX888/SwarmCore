from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def _module() -> Any:
    path = Path("scripts/qualification_audit.py")
    spec = importlib.util.spec_from_file_location("qualification_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_model_and_ocr_require_real_execution_evidence() -> None:
    audit = _module()
    model: dict[str, Any] = {
        "run": {"runId": "run-model", "status": "SUCCEEDED"},
        "runResult": {
            "status": "SUCCEEDED",
            "usage": {"inputTokens": 10, "outputTokens": 2},
            "output": {
                "status": "COMPLETED_DEGRADED",
                "resultHash": "a" * 64,
                "sandbox": {"status": "PASSED"},
            },
        },
    }
    ocr: dict[str, Any] = {
        "document": {"documentId": "doc-ocr"},
        "processing": {"status": "REVIEW_REQUIRED"},
        "processingResult": {
            "result": {
                "content": {
                    "layout": {"ocrProvider": "ocr://http-ocr@2"},
                    "pages": [{"page": 1, "sourceKind": "OCR"}],
                    "warnings": ["OCR_APPLIED"],
                }
            }
        },
        "run": {"runId": "run-ocr", "status": "SUCCEEDED"},
        "runArtifacts": {"total": 1},
        "publishedPackage": {"status": "READY"},
    }

    assert audit.audit_model(model)["status"] == "PASSED"
    assert audit.audit_ocr(ocr)["status"] == "PASSED"
    ocr["processingResult"]["result"]["content"]["pages"] = []
    assert audit.audit_ocr(ocr)["status"] == "FAILED"


def test_overall_qualification_fails_closed_without_external_evidence() -> None:
    audit = _module()
    report = audit.build_report(
        model_evidence={},
        ocr_evidence={},
        authorized_source_evidence=None,
        production_evidence=None,
    )

    assert report["status"] == "INCOMPLETE"
    assert report["checks"]["authorizedBusinessSource"]["status"] == "MISSING"
    assert report["checks"]["productionQualification"]["status"] == "MISSING"


def test_authorized_source_and_production_require_all_declared_gates() -> None:
    audit = _module()
    source: dict[str, Any] = {
        "authorization": {"authorizedBy": "data-owner", "scope": "erp.read"},
        "source": {
            "connectorRef": "connector://enterprise/erp@1",
            "sourceSystem": "ERP",
            "sourceRecordId": "PO-100",
            "contentHash": "b" * 64,
            "healthStatus": "PASSED",
        },
        "run": {"runId": "run-source", "status": "SUCCEEDED"},
    }
    production: dict[str, Any] = {
        "environment": "STAGING",
        "status": "PASSED",
        "cluster": "staging-a",
        "imageDigest": f"sha256:{'c' * 64}",
        "evidenceRef": "artifact://qualification/m6",
        "gates": {gate: "PASSED" for gate in audit.PRODUCTION_GATES},
    }

    assert audit.audit_authorized_source(source)["status"] == "PASSED"
    assert audit.audit_production(production)["status"] == "PASSED"
    production["gates"]["mtls"] = "FAILED"
    result = audit.audit_production(production)
    assert result["status"] == "FAILED"
    assert "PRODUCTION_GATE_NOT_PASSED:mtls" in result["reasons"]
