"""Restore controlled deletion for unused capability pack versions."""

from collections.abc import Sequence

from alembic import op

revision: str = "0012_restore_pack_delete"
down_revision: str | None = "0011_business_context_resources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION swarmcore_reject_immutable_update()
        RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE'
               AND TG_TABLE_NAME = 'capability_pack_versions'
               AND current_setting('app.allow_capability_pack_version_delete', true) = 'on'
            THEN
                RETURN OLD;
            END IF;
            RAISE EXCEPTION 'immutable business fact cannot be updated or deleted';
        END;
        $$ LANGUAGE plpgsql
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION swarmcore_reject_immutable_update()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'immutable business fact cannot be updated or deleted';
        END;
        $$ LANGUAGE plpgsql
        """
    )
