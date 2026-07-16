import json


def test_nats_payload_canonical_encoding() -> None:
    first = json.dumps({"b": 2, "a": 1}, sort_keys=True, separators=(",", ":"))
    second = json.dumps({"a": 1, "b": 2}, sort_keys=True, separators=(",", ":"))
    assert first == second
