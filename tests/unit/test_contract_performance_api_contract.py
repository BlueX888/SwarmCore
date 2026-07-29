from __future__ import annotations

from pathlib import Path

from fastapi.routing import APIRoute
from swarmcore_api.main import create_app
from swarmcore_api.settings import Settings
from swarmcore_persistence.models import Base


def test_contract_performance_rest_routes_are_registered() -> None:
    app = create_app(Settings())
    routes = {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }
    prefix = "/v1/projects/{project_id}/contract-performance/cases"
    assert {
        ("POST", prefix),
        ("POST", f"{prefix}/{{case_id}}:initialize"),
        ("POST", f"{prefix}/{{case_id}}/plans/{{version}}:publish"),
        ("POST", f"{prefix}/{{case_id}}:collect"),
        ("GET", f"{prefix}/{{case_id}}/plan"),
        ("GET", f"{prefix}/{{case_id}}/gantt"),
        ("GET", f"{prefix}/{{case_id}}/evidence"),
        ("GET", f"{prefix}/{{case_id}}/snapshots/{{snapshot_id}}"),
    } <= routes


def test_contract_performance_migration_has_scoped_rls_and_new_history() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0017_contract_performance.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0016_invoice_assurance_p1_p2"' in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "app.tenant_id" in migration
    assert "app.project_id" in migration
    assert set(
        (
            "contract_performance_cases",
            "contract_performance_plan_versions",
            "contract_performance_evidence",
            "contract_performance_evidence_links",
            "contract_performance_snapshots",
            "contract_performance_collection_cursors",
        )
    ) <= Base.metadata.tables.keys()
