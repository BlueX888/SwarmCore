from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy import UniqueConstraint
from swarmcore_api import create_app
from swarmcore_api.settings import Settings
from swarmcore_application import DocumentLibraryService
from swarmcore_capability_contract_post_evaluation import MANIFEST
from swarmcore_persistence.models import (
    Base,
    BlobObject,
    BusinessDocument,
    BusinessDocumentVersion,
    DocumentUsageSnapshot,
    Evaluation,
)


def test_document_library_migration_has_scope_rls_and_immutable_facts() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0013_business_document_library.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0012_restore_pack_delete"' in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "app.tenant_id" in migration and "app.project_id" in migration
    assert "business_document_versions" in migration
    assert "document_processing_results" in migration
    assert "document_usage_snapshots" in migration
    assert "swarmcore_reject_immutable_update" in migration


def test_document_library_tables_keep_project_scope_and_version_uniqueness() -> None:
    expected = {
        "business_documents",
        "business_document_versions",
        "document_business_object_links",
        "document_work_bindings",
        "document_processing_results",
        "document_usage_snapshots",
    }
    assert expected <= set(Base.metadata.tables)
    version_constraints = {
        constraint.name
        for constraint in Base.metadata.tables["business_document_versions"].constraints
        if isinstance(constraint, UniqueConstraint)
    }
    snapshot_constraints = {
        constraint.name
        for constraint in Base.metadata.tables["document_usage_snapshots"].constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert "uq_business_document_versions_number" in version_constraints
    assert "uq_document_usage_snapshots_version" in snapshot_constraints
    for table_name in expected:
        columns = Base.metadata.tables[table_name].columns
        assert "tenant_id" in columns
        assert "project_id" in columns


def test_contract_post_evaluation_declares_documents_not_external_resources() -> None:
    spec = MANIFEST["spec"]
    assert spec["documents"] == [{"category": "CONTRACT", "required": True}]
    assert "resources" not in spec
    assert "tool://document/read-versions@1" in spec["tools"]
    assert all("resource/read-bound" not in value for value in spec["tools"])


def test_document_rest_contract_is_present_in_openapi() -> None:
    schema = create_app(Settings()).openapi()
    paths = schema["paths"]
    assert "/v1/projects/{project_id}/documents:initiate" in paths
    assert "/v1/projects/{project_id}/document-uploads/{upload_id}:complete" in paths
    assert "/v1/projects/{project_id}/documents" in paths
    assert "/v1/projects/{project_id}/documents/{document_id}" in paths
    assert (
        "/v1/projects/{project_id}/assessments/{assessment_id}/document-snapshots"
        in paths
    )


@pytest.mark.asyncio
async def test_assessment_snapshot_freezes_blob_version_and_sha256() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    document = BusinessDocument(
        id=uuid4(),
        tenant_id=tenant_id,
        project_id=project_id,
        name="contract.pdf",
        category="CONTRACT",
        tags=[],
        status="AVAILABLE",
        current_version=2,
        created_by="tester",
    )
    blob = BlobObject(
        id=uuid4(),
        tenant_id=tenant_id,
        project_id=project_id,
        object_key="test/document/v2",
        version=2,
        filename="contract.pdf",
        media_type="application/pdf",
        size_bytes=42,
        sha256="a" * 64,
        status="AVAILABLE",
        scan_status="CLEAN",
        retention_until=datetime.now(UTC) + timedelta(days=1),
        metadata_json={},
    )
    version = BusinessDocumentVersion(
        id=uuid4(),
        tenant_id=tenant_id,
        project_id=project_id,
        business_document_id=document.id,
        blob_id=blob.id,
        version=2,
        filename=blob.filename,
        media_type=blob.media_type,
        size_bytes=blob.size_bytes,
        sha256=blob.sha256,
        processing_status="AVAILABLE",
        created_by="tester",
    )
    evaluation = Mock(spec=Evaluation)
    evaluation.id = uuid4()
    evaluation.run_id = uuid4()
    session = AsyncMock()
    session.add = Mock()
    session.scalar.return_value = None

    snapshots = await DocumentLibraryService().freeze_usage(
        session,
        tenant_id=tenant_id,
        project_id=project_id,
        evaluation=evaluation,
        business_work_key="document-integrity",
        documents=[(document, version, blob)],
    )

    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert isinstance(snapshot, DocumentUsageSnapshot)
    assert snapshot.tenant_id == tenant_id
    assert snapshot.project_id == project_id
    assert snapshot.run_id == evaluation.run_id
    assert snapshot.business_document_version_id == version.id
    assert snapshot.blob_id == blob.id
    assert snapshot.document_version == 2
    assert snapshot.sha256 == "a" * 64
    assert snapshot.size_bytes == 42
    session.add.assert_called_once_with(snapshot)
    session.flush.assert_awaited_once()


@pytest.mark.parametrize(
    ("filename", "size_bytes", "sha256"),
    [
        ("../contract.pdf", 1, "a" * 64),
        ("contract.pdf", 0, "a" * 64),
        ("contract.pdf", 1, "not-a-hash"),
    ],
)
def test_document_registration_rejects_invalid_file_identity(
    filename: str, size_bytes: int, sha256: str
) -> None:
    with pytest.raises(ValueError):
        DocumentLibraryService._validate_file(filename, size_bytes, sha256)
