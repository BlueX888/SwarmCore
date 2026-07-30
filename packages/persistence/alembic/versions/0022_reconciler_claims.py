"""add reconciler scan cursor

Revision ID: 0022_reconciler_claims
Revises: 0021_distributed_lease_fencing
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0022_reconciler_claims"
down_revision: str | None = "0021_distributed_lease_fencing"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_runs_reconciled_at",
        "runs",
        ["reconciled_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_runs_reconciled_at", table_name="runs")
    op.drop_column("runs", "reconciled_at")
