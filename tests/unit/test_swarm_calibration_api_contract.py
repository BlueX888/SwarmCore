from fastapi.testclient import TestClient
from swarmcore_api import create_app
from swarmcore_api.business_schemas import RunSwarmCalibrationRequest
from swarmcore_api.settings import Settings


def test_swarm_calibration_request_preserves_public_contract() -> None:
    request = RunSwarmCalibrationRequest.model_validate(
        {
            "calibrationMode": "GITHUB_ENGINEERING_ISSUE",
            "title": "调度校准",
            "issueUrl": "https://github.com/temporalio/sdk-python/issues/782",
            "objective": "确认真实修复与调度策略一致",
            "acceptanceCriteria": ["结论有冻结证据"],
            "sandbox": {
                "enabled": True,
                "testCommand": ["python", "-m", "compileall", "-q", "."],
            },
        }
    )

    payload = request.model_dump(by_alias=True, mode="json", exclude_none=True)

    assert payload["issueUrl"].endswith("/issues/782")
    assert payload["calibrationMode"] == "GITHUB_ENGINEERING_ISSUE"
    assert payload["acceptanceCriteria"] == ["结论有冻结证据"]
    assert payload["sandbox"]["testCommand"][0] == "python"


def test_swarm_calibration_rest_route_is_published() -> None:
    with TestClient(create_app(Settings())) as client:
        schema = client.get("/openapi.json").json()

    operation = schema["paths"]["/v1/projects/{project_id}/swarm-calibration:run"]["post"]
    assert operation["responses"]["202"]
