from swarmcore_api import create_app
from swarmcore_api.settings import Settings


def test_business_work_bind_strategy_route_is_registered() -> None:
    app = create_app(Settings(telemetry_enabled=False))
    routes = [
        (frozenset(route.methods or ()), route.path)
        for route in app.routes
        if hasattr(route, "path") and hasattr(route, "methods")
        and "business-works" in route.path
    ]
    bind_path = "/v1/projects/{project_id}/business-works/{work_key}:bind-strategy"
    get_path = "/v1/projects/{project_id}/business-works/{work_key}"
    assert (frozenset({"POST"}), bind_path) in routes
    assert (frozenset({"GET"}), get_path) in routes
    bind_index = next(i for i, item in enumerate(routes) if item[1] == bind_path)
    get_index = next(i for i, item in enumerate(routes) if item[1] == get_path)
    assert bind_index < get_index
