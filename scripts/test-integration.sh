#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT/deployments/compose/compose.integration.yaml"
PROJECT="swarmcore-integration"
DATABASE_URL="postgresql+asyncpg://swarmcore:swarmcore@localhost:15432/swarmcore_test"

cleanup() {
  docker compose --project-name "$PROJECT" --file "$COMPOSE_FILE" down --volumes --remove-orphans
}
trap cleanup EXIT

cd "$ROOT"
cleanup
docker compose --project-name "$PROJECT" --file "$COMPOSE_FILE" up --detach --wait --wait-timeout 300

export SWARMCORE_DATABASE_URL="$DATABASE_URL"
export SWARMCORE_TEST_DATABASE_URL="$DATABASE_URL"
export SWARMCORE_TEST_TEMPORAL_ADDRESS="localhost:17233"
export SWARMCORE_TEST_TEMPORAL_NAMESPACE="default"
export SWARMCORE_TEST_S3_ENDPOINT="http://localhost:19000"
export SWARMCORE_TEST_S3_ACCESS_KEY="swarmcore-test"
export SWARMCORE_TEST_S3_SECRET_KEY="swarmcore-test-secret"
export SWARMCORE_TEST_VAULT_ADDRESS="http://localhost:18200"
export SWARMCORE_TEST_VAULT_TOKEN="integration-root-token"

uv run alembic -c packages/persistence/alembic.ini upgrade head
uv run pytest -q tests/integration
