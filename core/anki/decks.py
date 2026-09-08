"""Deck tree traversal and hierarchy queries."""
from __future__ import annotations

from typing import Any, Dict
from core.anki.main_thread import get_collection, ok_response, error_response, run_on_main


def list_decks() -> Dict[str, Any]:
    """Retrieve all active Anki decks with hierarchy levels."""
    def _inner():
        col = get_collection()
        if not col:
            return error_response("E_COLLECTION_CLOSED", "Open a profile before reading decks.")
        decks = [
            {"id": int(did), "name": deck["name"], "level": deck["name"].count("::")}
            for did, deck in col.decks.decks.items()
            if deck.get("name")
        ]
        return ok_response({"decks": sorted(decks, key=lambda d: d["name"].lower())})

    return run_on_main(_inner)
