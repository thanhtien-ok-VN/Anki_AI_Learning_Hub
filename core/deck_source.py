"""Read-only, main-thread access to the active Anki collection.

The web UI always chooses a note type and two fields explicitly.  That keeps
collection access predictable even when one deck contains several note types.
"""
from __future__ import annotations

import html
import random
import re
from typing import Any

from aqt import mw

MAX_SAMPLE_SIZE = 50
_TAG_RE = re.compile(r"<[^>]*>")
_MEDIA_RE = re.compile(r"\[sound:[^\]]+\]", re.IGNORECASE)


def _collection() -> Any:
    return getattr(mw, "col", None)


def _ok(data: dict | None = None) -> dict:
    return {"success": True, "data": data or {}}


def _error(code: str, message: str) -> dict:
    return {"success": False, "data": {}, "error_code": code, "message": message}


def _plain(value: str) -> str:
    """Return useful text from an Anki field without HTML or media markup."""
    value = _MEDIA_RE.sub("", value or "")
    value = _TAG_RE.sub(" ", value)
    return " ".join(html.unescape(value).split())


def list_decks() -> dict:
    col = _collection()
    if not col:
        return _error("E_COLLECTION_CLOSED", "Open a profile before reading decks.")
    decks = [
        {"id": int(did), "name": deck["name"], "level": deck["name"].count("::")}
        for did, deck in col.decks.decks.items()
        if deck.get("name")
    ]
    return _ok({"decks": sorted(decks, key=lambda deck: deck["name"].lower())})


def _note_ids(deck_id: int | None = None, model_id: int | None = None) -> list[int]:
    col = _collection()
    if not col:
        return []
    if deck_id is None:
        query = f"mid:{int(model_id)}" if model_id is not None else ""
        return col.find_notes(query)
    # In Anki 25, `decks.decks` is a DecksDictProxy (iteration only); use
    # the public DeckManager method for an individual deck lookup.
    root = col.decks.get(int(deck_id))
    if not root:
        return []
    root_name = root.get("name", "")
    # Anki's `did:` predicate is exact. Build the descendant set explicitly so
    # selecting "A" includes notes in A::B, A::C, and deeper descendants.
    deck_ids = [
        int(did) for did, deck in col.decks.decks.items()
        if deck.get("name") == root_name or deck.get("name", "").startswith(root_name + "::")
    ]
    note_ids: set[int] = set()
    for did in deck_ids:
        query = f"did:{did}"
        if model_id is not None:
            query += f" mid:{int(model_id)}"
        note_ids.update(col.find_notes(query))
    return list(note_ids)


def list_source_models(deck_id: int | None = None) -> dict:
    col = _collection()
    if not col:
        return _error("E_COLLECTION_CLOSED", "Open a profile before reading note types.")
    if deck_id is None:
        return _error("E_DECK_REQUIRED", "Choose a deck before choosing a note type.")
    if not col.decks.get(int(deck_id)):
        return _error("E_DECK_NOT_FOUND", "The selected deck no longer exists.")
    ids = _note_ids(deck_id=deck_id)
    model_ids = {int(col.get_note(nid).mid) for nid in ids}
    models = []
    for mid in model_ids:
        model = col.models.get(mid)
        if model:
            models.append({"id": mid, "name": model.get("name", str(mid))})
    return _ok({"models": sorted(models, key=lambda model: model["name"].lower())})


def list_source_fields(model_id: int) -> dict:
    col = _collection()
    if not col:
        return _error("E_COLLECTION_CLOSED", "Open a profile before reading fields.")
    model = col.models.get(int(model_id))
    if not model:
        return _error("E_MODEL_NOT_FOUND", "The selected note type no longer exists.")
    return _ok({"fields": [field["name"] for field in model.get("flds", [])]})


def sample_vocab_pairs(
    *, deck_id: int | None, model_id: int, term_field: str, definition_field: str,
    limit: int = 50, excluded_pair_keys: list[str] | None = None,
    weak_words: list[str] | None = None,
) -> dict:
    """Sample de-duplicated pairs.  The hard cap is deliberately server-side."""
    col = _collection()
    if not col:
        return _error("E_COLLECTION_CLOSED", "Open a profile before reading cards.")
    if deck_id is None:
        return _error("E_DECK_REQUIRED", "Choose a deck before sampling vocabulary.")
    if not col.decks.get(int(deck_id)):
        return _error("E_DECK_NOT_FOUND", "The selected deck no longer exists.")
    limit = max(1, min(int(limit or MAX_SAMPLE_SIZE), MAX_SAMPLE_SIZE))
    model = col.models.get(int(model_id))
    flds = (model or {}).get("flds", [])
    known_fields = [field["name"] for field in flds]

    # Dynamic Field Detection: auto-detect term_field (word)
    if not term_field or term_field not in known_fields:
        term_keywords = ["front", "word", "term", "voc", "english", "keyword"]
        found_term = None
        for f in known_fields:
            if any(kw in f.lower() for kw in term_keywords):
                found_term = f
                break
        if found_term:
            term_field = found_term
        else:
            note_ids = _note_ids(deck_id=deck_id, model_id=model_id)
            if note_ids:
                note = col.get_note(note_ids[0])
                for f in known_fields:
                    val = _plain(note[f])
                    if val and len(val) < 50:
                        term_field = f
                        break
            if (not term_field or term_field not in known_fields) and known_fields:
                term_field = known_fields[0]

    # Dynamic Field Detection: auto-detect definition_field (meaning)
    if not definition_field or definition_field not in known_fields or definition_field == term_field:
        def_keywords = ["back", "meaning", "def", "translation", "vietnamese", "explain"]
        found_def = None
        for f in known_fields:
            if f == term_field:
                continue
            if any(kw in f.lower() for kw in def_keywords):
                found_def = f
                break
        if found_def:
            definition_field = found_def
        else:
            if known_fields:
                for f in known_fields:
                    if f != term_field:
                        definition_field = f
                        break
            if (not definition_field or definition_field not in known_fields or definition_field == term_field) and len(known_fields) > 1:
                definition_field = known_fields[1]

    if term_field not in known_fields or definition_field not in known_fields:
        return _error("E_FIELD_NOT_FOUND", "Choose two fields from the selected note type.")
    if term_field == definition_field:
        return _error("E_FIELDS_IDENTICAL", "Term and definition must be different fields.")

    excluded = set(excluded_pair_keys or [])
    note_ids = _note_ids(deck_id=deck_id, model_id=model_id)

    weak_words_set = {w.strip().lower() for w in (weak_words or []) if w.strip()}
    weak_note_ids = []
    normal_note_ids = []

    if weak_words_set:
        for nid in note_ids:
            try:
                note = col.get_note(nid)
                term = _plain(note[term_field]).strip().lower()
                if term in weak_words_set:
                    weak_note_ids.append(nid)
                else:
                    normal_note_ids.append(nid)
            except Exception:
                normal_note_ids.append(nid)
        random.shuffle(weak_note_ids)
        random.shuffle(normal_note_ids)
    else:
        normal_note_ids = list(note_ids)
        random.shuffle(normal_note_ids)

    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    # 1. Select weak words first (up to 30% of the limit)
    weak_limit = max(1, int(limit * 0.3)) if weak_words_set else 0
    if weak_note_ids and weak_limit > 0:
        for nid in weak_note_ids:
            try:
                note = col.get_note(nid)
                term, definition = _plain(note[term_field]), _plain(note[definition_field])
                key = (term.casefold(), definition.casefold())
                wire_key = f"{key[0]}\0{key[1]}"
                if not term or not definition or key in seen or wire_key in excluded:
                    continue
                seen.add(key)
                pairs.append({"id": nid, "key": wire_key, "term": term, "definition": definition, "is_weak": True})
                if len(pairs) == weak_limit:
                    break
            except Exception:
                continue

    # 2. Fill the remaining space with normal notes
    for nid in normal_note_ids:
        if len(pairs) >= limit:
            break
        try:
            note = col.get_note(nid)
            term, definition = _plain(note[term_field]), _plain(note[definition_field])
            key = (term.casefold(), definition.casefold())
            wire_key = f"{key[0]}\0{key[1]}"
            if not term or not definition or key in seen or wire_key in excluded:
                continue
            seen.add(key)
            pairs.append({"id": nid, "key": wire_key, "term": term, "definition": definition})
        except Exception:
            continue

    # Shuffle the final combined list to distribute weak words randomly
    random.shuffle(pairs)

    return _ok({
        "pairs": pairs, "total": len(pairs), "limit": limit,
        "exhausted": not pairs and bool(excluded),
    })
