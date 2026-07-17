"""Add capability packs, business workbench, rules, findings, and reports."""

from collections.abc import Sequence

from alembic import op
from swarmcore_persistence.models import Base

revision: str = "0008_business_workbench"
down_revision: str | None = "0007_project_configurations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "capability_packs",
    "capability_pack_versions",
    "project_capability_bindings",
    "work_items",
    "work_item_revisions",
    "blob_objects",
    "work_item_attachments",
    "rule_sets",
    "rule_set_drafts",
    "rule_set_versions",
    "evaluations",
    "findings",
    "finding_actions",
    "reports",
)

_TENANT_TABLES = {"capability_packs", "capability_pack_versions"}
_IMMUTABLE_TABLES = {
    "capability_pack_versions",
    "work_item_revisions",
    "rule_set_versions",
}


def upgrade() -> None:
    bind = op.get_bind()
    for name in _TABLES:
        Base.metadata.tables[name].create(bind=bind, checkfirst=True)
        op.execute(f'ALTER TABLE "{name}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{name}" FORCE ROW LEVEL SECURITY')
        _create_rls_policy(name)
    for name in _IMMUTABLE_TABLES:
        _create_immutability_trigger(name)


def downgrade() -> None:
    for name in reversed(_TABLES):
        op.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')
    op.execute("DROP FUNCTION IF EXISTS swarmcore_reject_immutable_update()")


def _create_rls_policy(name: str) -> None:
    tenant = "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
    scope = tenant
    if name not in _TENANT_TABLES:
        scope += (
            " AND project_id = "
            "NULLIF(current_setting('app.project_id', true), '')::uuid"
        )
    policy = f"{name}_isolation"
    op.execute(f'DROP POLICY IF EXISTS "{policy}" ON "{name}"')
    op.execute(
        f'CREATE POLICY "{policy}" ON "{name}" '
        f"USING ({scope}) WITH CHECK ({scope})"
    )


def _create_immutability_trigger(name: str) -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION swarmcore_reject_immutable_update()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'immutable business version cannot be updated or deleted';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    trigger = f"{name}_immutable"
    op.execute(f'DROP TRIGGER IF EXISTS "{trigger}" ON "{name}"')
    op.execute(
        f'CREATE TRIGGER "{trigger}" BEFORE UPDATE OR DELETE ON "{name}" '
        "FOR EACH ROW EXECUTE FUNCTION swarmcore_reject_immutable_update()"
    )
