"""Add immutable scheduling-calibration evidence and decision records."""

from collections.abc import Sequence

from alembic import op
from swarmcore_persistence.models import Base

revision: str = "0018_swarm_calibration"
down_revision: str | None = "0017_contract_performance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "calibration_evidence_snapshots",
    "calibration_route_decisions",
    "calibration_quality_evaluations",
    "calibration_fallback_records",
)


def upgrade() -> None:
    bind = op.get_bind()
    for name in _TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)
        op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
        _create_rls_policy(name)
        op.execute(
            f'CREATE TRIGGER "{name}_immutable" BEFORE UPDATE OR DELETE ON "{name}" '
            "FOR EACH ROW EXECUTE FUNCTION swarmcore_reject_immutable_update()"
        )


def downgrade() -> None:
    for name in reversed(_TABLES):
        op.execute(f'DROP TRIGGER IF EXISTS "{name}_immutable" ON "{name}"')
        op.execute(f'DROP TABLE IF EXISTS "{name}"')


def _create_rls_policy(name: str) -> None:
    scope = (
        "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
        " AND project_id = NULLIF(current_setting('app.project_id', true), '')::uuid"
    )
    policy = f"{name}_isolation"
    op.execute(f'DROP POLICY IF EXISTS "{policy}" ON "{name}"')
    op.execute(f'CREATE POLICY "{policy}" ON "{name}" USING ({scope}) WITH CHECK ({scope})')
