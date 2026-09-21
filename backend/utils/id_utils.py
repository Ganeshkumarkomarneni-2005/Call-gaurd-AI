"""Utility functions for generating unique identifiers."""

from __future__ import annotations

import uuid


def generate_id() -> str:
    """Return a new UUID4 as a lowercase hyphenated string."""
    return str(uuid.uuid4())


def generate_call_id() -> str:
    """Return a new UUID4 string suitable for use as a call identifier."""
    return str(uuid.uuid4())
