"""Vocabulary pair extraction, dynamic field detection, and weak-word priority sampling."""
from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from core.anki.main_thread import (
    get_collection,
    ok_response,
    error_response,
    plain_text,
    run_on_main,
)
from core.anki.queries import get_note_ids

MAX_SAMPLE_SIZE = 50


def detect_fields(known_fields: List[str], term_field: str, definition_field: str, col: Any, sample_note_id: Optional[int]) -> Tuple[str, str]:
    """Auto-detect appropriate term and definition fields if not specified."""
    local_term_field = term_field
    local_def_field = definition_field

    # Auto-detect term_field (word)
    if not local_term_field or local_term_field not in known_fields:
        term_keywords = ["front", "word", "term", "voc", "english", "keyword"]
        found_term = None
        for f in known_fields:
            if any(kw in f.lower() for kw in term_keywords):
                found_term = f
                break
        if found_term:
            local_term_field = found_term
        else:
            if sample_note_id:
                try:
                    note = col.get_note(sample_note_id)
                    for f in known_fields:
                        val = plain_text(note[f])
                        if val and len(val) < 50:
                            local_term_field = f
                            break
                except Exception:
                    pass
            if (not local_term_field or local_term_field not in known_fields) and known_fields:
                local_term_field = known_fields[0]

    # Auto-detect definition_field (meaning)
    if (
        not local_def_field
        or local_def_field not in known_fields
        or local_def_field == local_term_field
    ):
        def_keywords = ["back", "meaning", "def", "translation", "vietnamese", "explain"]
        found_def = None
        for f in known_fields:
            if f == local_term_field:
                continue
            if any(kw in f.lower() for kw in def_keywords):
                found_def = f
                break
        if found_def:
            local_def_field = found_def
        else:
            if known_fields:
                for f in known_fields:
                    if f != local_term_field:
                        local_def_field = f
                        break
            if (
                not local_def_field
                or local_def_field not in known_fields
                or local_def_field == local_term_field
            ) and len(known_fields) > 1:
                local_def_field = known_fields[1]

    return local_term_field, local_def_field


def sample_vocab_pairs(
    *,
    deck_id: Optional[int],
    model_id: int,
    term_field: str,
    definition_field: str,
    limit: int = 50,
    excluded_pair_keys: Optional[List[str]] = None,
    weak_words: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Sample de-duplicated vocabulary pairs bounded by server-side limit."""
    def _inner():
        col = get_collection()
        if not col:
            return error_response("E_COLLECTION_CLOSED", "Open a profile before reading cards.")
        if deck_id is None:
            return error_response("E_DECK_REQUIRED", "Choose a deck before sampling vocabulary.")
        try:
            did = int(deck_id)
        except (ValueError, TypeError):
            return error_response("E_DECK_INVALID", "Invalid deck ID specified.")
        if not col.decks.get(did):
            return error_response("E_DECK_NOT_FOUND", "The selected deck no longer exists.")

        if model_id is None:
            return error_response("E_MODEL_REQUIRED", "Choose a note type before sampling vocabulary.")
        try:
            mid = int(model_id)
        except (ValueError, TypeError):
            return error_response("E_MODEL_INVALID", "Invalid note type ID specified.")

        clamped_limit = max(1, min(int(limit or MAX_SAMPLE_SIZE), MAX_SAMPLE_SIZE))
        model = col.models.get(mid)
        flds = (model or {}).get("flds", [])
        known_fields = [field["name"] for field in flds]

        note_ids = get_note_ids(deck_id=did, model_id=mid)
        sample_nid = note_ids[0] if note_ids else None

        local_term_field, local_def_field = detect_fields(
            known_fields, term_field, definition_field, col, sample_nid
        )

        if local_term_field not in known_fields or local_def_field not in known_fields:
            return error_response("E_FIELD_NOT_FOUND", "Choose two fields from the selected note type.")
        if local_term_field == local_def_field:
            return error_response("E_FIELDS_IDENTICAL", "Term and definition must be different fields.")

        excluded = set(excluded_pair_keys or [])
        weak_words_set = {w.strip().lower() for w in (weak_words or []) if w.strip()}
        pairs: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, str]] = set()

        # 1. Select weak words first (up to 30% of the limit)
        weak_limit = max(1, int(clamped_limit * 0.3)) if weak_words_set else 0
        weak_nids_used: Set[int] = set()

        if weak_words_set and weak_limit > 0:
            candidate_weak_nids: List[int] = []
            note_ids_set = set(note_ids)

            # Fast targeted search per weak word via find_notes
            for w in weak_words_set:
                if len(candidate_weak_nids) >= weak_limit * 5:
                    break
                safe_w = re.sub(r'["\\]', "", w).strip()
                if not safe_w:
                    continue
                try:
                    found = col.find_notes(f'"{safe_w}"')
                    for nid in found:
                        if nid in note_ids_set and nid not in candidate_weak_nids:
                            candidate_weak_nids.append(nid)
                except Exception:
                    pass

            if not candidate_weak_nids and len(note_ids) <= 300:
                for nid in note_ids:
                    try:
                        note = col.get_note(nid)
                        term = plain_text(note[local_term_field]).strip().lower()
                        if term in weak_words_set:
                            candidate_weak_nids.append(nid)
                    except Exception:
                        pass

            random.shuffle(candidate_weak_nids)
            for nid in candidate_weak_nids:
                if len(pairs) >= weak_limit:
                    break
                try:
                    note = col.get_note(nid)
                    term = plain_text(note[local_term_field]).strip()
                    definition = plain_text(note[local_def_field]).strip()
                    if term.lower() not in weak_words_set:
                        continue
                    key = (term.casefold(), definition.casefold())
                    wire_key = f"{key[0]}\0{key[1]}"
                    if not term or not definition or key in seen or wire_key in excluded:
                        continue
                    seen.add(key)
                    pairs.append(
                        {
                            "id": nid,
                            "key": wire_key,
                            "term": term,
                            "definition": definition,
                            "is_weak": True,
                        }
                    )
                    weak_nids_used.add(nid)
                except Exception:
                    continue

        # 2. Fill remaining space with normal notes bounded by clamped_limit
        remaining_nids = [nid for nid in note_ids if nid not in weak_nids_used]
        random.shuffle(remaining_nids)

        for nid in remaining_nids:
            if len(pairs) >= clamped_limit:
                break
            try:
                note = col.get_note(nid)
                term = plain_text(note[local_term_field])
                definition = plain_text(note[local_def_field])
                key = (term.casefold(), definition.casefold())
                wire_key = f"{key[0]}\0{key[1]}"
                if not term or not definition or key in seen or wire_key in excluded:
                    continue
                seen.add(key)
                pairs.append({"id": nid, "key": wire_key, "term": term, "definition": definition})
            except Exception:
                continue

        random.shuffle(pairs)

        return ok_response(
            {
                "pairs": pairs,
                "total": len(pairs),
                "limit": clamped_limit,
                "exhausted": not pairs and bool(excluded),
            }
        )

    return run_on_main(_inner)
