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
`swarmcore-projection-reconciler`, plus the M4 processes `swarmcore-worker-webhook`,
`swarmcore-artifact-gateway`, `swarmcore-model-gateway`, and `swarmcore-sandbox-manager`. Copy
`.env.example` to `.env` before starting them. The Control
Worker, Tool Worker, and Tool Gateway must share `SWARMCORE_TOOL_CAPABILITY_SECRET`; replace the
development value with at least 32 random bytes. The Gateway listens on port 8090 by default, and
the Agent Worker reaches it through `SWARMCORE_TOOL_GATEWAY_URL`. Phoenix receives OTLP traces and
metrics at port 4317; its UI is on port 6006.

Local mode uses header identity and the in-process role policy. Production deployments must set
`SWARMCORE_DEPLOYMENT_MODE=production`, `SWARMCORE_AUTH_MODE=jwt`, configure issuer/audience/JWKS,
set `SWARMCORE_POLICY_MODE=opa`, and use workload Vault authentication. Internal Gateway clients
and servers require `SWARMCORE_WORKLOAD_TLS_CA_FILE`, `SWARMCORE_WORKLOAD_TLS_CERT_FILE`, and
`SWARMCORE_WORKLOAD_TLS_KEY_FILE`; incomplete production security settings fail at startup.
`secret://path` reads Vault KV v2; leased dynamic credentials use
`secret://dynamic/<mount>/<path>` and are revoked when the activity exits. The Artifact, Model, and
Sandbox capability secrets are independent and must also be replaced. Artifact Gateway uses the
local store by default and can select S3 plus ClamAV; Model Gateway routes logical model names to
LiteLLM, and the production Agent Worker creates only run-scoped Model Gateway clients. Sandbox
Manager is dry-run locally and admits only digest-pinned allowlisted images.

M4 also adds scoped Artifact listing and one-time download grants, append-only Audit query/NDJSON
export, and Webhook endpoint APIs under `/v1`. Every console process emits redacted JSON logs and
exports OpenTelemetry traces/metrics when telemetry is enabled.

Project-scoped agent, tool, and model configurations are persisted through
`/v1/projects/{project_id}/configurations/{agent|tool|model}`. Saved configurations reference the
immutable built-in Registry, remain isolated by tenant and project RLS, and create audit records on
create, update, and delete. Updates retain the configuration ID and increment its revision. Apply
Alembic migrations before using these endpoints.

The unified Capability Center is enabled by default and can be disabled with
`SWARMCORE_CAPABILITY_CENTER_V2=false`. It adds
`/v1/projects/{project_id}/capability-center`, `/capability-runs`, and `/presets` while retaining the
configuration APIs above. Readiness is projected from Tool Gateway executors, Model Gateway route,
secret and endpoint checks, and the Agent Worker adapter probe on port 8094; unavailable resources
remain visible only when explicitly requested and cannot be run. MCP exposes
`swarm.capability-center.list` and `swarm.capability.run` under the same feature flag.

The MCP endpoint is `/mcp` and exposes the canonical tools
`swarm.capabilities.get`, `swarm.strategy.validate`, `swarm.strategy.compile`,
`swarm.run.create`, `swarm.run.status`, `swarm.run.result`, and `swarm.run.control`.
Business Workbench also exposes `list_capability_packs`, `create_work_item`,
`execute_work_item`, `get_evaluation`, `list_findings`, `act_on_finding`, and `get_report`; these
tools call the same application services as REST.
Run control actions, including cancellation, are submitted through `swarm.run.control`;
the former `swarm.run.start`, `swarm.run.get`, and `swarm.run.cancel` aliases are not supported.

For a credential-free local demo, set `SWARMCORE_USE_FAKE_AGENT=true` before starting the Agent
Worker. This selects the deterministic test adapter only; the default production path remains the
Agno adapter. The seed command is idempotent and creates the documented local tenant, project, and
one published example strategy without secrets.

Agent tools are exposed to Agno only as Gateway proxy functions. Side-effecting tools must be
explicit `tool` nodes so Temporal can retain a stable effect ID across Activity retries; HIGH and
CRITICAL tools enter the durable Approval flow before a capability token is issued.

The first trusted business capability pack is `contract-integrity`. Its generic REST resources are
under `/v1/projects/{project_id}/capability-packs`, `/work-items`, `/evaluations`, `/findings`,
`/reports`, and `/rule-sets`. Capability-pack list and enable responses include the current
project binding `configuration`; updating it re-enables the same immutable version with new
project-scoped parameters. `POST /v1/projects/{project_id}/capability-packs` publishes a custom
Manifest bound to an existing published `StrategyVersion`; the server reads the frozen plan and
rejects Agent/Tool declarations that differ from that version. The Web console builds this request
from a trusted business-asset template and a version selected from Strategy Management. Input files
are initiated through the API, uploaded to Artifact
Gateway with a short-lived Blob capability, hash/scanned there, and only then attached to an
immutable WorkItemRevision. Set `VITE_ARTIFACT_GATEWAY_URL` for browser uploads and include the
Web console origin in `SWARMCORE_CORS_ORIGINS`. Apply migration
`0008_business_workbench` before using these resources.

To run the PostgreSQL RLS integration contract against a migrated test database, set
`SWARMCORE_TEST_DATABASE_URL` before `uv run pytest`.

The `agno/` and `agent-ui/` directories are upstream references and are not part of the SwarmCore
workspace.
