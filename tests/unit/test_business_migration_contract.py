from pathlib import Path


def test_business_migration_has_rls_and_immutable_versions() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0008_business_workbench.py"
    ).read_text(encoding="utf-8")
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "app.tenant_id" in migration
    assert "app.project_id" in migration
    assert "capability_pack_versions" in migration
    assert "work_item_revisions" in migration
    assert "rule_set_versions" in migration
    assert "swarmcore_reject_immutable_update" in migration
