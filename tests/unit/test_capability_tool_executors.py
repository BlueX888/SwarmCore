from __future__ import annotations

import base64
import hashlib

import pytest
from jsonschema import Draft202012Validator
from swarmcore_application import (
    capability_executors,
    cross_file_consistency,
    document_read,
    report_render,
    rules_evaluate,
)
from swarmcore_registry import builtin_registry

PHASE_SIX_OPERATIONS = {
    "contract.document_read",
    "contract.rules_evaluate",
    "contract.cross_file_consistency",
    "workbench.record_evaluation",
    "report.render",
}


def test_phase_six_tools_have_executors_and_closed_contracts() -> None:
    registrations = {
        item.operation: item
        for item in builtin_registry().tools
        if item.operation in PHASE_SIX_OPERATIONS
    }
    assert set(registrations) == PHASE_SIX_OPERATIONS
    assert set(capability_executors(None)) == PHASE_SIX_OPERATIONS  # type: ignore[arg-type]
    for registration in registrations.values():
        Draft202012Validator.check_schema(registration.input_schema)
        Draft202012Validator.check_schema(registration.output_schema)
        assert registration.input_schema["additionalProperties"] is False
        assert registration.output_schema["additionalProperties"] is False
        assert registration.recovery_policy == "idempotent"


@pytest.mark.asyncio
async def test_document_read_verifies_content_and_returns_real_pages() -> None:
    content = "第一页\f第二页".encode()
    result = await document_read(
        {
            "documentId": "00000000-0000-0000-0000-000000000001",
            "filename": "contract.txt",
            "mediaType": "text/plain",
            "sha256": hashlib.sha256(content).hexdigest(),
            "contentBase64": base64.b64encode(content).decode(),
        },
        "effect-1",
    )
    assert [page["text"] for page in result["pages"]] == ["第一页", "第二页"]
    with pytest.raises(ValueError, match="sha256"):
        await document_read(
            {
                "documentId": "00000000-0000-0000-0000-000000000001",
                "filename": "contract.txt",
                "mediaType": "text/plain",
                "sha256": "0" * 64,
                "contentBase64": base64.b64encode(content).decode(),
            },
            "effect-2",
        )


@pytest.mark.asyncio
async def test_rules_evaluate_executes_integrity_rules() -> None:
    result = await rules_evaluate(
        {
            "ruleSetVersionId": "rules-1",
            "attachmentManifestHash": "manifest",
            "rules": {
                "schemaVersion": "schema://contract/checklist-rule@1",
                "match": {},
                "requirements": [{"key": "contract", "documentType": "contract", "required": True}],
            },
            "attachments": [],
        },
        "effect-1",
    )
    assert result["passed"] is False
    assert result["findings"][0]["code"] == "DOCUMENT_MISSING"


@pytest.mark.asyncio
async def test_report_render_returns_a_verifiable_pdf() -> None:
    first = await report_render({"title": "Evidence", "results": [], "rules": []}, "effect-1")
    retried = await report_render({"title": "Evidence", "results": [], "rules": []}, "effect-2")
    assert retried == first
    content = base64.b64decode(first["contentBase64"])
    assert content.startswith(b"%PDF-")
    assert hashlib.sha256(content).hexdigest() == first["sha256"]


@pytest.mark.asyncio
async def test_cross_file_consistency_rejects_invalid_structured_results() -> None:
    with pytest.raises(ValueError):
        await cross_file_consistency(
            {"results": [{"status": "COMPLETED"}], "rules": []}, "effect-1"
        )
