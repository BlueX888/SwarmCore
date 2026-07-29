from pathlib import Path

from fastapi.routing import APIRoute
from swarmcore_api.main import create_app
from swarmcore_api.settings import Settings
from swarmcore_persistence.models import Base


def test_procurement_supplier_risk_rest_routes_are_registered() -> None:
    app = create_app(Settings())
    routes = {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    }
    prefix = "/v1/projects/{project_id}/procurement-supplier-risk"
    assert {
        ("POST", f"{prefix}/monitors"),
        ("GET", f"{prefix}/monitors/{{monitor_id}}"),
        ("POST", f"{prefix}/monitors/{{monitor_id}}:refresh"),
        ("GET", f"{prefix}/monitors/{{monitor_id}}/history"),
        ("GET", f"{prefix}/alerts"),
        ("POST", f"{prefix}/alerts/{{alert_id}}/work-orders"),
        ("GET", f"{prefix}/work-orders"),
        ("PATCH", f"{prefix}/work-orders/{{work_order_id}}"),
    } <= routes


def test_procurement_supplier_risk_migration_is_scoped_and_traceable() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0019_procurement_supplier_risk.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0018_swarm_calibration"' in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "app.tenant_id" in migration
    assert "app.project_id" in migration
    assert "swarmcore_reject_immutable_update" in migration
    assert {
        "supplier_risk_monitors",
        "supplier_risk_snapshots",
        "supplier_risk_alerts",
        "supplier_risk_work_orders",
        "supplier_risk_work_order_actions",
    } <= Base.metadata.tables.keys()
