from swarmcore_api import create_app
from swarmcore_api.settings import Settings


def test_capability_pack_delete_route_is_registered() -> None:
    app = create_app(Settings(telemetry_enabled=False))
    routes = [
        (sorted(route.methods or ()), route.path)
        for route in app.routes
        if hasattr(route, "path") and hasattr(route, "methods")
    ]
    assert (
        ["DELETE"],
        "/v1/projects/{project_id}/capability-packs/{version_id}",
    ) in routes
