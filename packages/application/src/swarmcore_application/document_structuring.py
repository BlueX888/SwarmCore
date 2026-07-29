"""Deterministic functions around the document-structuring Agent."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from typing import Any, cast

from .document_processing.structuring import estimate_tokens

PACKAGE_SCHEMA = "schema://document-structuring/package@1"
AGENT_SCHEMA = "schema://document-structuring/agent-result@1"


def prepare_document_structuring(
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    prepared: list[dict[str, Any]] = []
    for source in documents:
        data = dict(source.get("data") or {})
        content = dict(data.get("content") or {})
        chunks = [
            _compact_chunk(value)
            for value in content.get("chunks") or []
            if isinstance(value, dict)
        ]
        extractions = [
            _compact_field(value)
            for value in data.get("extractions") or []
            if isinstance(value, dict)
        ]
        prepared.append(
            {
                "documentId": str(source.get("documentId") or ""),
                "documentVersionId": str(source.get("documentVersionId") or ""),
                "filename": str(source.get("filename") or source.get("name") or ""),
                "mediaType": str(source.get("mediaType") or ""),
                "sha256": str(source.get("sha256") or ""),
                "category": str(source.get("category") or ""),
                "processingStatus": str(data.get("status") or "UNKNOWN"),
                "documentType": dict(data.get("documentType") or {}),
                "textExcerpt": str(content.get("textExcerpt") or "")[:8_000],
                "sections": [
                    dict(value)
                    for value in content.get("sections") or []
                    if isinstance(value, dict)
                ][:200],
                "chunks": chunks[:40],
                "tables": [
                    _compact_table(value)
                    for value in content.get("tables") or []
                    if isinstance(value, dict)
                ][:100],
                "extractions": extractions,
                "qualityFlags": [
                    str(value) for value in data.get("qualityFlags") or []
                ],
                "evidence": [
                    dict(value)
                    for value in source.get("evidence") or data.get("evidence") or []
                    if isinstance(value, dict)
                ][:200],
                "contentArtifactRef": data.get("contentArtifactRef"),
                "provenance": dict(data.get("provenance") or {}),
            }
        )
    return {
        "schemaVersion": "schema://document-structuring/prepared@1",
        "documents": prepared,
        "documentCount": len(prepared),
        "contentHash": _hash(prepared),
        "instructions": {
            "evidenceRequired": True,
            "placeholderValuesMustBeNull": True,
            "allowedDocumentVersionIds": [
                item["documentVersionId"] for item in prepared
            ],
        },
    }


def finalize_document_structuring(
    prepared: dict[str, Any],
    analysis: dict[str, Any],
) -> dict[str, Any]:
    sources = [
        dict(value)
        for value in prepared.get("documents") or []
        if isinstance(value, dict)
    ]
    agent_documents = {
        str(value.get("documentVersionId") or ""): dict(value)
        for value in analysis.get("documents") or []
        if isinstance(value, dict)
    }
    documents: list[dict[str, Any]] = []
    global_flags: list[str] = []
    for source in sources:
        version_id = str(source["documentVersionId"])
        candidate = agent_documents.get(version_id, {})
        if not candidate:
            global_flags.append("AGENT_DOCUMENT_RESULT_MISSING")
        fields = _validated_fields(
            [
                dict(value)
                for value in candidate.get("fields") or source.get("extractions") or []
                if isinstance(value, dict)
            ]
        )
        flags = list(
            dict.fromkeys(
                [
                    *[str(value) for value in source.get("qualityFlags") or []],
                    *[str(value) for value in candidate.get("qualityFlags") or []],
                    *[
                        flag
                        for field in fields
                        for flag in field.get("qualityFlags") or []
                    ],
                ]
            )
        )
        classification = dict(
            candidate.get("classification")
            or source.get("documentType")
            or {
                "label": source.get("category") or "UNCLASSIFIED",
                "displayName": source.get("category") or "未分类",
                "confidence": 0,
                "evidence": [],
            }
        )
        if not classification.get("evidence"):
            flags.append("CLASSIFICATION_EVIDENCE_MISSING")
        documents.append(
            {
                "documentId": source["documentId"],
                "documentVersionId": version_id,
                "filename": source["filename"],
                "mediaType": source["mediaType"],
                "sha256": source["sha256"],
                "classification": classification,
                "sections": source.get("sections") or [],
                "chunks": source.get("chunks") or [],
                "tables": source.get("tables") or [],
                "fields": fields,
                "organization": dict(candidate.get("organization") or {}),
                "qualityFlags": list(dict.fromkeys(flags)),
                "contentArtifactRef": source.get("contentArtifactRef"),
                "provenance": {
                    **dict(source.get("provenance") or {}),
                    "agentRef": "agent://document/structurer@1",
                },
            }
        )

    consistency = _cross_format_consistency(documents)
    if consistency["status"] != "CONSISTENT":
        global_flags.append("CROSS_FORMAT_CONFLICT")
    global_flags.extend(
        str(value) for value in analysis.get("qualityFlags") or []
    )
    global_flags = list(dict.fromkeys(global_flags))
    review_required = bool(
        analysis.get("reviewRequired")
        or global_flags
        or any(document["qualityFlags"] for document in documents)
        or any(
            field.get("reviewStatus") in {"PENDING", "UNCONFIRMED"}
            for document in documents
            for field in document["fields"]
        )
    )
    package = {
        "schemaVersion": PACKAGE_SCHEMA,
        "status": "REVIEW_REQUIRED" if review_required else "READY",
        "reviewRequired": review_required,
        "documents": documents,
        "crossFormatConsistency": consistency,
        "summary": str(analysis.get("summary") or "")[:4_000],
        "qualityFlags": global_flags,
        "provenance": {
            "preparedContentHash": str(prepared.get("contentHash") or ""),
            "agentSchemaVersion": str(
                analysis.get("schemaVersion") or AGENT_SCHEMA
            ),
            "agentRef": "agent://document/structurer@1",
            "toolRefs": [
                "tool://document/read-versions@1",
                "tool://document/structure-prepare@1",
                "tool://document/quality-check@1",
                "tool://document/publish@1",
            ],
        },
    }
    package["contentHash"] = _hash(package)
    return package


def document_package_artifacts(package: dict[str, Any]) -> dict[str, bytes]:
    files: dict[str, bytes] = {
        "structured-document.json": json.dumps(
            package, ensure_ascii=False, indent=2, sort_keys=True
        ).encode(),
        "content.md": _content_markdown(package).encode(),
        "evidence-manifest.json": json.dumps(
            _evidence_manifest(package),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode(),
        "review-log.json": json.dumps(
            {
                "status": package.get("status"),
                "reviewRequired": package.get("reviewRequired"),
                "qualityFlags": package.get("qualityFlags") or [],
                "fields": [
                    {
                        "documentVersionId": document.get("documentVersionId"),
                        "fieldPath": field.get("fieldPath"),
                        "machineValue": field.get("machineValue"),
                        "confirmedValue": field.get("confirmedValue"),
                        "reviewStatus": field.get("reviewStatus"),
                        "qualityFlags": field.get("qualityFlags") or [],
                    }
                    for document in package.get("documents") or []
                    for field in document.get("fields") or []
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode(),
    }
    for document in package.get("documents") or []:
        for table in document.get("tables") or []:
            table_id = str(table.get("tableId") or "table")
            filename = (
                f"tables/{document.get('documentVersionId')}-{table_id}.csv"
            )
            stream = io.StringIO(newline="")
            writer = csv.writer(stream)
            writer.writerows(table.get("rows") or [])
            files[filename] = stream.getvalue().encode("utf-8-sig")
    return files


def apply_human_review(
    package: dict[str, Any],
    approval: dict[str, Any] | None,
) -> dict[str, Any]:
    if not approval:
        if package.get("reviewRequired"):
            raise ValueError("review-required package cannot be published without approval")
        return package
    decision = str(approval.get("decision") or "")
    if decision not in {"CONFIRM", "CORRECT"}:
        raise ValueError(f"document package cannot be published after {decision or 'empty'}")
    reviewed = cast(dict[str, Any], json.loads(json.dumps(package)))
    corrections = [
        dict(value)
        for value in approval.get("fieldCorrections") or []
        if isinstance(value, dict)
    ]
    field_index = {
        (
            str(document.get("documentVersionId") or ""),
            str(field.get("fieldPath") or ""),
        ): field
        for document in reviewed.get("documents") or []
        for field in document.get("fields") or []
    }
    for correction in corrections:
        key = (
            str(correction.get("documentVersionId") or ""),
            str(correction.get("fieldPath") or ""),
        )
        field = field_index.get(key)
        if field is None:
            raise ValueError("field correction does not target a published field")
        field["confirmedValue"] = correction.get("value")
        field["effectiveValue"] = correction.get("value")
        field["reviewStatus"] = "CONFIRMED"
        field["qualityFlags"] = [
            flag
            for flag in field.get("qualityFlags") or []
            if flag
            not in {
                "EXTRACTION_EVIDENCE_MISSING",
                "EXTRACTION_CONFIDENCE_LOW",
                "CRITICAL_FIELD_CONFIDENCE_LOW",
                "PLACEHOLDER_NOT_FILLED",
            }
        ]
    reviewed["status"] = "READY"
    reviewed["reviewRequired"] = False
    reviewed["humanReview"] = {
        "decision": decision,
        "reason": str(approval.get("reason") or ""),
        "correctionCount": len(corrections),
    }
    reviewed["contentHash"] = _hash(
        {key: value for key, value in reviewed.items() if key != "contentHash"}
    )
    return reviewed


def _compact_chunk(value: dict[str, Any]) -> dict[str, Any]:
    text = str(value.get("text") or "")[:6_000]
    return {
        "chunkId": str(value.get("chunkId") or ""),
        "kind": str(value.get("kind") or "TEXT"),
        "sectionPath": [
            str(part) for part in value.get("sectionPath") or []
        ],
        "text": text,
        "tokenCount": int(value.get("tokenCount") or estimate_tokens(text)),
        "pageStart": value.get("pageStart"),
        "pageEnd": value.get("pageEnd"),
        "evidenceRefs": [
            dict(item)
            for item in value.get("evidenceRefs") or []
            if isinstance(item, dict)
        ][:20],
        "contentHash": str(value.get("contentHash") or _hash(text)),
    }


def _compact_table(value: dict[str, Any]) -> dict[str, Any]:
    rows = [
        [str(cell) for cell in row]
        for row in value.get("rows") or []
        if isinstance(row, list)
    ]
    return {
        "tableId": str(value.get("tableId") or ""),
        "name": str(value.get("name") or ""),
        "columns": [str(cell) for cell in value.get("columns") or []],
        "rows": rows[:2_000],
        "rowCount": int(value.get("rowCount") or len(rows)),
        "columnCount": int(
            value.get("columnCount")
            or max((len(row) for row in rows), default=0)
        ),
        "pageStart": value.get("pageStart"),
        "pageEnd": value.get("pageEnd"),
        "sourceKind": str(value.get("sourceKind") or "NATIVE"),
        "evidenceRefs": [
            dict(item)
            for item in value.get("evidenceRefs") or []
            if isinstance(item, dict)
        ],
    }


def _compact_field(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "fieldPath": str(value.get("fieldPath") or ""),
        "displayName": str(value.get("displayName") or ""),
        "valueType": str(value.get("valueType") or "string"),
        "critical": bool(value.get("critical", False)),
        "machineValue": value.get("machineValue", value.get("value")),
        "confirmedValue": value.get("confirmedValue"),
        "effectiveValue": (
            value.get("confirmedValue")
            if value.get("confirmedValue") is not None
            else value.get("machineValue", value.get("value"))
        ),
        "confidence": float(value.get("confidence") or 0),
        "reviewStatus": str(value.get("reviewStatus") or "PENDING"),
        "evidenceRefs": [
            dict(item)
            for item in value.get("evidenceRefs") or []
            if isinstance(item, dict)
        ],
        "qualityFlags": [
            str(item) for item in value.get("qualityFlags") or []
        ],
    }


def _validated_fields(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for value in values:
        field = _compact_field(value)
        flags = list(field["qualityFlags"])
        if field["machineValue"] is not None and not field["evidenceRefs"]:
            flags.append("EXTRACTION_EVIDENCE_MISSING")
            field["reviewStatus"] = "PENDING"
        if _placeholder(field["machineValue"]):
            field["machineValue"] = None
            field["effectiveValue"] = field["confirmedValue"]
            flags.append("PLACEHOLDER_NOT_FILLED")
            field["reviewStatus"] = (
                "CONFIRMED"
                if field["confirmedValue"] is not None
                else "UNCONFIRMED"
            )
        field["qualityFlags"] = list(dict.fromkeys(flags))
        fields.append(field)
    return fields


def _placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower().rstrip(".")
    return (
        "click here to enter" in normalized
        or normalized.startswith("enter information")
        or normalized.startswith("buyer to insert")
        or normalized in {"tbc", "tbd", "n/a", "not applicable"}
        or (normalized.startswith("[") and normalized.endswith("]"))
    )


def _cross_format_consistency(
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    keys = ("document.title", "contract.reference")
    values: dict[str, dict[str, list[str]]] = {}
    conflicts: list[dict[str, Any]] = []
    for key in keys:
        grouped: dict[str, list[str]] = {}
        for document in documents:
            field = next(
                (
                    item
                    for item in document.get("fields") or []
                    if item.get("fieldPath") == key
                ),
                None,
            )
            if not field or field.get("effectiveValue") is None:
                continue
            normalized = " ".join(
                str(field["effectiveValue"]).lower().split()
            )
            grouped.setdefault(normalized, []).append(
                str(document["documentVersionId"])
            )
        values[key] = grouped
        if len(grouped) > 1:
            conflicts.append({"fieldPath": key, "variants": grouped})
    return {
        "status": "CONSISTENT" if not conflicts else "CONFLICTED",
        "checkedFields": list(keys),
        "values": values,
        "conflicts": conflicts,
    }


def _content_markdown(package: dict[str, Any]) -> str:
    lines = ["# Structured document package", ""]
    for document in package.get("documents") or []:
        lines.extend(
            [
                f"## {document.get('filename')}",
                "",
                f"- Document version: `{document.get('documentVersionId')}`",
                f"- SHA-256: `{document.get('sha256')}`",
                f"- Type: `{document.get('mediaType')}`",
                "",
            ]
        )
        for section in document.get("sections") or []:
            title = str(section.get("title") or "").strip()
            if title:
                level = min(6, max(3, int(section.get("level") or 1) + 2))
                lines.extend([f"{'#' * level} {title}", ""])
        for chunk in document.get("chunks") or []:
            text = str(chunk.get("text") or "").strip()
            if text:
                lines.extend([text, ""])
    return "\n".join(lines).strip() + "\n"


def _evidence_manifest(package: dict[str, Any]) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    for document in package.get("documents") or []:
        version_id = document.get("documentVersionId")
        sha256 = document.get("sha256")
        for field in document.get("fields") or []:
            for item in field.get("evidenceRefs") or []:
                evidence.append(
                    {
                        **dict(item),
                        "documentVersionId": version_id,
                        "blobSha256": sha256,
                        "fieldPath": field.get("fieldPath"),
                    }
                )
    return {
        "schemaVersion": "schema://document-structuring/evidence-manifest@1",
        "packageHash": package.get("contentHash"),
        "evidence": evidence,
    }


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
