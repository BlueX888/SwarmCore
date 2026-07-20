"""Add immutable, idempotent document intelligence results."""

from collections.abc import Sequence

from alembic import op
from swarmcore_persistence.models import Base

revision: str = "0009_document_intelligence"
down_revision: str | None = "0008_business_workbench"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_blob_objects_scope_id'
            ) THEN
                ALTER TABLE blob_objects ADD CONSTRAINT uq_blob_objects_scope_id
                UNIQUE (tenant_id, project_id, id);
            END IF;
        END $$
        """
    )
    Base.metadata.tables["document_extractions"].create(bind=op.get_bind(), checkfirst=True)
    op.execute('ALTER TABLE "document_extractions" ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE "document_extractions" FORCE ROW LEVEL SECURITY')
    tenant = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    project = "project_id = NULLIF(current_setting('app.project_id', true), '')::uuid"
    op.execute(
        'CREATE POLICY "document_extractions_isolation" ON "document_extractions" '
        f"USING ({tenant} AND {project}) WITH CHECK ({tenant} AND {project})"
    )
    op.execute(
        'CREATE TRIGGER "document_extractions_immutable" '
        'BEFORE UPDATE OR DELETE ON "document_extractions" '
        "FOR EACH ROW EXECUTE FUNCTION swarmcore_reject_immutable_update()"
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS "document_extractions" CASCADE')
    op.execute("ALTER TABLE blob_objects DROP CONSTRAINT IF EXISTS uq_blob_objects_scope_id")
