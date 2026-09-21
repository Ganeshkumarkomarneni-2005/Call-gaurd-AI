"""Time-related utility functions for CallGuard AI."""

from __future__ import annotations

import time
from datetime import datetime, timezone


def now_utc() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def timestamp_ms() -> int:
    """Return the current UNIX timestamp in milliseconds."""
    return int(time.time() * 1000)


def format_duration(seconds: int) -> str:
    """Format an integer number of seconds into a human-readable string.

    Examples::

        >>> format_duration(154)
        '2m 34s'
        >>> format_duration(45)
        '45s'
        >>> format_duration(3661)
        '1h 1m 1s'
    """
    if seconds < 0:
        seconds = 0
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
