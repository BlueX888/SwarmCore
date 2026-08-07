"""Add stable product business-work identity to work items.

Revision ID: 0024_business_work_identity
Revises: 0023_business_work_read_indexes
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0024_business_work_identity"
down_revision: str | None = "0023_business_work_read_indexes"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "work_items",
        sa.Column("business_work_key", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_work_items_project_business_work",
        "work_items",
        ["project_id", "business_work_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_work_items_project_business_work", table_name="work_items")
    op.drop_column("work_items", "business_work_key")
