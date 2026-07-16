# Local infrastructure

```powershell
docker compose -f deployments/compose/compose.yaml up -d
uv run alembic -c packages/persistence/alembic.ini upgrade head
```

The development profile exposes PostgreSQL (host port **5433**), Temporal, NATS JetStream, OPA, Vault, and Phoenix on
localhost. Credentials are development-only defaults. Host port 5433 avoids clashing with a local PostgreSQL on 5432.
