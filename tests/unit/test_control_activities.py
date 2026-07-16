import asyncio
from typing import Any

from swarmcore_runtime_temporal.activities import ControlActivities


class Plans:
    async def load(
        self, *, tenant_id: str, project_id: str, run_id: str, plan_hash: str
    ) -> dict[str, Any]:
        return {"tenant": tenant_id, "project": project_id, "run": run_id, "hash": plan_hash}


class Projector:
    async def project(self, transition: dict[str, Any]) -> None:
        pass


def test_merge_object_reducer_is_stable() -> None:
    activities = ControlActivities(Plans(), Projector())
    result = asyncio.run(
        activities.execute_control_node(
            {
                "node": {"type": "reducer", "config": {"reducer": "merge_object"}},
                "dependencyOutputs": {"b": {"b": 2}, "a": {"a": 1}},
            }
        )
    )
    assert result == {"a": 1, "b": 2}
