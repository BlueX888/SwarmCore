$env:SWARMCORE_REAL_CHAIN_API_URL = "http://127.0.0.1:8010"
$env:SWARMCORE_REAL_CHAIN_ARTIFACT_URL = "http://127.0.0.1:8091"

& "C:\Project\SwarmCore\.venv\Scripts\python.exe" `
  "C:\Project\SwarmCore\scripts\run-procurement-supplier-risk-real-chain.py"
