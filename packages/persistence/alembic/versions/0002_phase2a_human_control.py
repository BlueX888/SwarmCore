"""Add durable human-control requests and retry audit fields."""

from collections.abc import Sequence

from alembic import op
from swarmcore_persistence.models import Base

revision: str = "0002_phase2a_human_control"
down_revision: str | None = "0001_phase1_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("ALTER TABLE runs ADD COLUMN IF NOT EXISTS project_id uuid")
    op.execute(
        "ALTER TABLE run_tasks ADD COLUMN IF NOT EXISTS retry_generation integer NOT NULL DEFAULT 0"
    )
    op.execute("ALTER TABLE run_tasks ADD COLUMN IF NOT EXISTS last_retry_command_id uuid")
    op.execute(
        "ALTER TABLE run_commands ADD COLUMN IF NOT EXISTS "
        "actor varchar(256) NOT NULL DEFAULT 'system'"
    )
    op.execute(
        """DO $$ BEGIN
        ALTER TABLE runs ADD CONSTRAINT uq_runs_scope_id UNIQUE (tenant_id, project_id, id);
        EXCEPTION WHEN duplicate_object THEN NULL; END $$"""
    )
    for name in ("approval_requests", "external_input_requests"):
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)
        op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{name}"')
        op.execute(
            f'''CREATE POLICY tenant_isolation ON "{name}"
                USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)'''
        )


def downgrade() -> None:
    for name in ("external_input_requests", "approval_requests"):
        op.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')
    op.execute("ALTER TABLE run_commands DROP COLUMN IF EXISTS actor")
    op.execute("ALTER TABLE run_tasks DROP COLUMN IF EXISTS last_retry_command_id")
    op.execute("ALTER TABLE run_tasks DROP COLUMN IF EXISTS retry_generation")
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS uq_runs_scope_id")
