"""Parser adapter registry and built-in parsers."""

from __future__ import annotations

import csv
import io
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Protocol
from xml.etree import ElementTree

from .contracts import ParsedContent
from .native_parsers import OdfParser, PptxParser


class DocumentParser(Protocol):
    name: str
    version: str

    def supports(self, media_type: str) -> bool: ...

    def parse(self, *, filename: str, media_type: str, content: bytes) -> ParsedContent: ...


@dataclass(frozen=True)
class ParserRef:
    name: str
    version: str

    @property
    def ref(self) -> str:
        return f"parser://{self.name}@{self.version}"


class TextMarkdownParser:
    name = "text-markdown"
    version = "1"

    def supports(self, media_type: str) -> bool:
        return media_type in {"text/plain", "text/markdown", "text/x-markdown"}

    def parse(self, *, filename: str, media_type: str, content: bytes) -> ParsedContent:
        text = content.decode("utf-8", errors="replace")
        paragraphs = [
            {"index": index, "text": line}
            for index, line in enumerate((part for part in text.splitlines() if part.strip()), 1)
        ]
        excerpt = text[:4000]
        return ParsedContent(
            pages=[{"page": 1, "text": text}],
            paragraphs=paragraphs,
            tables=[],
            sheets=[],
            embeddedMetadata={"filename": filename, "mediaType": media_type},
            warnings=[],
            textExcerpt=excerpt,
            needsOcr=False,
        )


class StructuredTextParser:
    name = "structured-text"
    version = "1"

    def supports(self, media_type: str) -> bool:
        return media_type in {
            "application/csv",
            "application/json",
            "text/csv",
            "text/json",
        }

    def parse(self, *, filename: str, media_type: str, content: bytes) -> ParsedContent:
        text = content.decode("utf-8-sig", errors="replace")
        tables: list[dict[str, Any]] = []
        if "json" in media_type:
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError("DOCUMENT_PARSE_FAILED") from exc
            normalized = json.dumps(value, ensure_ascii=False, indent=2)
            rows = value if isinstance(value, list) else [value]
            if rows and all(isinstance(row, dict) for row in rows):
                columns = sorted(
                    {str(key) for row in rows for key in row}
                )
                tables.append(
                    {
                        "name": filename,
                        "columns": columns,
                        "rows": [
                            [str(row.get(column, "")) for column in columns]
                            for row in rows[:500]
                        ],
                    }
                )
        else:
            csv_rows = list(csv.reader(io.StringIO(text)))
            normalized = "\n".join(" | ".join(row) for row in csv_rows)
            if csv_rows:
                tables.append(
                    {
                        "name": filename,
                        "columns": csv_rows[0],
                        "rows": csv_rows[1:501],
                    }
                )
        return ParsedContent(
            pages=[{"page": 1, "text": normalized}],
            paragraphs=[
                {"index": index, "text": line}
                for index, line in enumerate(normalized.splitlines(), start=1)
                if line.strip()
            ][:500],
            tables=tables,
            sheets=[],
            embeddedMetadata={"filename": filename, "mediaType": media_type},
            warnings=[],
            textExcerpt=normalized[:4000],
            needsOcr=False,
        )


class DocxParser:
    name = "docx"
    version = "2"
    _NS: ClassVar[dict[str, str]] = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    }

    def supports(self, media_type: str) -> bool:
        return media_type in {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        }

    def parse(self, *, filename: str, media_type: str, content: bytes) -> ParsedContent:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                xml = archive.read("word/document.xml")
        except (KeyError, zipfile.BadZipFile) as exc:
            raise ValueError("DOCUMENT_PARSE_FAILED") from exc
        root = ElementTree.fromstring(xml)
        document_body = root.find("w:body", self._NS)
        if document_body is None:
            raise ValueError("DOCUMENT_PARSE_FAILED")
        paragraphs: list[dict[str, Any]] = []
        sections: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        section_path: list[str] = []
        paragraph_tag = f"{{{self._NS['w']}}}p"
        table_tag = f"{{{self._NS['w']}}}tbl"
        for node in list(document_body):
            if node.tag == paragraph_tag:
                value = self._node_text(node)
                if not value:
                    continue
                level = self._heading_level(node)
                if level is not None:
                    section_path = section_path[: level - 1]
                    section_path.append(value)
                    sections.append(
                        {
                            "sectionId": f"section-{len(sections) + 1}",
                            "title": value,
                            "level": level,
                            "path": list(section_path),
                            "paragraphStart": len(paragraphs) + 1,
                        }
                    )
                paragraphs.append(
                    {
                        "index": len(paragraphs) + 1,
                        "text": value,
                        "kind": "heading" if level is not None else "paragraph",
                        "level": level,
                        "sectionPath": list(section_path),
                    }
                )
            elif node.tag == table_tag:
                rows = [
                    [self._node_text(cell) for cell in row.findall("w:tc", self._NS)]
                    for row in node.findall("w:tr", self._NS)
                ]
                width = max((len(row) for row in rows), default=0)
                normalized = [row + [""] * (width - len(row)) for row in rows]
                tables.append(
                    {
                        "tableId": f"table-{len(tables) + 1}",
                        "name": f"Table {len(tables) + 1}",
                        "columns": normalized[0] if normalized else [],
                        "rows": normalized,
                        "rowCount": len(normalized),
                        "columnCount": width,
                        "sourceKind": "NATIVE",
                        "evidenceRefs": [{"sourcePath": "word/document.xml"}],
                    }
                )
        for index, section in enumerate(sections):
            next_start = (
                int(sections[index + 1]["paragraphStart"])
                if index + 1 < len(sections)
                else len(paragraphs) + 1
            )
            section["paragraphEnd"] = max(
                int(section["paragraphStart"]), next_start - 1
            )
        source_tables = document_body.findall(".//w:tbl", self._NS)
        if len(source_tables) != len(tables):
            tables = [
                self._table(node, index)
                for index, node in enumerate(source_tables, start=1)
            ]
        body = "\n".join(str(item["text"]) for item in paragraphs)
        return ParsedContent(
            pages=[{"page": 1, "text": body}],
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            sheets=[],
            embeddedMetadata={
                "filename": filename,
                "mediaType": media_type,
                "headingCount": len(sections),
                "paragraphCount": len(
                    document_body.findall(".//w:p", self._NS)
                ),
                "semanticParagraphCount": len(paragraphs),
                "tableCount": len(tables),
            },
            warnings=[] if body else ["DOCX_EMPTY_TEXT"],
            textExcerpt=body[:8000],
            needsOcr=not bool(body.strip()),
        )

    def _table(
        self, node: ElementTree.Element, ordinal: int
    ) -> dict[str, Any]:
        rows = [
            [self._node_text(cell) for cell in row.findall("w:tc", self._NS)]
            for row in node.findall("w:tr", self._NS)
        ]
        width = max((len(row) for row in rows), default=0)
        normalized = [row + [""] * (width - len(row)) for row in rows]
        return {
            "tableId": f"table-{ordinal}",
            "name": f"Table {ordinal}",
            "columns": normalized[0] if normalized else [],
            "rows": normalized,
            "rowCount": len(normalized),
            "columnCount": width,
            "sourceKind": "NATIVE",
            "evidenceRefs": [{"sourcePath": "word/document.xml"}],
        }

    def _node_text(self, node: ElementTree.Element) -> str:
        return " ".join(
            value.strip()
            for text in node.findall(".//w:t", self._NS)
            if (value := str(text.text or "")).strip()
        )

    def _heading_level(self, node: ElementTree.Element) -> int | None:
        style = node.find("w:pPr/w:pStyle", self._NS)
        if style is None:
            return None
        raw = style.attrib.get(f"{{{self._NS['w']}}}val", "")
        match = __import__("re").search(r"(?:Heading|标题)\s*(\d+)", raw, flags=__import__("re").I)
        return min(10, max(1, int(match.group(1)))) if match else None


class XlsxParser:
    name = "xlsx"
    version = "2"
    _NS: ClassVar[dict[str, str]] = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    }

    def supports(self, media_type: str) -> bool:
        return media_type in {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        }

    def parse(self, *, filename: str, media_type: str, content: bytes) -> ParsedContent:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                shared = self._shared_strings(archive)
                sheets: list[dict[str, Any]] = []
                tables: list[dict[str, Any]] = []
                paragraphs: list[dict[str, Any]] = []
                for name in archive.namelist():
                    if not name.startswith("xl/worksheets/sheet") or not name.endswith(".xml"):
                        continue
                    root = ElementTree.fromstring(archive.read(name))
                    rows: list[list[str]] = []
                    for row in root.findall(".//m:sheetData/m:row", self._NS):
                        values: list[str] = []
                        for cell in row.findall("m:c", self._NS):
                            values.append(self._cell_value(cell, shared))
                        if any(values):
                            rows.append(values)
                            paragraphs.append(
                                {
                                    "index": len(paragraphs) + 1,
                                    "text": " | ".join(values),
                                    "sheet": name,
                                }
                            )
                    normalized_name = name.split("/")[-1]
                    capped_rows = rows[:500_000]
                    sheets.append(
                        {
                            "name": normalized_name,
                            "rows": capped_rows,
                            "rowCount": len(rows),
                            "columnCount": max(
                                (len(row) for row in capped_rows), default=0
                            ),
                        }
                    )
                    tables.append(
                        {
                            "tableId": f"table-{len(tables) + 1}",
                            "name": normalized_name,
                            "columns": capped_rows[0] if capped_rows else [],
                            "rows": capped_rows,
                            "rowCount": len(rows),
                            "columnCount": max(
                                (len(row) for row in capped_rows), default=0
                            ),
                            "sourceKind": "NATIVE",
                            "evidenceRefs": [{"sourcePath": name}],
                        }
                    )
        except (KeyError, zipfile.BadZipFile) as exc:
            raise ValueError("DOCUMENT_PARSE_FAILED") from exc
        excerpt = "\n".join(item["text"] for item in paragraphs[:80])
        return ParsedContent(
            pages=[{"page": 1, "text": excerpt}],
            paragraphs=paragraphs[:500],
            sections=[],
            tables=tables,
            sheets=sheets,
            embeddedMetadata={
                "filename": filename,
                "mediaType": media_type,
                "sheetCount": len(sheets),
                "rowCount": sum(int(item["rowCount"]) for item in sheets),
                "tableCount": len(tables),
            },
            warnings=[] if excerpt else ["XLSX_EMPTY"],
            textExcerpt=excerpt[:4000],
            needsOcr=False,
        )

    def _shared_strings(self, archive: zipfile.ZipFile) -> list[str]:
        if "xl/sharedStrings.xml" not in archive.namelist():
            return []
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
        values: list[str] = []
        for item in root.findall("m:si", self._NS):
            texts = [node.text or "" for node in item.findall(".//m:t", self._NS)]
            values.append("".join(texts))
        return values

    def _cell_value(self, cell: ElementTree.Element, shared: list[str]) -> str:
        cell_type = cell.attrib.get("t")
        raw = cell.find("m:v", self._NS)
        if raw is None or raw.text is None:
            return ""
        if cell_type == "s":
            index = int(raw.text)
            return shared[index] if 0 <= index < len(shared) else ""
        return raw.text


class PdfParser:
    name = "pdf-text"
    version = "2"

    def supports(self, media_type: str) -> bool:
        return media_type == "application/pdf"

    def parse(self, *, filename: str, media_type: str, content: bytes) -> ParsedContent:
        poppler_text = self._extract_with_poppler(content)
        if _meaningful_text(poppler_text):
            page_texts = poppler_text.split("\f")
            if page_texts and not page_texts[-1].strip():
                page_texts.pop()
            return self._parsed_pdf(
                filename=filename,
                media_type=media_type,
                pages=[
                    {"page": index, "text": value}
                    for index, value in enumerate(page_texts, start=1)
                ],
                warning="PDF_TEXT_POPPLER",
            )
        fallback_pages: list[dict[str, Any]] = []
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            pages: list[dict[str, Any]] = []
            for index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                pages.append({"page": index, "text": page_text})
            fallback_pages = pages
            body = "\n".join(str(page["text"]) for page in pages)
            if _meaningful_text(body):
                return self._parsed_pdf(
                    filename=filename,
                    media_type=media_type,
                    pages=pages,
                    warning=None,
                )
        except Exception:
            pass
        if not fallback_pages:
            fallback_pages = [{"page": 1, "text": ""}]
        return ParsedContent(
            pages=[
                {
                    **page,
                    "sourceKind": "OCR",
                    "routeReason": "NATIVE_TEXT_INSUFFICIENT",
                }
                for page in fallback_pages
            ],
            paragraphs=[],
            tables=[],
            sheets=[],
            layout={
                "pageRoutes": [
                    {
                        "page": page["page"],
                        "route": "OCR",
                        "reason": "NATIVE_TEXT_INSUFFICIENT",
                        "textCharacters": len(str(page.get("text") or "").strip()),
                    }
                    for page in fallback_pages
                ],
                "ocrPages": [page["page"] for page in fallback_pages],
            },
            embeddedMetadata={
                "filename": filename,
                "mediaType": media_type,
                "pageCount": len(fallback_pages),
            },
            warnings=["PDF_NO_MEANINGFUL_TEXT"],
            textExcerpt="",
            needsOcr=True,
        )

    def _extract_with_poppler(self, content: bytes) -> str:
        command = os.getenv("SWARMCORE_PDFTOTEXT_CMD", "").strip() or shutil.which("pdftotext")
        if command is None:
            return ""
        with tempfile.TemporaryDirectory(prefix="swarmcore-pdf-") as temp:
            source = Path(temp) / "source.pdf"
            source.write_bytes(content)
            try:
                completed = subprocess.run(
                    [command, "-layout", str(source), "-"],
                    check=False,
                    capture_output=True,
                    timeout=120,
                )
            except (OSError, subprocess.TimeoutExpired):
                return ""
        if completed.returncode != 0:
            return ""
        return completed.stdout.decode("utf-8", errors="replace")

    def _parsed_pdf(
        self,
        *,
        filename: str,
        media_type: str,
        pages: list[dict[str, Any]],
        warning: str | None,
    ) -> ParsedContent:
        body = "\n".join(str(page["text"]) for page in pages)
        page_routes = [
            {
                "page": int(page["page"]),
                "route": (
                    "NATIVE"
                    if _meaningful_text(str(page.get("text") or ""))
                    else "OCR"
                ),
                "reason": (
                    "NATIVE_TEXT_SUFFICIENT"
                    if _meaningful_text(str(page.get("text") or ""))
                    else "NATIVE_TEXT_INSUFFICIENT"
                ),
                "textCharacters": len(str(page.get("text") or "").strip()),
            }
            for page in pages
        ]
        normalized_pages = [
            {
                **page,
                "sourceKind": page_routes[index]["route"],
                "routeReason": page_routes[index]["reason"],
            }
            for index, page in enumerate(pages)
        ]
        ocr_pages = [
            int(item["page"]) for item in page_routes if item["route"] == "OCR"
        ]
        return ParsedContent(
            pages=normalized_pages or [{"page": 1, "text": ""}],
            paragraphs=[
                {
                    "index": index,
                    "text": str(page["text"]),
                    "page": page["page"],
                    "sourceKind": "NATIVE",
                }
                for index, page in enumerate(normalized_pages, start=1)
                if str(page.get("text") or "").strip()
            ][:500],
            tables=[],
            sheets=[],
            layout={"pageRoutes": page_routes, "ocrPages": ocr_pages},
            embeddedMetadata={
                "filename": filename,
                "mediaType": media_type,
                "pageCount": len(pages),
            },
            warnings=[warning] if warning else [],
            textExcerpt=body[:4000],
            needsOcr=bool(ocr_pages),
        )


def _meaningful_text(value: str) -> bool:
    text = value.strip()
    if len(text) < 20:
        return False
    visible = sum(1 for char in text if char.isprintable() or char.isspace())
    semantic = sum(1 for char in text if char.isalnum() or "\u4e00" <= char <= "\u9fff")
    return visible / len(text) >= 0.95 and semantic / len(text) >= 0.2


class ImageMetadataParser:
    name = "image-metadata"
    version = "1"

    def supports(self, media_type: str) -> bool:
        return media_type in {
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/tiff",
        }

    def parse(self, *, filename: str, media_type: str, content: bytes) -> ParsedContent:
        metadata: dict[str, Any] = {
            "filename": filename,
            "mediaType": media_type,
            "sizeBytes": len(content),
        }
        if content[:8] == b"\x89PNG\r\n\x1a\n":
            metadata["format"] = "png"
        elif content[:2] == b"\xff\xd8":
            metadata["format"] = "jpeg"
        elif content[:4] in {b"II*\x00", b"MM\x00*"}:
            metadata["format"] = "tiff"
        return ParsedContent(
            pages=[{"page": 1, "text": ""}],
            paragraphs=[],
            tables=[],
            sheets=[],
            embeddedMetadata=metadata,
            warnings=["IMAGE_REQUIRES_OCR"],
            textExcerpt="",
            needsOcr=True,
        )


class ParserRegistry:
    def __init__(self, parsers: list[DocumentParser] | None = None) -> None:
        self._parsers = parsers or [
            TextMarkdownParser(),
            StructuredTextParser(),
            OdfParser(),
            DocxParser(),
            XlsxParser(),
            PptxParser(),
            PdfParser(),
            ImageMetadataParser(),
        ]

    def select(self, media_type: str) -> DocumentParser:
        for parser in self._parsers:
            if parser.supports(media_type):
                return parser
        raise ValueError("UNSUPPORTED_MEDIA_TYPE")

    def parse(self, *, filename: str, media_type: str, content: bytes) -> tuple[str, ParsedContent]:
        parser = self.select(media_type)
        return f"parser://{parser.name}@{parser.version}", parser.parse(
            filename=filename, media_type=media_type, content=content
        )
