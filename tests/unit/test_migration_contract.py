from pathlib import Path


def test_initial_migration_enables_rls_and_version_immutability() -> None:
    migration = Path("packages/persistence/alembic/versions/0001_phase1_core.py").read_text(
        encoding="utf-8"
    )
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "current_setting('app.tenant_id'" in migration
    assert "strategy_versions_immutable" in migration
