from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_application import DocumentLibraryService
from swarmcore_persistence import Database, tenant_transaction
from swarmcore_persistence.models import BusinessDocumentVersion


@pytest.mark.asyncio
async def test_document_library_enforces_scope_and_immutable_versions() -> None:
    database_url = os.getenv("SWARMCORE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("SWARMCORE_TEST_DATABASE_URL is not configured")
    tenant_id, other_tenant_id = uuid4(), uuid4()
    project_id, other_project_id = uuid4(), uuid4()
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO tenants (id, name, status, created_at, updated_at) "
                "VALUES (:tenant, :name, 'ACTIVE', now(), now()), "
                "(:other_tenant, :other_name, 'ACTIVE', now(), now())"
            ),
            {
                "tenant": tenant_id,
                "name": f"documents-{tenant_id}",
                "other_tenant": other_tenant_id,
                "other_name": f"documents-{other_tenant_id}",
            },
        )
        for tenant, project, name in (
            (tenant_id, project_id, "documents"),
            (other_tenant_id, other_project_id, "other-documents"),
        ):
            await connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": str(tenant)},
            )
            await connection.execute(
                text(
                    "INSERT INTO projects "
                    "(id, tenant_id, name, settings, created_at, updated_at) "
                    "VALUES (:project, :tenant, :name, '{}', now(), now())"
                ),
                {"project": project, "tenant": tenant, "name": name},
            )
    await engine.dispose()

    database = Database(database_url)
    documents = DocumentLibraryService()
    digest = "a" * 64
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        document, blob, upload_id, number = await documents.initiate(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            name="采购合同",
            category="CONTRACT",
            tags=["采购"],
            filename="contract.pdf",
            media_type="application/pdf",
            size_bytes=42,
            sha256=digest,
            business_object_ids=[],
            business_work_keys=["contract-post-evaluation", "document-integrity"],
            retention_days=30,
            idempotency_key="document-integration-initiate",
            actor="integration",
        )
        blob.status = "AVAILABLE"
        blob.scan_status = "CLEAN"
        completed, version = await documents.complete(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            upload_id=upload_id,
            sha256=digest,
            idempotency_key="document-integration-complete",
            actor="integration",
        )
        assert completed.id == document.id
        assert number == version.version == 1
        assert version.blob_id == blob.id
        assert version.sha256 == digest
        assert version.size_bytes == 42
        version_id = version.id

    async with tenant_transaction(
        database.sessions, tenant_id=other_tenant_id, project_id=other_project_id
    ) as session:
        assert (
            await documents.list_documents(
                session,
                tenant_id=other_tenant_id,
                project_id=other_project_id,
            )
            == []
        )

    with pytest.raises(DBAPIError):
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            await session.execute(
                update(BusinessDocumentVersion)
                .where(BusinessDocumentVersion.id == version_id)
                .values(sha256="b" * 64)
            )
    await database.dispose()
