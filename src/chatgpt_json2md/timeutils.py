"""Time helpers for ChatGPT export timestamps."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def parse_epoch(value: Any) -> float | None:
    """Return a Unix timestamp as float, or None when it is missing/invalid."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_epoch(value: Any) -> str:
    """Format a Unix timestamp in UTC for Markdown output."""
    timestamp = parse_epoch(value)
    if timestamp is None:
        return "Unknown"
    try:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return "Unknown"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

