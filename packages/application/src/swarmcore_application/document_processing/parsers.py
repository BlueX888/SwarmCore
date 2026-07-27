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
                    {str(key) for row in rows for key in row.keys()}
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
    version = "1"
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
        texts = [
            node.text.strip()
            for node in root.findall(".//w:t", self._NS)
            if node.text and node.text.strip()
        ]
        body = "\n".join(texts)
        paragraphs = [
            {"index": index, "text": value} for index, value in enumerate(texts, start=1)
        ]
        return ParsedContent(
            pages=[{"page": 1, "text": body}],
            paragraphs=paragraphs,
            tables=[],
            sheets=[],
            embeddedMetadata={"filename": filename, "mediaType": media_type},
            warnings=[] if body else ["DOCX_EMPTY_TEXT"],
            textExcerpt=body[:4000],
            needsOcr=not bool(body.strip()),
        )


class XlsxParser:
    name = "xlsx"
    version = "1"
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
                    sheets.append({"name": name.split("/")[-1], "rows": rows[:200]})
        except (KeyError, zipfile.BadZipFile) as exc:
            raise ValueError("DOCUMENT_PARSE_FAILED") from exc
        excerpt = "\n".join(item["text"] for item in paragraphs[:80])
        return ParsedContent(
            pages=[{"page": 1, "text": excerpt}],
            paragraphs=paragraphs[:500],
            tables=[],
            sheets=sheets,
            embeddedMetadata={"filename": filename, "mediaType": media_type},
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
            return self._parsed_pdf(
                filename=filename,
                media_type=media_type,
                pages=[
                    {"page": index, "text": value}
                    for index, value in enumerate(
                        poppler_text.split("\f"), start=1
                    )
                    if value.strip()
                ],
                warning="PDF_TEXT_POPPLER",
            )
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            pages: list[dict[str, Any]] = []
            for index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                pages.append({"page": index, "text": page_text})
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
        return ParsedContent(
            pages=[{"page": 1, "text": ""}],
            paragraphs=[],
            tables=[],
            sheets=[],
            embeddedMetadata={"filename": filename, "mediaType": media_type},
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
        return ParsedContent(
            pages=pages or [{"page": 1, "text": ""}],
            paragraphs=[
                {"index": index, "text": line}
                for index, line in enumerate(body.splitlines(), start=1)
                if line.strip()
            ][:500],
            tables=[],
            sheets=[],
            embeddedMetadata={
                "filename": filename,
                "mediaType": media_type,
                "pageCount": len(pages),
            },
            warnings=[warning] if warning else [],
            textExcerpt=body[:4000],
            needsOcr=False,
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
        return media_type in {"image/png", "image/jpeg", "image/jpg"}

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
            DocxParser(),
            XlsxParser(),
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
