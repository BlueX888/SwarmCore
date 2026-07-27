"""Add persistent invoice-assurance batch queues."""

from collections.abc import Sequence

from alembic import op
from swarmcore_persistence.models import Base

revision: str = "0016_invoice_assurance_p1_p2"
down_revision: str | None = "0015_doc_ver_proc_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("invoice_assurance_batches", "invoice_assurance_batch_items")


def upgrade() -> None:
    bind = op.get_bind()
    for name in _TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)
        op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
        _create_rls_policy(name)


def downgrade() -> None:
    for name in reversed(_TABLES):
        op.execute(f'DROP TABLE IF EXISTS "{name}"')


def _create_rls_policy(name: str) -> None:
    scope = (
        "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
        " AND project_id = NULLIF(current_setting('app.project_id', true), '')::uuid"
    )
    policy = f"{name}_isolation"
    op.execute(f'DROP POLICY IF EXISTS "{policy}" ON "{name}"')
    op.execute(f'CREATE POLICY "{policy}" ON "{name}" USING ({scope}) WITH CHECK ({scope})')
