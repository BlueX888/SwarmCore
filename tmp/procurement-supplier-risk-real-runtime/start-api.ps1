$env:SWARMCORE_TOOL_GATEWAY_URL = "http://127.0.0.1:8090"
$env:SWARMCORE_MODEL_GATEWAY_URL = "http://127.0.0.1:8093"
$env:SWARMCORE_AGENT_READINESS_URL = "http://127.0.0.1:8094"
$env:SWARMCORE_ARTIFACT_GATEWAY_URL = "http://127.0.0.1:8091"
$env:SWARMCORE_TELEMETRY_ENABLED = "false"

& "C:\Project\SwarmCore\.venv\Scripts\python.exe" -m uvicorn `
  swarmcore_api.main:create_app --factory --host 127.0.0.1 --port 8010
