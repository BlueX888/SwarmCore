param(
    [string]$Model = "qwen3:0.6b"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$server = Start-Process -FilePath "ollama" -ArgumentList "serve" -PassThru -WindowStyle Hidden
try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 500
        & ollama list *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
    }
    if (-not $ready) {
        throw "Ollama did not become ready"
    }

    $env:SWARMCORE_SMOKE_MODEL = $Model
    @'
import asyncio
import os

from agno.models.ollama import Ollama
from swarmcore_adapter_agno import AgnoAdapter


class Resolver:
    def resolve(self, reference: str) -> Ollama:
        if reference != "model://smoke":
            raise ValueError(reference)
        return Ollama(id=os.environ["SWARMCORE_SMOKE_MODEL"])


async def main() -> None:
    result = await AgnoAdapter(Resolver()).execute(
        {
            "agent": {
                "role": "Smoke tester",
                "instructions": "Return exactly OK and nothing else.",
                "model": "model://smoke",
            },
            "run": {"runId": "agno-smoke", "input": {"prompt": "health check"}},
            "node": {"key": "model", "config": {}},
            "taskExecutionId": "agno-smoke-task",
            "agentInstanceId": "agno-smoke-agent",
            "dependencyOutputs": {},
        }
    )
    if result["status"] != "COMPLETED" or not result.get("content"):
        raise AssertionError(result)
    print(f"AGNO_OLLAMA_SMOKE_OK model={result['model']}")


asyncio.run(main())
'@ | uv run --all-packages python -
}
finally {
    Remove-Item Env:SWARMCORE_SMOKE_MODEL -ErrorAction SilentlyContinue
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force
    }
}
