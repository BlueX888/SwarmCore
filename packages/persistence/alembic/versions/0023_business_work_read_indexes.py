"""add business work read indexes

Revision ID: 0023_business_work_read_indexes
Revises: 0022_reconciler_claims
"""

from __future__ import annotations

from alembic import op

revision: str = "0023_business_work_read_indexes"
down_revision: str | None = "0022_reconciler_claims"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_index(
        "ix_runs_scope_strategy_created",
        "runs",
        ["tenant_id", "project_id", "strategy_version_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_runs_scope_strategy_created", table_name="runs")
