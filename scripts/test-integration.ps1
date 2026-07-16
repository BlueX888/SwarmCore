param(
    [switch]$KeepInfrastructure
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$root = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $root "deployments/compose/compose.integration.yaml"
$databaseUrl = "postgresql+asyncpg://swarmcore:swarmcore@localhost:15432/swarmcore_test"
$project = "swarmcore-integration"

Push-Location $root
try {
    docker compose --project-name $project --file $composeFile down --volumes --remove-orphans
    docker compose --project-name $project --file $composeFile up --detach --wait --wait-timeout 300

    $env:SWARMCORE_DATABASE_URL = $databaseUrl
    $env:SWARMCORE_TEST_DATABASE_URL = $databaseUrl
    $env:SWARMCORE_TEST_TEMPORAL_ADDRESS = "localhost:17233"
    $env:SWARMCORE_TEST_TEMPORAL_NAMESPACE = "default"

    uv run alembic -c packages/persistence/alembic.ini upgrade head
    uv run pytest -q tests/integration
}
finally {
    if (-not $KeepInfrastructure) {
        docker compose --project-name $project --file $composeFile down --volumes --remove-orphans
    }
    Pop-Location
}
