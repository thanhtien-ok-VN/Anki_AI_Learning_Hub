"""Read-only, main-thread access to the active Anki collection.

Thin backward-compatibility facade delegating directly to core.anki package.
"""
from __future__ import annotations

try:
    from aqt import mw
except ImportError:
    mw = None
from core.anki import (
    MAX_SAMPLE_SIZE,
    get_collection,
    ok_response,
    error_response,
    plain_text,
    run_on_main,
    get_note_ids,
    list_decks,
    list_source_models,
    list_source_fields,
    sample_vocab_pairs,
)

# Aliases preserving internal names for backward compatibility with existing tests
_collection = get_collection
_ok = ok_response
_error = error_response
_plain = plain_text
_run_on_main = run_on_main
_note_ids = get_note_ids

__all__ = [
    "MAX_SAMPLE_SIZE",
    "get_collection",
    "ok_response",
    "error_response",
    "plain_text",
    "run_on_main",
    "list_decks",
    "list_source_models",
    "list_source_fields",
    "sample_vocab_pairs",
    "_collection",
    "_ok",
    "_error",
    "_plain",
    "_run_on_main",
    "_note_ids",
]
