"""Allow processing_status updates on immutable document versions."""

from collections.abc import Sequence

from alembic import op

revision: str = "0015_doc_ver_proc_status"
down_revision: str | None = "0014_doc_processing_pipeline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FUNCTION = "swarmcore_allow_document_version_processing_update"
_TRIGGER = "business_document_versions_immutable"


def upgrade() -> None:
    op.execute(f'DROP TRIGGER IF EXISTS "{_TRIGGER}" ON "business_document_versions"')
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_FUNCTION}()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'immutable business fact cannot be updated or deleted';
          END IF;
          IF NEW.id IS DISTINCT FROM OLD.id
             OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
             OR NEW.project_id IS DISTINCT FROM OLD.project_id
             OR NEW.business_document_id IS DISTINCT FROM OLD.business_document_id
             OR NEW.blob_id IS DISTINCT FROM OLD.blob_id
             OR NEW.version IS DISTINCT FROM OLD.version
             OR NEW.filename IS DISTINCT FROM OLD.filename
             OR NEW.media_type IS DISTINCT FROM OLD.media_type
             OR NEW.size_bytes IS DISTINCT FROM OLD.size_bytes
             OR NEW.sha256 IS DISTINCT FROM OLD.sha256
             OR NEW.created_by IS DISTINCT FROM OLD.created_by
             OR NEW.created_at IS DISTINCT FROM OLD.created_at
          THEN
            RAISE EXCEPTION 'immutable business fact cannot be updated or deleted';
          END IF;
          RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        f'CREATE TRIGGER "{_TRIGGER}" BEFORE UPDATE OR DELETE ON "business_document_versions" '
        f"FOR EACH ROW EXECUTE FUNCTION {_FUNCTION}()"
    )


def downgrade() -> None:
    op.execute(f'DROP TRIGGER IF EXISTS "{_TRIGGER}" ON "business_document_versions"')
    op.execute(f"DROP FUNCTION IF EXISTS {_FUNCTION}()")
    op.execute(
        f'CREATE TRIGGER "{_TRIGGER}" BEFORE UPDATE OR DELETE ON "business_document_versions" '
        "FOR EACH ROW EXECUTE FUNCTION swarmcore_reject_immutable_update()"
    )
