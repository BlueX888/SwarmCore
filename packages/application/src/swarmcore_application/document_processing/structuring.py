"""Deterministic layout normalization, chunking, and quality gates."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from .contracts import ClassificationResult, ExtractionField, ParsedContent


def estimate_tokens(value: str) -> int:
    """Stable tokenizer-independent estimate used for bounded chunk planning."""

    if not value:
        return 0
    cjk = sum(1 for char in value if "\u3400" <= char <= "\u9fff")
    latin = len(re.findall(r"[A-Za-z0-9]+|[^\w\s]", value))
    return cjk + latin


def _evidence_for_paragraph(item: dict[str, Any]) -> list[dict[str, Any]]:
    evidence: dict[str, Any] = {
        "sourceKind": str(item.get("sourceKind") or "NATIVE"),
        "text": str(item.get("text") or "")[:500],
    }
    if item.get("page") is not None:
        evidence["page"] = item["page"]
    if item.get("bbox") is not None:
        evidence["bbox"] = item["bbox"]
    if item.get("sourcePath") is not None:
        evidence["sourcePath"] = item["sourcePath"]
    return [evidence]


@dataclass(frozen=True)
class ChunkingPolicy:
    target_tokens: int = 1_000
    maximum_tokens: int = 1_600
    overlap_tokens: int = 100


class DocumentChunker:
    name = "structure-aware"
    version = "1"

    def __init__(self, policy: ChunkingPolicy | None = None) -> None:
        self._policy = policy or ChunkingPolicy()

    @property
    def ref(self) -> str:
        return f"chunker://{self.name}@{self.version}"

    def chunk(self, content: ParsedContent) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        buffer: list[dict[str, Any]] = []
        buffer_tokens = 0
        current_path: list[str] = []

        def flush() -> None:
            nonlocal buffer, buffer_tokens
            if not buffer:
                return
            text = "\n\n".join(str(item.get("text") or "") for item in buffer).strip()
            if text:
                chunks.append(
                    self._chunk_record(
                        kind="TEXT",
                        text=text,
                        section_path=current_path,
                        evidence=[
                            evidence
                            for item in buffer
                            for evidence in _evidence_for_paragraph(item)
                        ],
                        pages=[
                            int(item["page"])
                            for item in buffer
                            if isinstance(item.get("page"), int)
                        ],
                    )
                )
            buffer = []
            buffer_tokens = 0

        for paragraph in content.paragraphs:
            text = str(paragraph.get("text") or "").strip()
            if not text:
                continue
            next_path = [
                str(part)
                for part in paragraph.get("sectionPath") or current_path
                if str(part).strip()
            ]
            if next_path != current_path and buffer:
                flush()
            current_path = next_path
            if buffer and buffer_tokens >= self._policy.target_tokens:
                overlap = self._overlap(buffer)
                flush()
                buffer = overlap
                buffer_tokens = sum(
                    estimate_tokens(str(item.get("text") or "")) for item in buffer
                )
            tokens = estimate_tokens(text)
            if tokens > self._policy.maximum_tokens:
                flush()
                for part in self._split_long_text(text):
                    chunks.append(
                        self._chunk_record(
                            kind="TEXT",
                            text=part,
                            section_path=current_path,
                            evidence=_evidence_for_paragraph(paragraph),
                            pages=(
                                [int(paragraph["page"])]
                                if isinstance(paragraph.get("page"), int)
                                else []
                            ),
                        )
                    )
                continue
            if buffer and buffer_tokens + tokens > self._policy.maximum_tokens:
                overlap = self._overlap(buffer)
                flush()
                buffer = overlap
                buffer_tokens = sum(
                    estimate_tokens(str(item.get("text") or "")) for item in buffer
                )
            buffer.append(paragraph)
            buffer_tokens += tokens
        flush()

        for table in content.tables:
            chunks.extend(self._table_chunks(table))

        for index, chunk in enumerate(chunks, start=1):
            chunk["ordinal"] = index
        return chunks

    def _split_long_text(self, text: str) -> list[str]:
        sentences = [
            part.strip()
            for part in re.split(r"(?<=[。\uFF01\uFF1F.!?;\uFF1B])\s*", text)
            if part.strip()
        ]
        if len(sentences) <= 1:
            characters = max(200, self._policy.maximum_tokens * 2)
            return [
                text[index : index + characters]
                for index in range(0, len(text), characters)
            ]
        parts: list[str] = []
        current: list[str] = []
        tokens = 0
        for sentence in sentences:
            next_tokens = estimate_tokens(sentence)
            if current and tokens + next_tokens > self._policy.maximum_tokens:
                parts.append(" ".join(current))
                current = []
                tokens = 0
            current.append(sentence)
            tokens += next_tokens
        if current:
            parts.append(" ".join(current))
        return parts

    def _overlap(self, paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        tokens = 0
        for item in reversed(paragraphs):
            item_tokens = estimate_tokens(str(item.get("text") or ""))
            if selected and tokens + item_tokens > self._policy.overlap_tokens:
                break
            selected.append(item)
            tokens += item_tokens
        selected.reverse()
        return selected

    def _table_chunks(self, table: dict[str, Any]) -> list[dict[str, Any]]:
        rows = [
            [str(value) for value in row]
            for row in table.get("rows") or []
            if isinstance(row, list)
        ]
        if not rows:
            return []
        header = rows[0]
        result: list[dict[str, Any]] = []
        current = [header]
        for row in rows[1:]:
            candidate = self._table_markdown([*current, row])
            if len(current) > 1 and estimate_tokens(candidate) > self._policy.maximum_tokens:
                result.append(self._table_chunk_record(table, current))
                current = [header, row]
            else:
                current.append(row)
        if current:
            result.append(self._table_chunk_record(table, current))
        return result

    def _table_chunk_record(
        self, table: dict[str, Any], rows: list[list[str]]
    ) -> dict[str, Any]:
        pages = [
            int(value)
            for value in (table.get("pageStart"), table.get("pageEnd"))
            if isinstance(value, int)
        ]
        evidence = [
            dict(value)
            for value in table.get("evidenceRefs") or []
            if isinstance(value, dict)
        ]
        return self._chunk_record(
            kind="TABLE",
            text=self._table_markdown(rows),
            section_path=[str(table.get("name") or table.get("tableId") or "Table")],
            evidence=evidence,
            pages=pages,
            table_id=str(table.get("tableId") or ""),
        )

    def _table_markdown(self, rows: list[list[str]]) -> str:
        width = max((len(row) for row in rows), default=0)
        normalized = [row + [""] * (width - len(row)) for row in rows]
        if not normalized:
            return ""
        header = normalized[0]
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join("---" for _ in header) + " |",
        ]
        lines.extend("| " + " | ".join(row) + " |" for row in normalized[1:])
        return "\n".join(lines)

    def _chunk_record(
        self,
        *,
        kind: str,
        text: str,
        section_path: list[str],
        evidence: list[dict[str, Any]],
        pages: list[int],
        table_id: str | None = None,
    ) -> dict[str, Any]:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        stable = json.dumps(
            {
                "kind": kind,
                "sectionPath": section_path,
                "contentHash": content_hash,
                "tableId": table_id,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        value: dict[str, Any] = {
            "chunkId": hashlib.sha256(stable.encode("utf-8")).hexdigest()[:32],
            "kind": kind,
            "sectionPath": list(section_path),
            "text": text,
            "tokenCount": estimate_tokens(text),
            "pageStart": min(pages) if pages else None,
            "pageEnd": max(pages) if pages else None,
            "evidenceRefs": evidence,
            "contentHash": content_hash,
            "chunkerRef": self.ref,
        }
        if table_id:
            value["tableId"] = table_id
        return value


class DocumentQualityChecker:
    name = "document-structure-gates"
    version = "1"

    @property
    def ref(self) -> str:
        return f"quality://{self.name}@{self.version}"

    def check(
        self,
        *,
        content: ParsedContent,
        classification: ClassificationResult | None,
        extractions: list[ExtractionField],
        classification_threshold: float,
        extraction_threshold: float,
        critical_extraction_threshold: float,
        ocr_threshold: float,
    ) -> dict[str, Any]:
        flags: list[str] = []
        checks: dict[str, bool] = {}

        checks["hasContent"] = bool(
            content.paragraphs or content.tables or content.sheets
        )
        if not checks["hasContent"]:
            flags.append("NO_STRUCTURED_CONTENT")

        checks["classificationAccepted"] = bool(
            classification is not None
            and classification.confidence >= classification_threshold
            and classification.evidence
        )
        if classification is not None and not checks["classificationAccepted"]:
            flags.append("CLASSIFICATION_REVIEW_REQUIRED")

        checks["fieldsHaveEvidence"] = all(
            field.machine_value is None or bool(field.evidence_refs)
            for field in extractions
        )
        if not checks["fieldsHaveEvidence"]:
            flags.append("EXTRACTION_EVIDENCE_MISSING")

        checks["fieldConfidenceAccepted"] = all(
            field.machine_value is None
            or field.confidence
            >= (
                critical_extraction_threshold
                if field.critical
                else extraction_threshold
            )
            for field in extractions
        )
        if not checks["fieldConfidenceAccepted"]:
            flags.append("EXTRACTION_REVIEW_REQUIRED")

        placeholder_fields = [
            field.field_path
            for field in extractions
            if "PLACEHOLDER_NOT_FILLED" in field.quality_flags
        ]
        checks["placeholdersResolved"] = not placeholder_fields
        if placeholder_fields:
            flags.append("PLACEHOLDER_NOT_FILLED")

        malformed_tables = [
            str(table.get("tableId") or table.get("name") or "table")
            for table in content.tables
            if not self._table_is_rectangular(table)
        ]
        checks["tablesRectangular"] = not malformed_tables
        if malformed_tables:
            flags.append("TABLE_SHAPE_REVIEW_REQUIRED")

        ocr_confidences = [
            float(block["confidence"])
            for block in content.layout.get("blocks", [])
            if isinstance(block, dict)
            and block.get("sourceKind") == "OCR"
            and isinstance(block.get("confidence"), int | float)
        ]
        average_ocr = (
            sum(ocr_confidences) / len(ocr_confidences)
            if ocr_confidences
            else None
        )
        has_ocr = any(
            page.get("sourceKind") == "OCR" for page in content.pages
        ) or any(
            isinstance(block, dict) and block.get("sourceKind") == "OCR"
            for block in content.layout.get("blocks", [])
        )
        checks["ocrConfidencePresent"] = not has_ocr or bool(ocr_confidences)
        if not checks["ocrConfidencePresent"]:
            flags.append("OCR_CONFIDENCE_MISSING")
        checks["ocrAccepted"] = (
            not has_ocr
            or (
                average_ocr is not None
                and average_ocr >= ocr_threshold
            )
        )
        if not checks["ocrAccepted"]:
            flags.append("OCR_REVIEW_REQUIRED")

        checks["chunkBounds"] = all(
            int(chunk.get("tokenCount") or 0) <= 1_600 for chunk in content.chunks
        )
        if not checks["chunkBounds"]:
            flags.append("CHUNK_LIMIT_EXCEEDED")

        return {
            "qualityRef": self.ref,
            "passed": not flags,
            "checks": checks,
            "flags": flags,
            "metrics": {
                "pageCount": len(content.pages),
                "paragraphCount": len(content.paragraphs),
                "sectionCount": len(content.sections),
                "tableCount": len(content.tables),
                "sheetCount": len(content.sheets),
                "chunkCount": len(content.chunks),
                "averageOcrConfidence": average_ocr,
                "malformedTables": malformed_tables,
                "placeholderFields": placeholder_fields,
            },
        }

    def _table_is_rectangular(self, table: dict[str, Any]) -> bool:
        rows = [row for row in table.get("rows") or [] if isinstance(row, list)]
        if not rows:
            return True
        width = max(len(row) for row in rows)
        return all(len(row) == width for row in rows)
