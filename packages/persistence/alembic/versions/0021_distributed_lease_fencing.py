"""Add fencing generations to distributed leases.

Revision ID: 0021_distributed_lease_fencing
Revises: 0020_doc_processing_events
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0021_distributed_lease_fencing"
down_revision: str | None = "0020_doc_processing_events"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "outbox_events",
        sa.Column("lock_generation", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tool_effects",
        sa.Column("lease_owner", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "tool_effects",
        sa.Column("lease_generation", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("tool_effects", "lease_generation")
    op.drop_column("tool_effects", "lease_owner")
    op.drop_column("outbox_events", "lock_generation")
