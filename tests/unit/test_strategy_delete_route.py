from swarmcore_api import create_app
from swarmcore_api.settings import Settings


def test_strategy_delete_routes_are_registered() -> None:
    app = create_app(Settings(telemetry_enabled=False))
    routes = {
        (method, route.path)
        for route in app.routes
        if hasattr(route, "path") and hasattr(route, "methods")
        for method in (route.methods or ())
    }
    assert (
        "GET",
        "/v1/projects/{project_id}/strategies/{strategy_id}/delete-impact",
    ) in routes
    assert ("DELETE", "/v1/projects/{project_id}/strategies/{strategy_id}") in routes
