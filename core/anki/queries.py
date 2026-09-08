"""Fast-path SQLite and collection queries for notes, models, and fields."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from core.anki.main_thread import get_collection, ok_response, error_response, run_on_main


def get_descendant_deck_ids(col: Any, root_deck_id: int) -> List[int]:
    """Resolve IDs of the root deck and all its nested descendants."""
    root = col.decks.get(int(root_deck_id))
    if not root:
        return []
    root_name = root.get("name", "")
    return [
        int(did)
        for did, deck in col.decks.decks.items()
        if deck.get("name") == root_name or deck.get("name", "").startswith(root_name + "::")
    ]


def get_note_ids(deck_id: Optional[int] = None, model_id: Optional[int] = None) -> List[int]:
    """Retrieve note IDs bounded by deck and optional model filter via SQLite fast-path."""
    col = get_collection()
    if not col:
        return []
    if deck_id is None:
        query = f"mid:{int(model_id)}" if model_id is not None else ""
        return col.find_notes(query)

    deck_ids = get_descendant_deck_ids(col, deck_id)
    if not deck_ids:
        return []

    # Fast-path via SQLite if col.db is available
    if hasattr(col, "db") and hasattr(col.db, "list"):
        try:
            placeholders = ",".join("?" for _ in deck_ids)
            if model_id is not None:
                sql = (
                    f"SELECT DISTINCT c.nid FROM cards c JOIN notes n ON c.nid = n.id "
                    f"WHERE c.did IN ({placeholders}) AND n.mid = ?"
                )
                return [int(nid) for nid in col.db.list(sql, *(deck_ids + [int(model_id)]))]
            else:
                sql = f"SELECT DISTINCT nid FROM cards WHERE did IN ({placeholders})"
                return [int(nid) for nid in col.db.list(sql, *deck_ids)]
        except Exception:
            pass

    note_ids: Set[int] = set()
    for did in deck_ids:
        query = f"did:{did}"
        if model_id is not None:
            query += f" mid:{int(model_id)}"
        note_ids.update(col.find_notes(query))
    return list(note_ids)


def list_source_models(deck_id: Optional[int] = None) -> Dict[str, Any]:
    """Enumerate note types associated with a given deck."""
    def _inner():
        col = get_collection()
        if not col:
            return error_response("E_COLLECTION_CLOSED", "Open a profile before reading note types.")
        if deck_id is None:
            return error_response("E_DECK_REQUIRED", "Choose a deck before choosing a note type.")
        root = col.decks.get(int(deck_id))
        if not root:
            return error_response("E_DECK_NOT_FOUND", "The selected deck no longer exists.")

        model_ids: Set[int] = set()
        used_fast_path = False

        if hasattr(col, "db") and hasattr(col.db, "list"):
            try:
                deck_ids = get_descendant_deck_ids(col, deck_id)
                if deck_ids:
                    placeholders = ",".join("?" for _ in deck_ids)
                    sql = f"SELECT DISTINCT n.mid FROM cards c JOIN notes n ON c.nid = n.id WHERE c.did IN ({placeholders})"
                    model_ids = {int(mid) for mid in col.db.list(sql, *deck_ids)}
                    used_fast_path = True
            except Exception:
                used_fast_path = False

        if not used_fast_path:
            ids = get_note_ids(deck_id=deck_id)
            model_ids = {int(col.get_note(nid).mid) for nid in ids}

        models = []
        for mid in model_ids:
            model = col.models.get(mid)
            if model:
                models.append({"id": mid, "name": model.get("name", str(mid))})
        return ok_response({"models": sorted(models, key=lambda m: m["name"].lower())})

    return run_on_main(_inner)


def list_source_fields(model_id: int) -> Dict[str, Any]:
    """Retrieve field names for a specific note type."""
    def _inner():
        col = get_collection()
        if not col:
            return error_response("E_COLLECTION_CLOSED", "Open a profile before reading fields.")
        model = col.models.get(int(model_id))
        if not model:
            return error_response("E_MODEL_NOT_FOUND", "The selected note type no longer exists.")
        return ok_response({"fields": [field["name"] for field in model.get("flds", [])]})

    return run_on_main(_inner)
