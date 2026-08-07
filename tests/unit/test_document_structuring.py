"""Tests for the file-structuring parsing, chunking, and quality core."""

from __future__ import annotations

import io
import zipfile
from xml.etree.ElementTree import Element, SubElement, tostring

import pypdf
import pytest
from pypdf import PdfWriter
from swarmcore_application.document_processing import (
    BUSINESS_STRUCTURING_PROFILE,
    ClassificationResult,
    DocumentChunker,
    DocumentQualityChecker,
    ExtractionField,
    ParsedContent,
    ParserRegistry,
    SchemaDrivenExtractor,
    resolve_profile,
    schema_for_ref,
)
from swarmcore_application.document_processing import parsers as parser_module
from swarmcore_application.document_processing.limits import (
    ArchiveBudget,
    DocumentLimitError,
)
from swarmcore_application.document_processing.service import _detect_media_type
from swarmcore_worker_control.document_processing import (
    _extract_group,
    _processing_groups,
)

ODF_OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
ODF_TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
ODF_TABLE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"


def _odf_package(media_type: str, content_xml: bytes) -> bytes:
    value = io.BytesIO()
    with zipfile.ZipFile(value, "w") as archive:
        archive.writestr("mimetype", media_type, compress_type=zipfile.ZIP_STORED)
        archive.writestr("content.xml", content_xml)
    return value.getvalue()


def _odt() -> bytes:
    document = Element(f"{{{ODF_OFFICE}}}document-content")
    body = SubElement(document, f"{{{ODF_OFFICE}}}body")
    text = SubElement(body, f"{{{ODF_OFFICE}}}text")
    heading = SubElement(
        text,
        f"{{{ODF_TEXT}}}h",
        {f"{{{ODF_TEXT}}}outline-level": "1"},
    )
    heading.text = "Call-Off Contract"
    paragraph = SubElement(text, f"{{{ODF_TEXT}}}p")
    paragraph.text = "Framework reference RM1043.6"
    table = SubElement(
        text,
        f"{{{ODF_TABLE}}}table",
        {f"{{{ODF_TABLE}}}name": "Order form"},
    )
    for values in (("Field", "Value"), ("Buyer", "Click here to enter")):
        row = SubElement(table, f"{{{ODF_TABLE}}}table-row")
        for value in values:
            cell = SubElement(row, f"{{{ODF_TABLE}}}table-cell")
            cell_text = SubElement(cell, f"{{{ODF_TEXT}}}p")
            cell_text.text = value
    return _odf_package(
        "application/vnd.oasis.opendocument.text",
        tostring(document, encoding="utf-8", xml_declaration=True),
    )


def _ods() -> bytes:
    document = Element(f"{{{ODF_OFFICE}}}document-content")
    body = SubElement(document, f"{{{ODF_OFFICE}}}body")
    spreadsheet = SubElement(body, f"{{{ODF_OFFICE}}}spreadsheet")
    table = SubElement(
        spreadsheet,
        f"{{{ODF_TABLE}}}table",
        {f"{{{ODF_TABLE}}}name": "Amounts"},
    )
    for values in (("Item", "Amount"), ("A", "100")):
        row = SubElement(table, f"{{{ODF_TABLE}}}table-row")
        for value in values:
            cell = SubElement(row, f"{{{ODF_TABLE}}}table-cell")
            cell_text = SubElement(cell, f"{{{ODF_TEXT}}}p")
            cell_text.text = value
    return _odf_package(
        "application/vnd.oasis.opendocument.spreadsheet",
        tostring(document, encoding="utf-8", xml_declaration=True),
    )


def _pptx() -> bytes:
    presentation = (
        '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>'
    )
    slide = (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Project status</a:t>"
        "</a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
    )
    value = io.BytesIO()
    with zipfile.ZipFile(value, "w") as archive:
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/slides/slide1.xml", slide)
    return value.getvalue()


def test_business_structuring_profile_is_resolvable() -> None:
    profile = resolve_profile("document-profile://business-structuring@1")
    assert profile == BUSINESS_STRUCTURING_PROFILE
    assert "application/vnd.oasis.opendocument.text" in profile.accepted_media_types
    assert profile.parser_policy["pageBatchSize"] == 10
    assert profile.quality_thresholds["classification"] == 0.90


def test_odf_detection_uses_package_mimetype_without_extension() -> None:
    content = _odt()
    detected = _detect_media_type(content, "renamed.bin", "application/octet-stream")
    assert detected == "application/vnd.oasis.opendocument.text"


def test_odt_parser_preserves_headings_paragraphs_and_tables() -> None:
    parser_ref, parsed = ParserRegistry().parse(
        filename="contract.odt",
        media_type="application/vnd.oasis.opendocument.text",
        content=_odt(),
    )
    assert parser_ref == "parser://odf-native@1"
    assert parsed.sections[0]["title"] == "Call-Off Contract"
    assert "RM1043.6" in parsed.text_excerpt
    assert parsed.tables[0]["name"] == "Order form"
    assert parsed.tables[0]["rows"][1] == ["Buyer", "Click here to enter"]
    assert parsed.embedded_metadata["tableCount"] == 1


def test_ods_parser_returns_sheet_and_rectangular_table() -> None:
    _, parsed = ParserRegistry().parse(
        filename="amounts.ods",
        media_type="application/vnd.oasis.opendocument.spreadsheet",
        content=_ods(),
    )
    assert parsed.sheets[0]["name"] == "Amounts"
    assert parsed.sheets[0]["rowCount"] == 2
    assert parsed.tables[0]["rows"] == [["Item", "Amount"], ["A", "100"]]


def test_archive_budget_rejects_high_ratio_member() -> None:
    value = io.BytesIO()
    with zipfile.ZipFile(value, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", b"A" * (2 * 1024 * 1024))

    with (
        zipfile.ZipFile(io.BytesIO(value.getvalue())) as archive,
        pytest.raises(DocumentLimitError, match="COMPRESSION_RATIO"),
    ):
        ArchiveBudget(archive).read("word/document.xml")


def test_processing_planner_rejects_high_ratio_xlsx() -> None:
    worksheet = (
        b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + b"<row></row>" * 200_000
        + b"</worksheet>"
    )
    value = io.BytesIO()
    with zipfile.ZipFile(value, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)

    with pytest.raises(DocumentLimitError, match="COMPRESSION_RATIO"):
        _processing_groups(
            value.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "amplification.xlsx",
        )


def test_ods_parser_rejects_multiplicative_repeat_expansion() -> None:
    document = Element(f"{{{ODF_OFFICE}}}document-content")
    body = SubElement(document, f"{{{ODF_OFFICE}}}body")
    spreadsheet = SubElement(body, f"{{{ODF_OFFICE}}}spreadsheet")
    table = SubElement(spreadsheet, f"{{{ODF_TABLE}}}table")
    row = SubElement(
        table,
        f"{{{ODF_TABLE}}}table-row",
        {f"{{{ODF_TABLE}}}number-rows-repeated": "10000"},
    )
    SubElement(
        row,
        f"{{{ODF_TABLE}}}table-cell",
        {f"{{{ODF_TABLE}}}number-columns-repeated": "10000"},
    )
    content = _odf_package(
        "application/vnd.oasis.opendocument.spreadsheet",
        tostring(document, encoding="utf-8", xml_declaration=True),
    )

    with pytest.raises(DocumentLimitError, match="CELL_LIMIT"):
        ParserRegistry().parse(
            filename="amplification.ods",
            media_type="application/vnd.oasis.opendocument.spreadsheet",
            content=content,
        )


def test_pdf_parser_rejects_excess_page_count(monkeypatch: pytest.MonkeyPatch) -> None:
    class Reader:
        pages = [object()] * 1001

    monkeypatch.setattr(parser_module.shutil, "which", lambda _name: None)
    monkeypatch.setattr(pypdf, "PdfReader", lambda _source: Reader())

    with pytest.raises(DocumentLimitError, match="PAGE_LIMIT"):
        parser_module.PdfParser().parse(
            filename="oversized.pdf", media_type="application/pdf", content=b"%PDF"
        )


def test_pptx_is_detected_and_parsed_without_extension() -> None:
    content = _pptx()
    media_type = _detect_media_type(content, "presentation.bin", "application/octet-stream")
    assert media_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    parser_ref, parsed = ParserRegistry().parse(
        filename="presentation.bin",
        media_type=media_type,
        content=content,
    )
    assert parser_ref == "parser://pptx-native@1"
    assert parsed.pages == [{"page": 1, "text": "Project status", "title": "Project status"}]


def test_chunker_respects_sections_and_keeps_tables_as_table_chunks() -> None:
    content = ParsedContent(
        pages=[{"page": 1, "text": "Contract"}],
        paragraphs=[
            {
                "index": 1,
                "text": "Contract terms",
                "page": 1,
                "sectionPath": ["Part A"],
            },
            {
                "index": 2,
                "text": "Payment terms",
                "page": 2,
                "sectionPath": ["Part B"],
            },
        ],
        tables=[
            {
                "tableId": "t1",
                "name": "Charges",
                "rows": [["Item", "Amount"], ["Service", "100"]],
                "evidenceRefs": [{"page": 3}],
            }
        ],
    )
    chunks = DocumentChunker().chunk(content)
    assert [chunk["kind"] for chunk in chunks] == ["TEXT", "TEXT", "TABLE"]
    assert chunks[0]["sectionPath"] == ["Part A"]
    assert chunks[1]["sectionPath"] == ["Part B"]
    assert chunks[2]["tableId"] == "t1"
    assert "| Item | Amount |" in chunks[2]["text"]
    assert all(chunk["tokenCount"] <= 1_600 for chunk in chunks)
    assert all(len(chunk["contentHash"]) == 64 for chunk in chunks)


def test_quality_gate_requires_evidence_and_flags_low_ocr() -> None:
    content = ParsedContent(
        pages=[{"page": 1, "text": "Contract"}],
        paragraphs=[{"index": 1, "text": "Contract", "page": 1}],
        chunks=[{"chunkId": "c1", "tokenCount": 10}],
        layout={
            "blocks": [
                {
                    "text": "Contract",
                    "sourceKind": "OCR",
                    "confidence": 0.70,
                }
            ]
        },
    )
    classification = ClassificationResult(
        label="CONTRACT",
        displayName="合同",
        confidence=0.95,
        evidence=[{"page": 1, "text": "Contract"}],
    )
    fields = [
        ExtractionField(
            fieldPath="document.title",
            displayName="标题",
            value="Contract",
            machineValue="Contract",
            confidence=0.90,
            evidenceRefs=[],
        )
    ]
    result = DocumentQualityChecker().check(
        content=content,
        classification=classification,
        extractions=fields,
        classification_threshold=0.90,
        extraction_threshold=0.85,
        critical_extraction_threshold=0.95,
        ocr_threshold=0.90,
    )
    assert result["passed"] is False
    assert "EXTRACTION_EVIDENCE_MISSING" in result["flags"]
    assert "OCR_REVIEW_REQUIRED" in result["flags"]
    assert result["metrics"]["averageOcrConfidence"] == 0.70


def test_contract_extractor_does_not_promote_template_placeholder() -> None:
    schema = schema_for_ref("schema://document/contract-structure@1")
    assert schema is not None
    content = ParsedContent(
        pages=[
            {
                "page": 4,
                "text": (
                    "Digital Outcomes and Specialists 4 Framework Agreement "
                    "Call-Off Contract\nFramework Agreement (RM1043.6)\n"
                    "Buyer name: Click here to enter name."
                ),
            }
        ],
        paragraphs=[],
        textExcerpt=(
            "Digital Outcomes and Specialists 4 Framework Agreement "
            "Call-Off Contract\nFramework Agreement (RM1043.6)\n"
            "Buyer name: Click here to enter name."
        ),
    )
    fields = SchemaDrivenExtractor().extract(
        content=content,
        schema=schema,
        classification=ClassificationResult(
            label="CONTRACT",
            displayName="合同",
            confidence=0.95,
            evidence=[{"page": 1, "text": "Call-Off Contract"}],
        ),
        profile=BUSINESS_STRUCTURING_PROFILE,
    )
    reference = next(field for field in fields if field.field_path == "contract.reference")
    buyer = next(field for field in fields if field.field_path == "contract.buyer")
    assert reference.machine_value == "RM1043.6"
    assert reference.evidence_refs[0]["page"] == 4
    assert buyer.machine_value is None
    assert buyer.review_status == "UNCONFIRMED"
    assert buyer.quality_flags == ["PLACEHOLDER_NOT_FILLED"]


def test_large_pdf_is_split_into_seven_bounded_temporal_groups() -> None:
    stream = io.BytesIO()
    writer = PdfWriter()
    for _ in range(68):
        writer.add_blank_page(width=612, height=792)
    writer.write(stream)
    content = stream.getvalue()

    groups, page_count, row_count = _processing_groups(content, "application/pdf", "contract.pdf")

    assert page_count == 68
    assert row_count == 0
    assert len(groups) == 7
    assert all(int(group["pageEnd"]) - int(group["pageStart"]) + 1 <= 10 for group in groups)
    assert groups[0]["pageStart"] == 1
    assert groups[-1]["pageEnd"] == 68
    extracted = _extract_group(content, "application/pdf", groups[-1])
    assert extracted["itemCount"] == 8
    assert [page["page"] for page in extracted["pages"]] == list(range(61, 69))
