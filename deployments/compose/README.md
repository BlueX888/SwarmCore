# Local infrastructure

```powershell
docker compose -f deployments/compose/compose.yaml up -d
uv run alembic -c packages/persistence/alembic.ini upgrade head
```

The development profile exposes PostgreSQL (host port **5433**), Temporal, NATS JetStream, OPA, Vault, and Phoenix on
localhost. Credentials are development-only defaults. Host port 5433 avoids clashing with a local PostgreSQL on 5432.
OPA loads `opa/swarmcore.rego` and exposes the decision document at
`http://localhost:8181/v1/data/swarmcore/decision`. Vault runs in dev mode with root token
`local-dev-only`; set that token only for local smoke tests. Production workers must use workload
authentication and must never receive a root token.

Run the isolated PostgreSQL and Temporal integration suite from the repository root:

```powershell
./scripts/test-integration.ps1
```

Linux/CI:

```bash
bash scripts/test-integration.sh
```

The script recreates an isolated stack on ports `15432` and `17233`, applies all migrations, runs every integration
test, and removes the test containers and data. Pass `-KeepInfrastructure` to retain the stack for diagnosis.
