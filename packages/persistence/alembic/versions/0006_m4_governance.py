"""Add M4 governance, security and production records."""

from collections.abc import Sequence

from alembic import op
from swarmcore_persistence.models import Base

revision: str = "0006_m4_governance"
down_revision: str | None = "0005_m3_tool_effect_lease"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "artifacts",
    "artifact_download_grants",
    "audit_logs",
    "model_usage_records",
    "webhook_endpoints",
    "webhook_deliveries",
    "sandbox_executions",
    "compensation_records",
)


def upgrade() -> None:
    op.execute(
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS "
        "initiated_by varchar(256) NOT NULL DEFAULT 'system'"
    )
    op.execute(
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS "
        "submitted_scopes jsonb NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute(
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS "
        "auth_context_hash varchar(64) NOT NULL DEFAULT 'unknown'"
    )
    op.execute(
        "ALTER TABLE runs ADD COLUMN IF NOT EXISTS "
        "policy_revision varchar(128) NOT NULL DEFAULT 'unknown'"
    )
    op.execute(
        "ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS task_execution_id varchar(128)"
    )
    op.execute("ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS tool_ref varchar(512)")
    op.execute(
        "ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS tool_version varchar(128)"
    )
    op.execute(
        "ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS canonical_input_hash varchar(64)"
    )
    op.execute(
        "ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS policy_revision varchar(128)"
    )
    op.execute(
        "ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS expires_at timestamptz"
    )
    op.execute(
        "ALTER TABLE approval_requests ADD COLUMN IF NOT EXISTS "
        "requires_distinct_approver boolean NOT NULL DEFAULT false"
    )
    for name in _TABLES:
        Base.metadata.tables[name].create(bind=op.get_bind(), checkfirst=True)
        op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON "{name}"')
        op.execute(
            f'''CREATE POLICY tenant_isolation ON "{name}"
                USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)'''
        )
    op.execute(
        """CREATE OR REPLACE FUNCTION reject_audit_mutation() RETURNS trigger AS $$
           BEGIN RAISE EXCEPTION 'audit logs are append-only'; END; $$ LANGUAGE plpgsql"""
    )
    op.execute(
        """CREATE TRIGGER audit_logs_append_only BEFORE UPDATE OR DELETE ON audit_logs
           FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()"""
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS reject_audit_mutation()")
    for name in reversed(_TABLES):
        op.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')
    for column in (
        "requires_distinct_approver",
        "expires_at",
        "policy_revision",
        "canonical_input_hash",
        "tool_version",
        "tool_ref",
        "task_execution_id",
    ):
        op.drop_column("approval_requests", column)
    for column in ("policy_revision", "auth_context_hash", "submitted_scopes", "initiated_by"):
        op.drop_column("runs", column)
