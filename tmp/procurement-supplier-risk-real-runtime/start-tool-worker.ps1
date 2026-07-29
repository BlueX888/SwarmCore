$env:SWARMCORE_TELEMETRY_ENABLED = "false"
$env:SWARMCORE_TOOL_TASK_QUEUE = "tool-trusted"
& "C:\Project\SwarmCore\.venv\Scripts\python.exe" `
  "C:\Project\SwarmCore\.venv\Scripts\swarmcore-worker-tool.exe"
