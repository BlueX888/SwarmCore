"""Add ordered document processing events.

Revision ID: 0020_doc_processing_events
Revises: 0019_procurement_supplier_risk
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "0020_doc_processing_events"
down_revision: str | None = "0019_procurement_supplier_risk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    database = inspect(op.get_bind())
    existing_columns = {
        column["name"]
        for column in database.get_columns("document_processing_runs")
    }
    if "next_event_seq" not in existing_columns:
        op.add_column(
            "document_processing_runs",
            sa.Column(
                "next_event_seq",
                sa.BigInteger(),
                nullable=False,
                server_default=sa.text("1"),
            ),
        )
    if not database.has_table("document_processing_events"):
        op.create_table(
            "document_processing_events",
            sa.Column(
                "project_id", postgresql.UUID(as_uuid=True), nullable=False
            ),
            sa.Column(
                "processing_run_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "business_document_version_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column("event_seq", sa.BigInteger(), nullable=False),
            sa.Column("type", sa.String(length=128), nullable=False),
            sa.Column("stage", sa.String(length=64), nullable=False),
            sa.Column(
                "payload",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column("input_hash", sa.String(length=64), nullable=True),
            sa.Column("output_hash", sa.String(length=64), nullable=True),
            sa.Column("tool_ref", sa.String(length=256), nullable=True),
            sa.Column("actor_id", sa.String(length=256), nullable=False),
            sa.Column("trace_id", sa.String(length=64), nullable=True),
            sa.Column(
                "occurred_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "tenant_id", postgresql.UUID(as_uuid=True), nullable=False
            ),
            sa.ForeignKeyConstraint(
                ["tenant_id", "project_id", "processing_run_id"],
                [
                    "document_processing_runs.tenant_id",
                    "document_processing_runs.project_id",
                    "document_processing_runs.id",
                ],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "processing_run_id",
                "event_seq",
                name="uq_document_processing_event_sequence",
            ),
            sa.UniqueConstraint(
                "tenant_id",
                "id",
                name="uq_document_processing_events_tenant_id",
            ),
        )
    index_names = {
        index["name"]
        for index in inspect(op.get_bind()).get_indexes(
            "document_processing_events"
        )
    }
    if "ix_document_processing_events_run_sequence" not in index_names:
        op.create_index(
            "ix_document_processing_events_run_sequence",
            "document_processing_events",
            ["processing_run_id", "event_seq"],
            unique=False,
        )
    op.execute("ALTER TABLE document_processing_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE document_processing_events FORCE ROW LEVEL SECURITY")
    op.execute(
        "DROP POLICY IF EXISTS document_processing_events_tenant_isolation "
        "ON document_processing_events"
    )
    op.execute(
        """
        CREATE POLICY document_processing_events_tenant_isolation
        ON document_processing_events
        USING (
          tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
          AND project_id = NULLIF(current_setting('app.project_id', true), '')::uuid
        )
        WITH CHECK (
          tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
          AND project_id = NULLIF(current_setting('app.project_id', true), '')::uuid
        )
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS document_processing_events_tenant_isolation "
        "ON document_processing_events"
    )
    op.drop_index(
        "ix_document_processing_events_run_sequence",
        table_name="document_processing_events",
    )
    op.drop_table("document_processing_events")
    op.drop_column("document_processing_runs", "next_event_seq")
