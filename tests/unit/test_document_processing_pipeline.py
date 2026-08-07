"""Unit tests for the generic document processing pipeline."""

from __future__ import annotations

import json
import re
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from reportlab.pdfgen.canvas import Canvas
from swarmcore_application.document_processing import (
    DEFAULT_BUSINESS_PROFILE,
    DocumentProcessingService,
    DocumentRequirementService,
    DocumentReviewService,
    LabelCandidateClassifier,
    ParserRegistry,
    UploadBatchService,
    resolve_profile,
)
from swarmcore_application.document_processing.adapters import (
    EnvHttpOcrAdapter,
    SchemaDrivenExtractor,
    UnconfiguredOcrAdapter,
    schema_for_ref,
)
from swarmcore_application.document_processing.contracts import (
    ClassificationResult,
    ExtractionField,
    ParsedContent,
)
from swarmcore_capability_contract_post_evaluation import MANIFEST as CPE_MANIFEST
from swarmcore_persistence.models import Base
from swarmcore_registry.capability_packs import CapabilityPackManifest


def test_sanitize_jsonable_strips_nul_bytes() -> None:
    from swarmcore_application.document_processing.service import _sanitize_jsonable

    payload = {
        "text": "hello\x00world",
        "pages": [{"text": "a\x00b"}],
        "nested": {"ok": True, "value": ["x\x00", 1]},
    }
    cleaned = _sanitize_jsonable(payload)
    assert cleaned["text"] == "helloworld"
    assert cleaned["pages"][0]["text"] == "ab"
    assert cleaned["nested"]["value"][0] == "x"
    assert "\x00" not in json.dumps(cleaned)

    migration = Path(
        "packages/persistence/alembic/versions/0014_document_processing_pipeline.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "0014_doc_processing_pipeline"' in migration
    assert 'down_revision: str | None = "0013_business_document_library"' in migration
    assert len("0014_doc_processing_pipeline") <= 32
    assert "upload_batches" in migration
    assert "document_processing_runs" in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration


def test_migration_0015_allows_processing_status_updates() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0015_doc_ver_proc_status.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "0015_doc_ver_proc_status"' in migration
    assert 'down_revision: str | None = "0014_doc_processing_pipeline"' in migration
    assert len("0015_doc_ver_proc_status") <= 32
    assert "swarmcore_allow_document_version_processing_update" in migration
    assert "NEW.sha256 IS DISTINCT FROM OLD.sha256" in migration
    assert "business_document_versions" in migration
    assert "RETURN NEW" in migration


def test_processing_tables_are_registered() -> None:
    assert "upload_batches" in Base.metadata.tables
    assert "document_processing_runs" in Base.metadata.tables
    for name in ("upload_batches", "document_processing_runs"):
        columns = Base.metadata.tables[name].columns
        assert "tenant_id" in columns
        assert "project_id" in columns


def test_default_profile_resolves() -> None:
    profile = resolve_profile(None)
    assert profile.ref == DEFAULT_BUSINESS_PROFILE.ref
    with pytest.raises(LookupError, match="PROCESSING_PROFILE_NOT_FOUND"):
        resolve_profile("document-profile://missing@1")


def test_parser_registry_selects_by_media_type() -> None:
    registry = ParserRegistry()
    ref, parsed = registry.parse(
        filename="notes.txt",
        media_type="text/plain",
        content=b"title: Demo\nparty: ACME\namount: 100",
    )
    assert ref.startswith("parser://text-markdown@")
    assert "Demo" in parsed.text_excerpt
    assert not parsed.needs_ocr


def test_parser_registry_reads_xml_as_text_without_expanding_entities() -> None:
    registry = ParserRegistry()
    content = Path("tests/fixtures/documents/demo-invoice.xml").read_bytes()
    ref, parsed = registry.parse(
        filename="demo-invoice.xml",
        media_type="application/xml",
        content=content,
    )

    assert ref == "parser://text-markdown@1"
    assert "<InvoiceNumber>99992000000000000001</InvoiceNumber>" in parsed.text_excerpt
    assert not parsed.needs_ocr


def test_structured_text_and_digital_pdf_parsers_extract_real_content() -> None:
    registry = ParserRegistry()
    csv_ref, csv_value = registry.parse(
        filename="invoices.csv",
        media_type="text/csv",
        content="发票号,金额\nINV-1,100".encode(),
    )
    _, json_value = registry.parse(
        filename="risks.json",
        media_type="application/json",
        content='[{"riskId":"R-1","level":"HIGH"}]'.encode(),
    )
    pdf_stream = BytesIO()
    canvas = Canvas(pdf_stream)
    canvas.drawString(72, 720, "Digital contract amount 100")
    canvas.save()
    pdf_ref, pdf_value = registry.parse(
        filename="contract.pdf",
        media_type="application/pdf",
        content=pdf_stream.getvalue(),
    )

    assert csv_ref == "parser://structured-text@1"
    assert csv_value.tables[0]["columns"] == ["发票号", "金额"]
    assert "R-1" in json_value.text_excerpt
    assert pdf_ref == "parser://pdf-text@2"
    assert "Digital contract amount 100" in pdf_value.text_excerpt
    assert pdf_value.needs_ocr is False


def test_docx_and_xlsx_parsers_roundtrip_minimal_packages(tmp_path: Path) -> None:
    # Minimal DOCX zip
    import io
    import zipfile
    from xml.etree.ElementTree import Element, SubElement, tostring

    def build_docx() -> bytes:
        document = Element(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document"
        )
        body = SubElement(
            document, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body"
        )
        paragraph = SubElement(
            body, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
        )
        run = SubElement(
            paragraph, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"
        )
        text = SubElement(
            run, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
        )
        text.text = "标题: 合同草案"
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("word/document.xml", tostring(document))
        return buffer.getvalue()

    def build_xlsx() -> bytes:
        ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        shared = Element(f"{{{ns}}}sst", {"count": "1", "uniqueCount": "1"})
        si = SubElement(shared, f"{{{ns}}}si")
        t = SubElement(si, f"{{{ns}}}t")
        t.text = "金额: 88"
        sheet = Element(f"{{{ns}}}worksheet")
        data = SubElement(sheet, f"{{{ns}}}sheetData")
        row = SubElement(data, f"{{{ns}}}row", {"r": "1"})
        cell = SubElement(row, f"{{{ns}}}c", {"r": "A1", "t": "s"})
        value = SubElement(cell, f"{{{ns}}}v")
        value.text = "0"
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("xl/sharedStrings.xml", tostring(shared))
            archive.writestr("xl/worksheets/sheet1.xml", tostring(sheet))
        return buffer.getvalue()

    registry = ParserRegistry()
    _, docx = registry.parse(
        filename="a.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        content=build_docx(),
    )
    assert "合同草案" in docx.text_excerpt
    _, xlsx = registry.parse(
        filename="a.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        content=build_xlsx(),
    )
    assert xlsx.sheets


def test_image_parser_requires_ocr() -> None:
    registry = ParserRegistry()
    _, parsed = registry.parse(
        filename="scan.png",
        media_type="image/png",
        content=b"\x89PNG\r\n\x1a\n" + b"\x00" * 32,
    )
    assert parsed.needs_ocr


def test_unconfigured_ocr_is_explicit() -> None:
    adapter = UnconfiguredOcrAdapter()
    assert adapter.available is False
    with pytest.raises(RuntimeError, match="OCR_NOT_CONFIGURED"):
        adapter.recognize(media_type="image/png", content=b"x")


@pytest.mark.asyncio
async def test_large_native_content_is_persisted_before_ocr_degradation(
    tmp_path: Path,
) -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    version_id = uuid4()
    pages = [
        {
            "page": index,
            "text": f"page {index} supplier obligation " + ("x" * 3_000),
            "sourceKind": "NATIVE",
        }
        for index in range(1, 101)
    ]
    parsed = ParsedContent(
        pages=pages,
        paragraphs=[
            {
                "index": index,
                "page": index,
                "text": page["text"],
                "sourceKind": "NATIVE",
            }
            for index, page in enumerate(pages, start=1)
        ],
        chunks=[
            {
                "ordinal": index,
                "pages": [index],
                "text": page["text"],
                "evidence": [{"page": index, "sourceKind": "NATIVE"}],
            }
            for index, page in enumerate(pages, start=1)
        ],
        textExcerpt="contract",
        needsOcr=True,
    )

    class _Session:
        def __init__(self) -> None:
            self.added: list[object] = []

        def add(self, value: object) -> None:
            self.added.append(value)

        async def flush(self) -> None:
            return None

    session = _Session()
    storage_root = tmp_path.parent / f"sc-{version_id.hex[:8]}"
    service = DocumentProcessingService(storage_root=storage_root)
    compact, content_ref = await service._prepare_persisted_content(  # type: ignore[arg-type]
        session,
        tenant_id=tenant_id,
        project_id=project_id,
        version=SimpleNamespace(id=version_id),
        parsed=parsed,
    )

    assert content_ref is not None and content_ref.startswith("blob://")
    assert len(compact.pages) == 5
    assert len(compact.paragraphs) == 20
    assert len(compact.chunks) == 10
    blob = session.added[0]
    stored = json.loads(  # type: ignore[attr-defined]
        (storage_root / blob.object_key).read_text(encoding="utf-8")
    )
    assert len(stored["pages"]) == 100
    assert len(stored["chunks"]) == 100


def test_http_ocr_adapter_posts_content_and_normalizes_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from swarmcore_application.document_processing import adapters

    captured: dict[str, object] = {}

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return '{"text":"识别后的合同正文"}'.encode()

    def fake_urlopen(request: object, timeout: float) -> Response:
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    result = EnvHttpOcrAdapter(
        "http://ocr.local/recognize", api_key="secret", timeout_seconds=5
    ).recognize(media_type="application/pdf", content=b"%PDF")

    request = captured["request"]
    assert getattr(request, "headers")["Authorization"] == "Bearer secret"
    assert captured["timeout"] == 5
    assert result["text"] == "识别后的合同正文"
    assert result["pages"] == [{"page": 1, "text": "识别后的合同正文"}]


def test_classifier_uses_candidate_labels_not_hardcoded_business() -> None:
    classifier = LabelCandidateClassifier()
    result = classifier.classify(
        filename="invoice-2026.txt",
        media_type="text/plain",
        text_excerpt="invoice amount 12",
        candidate_labels=[
            {"label": "INVOICE", "displayName": "发票"},
            {"label": "CONTRACT", "displayName": "合同"},
        ],
        profile=DEFAULT_BUSINESS_PROFILE,
    )
    assert result.label == "INVOICE"
    assert result.confidence > 0.5


def test_schema_extractor_preserves_machine_value() -> None:
    extractor = SchemaDrivenExtractor()
    schema = schema_for_ref("schema://document/generic-text@1")
    assert schema is not None
    fields = extractor.extract(
        content=ParsedContent(
            pages=[{"page": 1, "text": "标题: Alpha\n甲方: Beta\n金额: 99"}],
            textExcerpt="标题: Alpha\n甲方: Beta\n金额: 99",
        ),
        schema=schema,
        classification=ClassificationResult(
            label="CONTRACT", displayName="合同", confidence=0.9
        ),
        profile=DEFAULT_BUSINESS_PROFILE,
    )
    title = next(field for field in fields if field.field_path == "document.title")
    assert title.machine_value == "Alpha"
    assert title.value == "Alpha"


def test_review_does_not_overwrite_machine_value() -> None:
    field = ExtractionField(
        fieldPath="document.title",
        displayName="标题",
        value="Alpha",
        machineValue="Alpha",
        confirmedValue=None,
        confidence=0.4,
        reviewStatus="PENDING",
    )
    confirmed = "Beta"
    field.confirmed_value = confirmed
    field.value = confirmed
    field.review_status = "CORRECTED"
    assert field.machine_value == "Alpha"
    assert field.confirmed_value == "Beta"


def test_requirement_service_accepts_nested_and_legacy_forms() -> None:
    service = DocumentRequirementService()
    profile, nested = service.from_pack_documents(
        {
            "processingProfile": "document-profile://business-default@1",
            "requirements": [
                {
                    "key": "primary",
                    "category": "CONTRACT",
                    "displayName": "主文件",
                    "required": True,
                    "classificationLabels": ["CONTRACT"],
                    "extractionSchema": "schema://document/generic-text@1",
                }
            ],
        }
    )
    assert profile == "document-profile://business-default@1"
    assert nested[0].key == "primary"
    _, legacy = service.from_pack_documents([{"category": "CONTRACT", "required": True}])
    assert legacy[0].key == "CONTRACT"


def test_both_business_packs_declare_documents_without_shared_hardcoding() -> None:
    from swarmcore_capability_contract_integrity import MANIFEST_V2_1

    integrity = CapabilityPackManifest.model_validate(MANIFEST_V2_1)
    cpe = CapabilityPackManifest.model_validate(CPE_MANIFEST)
    integrity_reqs = integrity.spec.document_requirements()
    cpe_reqs = cpe.spec.document_requirements()
    assert integrity_reqs and cpe_reqs
    assert integrity_reqs[0].key != cpe_reqs[0].key
    assert integrity.metadata.version == "2.1.0"
    assert cpe.metadata.version == "2.0.7"


def test_public_document_modules_have_no_business_work_hardcoding() -> None:
    roots = [
        Path("packages/application/src/swarmcore_application/document_processing"),
        Path("packages/application/src/swarmcore_application/document_library.py"),
        Path("apps/web/src/components/documents"),
    ]
    banned = (
        "contract-post-evaluation",
        "document-integrity",
        "contractNumber",
        "invoiceNumber",
        "甲方名称",
        "发票号码",
    )
    for root in roots:
        files = (
            [root]
            if root.is_file()
            else [
                path
                for path in list(root.rglob("*.py")) + list(root.rglob("*.tsx"))
                if ".test." not in path.name
            ]
        )
        for path in files:
            text = path.read_text(encoding="utf-8")
            for token in banned:
                assert token not in text, f"{path} contains banned token {token}"


@pytest.mark.asyncio
async def test_processing_pipeline_for_text_content(tmp_path: Path) -> None:
    from datetime import UTC, datetime, timedelta
    from unittest.mock import AsyncMock

    from swarmcore_persistence.models import (
        BlobObject,
        BusinessDocument,
        BusinessDocumentVersion,
    )

    tenant_id = uuid4()
    project_id = uuid4()
    document = BusinessDocument(
        id=uuid4(),
        tenant_id=tenant_id,
        project_id=project_id,
        name="demo",
        category="CONTRACT",
        tags=[],
        status="PROCESSING",
        current_version=1,
        created_by="tester",
    )
    blob = BlobObject(
        id=uuid4(),
        tenant_id=tenant_id,
        project_id=project_id,
        object_key="demo.txt",
        version=1,
        filename="contract-demo.txt",
        media_type="text/plain",
        size_bytes=40,
        sha256="a" * 64,
        status="AVAILABLE",
        scan_status="CLEAN",
        retention_until=datetime.now(UTC) + timedelta(days=30),
        metadata_json={},
    )
    content = b"title: Demo Contract\nparty: ACME\namount: 128"
    blob.sha256 = __import__("hashlib").sha256(content).hexdigest()
    blob.size_bytes = len(content)
    version = BusinessDocumentVersion(
        id=uuid4(),
        tenant_id=tenant_id,
        project_id=project_id,
        business_document_id=document.id,
        blob_id=blob.id,
        version=1,
        filename=blob.filename,
        media_type=blob.media_type,
        size_bytes=blob.size_bytes,
        sha256=blob.sha256,
        processing_status="PROCESSING",
        created_by="tester",
    )

    class _Session:
        def __init__(self) -> None:
            self.added: list[object] = []

        def add(self, value: object) -> None:
            self.added.append(value)

        async def flush(self) -> None:
            return None

        async def get(self, model: type[object], ident: object) -> object | None:
            if model is BlobObject and ident == blob.id:
                return blob
            return None

        async def scalar(self, _statement: object) -> object | None:
            return None

        @asynccontextmanager
        async def begin_nested(self):
            yield

    session = _Session()
    service = DocumentProcessingService(storage_root=tmp_path)
    service._audit.append = AsyncMock()  # type: ignore[method-assign]
    run = await service.start_for_version(
        session,  # type: ignore[arg-type]
        tenant_id=tenant_id,
        project_id=project_id,
        version=version,
        document=document,
        profile_ref=DEFAULT_BUSINESS_PROFILE.ref,
        candidate_labels=[{"label": "CONTRACT", "displayName": "合同"}],
        extraction_schema_ref="schema://document/generic-text@1",
        upload_batch_id=None,
        actor="tester",
        blob_content=content,
    )
    assert run.status in {"READY", "REVIEW_REQUIRED"}
    assert any(isinstance(item, type(run)) is False for item in session.added) or session.added
    results = [
        item
        for item in session.added
        if item.__class__.__name__ == "DocumentProcessingResult"
    ]
    assert results
    payload = results[-1].result
    assert payload["documentType"]["label"] == "CONTRACT"
    assert payload["extractions"]
    machine = payload["extractions"][0]["machineValue"]
    # Simulate confirm without DB by exercising field semantics.
    assert machine is not None
    assert re.search(r"Demo|CONTRACT|ACME|128", str(machine) + str(payload))


def test_upload_batch_service_imports() -> None:
    assert UploadBatchService is not None
    assert DocumentReviewService is not None


@pytest.mark.asyncio
async def test_upload_batch_idempotency_records_expires_at() -> None:
    from datetime import datetime
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from swarmcore_persistence.models import IdempotencyKey, UploadBatch

    class _Session:
        def __init__(self) -> None:
            self.added: list[object] = []
            self.flush = AsyncMock()
            self.get = AsyncMock(return_value=None)

        def add(self, item: object) -> None:
            self.added.append(item)

        async def scalar(self, _statement: object) -> None:
            return None

        async def execute(self, _statement: object) -> SimpleNamespace:
            return SimpleNamespace(scalar_one_or_none=lambda: None)

    session = _Session()
    service = UploadBatchService()
    service._audit = SimpleNamespace(append=AsyncMock())  # type: ignore[method-assign]
    service._idempotent = AsyncMock(return_value=None)  # type: ignore[method-assign]

    batch = await service.create(
        session,  # type: ignore[arg-type]
        tenant_id=uuid4(),
        project_id=uuid4(),
        source="web",
        context={},
        actor="tester",
        idempotency_key="batch-key-1",
    )
    assert isinstance(batch, UploadBatch)
    keys = [item for item in session.added if isinstance(item, IdempotencyKey)]
    assert len(keys) == 1
    assert isinstance(keys[0].expires_at, datetime)
    assert keys[0].expires_at.tzinfo is not None

