$values = @{}
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^(DEEPSEEK_API_BASE|DEEPSEEK_API_KEY)=(.*)$") {
        $values[$matches[1]] = $matches[2]
    }
}
if (-not $values["DEEPSEEK_API_BASE"] -or -not $values["DEEPSEEK_API_KEY"]) {
    throw "DEEPSEEK_API_BASE and DEEPSEEK_API_KEY are required"
}

$env:SWARMCORE_MODEL_PROVIDER_URL = $values["DEEPSEEK_API_BASE"]
$env:SWARMCORE_MODEL_PROVIDER_API_KEY = $values["DEEPSEEK_API_KEY"]
$env:SWARMCORE_MODEL_ROUTES = '{"model://general":"DeepSeek-V4-Flash","model://contract-performance-reasoning":"DeepSeek-V4-Flash"}'
$env:SWARMCORE_TELEMETRY_ENABLED = "false"

uv run swarmcore-model-gateway
