"""Generate demo office/pdf fixtures for document intake demos."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

ROOT = Path(__file__).resolve().parent


def write_docx(path: Path, text: str) -> None:
    document = Element("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document")
    body = SubElement(document, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body")
    for line in text.splitlines():
        paragraph = SubElement(body, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p")
        run = SubElement(paragraph, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r")
        node = SubElement(run, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
        node.text = line
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", tostring(document, encoding="utf-8"))
    path.write_bytes(buffer.getvalue())


def write_xlsx(path: Path, rows: list[list[str]]) -> None:
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    shared = Element(f"{{{ns}}}sst", {"count": str(len(rows)), "uniqueCount": str(len(rows))})
    values: list[str] = []
    for row in rows:
        values.append(" | ".join(row))
        si = SubElement(shared, f"{{{ns}}}si")
        t = SubElement(si, f"{{{ns}}}t")
        t.text = values[-1]
    sheet = Element(f"{{{ns}}}worksheet")
    data = SubElement(sheet, f"{{{ns}}}sheetData")
    for index, _ in enumerate(values, start=1):
        row = SubElement(data, f"{{{ns}}}row", {"r": str(index)})
        cell = SubElement(row, f"{{{ns}}}c", {"r": f"A{index}", "t": "s"})
        value = SubElement(cell, f"{{{ns}}}v")
        value.text = str(index - 1)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", tostring(shared, encoding="utf-8"))
        archive.writestr("xl/worksheets/sheet1.xml", tostring(sheet, encoding="utf-8"))
    path.write_bytes(buffer.getvalue())


def write_minimal_pdf(path: Path, text: str) -> None:
    # Minimal digital PDF with a literal text string for the heuristic/pypdf parsers.
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1", errors="ignore")
    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n",
        b"4 0 obj<< /Length %d >>stream\n" % len(content) + content + b"\nendstream\nendobj\n",
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
    ]
    buffer = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(buffer))
        buffer.extend(obj)
    xref_pos = len(buffer)
    buffer.extend(f"xref\n0 {len(offsets)}\n".encode())
    buffer.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.extend(f"{offset:010d} 00000 n \n".encode())
    buffer.extend(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )
    path.write_bytes(buffer)


def main() -> None:
    write_docx(ROOT / "demo-contract.docx", "标题: 通用演示合同\n甲方: 示例供应商\n金额: 128000")
    write_xlsx(ROOT / "demo-amounts.xlsx", [["标题", "金额样例"], ["金额", "25600"]])
    write_minimal_pdf(ROOT / "demo-contract.pdf", "title: Demo Contract amount: 128000")
    print(f"wrote demo files under {ROOT}")


if __name__ == "__main__":
    main()
