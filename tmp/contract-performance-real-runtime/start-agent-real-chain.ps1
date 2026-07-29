$env:SWARMCORE_MODELS = '{"model://general":"kimi-k2.5","model://kimi-k2.5":"kimi-k2.5","model://contract-performance-reasoning":"kimi-k2.5"}'
$env:SWARMCORE_MODEL_GATEWAY_URL = "http://127.0.0.1:8093"
$env:SWARMCORE_TOOL_GATEWAY_URL = "http://127.0.0.1:8090"
$env:SWARMCORE_TELEMETRY_ENABLED = "false"

uv run swarmcore-worker-agent
