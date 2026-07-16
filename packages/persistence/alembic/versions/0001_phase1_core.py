"""Create Phase 1 core schema, RLS policies, and immutability guards."""

from collections.abc import Sequence

from alembic import op
from swarmcore_persistence.models import Base

revision: str = "0001_phase1_core"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TENANT_TABLES = (
    "projects",
    "strategies",
    "strategy_drafts",
    "strategy_versions",
    "runs",
    "run_tasks",
    "task_executions",
    "attempts",
    "run_events",
    "outbox_events",
    "run_commands",
    "idempotency_keys",
)


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=False)

    for table in _TENANT_TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
        op.execute(
            f'''CREATE POLICY tenant_isolation ON "{table}"
                USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)'''
        )

    op.execute(
        """
        CREATE FUNCTION reject_strategy_version_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'published strategy versions are immutable';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER strategy_versions_immutable
        BEFORE UPDATE OR DELETE ON strategy_versions
        FOR EACH ROW EXECUTE FUNCTION reject_strategy_version_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS strategy_versions_immutable ON strategy_versions")
    op.execute("DROP FUNCTION IF EXISTS reject_strategy_version_mutation")
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=False)
