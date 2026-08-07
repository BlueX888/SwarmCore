"""High-fidelity parsers for ODF and presentation packages."""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any, ClassVar
from xml.etree import ElementTree

from .contracts import ParsedContent
from .limits import MAX_SPREADSHEET_CELLS, MAX_SPREADSHEET_ROWS, ArchiveBudget, DocumentLimitError


def _text(node: ElementTree.Element) -> str:
    return " ".join(part.strip() for part in node.itertext() if part and part.strip()).strip()


def _repeated(value: str | None, *, maximum: int = 10_000) -> int:
    try:
        return min(maximum, max(1, int(value or "1")))
    except ValueError:
        return 1


class OdfParser:
    """Parse ODT, ODS, and ODP from their native ODF XML package."""

    name = "odf-native"
    version = "1"
    _NS: ClassVar[dict[str, str]] = {
        "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
        "presentation": "urn:oasis:names:tc:opendocument:xmlns:presentation:1.0",
    }
    _MEDIA_TYPES: ClassVar[set[str]] = {
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.text-template",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.spreadsheet-template",
        "application/vnd.oasis.opendocument.presentation",
        "application/vnd.oasis.opendocument.presentation-template",
    }

    def supports(self, media_type: str) -> bool:
        return media_type in self._MEDIA_TYPES

    def parse(self, *, filename: str, media_type: str, content: bytes) -> ParsedContent:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                budget = ArchiveBudget(archive)
                package_media_type = (
                    budget.read("mimetype").decode("ascii", errors="replace").strip()
                    if "mimetype" in archive.namelist()
                    else media_type
                )
                root = ElementTree.fromstring(budget.read("content.xml"))
                metadata = self._metadata(archive, budget)
        except DocumentLimitError:
            raise
        except (KeyError, ElementTree.ParseError, zipfile.BadZipFile) as exc:
            raise ValueError("DOCUMENT_PARSE_FAILED") from exc

        if package_media_type.startswith("application/vnd.oasis.opendocument.spreadsheet"):
            parsed = self._spreadsheet(root)
        elif package_media_type.startswith("application/vnd.oasis.opendocument.presentation"):
            parsed = self._presentation(root)
        else:
            parsed = self._text_document(root)

        parsed.embedded_metadata.update(
            {
                "filename": filename,
                "mediaType": package_media_type,
                "declaredMediaType": media_type,
                **metadata,
            }
        )
        return parsed

    def _text_document(self, root: ElementTree.Element) -> ParsedContent:
        body = root.find(".//office:body/office:text", self._NS)
        if body is None:
            raise ValueError("DOCUMENT_PARSE_FAILED")
        paragraphs: list[dict[str, Any]] = []
        sections: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        section_path: list[str] = []
        table_paragraph_ids = {
            id(paragraph)
            for table in body.findall(".//table:table", self._NS)
            for paragraph in table.findall(".//text:p", self._NS)
        }

        for node in body.iter():
            if node.tag == f"{{{self._NS['text']}}}h":
                value = _text(node)
                if not value:
                    continue
                level = _repeated(
                    node.attrib.get(f"{{{self._NS['text']}}}outline-level"),
                    maximum=10,
                )
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
                        "kind": "heading",
                        "level": level,
                        "sectionPath": list(section_path),
                    }
                )
            elif node.tag == f"{{{self._NS['text']}}}p":
                if id(node) in table_paragraph_ids:
                    continue
                value = _text(node)
                if value:
                    paragraphs.append(
                        {
                            "index": len(paragraphs) + 1,
                            "text": value,
                            "kind": "paragraph",
                            "sectionPath": list(section_path),
                        }
                    )
            elif node.tag == f"{{{self._NS['table']}}}table":
                tables.append(self._table(node, len(tables) + 1))

        for index, section in enumerate(sections):
            next_start = (
                int(sections[index + 1]["paragraphStart"])
                if index + 1 < len(sections)
                else len(paragraphs) + 1
            )
            section["paragraphEnd"] = max(int(section["paragraphStart"]), next_start - 1)
        text = "\n".join(str(item["text"]) for item in paragraphs)
        source_heading_count = len(body.findall(".//text:h", self._NS))
        source_paragraph_count = len(body.findall(".//text:p", self._NS))
        return ParsedContent(
            pages=[{"page": 1, "text": text}],
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            sheets=[],
            embeddedMetadata={
                "headingCount": source_heading_count,
                "paragraphCount": source_paragraph_count,
                "semanticHeadingCount": len(sections),
                "semanticParagraphCount": len(paragraphs),
                "tableCount": len(tables),
            },
            warnings=[] if text else ["ODF_EMPTY_TEXT"],
            textExcerpt=text[:8000],
            needsOcr=False,
        )

    def _spreadsheet(self, root: ElementTree.Element) -> ParsedContent:
        sheets: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        paragraphs: list[dict[str, Any]] = []
        spreadsheet = root.find(".//office:body/office:spreadsheet", self._NS)
        if spreadsheet is None:
            raise ValueError("DOCUMENT_PARSE_FAILED")
        for node in spreadsheet.findall("table:table", self._NS):
            table = self._table(node, len(tables) + 1)
            tables.append(table)
            rows = table["rows"]
            sheets.append(
                {
                    "name": table["name"],
                    "rows": rows,
                    "rowCount": len(rows),
                    "columnCount": max((len(row) for row in rows), default=0),
                }
            )
            for row in rows:
                if any(row):
                    paragraphs.append(
                        {
                            "index": len(paragraphs) + 1,
                            "text": " | ".join(row),
                            "sheet": table["name"],
                        }
                    )
        text = "\n".join(str(item["text"]) for item in paragraphs)
        return ParsedContent(
            pages=[{"page": 1, "text": text[:100_000]}],
            paragraphs=paragraphs,
            sections=[],
            tables=tables,
            sheets=sheets,
            embeddedMetadata={
                "sheetCount": len(sheets),
                "rowCount": sum(int(item["rowCount"]) for item in sheets),
                "tableCount": len(tables),
            },
            warnings=[] if sheets else ["ODS_EMPTY"],
            textExcerpt=text[:8000],
            needsOcr=False,
        )

    def _presentation(self, root: ElementTree.Element) -> ParsedContent:
        presentation = root.find(".//office:body/office:presentation", self._NS)
        if presentation is None:
            raise ValueError("DOCUMENT_PARSE_FAILED")
        pages: list[dict[str, Any]] = []
        paragraphs: list[dict[str, Any]] = []
        sections: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        for index, page in enumerate(presentation.findall("draw:page", self._NS), start=1):
            values = [_text(node) for node in page.findall(".//text:p", self._NS) if _text(node)]
            title = values[0] if values else f"Slide {index}"
            sections.append(
                {
                    "sectionId": f"slide-{index}",
                    "title": title,
                    "level": 1,
                    "path": [title],
                    "pageStart": index,
                    "pageEnd": index,
                }
            )
            for value in values:
                paragraphs.append(
                    {
                        "index": len(paragraphs) + 1,
                        "text": value,
                        "page": index,
                        "sectionPath": [title],
                    }
                )
            for table_node in page.findall(".//table:table", self._NS):
                table = self._table(table_node, len(tables) + 1)
                table["pageStart"] = index
                table["pageEnd"] = index
                table["evidenceRefs"] = [
                    {
                        **dict(value),
                        "page": index,
                    }
                    for value in table["evidenceRefs"]
                ]
                tables.append(table)
            pages.append({"page": index, "text": "\n".join(values), "title": title})
        text = "\n".join(str(item["text"]) for item in paragraphs)
        return ParsedContent(
            pages=pages,
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            sheets=[],
            embeddedMetadata={
                "pageCount": len(pages),
                "tableCount": len(tables),
            },
            warnings=[] if pages else ["ODP_EMPTY"],
            textExcerpt=text[:8000],
            needsOcr=False,
        )

    def _table(self, node: ElementTree.Element, ordinal: int) -> dict[str, Any]:
        name = node.attrib.get(f"{{{self._NS['table']}}}name") or f"Table {ordinal}"
        rows: list[list[str]] = []
        for row in node.findall(".//table:table-row", self._NS):
            row_values: list[str] = []
            for cell in list(row):
                if cell.tag not in {
                    f"{{{self._NS['table']}}}table-cell",
                    f"{{{self._NS['table']}}}covered-table-cell",
                }:
                    continue
                value = _text(cell)
                repeated = _repeated(
                    cell.attrib.get(f"{{{self._NS['table']}}}number-columns-repeated")
                )
                if len(row_values) + repeated > MAX_SPREADSHEET_CELLS:
                    raise DocumentLimitError("DOCUMENT_SPREADSHEET_CELL_LIMIT_EXCEEDED")
                row_values.extend([value] * repeated)
            row_repeat = _repeated(row.attrib.get(f"{{{self._NS['table']}}}number-rows-repeated"))
            if len(rows) + row_repeat > MAX_SPREADSHEET_ROWS:
                raise DocumentLimitError("DOCUMENT_SPREADSHEET_ROW_LIMIT_EXCEEDED")
            if (len(rows) + row_repeat) * len(row_values) > MAX_SPREADSHEET_CELLS:
                raise DocumentLimitError("DOCUMENT_SPREADSHEET_CELL_LIMIT_EXCEEDED")
            rows.extend([list(row_values) for _ in range(row_repeat)])
        columns = max((len(row) for row in rows), default=0)
        normalized = [row + [""] * (columns - len(row)) for row in rows]
        return {
            "tableId": f"table-{ordinal}",
            "name": name,
            "columns": normalized[0] if normalized else [],
            "rows": normalized,
            "rowCount": len(normalized),
            "columnCount": columns,
            "sourceKind": "NATIVE",
            "evidenceRefs": [{"sourcePath": "content.xml", "tableName": name}],
        }

    def _metadata(self, archive: zipfile.ZipFile, budget: ArchiveBudget) -> dict[str, Any]:
        if "meta.xml" not in archive.namelist():
            return {}
        try:
            root = ElementTree.fromstring(budget.read("meta.xml"))
        except ElementTree.ParseError:
            return {}
        metadata: dict[str, Any] = {}
        for node in root.iter():
            local = node.tag.rsplit("}", 1)[-1]
            if local in {"title", "subject", "creator", "creation-date"}:
                value = _text(node)
                if value:
                    metadata[local] = value
        return metadata


class PptxParser:
    name = "pptx-native"
    version = "1"
    _NS: ClassVar[dict[str, str]] = {
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    }

    def supports(self, media_type: str) -> bool:
        return media_type in {
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.ms-powerpoint",
        }

    def parse(self, *, filename: str, media_type: str, content: bytes) -> ParsedContent:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                budget = ArchiveBudget(archive)
                slide_names = sorted(
                    (
                        name
                        for name in archive.namelist()
                        if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
                    ),
                    key=lambda value: int(re.search(r"(\d+)", value).group(1)),  # type: ignore[union-attr]
                )
                pages: list[dict[str, Any]] = []
                paragraphs: list[dict[str, Any]] = []
                sections: list[dict[str, Any]] = []
                tables: list[dict[str, Any]] = []
                for page_number, name in enumerate(slide_names, start=1):
                    root = ElementTree.fromstring(budget.read(name))
                    values = [
                        node.text.strip()
                        for node in root.findall(".//a:t", self._NS)
                        if node.text and node.text.strip()
                    ]
                    title = values[0] if values else f"Slide {page_number}"
                    pages.append(
                        {
                            "page": page_number,
                            "text": "\n".join(values),
                            "title": title,
                        }
                    )
                    sections.append(
                        {
                            "sectionId": f"slide-{page_number}",
                            "title": title,
                            "level": 1,
                            "path": [title],
                            "pageStart": page_number,
                            "pageEnd": page_number,
                        }
                    )
                    for value in values:
                        paragraphs.append(
                            {
                                "index": len(paragraphs) + 1,
                                "text": value,
                                "page": page_number,
                                "sectionPath": [title],
                            }
                        )
                    for table_node in root.findall(".//a:tbl", self._NS):
                        rows = [
                            [_text(cell) for cell in row.findall("a:tc", self._NS)]
                            for row in table_node.findall("a:tr", self._NS)
                        ]
                        width = max((len(row) for row in rows), default=0)
                        normalized = [row + [""] * (width - len(row)) for row in rows]
                        tables.append(
                            {
                                "tableId": f"table-{len(tables) + 1}",
                                "name": f"Slide {page_number} table {len(tables) + 1}",
                                "columns": normalized[0] if normalized else [],
                                "rows": normalized,
                                "rowCount": len(normalized),
                                "columnCount": width,
                                "pageStart": page_number,
                                "pageEnd": page_number,
                                "sourceKind": "NATIVE",
                                "evidenceRefs": [{"page": page_number, "sourcePath": name}],
                            }
                        )
        except DocumentLimitError:
            raise
        except (ElementTree.ParseError, zipfile.BadZipFile) as exc:
            raise ValueError("DOCUMENT_PARSE_FAILED") from exc
        text = "\n".join(str(item["text"]) for item in paragraphs)
        return ParsedContent(
            pages=pages,
            paragraphs=paragraphs,
            sections=sections,
            tables=tables,
            sheets=[],
            embeddedMetadata={
                "filename": filename,
                "mediaType": media_type,
                "pageCount": len(pages),
                "tableCount": len(tables),
            },
            warnings=[] if pages else ["PPTX_EMPTY"],
            textExcerpt=text[:8000],
            needsOcr=False,
        )
