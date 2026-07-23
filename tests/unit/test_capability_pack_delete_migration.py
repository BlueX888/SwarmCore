from pathlib import Path


def test_capability_pack_delete_migration_allows_controlled_delete() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0010_pack_version_delete.py"
    ).read_text(encoding="utf-8")
    assert "app.allow_capability_pack_version_delete" in migration
    assert "capability_pack_versions" in migration
    assert "swarmcore_reject_immutable_update" in migration


def test_latest_migration_restores_pack_delete_after_business_context_triggers() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0012_restore_pack_version_delete_guard.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "0012_restore_pack_delete"' in migration
    assert 'down_revision: str | None = "0011_business_context_resources"' in migration
    assert "app.allow_capability_pack_version_delete" in migration
    assert "TG_TABLE_NAME = 'capability_pack_versions'" in migration
    assert "RETURN OLD" in migration
    assert "immutable business fact cannot be updated or deleted" in migration
