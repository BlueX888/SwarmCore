from pathlib import Path


def test_m3_effect_journal_migration_is_tenant_isolated() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0004_m3_tool_effects.py"
    ).read_text(encoding="utf-8")

    assert 'down_revision: str | None = "0003_m2c_strategy_editor_state"' in migration
    assert 'ALTER TABLE "tool_effects" ENABLE ROW LEVEL SECURITY' in migration
    assert 'ALTER TABLE "tool_effects" FORCE ROW LEVEL SECURITY' in migration
    assert "current_setting('app.tenant_id'" in migration

    lease_migration = Path(
        "packages/persistence/alembic/versions/0005_m3_tool_effect_lease.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0004_m3_tool_effects"' in lease_migration
    assert "lease_expires_at timestamptz" in lease_migration
