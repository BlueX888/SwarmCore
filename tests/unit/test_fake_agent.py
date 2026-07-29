import asyncio

from jsonschema import Draft202012Validator
from swarmcore_registry.models import calibration_agent_registrations
from swarmcore_worker_agent.fake import DeterministicFakeAgentAdapter


def test_fake_agent_is_deterministic_and_structured() -> None:
    request = {
        "run": {"input": {"topic": "retries", "_failOnce": False}},
        "node": {"key": "worker", "config": {"input": {}}},
        "taskExecutionId": "task-1",
        "dependencyOutputs": {},
    }
    adapter = DeterministicFakeAgentAdapter()
    first = asyncio.run(adapter.execute(request))
    second = asyncio.run(adapter.execute(request))
    assert first == second
    assert first["status"] == "COMPLETED"
    assert first["metrics"]["costUsd"] == 0.0


def test_fake_agent_emits_schema_valid_calibration_outputs() -> None:
    adapter = DeterministicFakeAgentAdapter()
    registrations = calibration_agent_registrations()
    evidence = {
        "evidenceIndex": [
            {"evidenceId": "ev-001"},
            {"evidenceId": "ev-002"},
            {"evidenceId": "ev-003"},
        ]
    }
    inputs = {
        "scheduling-calibration-supervisor": {
            "task": {},
            "evidenceSummary": evidence,
            "runtimePolicy": {},
        },
        "primary-engineering-diagnostician": {
            "task": {"acceptanceCriteria": ["测试通过"]},
            "evidence": evidence,
        },
        "standby-engineering-diagnostician": {
            "task": {"acceptanceCriteria": ["测试通过"]},
            "evidence": evidence,
        },
        "calibration-quality-supervisor": {
            "task": {},
            "diagnosis": {},
            "evidenceIndex": evidence["evidenceIndex"],
            "sandbox": {"status": "PASSED"},
        },
    }
    for registration in registrations:
        request = {
            "run": {"input": {}},
            "node": {
                "key": registration.role,
                "config": {"input": inputs[registration.role]},
            },
            "agent": registration.model_dump(by_alias=True),
            "taskExecutionId": registration.role,
            "dependencyOutputs": {},
        }
        result = asyncio.run(adapter.execute(request))
        Draft202012Validator(registration.output_schema).validate(result["content"])
