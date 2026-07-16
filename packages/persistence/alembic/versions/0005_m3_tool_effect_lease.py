"""Add a reclaimable execution lease to the Tool Gateway effect journal."""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_m3_tool_effect_lease"
down_revision: str | None = "0004_m3_tool_effects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE tool_effects ADD COLUMN IF NOT EXISTS "
        "lease_expires_at timestamptz NOT NULL DEFAULT now()"
    )
    op.execute("ALTER TABLE tool_effects ALTER COLUMN lease_expires_at DROP DEFAULT")


def downgrade() -> None:
    op.drop_column("tool_effects", "lease_expires_at")
