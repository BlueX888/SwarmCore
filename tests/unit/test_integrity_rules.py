from datetime import UTC, datetime, timedelta

import pytest
from swarmcore_application import (
    AttachmentInput,
    IntegrityRuleDocument,
    evaluate_integrity,
    select_unique_rule,
)


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
