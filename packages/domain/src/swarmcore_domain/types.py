from __future__ import annotations

import secrets
import time
from uuid import UUID


def uuid7(*, timestamp_ms: int | None = None) -> UUID:
    """Create an RFC 9562 UUIDv7 without relying on Python 3.14's uuid.uuid7."""
    if timestamp_ms is None:
        timestamp_ms = time.time_ns() // 1_000_000
    if not 0 <= timestamp_ms < 1 << 48:
        raise ValueError("timestamp_ms must fit in 48 bits")
    random_bits = secrets.randbits(74)
    value = timestamp_ms << 80
    value |= 0x7 << 76
    value |= ((random_bits >> 62) & 0xFFF) << 64
    value |= 0b10 << 62
    value |= random_bits & ((1 << 62) - 1)
    return UUID(int=value)
