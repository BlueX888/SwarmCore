from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy import select, text
from swarmcore_compiler import Compiler
from swarmcore_persistence import Database
from swarmcore_persistence.models import Project, Strategy, StrategyDraft, StrategyVersion, Tenant
from swarmcore_spec import SwarmStrategy

from .settings import Settings

TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
PROJECT_ID = UUID("00000000-0000-0000-0000-000000000002")
STRATEGY_ID = UUID("00000000-0000-0000-0000-000000000003")
DRAFT_ID = UUID("00000000-0000-0000-0000-000000000004")
VERSION_ID = UUID("00000000-0000-0000-0000-000000000005")

DEMO_SPEC = {
    "apiVersion": "swarmcore.io/v1",
    "kind": "SwarmStrategy",
    "metadata": {"name": "phase1-demo"},
    "spec": {
        "inputSchema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": ["topic"],
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "defaults": {"model": "model://fake-deterministic"},
        "agents": {
            "worker": {
                "role": "worker",
                "instructions": "Return a concise structured response.",
            }
        },
        "graph": {
            "entrypoint": "work",
            "nodes": {"work": {"type": "agent", "agent": "worker"}},
            "output": {"result": "{{ tasks.work.output }}"},
        },
    },
}


async def seed() -> None:
    database = Database(Settings().database_url)
    try:
        async with database.sessions() as session, session.begin():
            tenant = await session.get(Tenant, TENANT_ID)
            if tenant is None:
                session.add(Tenant(id=TENANT_ID, name="SwarmCore Local", status="ACTIVE"))
                await session.flush()
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": str(TENANT_ID)},
            )
            await session.execute(
                text("SELECT set_config('app.project_id', :project, true)"),
                {"project": str(PROJECT_ID)},
            )
            if await session.get(Project, PROJECT_ID) is None:
                session.add(Project(id=PROJECT_ID, tenant_id=TENANT_ID, name="Local Demo"))
                await session.flush()
            if await session.get(Strategy, STRATEGY_ID) is None:
                session.add(
                    Strategy(
                        id=STRATEGY_ID,
                        tenant_id=TENANT_ID,
                        project_id=PROJECT_ID,
                        name="phase1-demo",
                    )
                )
                await session.flush()
            if await session.get(StrategyDraft, DRAFT_ID) is None:
                session.add(
                    StrategyDraft(
                        id=DRAFT_ID,
                        tenant_id=TENANT_ID,
                        strategy_id=STRATEGY_ID,
                        raw_spec=DEMO_SPEC,
                        diagnostics=[],
                        updated_by="local-seed",
                    )
                )
            version = await session.scalar(
                select(StrategyVersion).where(StrategyVersion.id == VERSION_ID)
            )
            if version is None:
                spec = SwarmStrategy.model_validate(DEMO_SPEC)
                plan = Compiler().compile(
                    spec,
                    registry_snapshot="local-seed",
                    policy_revision="phase1",
                )
                session.add(
                    StrategyVersion(
                        id=VERSION_ID,
                        tenant_id=TENANT_ID,
                        strategy_id=STRATEGY_ID,
                        version=1,
                        raw_spec=DEMO_SPEC,
                        normalized_spec=spec.model_dump(
                            mode="json", by_alias=True, exclude_none=True
                        ),
                        plan=plan.model_dump(mode="json", by_alias=True),
                        plan_hash=plan.plan_hash,
                        schema_version=spec.api_version,
                        runtime_version=plan.runtime_version,
                    )
                )
    finally:
        await database.dispose()


def run() -> None:
    asyncio.run(seed())
