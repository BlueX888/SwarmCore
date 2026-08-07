"""Add role requirements to human approvals.

Revision ID: 0025_approval_required_roles
Revises: 0024_business_work_identity
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0025_approval_required_roles"
down_revision: str | None = "0024_business_work_identity"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "approval_requests",
        sa.Column(
            "required_roles",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("approval_requests", "required_roles")
