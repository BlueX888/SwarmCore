from pathlib import Path


def test_document_intelligence_migration_is_scoped_immutable_and_idempotent() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0009_document_intelligence.py"
    ).read_text(encoding="utf-8")
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "app.tenant_id" in migration and "app.project_id" in migration
    assert "document_extractions_immutable" in migration
    assert "0008_business_workbench" in migration
