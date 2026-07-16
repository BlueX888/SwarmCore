from datetime import timedelta

from swarmcore_command_dispatcher import retry_delay


def test_dispatcher_retry_is_exponential_and_capped() -> None:
    assert retry_delay(1) == timedelta(seconds=2)
    assert retry_delay(5) == timedelta(seconds=32)
    assert retry_delay(100) == timedelta(minutes=5)
