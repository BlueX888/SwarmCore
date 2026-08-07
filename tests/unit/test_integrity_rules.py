from datetime import UTC, datetime, timedelta

import pytest
from swarmcore_application import (
    AttachmentInput,
    IntegrityRuleDocument,
    evaluate_integrity,
    select_unique_rule,
)
from swarmcore_application.integrity import finalize_integrity_result


def _rules() -> IntegrityRuleDocument:
    return IntegrityRuleDocument.model_validate(
        {
            "schemaVersion": "schema://contract/checklist-rule@1",
            "match": {"contractType": "purchase"},
            "requirements": [
                {
                    "key": "contract",
                    "documentType": "contract",
                    "mediaTypes": ["application/pdf"],
                },
                {"key": "license", "documentType": "business-license"},
                {"key": "authorization", "documentType": "authorization"},
            ],
        }
    )


def _attachment(kind: str, digest: str | None = None) -> AttachmentInput:
    return AttachmentInput(
        attachmentId=f"attachment-{kind}",
        blobId=f"blob-{kind}",
        documentType=kind,
        filename=f"{kind}.pdf",
        mediaType="application/pdf",
        sha256=digest or kind.ljust(64, "0")[:64],
    )


def test_finalize_integrity_result_preserves_cross_file_findings_and_approval() -> None:
    result = finalize_integrity_result(
        {
            "passed": True,
            "ruleSetVersionId": "rules-v1",
            "attachmentManifestHash": "manifest-1",
            "checks": {"requirements": 1},
            "findings": [],
        },
        {
            "reviewRequired": True,
            "findings": [
                {
                    "ruleKey": "amount",
                    "code": "CROSS_FILE_MISMATCH",
                    "severity": "HIGH",
                    "detail": "合同金额不一致",
                    "requiresReview": True,
                    "evidence": [{"page": 1, "text": "100 元"}],
                }
            ],
        },
        {"schemaVersion": "schema://contract/document-extraction@1"},
        {"approved": True, "reason": "按补充协议处理"},
    )

    assert result["passed"] is False
    assert result["reviewRequired"] is True
    assert result["checks"]["crossFileFindings"] == 1
    assert result["findings"][0]["category"] == "cross-file-consistency"
    assert result["approval"]["reason"] == "按补充协议处理"


def test_fixed_integrity_scenario_missing_then_complete() -> None:
    first = evaluate_integrity(
        rule_set_version_id="rules-v1",
        document=_rules(),
        attachments=[_attachment("contract"), _attachment("business-license")],
        attachment_manifest_hash="manifest-1",
    )
    assert not first.passed
    assert [(item.rule_key, item.code) for item in first.findings] == [
        ("authorization", "DOCUMENT_MISSING")
    ]

    second = evaluate_integrity(
        rule_set_version_id="rules-v1",
        document=_rules(),
        attachments=[
            _attachment("contract"),
            _attachment("business-license"),
            _attachment("authorization"),
        ],
        attachment_manifest_hash="manifest-2",
    )
    assert second.passed
    assert second.findings == ()


def test_integrity_checks_format_duplicate_version_and_expiry() -> None:
    document = IntegrityRuleDocument.model_validate(
        {
            "schemaVersion": "schema://contract/checklist-rule@1",
            "match": {"contractType": "purchase"},
            "requirements": [
                {
                    "key": "license",
                    "documentType": "license",
                    "maxCount": 1,
                    "mediaTypes": ["application/pdf"],
                    "minimumVersion": 2,
                    "requireUnexpired": True,
                }
            ],
        }
    )
    expired = datetime.now(UTC) - timedelta(days=1)
    attachments = [
        AttachmentInput(
            attachmentId=f"a-{index}",
            blobId=f"b-{index}",
            documentType="license",
            filename="license.txt",
            mediaType="text/plain",
            sha256="a" * 64,
            version=1,
            readable=index == 0,
            expiresAt=expired,
        )
        for index in range(2)
    ]
    result = evaluate_integrity(
        rule_set_version_id="rules-v1",
        document=document,
        attachments=attachments,
        attachment_manifest_hash="manifest",
    )
    assert {finding.category for finding in result.findings} == {
        "count",
        "duplicate",
        "expiry",
        "format",
        "version",
    }


def test_rule_selection_returns_stable_diagnostics() -> None:
    with pytest.raises(ValueError, match="RULE_SET_NO_MATCH"):
        select_unique_rule({"contractType": "sale"}, [("v1", {"contractType": "purchase"})])
    with pytest.raises(ValueError, match="RULE_SET_AMBIGUOUS_MATCH: a,b"):
        select_unique_rule(
            {"contractType": "purchase"},
            [("b", {"contractType": "purchase"}), ("a", {"contractType": "purchase"})],
        )
