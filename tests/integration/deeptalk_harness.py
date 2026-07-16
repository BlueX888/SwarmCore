from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient


class DeepTalkContractHarness:
    def __init__(self, api: TestClient, *, tenant_id: str, project_id: str) -> None:
        self.api = api
        self.tenant_id = tenant_id
        self.project_id = project_id

    def rest_capabilities(self) -> dict[str, Any]:
        response = self.api.get(
            f"/v1/projects/{self.project_id}/capabilities",
            headers={"X-Tenant-ID": self.tenant_id},
        )
        assert response.status_code == 200
        return response.json()

    def rest_compile(self, spec: dict[str, Any]) -> dict[str, Any]:
        response = self.api.post(
            f"/v1/projects/{self.project_id}/strategies/compile",
            headers={"X-Tenant-ID": self.tenant_id},
            json={"spec": spec},
        )
        assert response.status_code == 200
        return response.json()

    def mcp(self, name: str, arguments: dict[str, object]) -> dict[str, Any]:
        response = self.api.post(
            "/mcp",
            headers={
                "X-Tenant-ID": self.tenant_id,
                "Authorization": "Bearer integration",
                "Mcp-Protocol-Version": "2025-11-25",
            },
            json={
                "jsonrpc": "2.0",
                "id": str(uuid4()),
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
        )
        assert response.status_code == 200
        result = response.json()["result"]
        assert result["isError"] is False
        return result["structuredContent"]
