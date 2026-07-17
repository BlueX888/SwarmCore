"""Add tenant and project scoped saved configurations."""

from collections.abc import Sequence

from alembic import op
from swarmcore_persistence.models import Base

revision: str = "0007_project_configurations"
down_revision: str | None = "0006_m4_governance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    name = "project_configurations"
    Base.metadata.tables[name].create(bind=op.get_bind(), checkfirst=True)
    op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
    op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
    op.execute(f'DROP POLICY IF EXISTS project_configuration_isolation ON "{name}"')
    op.execute(
        f'''CREATE POLICY project_configuration_isolation ON "{name}"
            USING (
                tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
                AND project_id = NULLIF(current_setting('app.project_id', true), '')::uuid
            )
            WITH CHECK (
                tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
                AND project_id = NULLIF(current_setting('app.project_id', true), '')::uuid
            )'''
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS "project_configurations" CASCADE')
