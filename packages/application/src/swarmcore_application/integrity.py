from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IntegrityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class DocumentRequirement(IntegrityModel):
    key: str = Field(min_length=1, max_length=128)
    document_type: str = Field(alias="documentType", min_length=1, max_length=128)
    required: bool = True
    min_count: int = Field(default=1, alias="minCount", ge=0)
    max_count: int | None = Field(default=None, alias="maxCount", ge=1)
    media_types: tuple[str, ...] = Field(default_factory=tuple, alias="mediaTypes")
    allow_duplicates: bool = Field(default=False, alias="allowDuplicates")
    minimum_version: int | None = Field(default=None, alias="minimumVersion", ge=1)
    require_unexpired: bool = Field(default=False, alias="requireUnexpired")
    severity: Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"

    @field_validator("max_count")
    @classmethod
    def valid_max_count(cls, value: int | None) -> int | None:
        return value


class IntegrityRuleDocument(IntegrityModel):
    schema_version: Literal["schema://contract/checklist-rule@1"] = Field(alias="schemaVersion")
    match: dict[str, str]
    requirements: tuple[DocumentRequirement, ...]

    @field_validator("requirements")
    @classmethod
    def unique_requirement_keys(
        cls, value: tuple[DocumentRequirement, ...]
    ) -> tuple[DocumentRequirement, ...]:
        keys = [item.key for item in value]
        if len(keys) != len(set(keys)):
            raise ValueError("requirement keys must be unique")
        for item in value:
            if item.max_count is not None and item.max_count < item.min_count:
                raise ValueError(f"maxCount is smaller than minCount for {item.key}")
        return value


class AttachmentInput(IntegrityModel):
    attachment_id: str = Field(alias="attachmentId")
    blob_id: str = Field(alias="blobId")
    document_type: str = Field(alias="documentType")
    filename: str
    media_type: str = Field(alias="mediaType")
    sha256: str
    version: int = 1
    readable: bool = True
    expires_at: datetime | None = Field(default=None, alias="expiresAt")


class IntegrityFinding(IntegrityModel):
    rule_key: str = Field(alias="ruleKey")
    code: str
    category: str
    severity: str
    title: str
    detail: str
    evidence: dict[str, Any]


class IntegrityResult(IntegrityModel):
    passed: bool
    rule_set_version_id: str = Field(alias="ruleSetVersionId")
    attachment_manifest_hash: str = Field(alias="attachmentManifestHash")
    checks: dict[str, int]
    findings: tuple[IntegrityFinding, ...]


def rule_matches(payload: dict[str, Any], expression: dict[str, Any]) -> bool:
    """Match equality-only paths without evaluating code."""
    return all(_resolve(payload, path) == expected for path, expected in expression.items())


def select_unique_rule(
    payload: dict[str, Any], candidates: list[tuple[str, dict[str, Any]]]
) -> tuple[str, dict[str, Any]]:
    matches = [
        (identifier, rules) for identifier, rules in candidates if rule_matches(payload, rules)
    ]
    if not matches:
        raise ValueError("RULE_SET_NO_MATCH")
    if len(matches) > 1:
        ids = ",".join(sorted(identifier for identifier, _ in matches))
        raise ValueError(f"RULE_SET_AMBIGUOUS_MATCH: {ids}")
    return matches[0]


def evaluate_integrity(
    *,
    rule_set_version_id: str,
    document: IntegrityRuleDocument,
    attachments: list[AttachmentInput],
    attachment_manifest_hash: str,
    now: datetime | None = None,
) -> IntegrityResult:
    checked_at = now or datetime.now(UTC)
    findings: list[IntegrityFinding] = []
    by_type: dict[str, list[AttachmentInput]] = {}
    for attachment in attachments:
        by_type.setdefault(attachment.document_type, []).append(attachment)

    for requirement in document.requirements:
        values = by_type.get(requirement.document_type, [])
        required_count = requirement.min_count if requirement.required else 0
        if len(values) < required_count:
            findings.append(
                _finding(
                    requirement,
                    "DOCUMENT_MISSING",
                    "presence",
                    f"缺少{requirement.document_type}",
                    f"至少需要 {required_count} 份, 当前为 {len(values)} 份。",
                    {"expected": required_count, "actual": len(values)},
                )
            )
        if requirement.max_count is not None and len(values) > requirement.max_count:
            findings.append(
                _finding(
                    requirement,
                    "DOCUMENT_COUNT_EXCEEDED",
                    "count",
                    f"{requirement.document_type}数量超限",
                    f"最多允许 {requirement.max_count} 份, 当前为 {len(values)} 份。",
                    {"expectedMaximum": requirement.max_count, "actual": len(values)},
                )
            )
        invalid_formats = [
            item
            for item in values
            if requirement.media_types and item.media_type not in requirement.media_types
        ]
        if invalid_formats:
            findings.append(
                _finding(
                    requirement,
                    "DOCUMENT_FORMAT_INVALID",
                    "format",
                    f"{requirement.document_type}格式不符合要求",
                    "附件 MIME 类型不在允许清单中。",
                    {"attachmentIds": [item.attachment_id for item in invalid_formats]},
                )
            )
        unreadable = [item for item in values if not item.readable]
        if unreadable:
            findings.append(
                _finding(
                    requirement,
                    "DOCUMENT_UNREADABLE",
                    "format",
                    f"{requirement.document_type}不可读",
                    "附件未通过可读性检查。",
                    {"attachmentIds": [item.attachment_id for item in unreadable]},
                )
            )
        duplicate_hashes = sorted(
            digest for digest, count in Counter(item.sha256 for item in values).items() if count > 1
        )
        if duplicate_hashes and not requirement.allow_duplicates:
            findings.append(
                _finding(
                    requirement,
                    "DOCUMENT_DUPLICATE",
                    "duplicate",
                    f"{requirement.document_type}存在重复文件",
                    "多个附件具有相同 SHA-256。",
                    {"sha256": duplicate_hashes},
                )
            )
        old_versions = [
            item
            for item in values
            if requirement.minimum_version is not None
            and item.version < requirement.minimum_version
        ]
        if old_versions:
            findings.append(
                _finding(
                    requirement,
                    "DOCUMENT_VERSION_OLD",
                    "version",
                    f"{requirement.document_type}版本过旧",
                    "附件版本低于规则要求。",
                    {"attachmentIds": [item.attachment_id for item in old_versions]},
                )
            )
        expired = [
            item
            for item in values
            if requirement.require_unexpired
            and (item.expires_at is None or item.expires_at <= checked_at)
        ]
        if expired:
            findings.append(
                _finding(
                    requirement,
                    "DOCUMENT_EXPIRED",
                    "expiry",
                    f"{requirement.document_type}已过期或缺少有效期",
                    "附件未提供有效的未来失效时间。",
                    {"attachmentIds": [item.attachment_id for item in expired]},
                )
            )

    ordered = tuple(sorted(findings, key=lambda item: (item.rule_key, item.code)))
    return IntegrityResult(
        passed=not ordered,
        ruleSetVersionId=rule_set_version_id,
        attachmentManifestHash=attachment_manifest_hash,
        checks={"requirements": len(document.requirements), "attachments": len(attachments)},
        findings=ordered,
    )


def _resolve(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def _finding(
    requirement: DocumentRequirement,
    code: str,
    category: str,
    title: str,
    detail: str,
    evidence: dict[str, Any],
) -> IntegrityFinding:
    return IntegrityFinding(
        ruleKey=requirement.key,
        code=code,
        category=category,
        severity=requirement.severity,
        title=title,
        detail=detail,
        evidence=evidence,
    )
