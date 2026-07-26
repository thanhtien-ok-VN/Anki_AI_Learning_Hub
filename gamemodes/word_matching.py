import random
from typing import Any, Optional
from aqt import mw
from anki.notes import Note

from .base import GameModeBase


class WordMatchingMode(GameModeBase):
    name = "matching"
    display_name = "Word Matching"
    icon = "🔗"
    is_offline = True

    BUILTIN_PAIRS = [
        ("ubiquitous", "present, appearing, or found everywhere"),
        ("pragmatic", "dealing with things in a practical way"),
        ("ambiguous", "open to more than one interpretation"),
        ("eloquent", "fluent or persuasive in speaking or writing"),
        ("resilient", "able to recover quickly from difficulties"),
        ("ephemeral", "lasting for a very short time"),
        ("consensus", "a general agreement among a group"),
        ("deteriorate", "to become progressively worse"),
        ("scrutiny", "critical observation or examination"),
        ("advocate", "to publicly recommend or support"),
        ("inevitable", "certain to happen; unavoidable"),
        ("mitigate", "to make less severe or serious"),
        ("paradigm", "a typical example or pattern of something"),
        ("verbose", "using more words than needed"),
        ("concise", "giving a lot of information briefly"),
        ("hypothesis", "a proposed explanation made as a starting point"),
        ("comprehensive", "including all elements or aspects"),
        ("perceive", "to become aware of through the senses"),
        ("plausible", "seeming reasonable or probable"),
        ("articulate", "having the ability to speak fluently and clearly"),
    ]

    def __init__(self, api_client=None, prompt_mgr=None):
        super().__init__(api_client, prompt_mgr)

    def generate(self, **kwargs) -> dict:
        count = kwargs.get("count", 8)
        source = kwargs.get("source", "builtin")
        selected_pairs = kwargs.get("vocab_pairs") or []

        if selected_pairs:
            pairs = [(pair.get("term", ""), pair.get("definition", "")) for pair in selected_pairs]
        elif source == "deck":
            pairs = self._extract_from_deck(kwargs.get("deck_name", ""), count)
        else:
            pairs = self.BUILTIN_PAIRS[:]

        selected = random.sample(pairs, min(count, len(pairs)))
        left = [p[0] for p in selected]
        right = [p[1] for p in selected]
        random.shuffle(left)
        random.shuffle(right)

        return {
            "error": False,
            "pairs": [
                {"term": p[0], "definition": p[1]} for p in selected
            ],
            "left_column": left,
            "right_column": right,
        }

    def _extract_from_deck(self, deck_name: str, count: int) -> list:
        pairs = []
        try:
            note_ids = mw.col.find_notes(f'deck:"{deck_name}"')
            for nid in note_ids[:count * 3]:
                note = mw.col.get_note(nid)
                fields = list(note.keys())
                if len(fields) >= 2:
                    pairs.append((note[fields[0]], note[fields[1]]))
                if len(pairs) >= count:
                    break
        except Exception:
            pass
        return pairs[:count] if pairs else self.BUILTIN_PAIRS[:count]

    def render_ui_data(self, raw_result: dict) -> dict:
        return raw_result

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        return {
            "correct": str(user_input) == str(correct),
            "selected": user_input,
            "expected": correct,
            "points": 1 if str(user_input) == str(correct) else 0,
        }

    def save_to_anki(self, pairs: list, deck_name: str = "AI Learning") -> int:
        model = mw.col.models.by_name("Basic")
        if not model:
            model = mw.col.models.current()
        deck = mw.col.decks.by_name(deck_name)
        if not deck:
            deck_id = mw.col.decks.add_normal_deck_with_name(deck_name)
        else:
            deck_id = deck["id"]

        count = 0
        for p in pairs:
            note = Note(mw.col, model)
            note["Front"] = p.get("term", "")
            note["Back"] = p.get("definition", "")
            note.note_type()["did"] = deck_id
            mw.col.add_note(note, deck_id)
            count += 1
        return count
