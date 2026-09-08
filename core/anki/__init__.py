"""Core Anki integration package for collection access, deck queries, and vocabulary sampling."""
from core.anki.main_thread import (
    get_collection,
    ok_response,
    error_response,
    plain_text,
    run_on_main,
)
from core.anki.decks import list_decks
from core.anki.queries import (
    get_descendant_deck_ids,
    get_note_ids,
    list_source_models,
    list_source_fields,
)
from core.anki.vocabulary_source import (
    MAX_SAMPLE_SIZE,
    detect_fields,
    sample_vocab_pairs,
)

__all__ = [
    "get_collection",
    "ok_response",
    "error_response",
    "plain_text",
    "run_on_main",
    "list_decks",
    "get_descendant_deck_ids",
    "get_note_ids",
    "list_source_models",
    "list_source_fields",
    "MAX_SAMPLE_SIZE",
    "detect_fields",
    "sample_vocab_pairs",
]
