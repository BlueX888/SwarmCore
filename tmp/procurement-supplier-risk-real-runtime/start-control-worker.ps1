$env:SWARMCORE_TELEMETRY_ENABLED = "false"
$env:SWARMCORE_TEMPORAL_TASK_QUEUE = "swarm-control"
& "C:\Project\SwarmCore\.venv\Scripts\python.exe" `
  "C:\Project\SwarmCore\.venv\Scripts\swarmcore-worker-control.exe"
