from pathlib import Path

from swarmcore_persistence.models import Base


def test_calibration_tables_are_scoped_and_immutable() -> None:
    expected = {
        "calibration_evidence_snapshots",
        "calibration_route_decisions",
        "calibration_quality_evaluations",
        "calibration_fallback_records",
    }
    assert expected.issubset(Base.metadata.tables)

    migration = Path(
        "packages/persistence/alembic/versions/0018_swarm_calibration.py"
    ).read_text(encoding="utf-8")
    for table in expected:
        assert table in migration
    assert '{name}_immutable' in migration
    assert '{name}_isolation' in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
