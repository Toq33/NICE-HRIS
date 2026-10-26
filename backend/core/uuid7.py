"""RFC 9562 UUIDv7 generator (time-ordered UUIDs)."""
import os
import time
import uuid


def uuid7() -> uuid.UUID:
    """Generate a time-ordered UUID v7 per RFC 9562."""
    timestamp_ms = time.time_ns() // 1_000_000
    rand_bytes = int.from_bytes(os.urandom(10), byteorder="big")
    rand_a = (rand_bytes >> 62) & 0x0FFF
    rand_b = rand_bytes & ((1 << 62) - 1)

    uuid_int = (timestamp_ms & ((1 << 48) - 1)) << 80
    uuid_int |= 0x7 << 76  # version 7
    uuid_int |= rand_a << 64
    uuid_int |= 0b10 << 62  # RFC 4122 variant
    uuid_int |= rand_b
    return uuid.UUID(int=uuid_int)
