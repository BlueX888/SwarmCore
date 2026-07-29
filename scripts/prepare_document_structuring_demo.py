"""Download and verify the public document-structuring acceptance corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image
from reportlab.pdfgen.canvas import Canvas

SOURCES = (
    {
        "key": "official-odt",
        "filename": "dos-4-call-off-contract.odt",
        "url": (
            "https://assets.publishing.service.gov.uk/media/"
            "5f6a40e9d3bf7f7239aa1482/dos-4-call-off-contract.odt"
        ),
        "sha256": "022e406c0d3f5ed3dc7968dcf8bb0e98b5665b0aaff8e7772a15b56688ad024d",
    },
    {
        "key": "official-docx",
        "filename": "dos-4-call-off-contract.docx",
        "url": (
            "https://assets.publishing.service.gov.uk/media/"
            "5d8de734e5274a2fab26b261/dos-4-call-off-contract.docx"
        ),
        "sha256": "d95290ad5badf1bd6a7ddfb5bf12f4292ee28f651101bb769d544e6da3963bb5",
    },
    {
        "key": "official-pdf",
        "filename": "dos-4-call-off-contract.pdf",
        "url": (
            "https://assets.publishing.service.gov.uk/media/"
            "5d8de7a5ed915d556c95a09e/dos-4-call-off-contract.pdf"
        ),
        "sha256": "50a497b74e379cc1e6f13965636a6c58128901410ebe6c3070a3c2d5d5a10c66",
    },
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".tmp/document-structuring-demo"),
    )
    parser.add_argument("--skip-ocr-fixture", action="store_true")
    parser.add_argument("--pdftoppm", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    records = [_download(output, source) for source in SOURCES]
    derived: dict[str, Any] | None = None
    if not args.skip_ocr_fixture:
        derived = _derive_ocr_fixture(
            output,
            output / "dos-4-call-off-contract.pdf",
            renderer_override=args.pdftoppm,
        )
    verification = _verify_runtime(output, derived)
    manifest = {
        "schemaVersion": "schema://document-structuring/demo-corpus@1",
        "retrievedAt": datetime.now(UTC).isoformat(),
        "publication": (
            "https://www.gov.uk/government/publications/"
            "digital-outcomes-and-specialists-4-call-off-contract"
        ),
        "license": "Open Government Licence v3.0",
        "usageNotice": (
            "The publication is withdrawn and is used only as a repeatable "
            "document-processing fixture, not as current procurement guidance."
        ),
        "sources": records,
        "derivedOcrFixture": derived,
        "runtimeVerification": verification,
    }
    (output / "corpus-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def _download(output: Path, source: dict[str, str]) -> dict[str, Any]:
    target = output / source["filename"]
    if not target.is_file() or _sha256(target) != source["sha256"]:
        request = urllib.request.Request(
            source["url"],
            headers={"User-Agent": "SwarmCore-DocumentStructuring-Demo/1.0"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            target.write_bytes(response.read())
    actual = _sha256(target)
    if actual != source["sha256"]:
        target.unlink(missing_ok=True)
        raise ValueError(f"public fixture hash mismatch: {source['filename']}")
    return {
        **source,
        "path": str(target),
        "sizeBytes": target.stat().st_size,
        "verified": True,
    }


def _derive_ocr_fixture(
    output: Path,
    source_pdf: Path,
    *,
    renderer_override: Path | None,
) -> dict[str, Any]:
    renderer = _resolve_renderer(renderer_override)
    if renderer is None:
        raise RuntimeError("pdftoppm is required to derive the OCR fixture")
    version = subprocess.run(
        [str(renderer), "-v"],
        check=False,
        capture_output=True,
        text=True,
    )
    prefix = output / "ocr-page"
    subprocess.run(
        [
            str(renderer),
            "-f",
            "4",
            "-l",
            "7",
            "-r",
            "300",
            "-gray",
            "-png",
            str(source_pdf),
            str(prefix),
        ],
        check=True,
        capture_output=True,
    )
    images = sorted(output.glob("ocr-page-*.png"))
    if len(images) != 4:
        raise RuntimeError("OCR fixture renderer did not produce four pages")
    target = output / "dos-4-call-off-contract-pages-4-7-scanned.pdf"
    canvas = Canvas(str(target))
    for image_path in images:
        with Image.open(image_path) as image:
            width = float(image.width) * 72 / 300
            height = float(image.height) * 72 / 300
        canvas.setPageSize((width, height))
        canvas.drawImage(
            str(image_path),
            0,
            0,
            width=width,
            height=height,
            preserveAspectRatio=True,
        )
        canvas.showPage()
    canvas.save()
    for image_path in images:
        image_path.unlink()
    return {
        "kind": "real-derived-ocr-fixture",
        "filename": target.name,
        "path": str(target),
        "sha256": _sha256(target),
        "sizeBytes": target.stat().st_size,
        "sourceSha256": _sha256(source_pdf),
        "sourcePages": [4, 5, 6, 7],
        "dpi": 300,
        "colorMode": "grayscale",
        "textLayer": False,
        "renderer": (version.stderr or version.stdout).strip().splitlines()[0],
    }


def _resolve_renderer(override: Path | None) -> Path | None:
    if override is not None:
        candidate = override.resolve()
        return candidate if candidate.is_file() else None
    discovered = shutil.which("pdftoppm")
    if discovered is None:
        return None
    candidate = Path(discovered).resolve()
    if candidate.suffix.lower() == ".exe":
        return candidate
    for parent in candidate.parents:
        bundled = parent / "native" / "poppler" / "Library" / "bin" / "pdftoppm.exe"
        if bundled.is_file():
            return bundled
    return candidate


def _verify_runtime(
    output: Path, derived: dict[str, Any] | None
) -> dict[str, Any]:
    from swarmcore_application.document_processing import ParserRegistry
    from swarmcore_application.document_processing.service import _detect_media_type
    from swarmcore_worker_control.document_processing import _processing_groups

    registry = ParserRegistry()
    values: dict[str, Any] = {}
    for source in SOURCES:
        path = output / source["filename"]
        content = path.read_bytes()
        detected = _detect_media_type(
            content, path.name, "application/octet-stream"
        )
        parser_ref, parsed = registry.parse(
            filename=path.name,
            media_type=detected,
            content=content,
        )
        values[source["key"]] = {
            "detectedMediaType": detected,
            "parserRef": parser_ref,
            "pageCount": len(parsed.pages),
            "headingCount": parsed.embedded_metadata.get("headingCount", 0),
            "paragraphCount": parsed.embedded_metadata.get("paragraphCount", 0),
            "tableCount": len(parsed.tables),
            "needsOcr": parsed.needs_ocr,
        }
    odt = values["official-odt"]
    if odt["detectedMediaType"] != "application/vnd.oasis.opendocument.text":
        raise ValueError("ODT content detection acceptance failed")
    if odt["headingCount"] < 80 or odt["tableCount"] < 20:
        raise ValueError("ODT native structure acceptance failed")
    pdf_path = output / "dos-4-call-off-contract.pdf"
    groups, page_count, _ = _processing_groups(
        pdf_path.read_bytes(), "application/pdf", pdf_path.name
    )
    if page_count != 68 or len(groups) != 7:
        raise ValueError("large PDF segmentation acceptance failed")
    if derived is not None:
        scan_path = Path(str(derived["path"]))
        scan_content = scan_path.read_bytes()
        _, scan = registry.parse(
            filename=scan_path.name,
            media_type="application/pdf",
            content=scan_content,
        )
        if len(scan.pages) != 4 or not scan.needs_ocr:
            raise ValueError("derived OCR routing acceptance failed")
        values["derived-ocr"] = {
            "pageCount": len(scan.pages),
            "needsOcr": scan.needs_ocr,
            "pageRoutes": scan.layout.get("pageRoutes", []),
        }
    values["largePdfPlan"] = {
        "pageCount": page_count,
        "groupCount": len(groups),
        "maxParallelism": 4,
        "groups": groups,
    }
    return values


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
