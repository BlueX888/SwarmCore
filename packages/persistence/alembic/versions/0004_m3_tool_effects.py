"""Add the tenant-scoped Tool Gateway effect journal."""

from collections.abc import Sequence

from alembic import op
from swarmcore_persistence.models import Base

revision: str = "0004_m3_tool_effects"
down_revision: str | None = "0003_m2c_strategy_editor_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    Base.metadata.tables["tool_effects"].create(bind=op.get_bind(), checkfirst=True)
    op.execute('ALTER TABLE "tool_effects" ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE "tool_effects" FORCE ROW LEVEL SECURITY')
    op.execute('DROP POLICY IF EXISTS tenant_isolation ON "tool_effects"')
    op.execute(
        """CREATE POLICY tenant_isolation ON "tool_effects"
           USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
           WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)"""
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS "tool_effects" CASCADE')
