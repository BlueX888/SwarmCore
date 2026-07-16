# SwarmCore

SwarmCore is a durable, multi-tenant swarm-agent execution runtime. The implementation follows
[`docs/swarmcore-system-design.md`](docs/swarmcore-system-design.md).

## Development

```powershell
uv sync --all-packages
uv run pytest
uv run ruff check .
uv run mypy
pnpm install
pnpm web:lint
pnpm web:test
pnpm web:build
pnpm web:e2e
```

Start infrastructure and apply the schema:

```powershell
docker compose -f deployments/compose/compose.yaml up -d
uv run alembic -c packages/persistence/alembic.ini upgrade head
```

The Phase 1 processes expose these console scripts: `swarmcore-api`,
`swarmcore-command-dispatcher`, `swarmcore-worker-control`, `swarmcore-worker-agent`,
`swarmcore-event-publisher`, and `swarmcore-projection-reconciler`. Copy `.env.example` to `.env`
before starting them. Phoenix receives OTLP traces and metrics at port 4317; its UI is on port 6006.

To run the PostgreSQL RLS integration contract against a migrated test database, set
`SWARMCORE_TEST_DATABASE_URL` before `uv run pytest`.

The `agno/` and `agent-ui/` directories are upstream references and are not part of the SwarmCore
workspace.
