"""Persist Strategy Canvas layout independently from SwarmSpec."""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_m2c_strategy_editor_state"
down_revision: str | None = "0002_phase2a_human_control"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE strategy_drafts ADD COLUMN IF NOT EXISTS "
        "editor_state jsonb NOT NULL DEFAULT '{}'::jsonb"
    )
    op.execute("ALTER TABLE strategy_drafts ALTER COLUMN editor_state DROP DEFAULT")


def downgrade() -> None:
    op.drop_column("strategy_drafts", "editor_state")
