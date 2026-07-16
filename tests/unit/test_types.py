from swarmcore_domain import uuid7


def test_uuid7_layout_and_timestamp_order() -> None:
    first = uuid7(timestamp_ms=1_000)
    second = uuid7(timestamp_ms=1_001)

    assert first.version == 7
    assert first.variant == "specified in RFC 4122"
    assert first.int < second.int
