# SwarmCore

SwarmCore is a protocol-neutral, durable multi-agent orchestration execution runtime. The
implementation follows [`docs/swarmcore-system-design.md`](docs/swarmcore-system-design.md), and
development progress is tracked in
[`docs/swarmcore-development-plan.md`](docs/swarmcore-development-plan.md).

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
uv run swarmcore-seed
```

The runtime processes expose these console scripts: `swarmcore-api`,
`swarmcore-command-dispatcher`, `swarmcore-worker-control`, `swarmcore-worker-agent`,
`swarmcore-worker-tool`, `swarmcore-tool-gateway-api`, `swarmcore-event-publisher`, and
`swarmcore-projection-reconciler`. Copy `.env.example` to `.env` before starting them. The Control
Worker, Tool Worker, and Tool Gateway must share `SWARMCORE_TOOL_CAPABILITY_SECRET`; replace the
development value with at least 32 random bytes. The Gateway listens on port 8090 by default, and
the Agent Worker reaches it through `SWARMCORE_TOOL_GATEWAY_URL`. Phoenix receives OTLP traces and
metrics at port 4317; its UI is on port 6006.

For a credential-free local demo, set `SWARMCORE_USE_FAKE_AGENT=true` before starting the Agent
Worker. This selects the deterministic test adapter only; the default production path remains the
Agno adapter. The seed command is idempotent and creates the documented local tenant, project, and
one published example strategy without secrets.

Agent tools are exposed to Agno only as Gateway proxy functions. Side-effecting tools must be
explicit `tool` nodes so Temporal can retain a stable effect ID across Activity retries; HIGH and
CRITICAL tools enter the durable Approval flow before a capability token is issued.

To run the PostgreSQL RLS integration contract against a migrated test database, set
`SWARMCORE_TEST_DATABASE_URL` before `uv run pytest`.

The `agno/` and `agent-ui/` directories are upstream references and are not part of the SwarmCore
workspace.
