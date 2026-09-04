"""Compatibility helpers for Anki task manager completion callbacks."""
from __future__ import annotations


def resolve_background_result(result) -> dict:
    """Unwrap Anki 25's Future while remaining compatible with direct results."""
    resolved = result.result() if hasattr(result, "result") and callable(result.result) else result
    if not isinstance(resolved, dict):
        raise TypeError("Invalid task result")
    return resolved
