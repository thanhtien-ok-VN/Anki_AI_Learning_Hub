from typing import Any
from aqt import mw
from anki.notes import Note

from .base import GameModeBase


class ClozeMode(GameModeBase):
    name = "cloze"
    display_name = "Cloze Paragraph"
    icon = "📖"

    def render_ui_data(self, raw_result: dict) -> dict:
        blanks = raw_result.get("blanks", [])
        return {
            "paragraph_with_blanks": raw_result.get("paragraph_with_blanks", ""),
            "paragraph_full": raw_result.get("paragraph_full", ""),
            "blanks": [
                {
                    "blank_id": b.get("blank_id", i),
                    "correct_word": b.get("correct_word", ""),
                    "options": b.get("options", []),
                    "correct_index": b.get("correct_index", 0),
                    "explanation_short": b.get("explanation_short", ""),
                    "explanation": b.get("explanation", ""),
                }
                for i, b in enumerate(blanks)
            ],
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        user_word = str(user_input).strip().lower() if user_input else ""
        correct_word = str(correct).strip().lower() if correct else ""
        return {
            "correct": user_word == correct_word,
            "user_word": user_word,
            "correct_word": correct_word,
            "points": 1 if user_word == correct_word else 0,
        }

    def save_to_anki(self, data: dict, deck_name: str = "AI Learning") -> int:
        model = mw.col.models.by_name("Basic")
        if not model:
            model = mw.col.models.current()
        deck = mw.col.decks.by_name(deck_name)
        if not deck:
            deck_id = mw.col.decks.add_normal_deck_with_name(deck_name)
        else:
            deck_id = deck["id"]

        note = Note(mw.col, model)
        paragraph = data.get("paragraph_full", "") or data.get("paragraph_with_blanks", "")
        note["Front"] = "Cloze: Fill the blanks"
        note["Back"] = paragraph
        note.note_type()["did"] = deck_id
        mw.col.add_note(note, deck_id)
        return 1
