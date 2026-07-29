$env:SWARMCORE_TELEMETRY_ENABLED = "false"
$env:SWARMCORE_AGENT_TASK_QUEUE = "agent-general"
$env:SWARMCORE_AGENT_READINESS_PORT = "8096"
$env:SWARMCORE_AGENT_MODEL_MAX_OUTPUT_TOKENS = "16384"
$env:SWARMCORE_TOOL_GATEWAY_URL = "http://127.0.0.1:8090"
$env:SWARMCORE_MODEL_GATEWAY_URL = "http://127.0.0.1:8093"
& "C:\Project\SwarmCore\.venv\Scripts\python.exe" `
  "C:\Project\SwarmCore\.venv\Scripts\swarmcore-worker-agent.exe"
