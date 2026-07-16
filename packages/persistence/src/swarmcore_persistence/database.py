from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    def __init__(self, url: str, *, echo: bool = False) -> None:
        self.engine: AsyncEngine = create_async_engine(url, echo=echo, pool_pre_ping=True)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def dispose(self) -> None:
        await self.engine.dispose()


@asynccontextmanager
async def tenant_transaction(
    sessions: async_sessionmaker[AsyncSession], *, tenant_id: UUID, project_id: UUID
) -> AsyncIterator[AsyncSession]:
    """Open a transaction with PostgreSQL RLS context scoped via SET LOCAL."""
    async with sessions() as session, session.begin():
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )
        await session.execute(
            text("SELECT set_config('app.project_id', :project_id, true)"),
            {"project_id": str(project_id)},
        )
        yield session
