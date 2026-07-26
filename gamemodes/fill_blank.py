from typing import Any
from aqt import mw
from anki.notes import Note

from .base import GameModeBase


class FillBlankMode(GameModeBase):
    name = "fill_blank"
    display_name = "Fill in the Blank"
    icon = "✍️"

    def render_ui_data(self, raw_result: dict) -> dict:
        questions = raw_result.get("questions", [])
        return {
            "questions": [
                {
                    "sentence_with_blank": q.get("sentence_with_blank", ""),
                    "full_sentence": q.get("full_sentence", ""),
                    "blank_word": q.get("blank_word", ""),
                    "options": q.get("options", []),
                    "correct_index": q.get("correct_index", 0),
                    "hint": q.get("hint", ""),
                    "explanation_short": q.get("explanation_short", ""),
                    "semantic": q.get("semantic", ""),
                    "grammar": q.get("grammar", ""),
                    "vocab_relation": q.get("vocab_relation", ""),
                }
                for q in questions
            ]
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        selected = int(user_input) if user_input is not None else -1
        correct_idx = int(correct)
        is_correct = selected == correct_idx
        return {
            "correct": is_correct,
            "selected": selected,
            "correct_index": correct_idx,
            "points": 1 if is_correct else 0,
        }

    def save_to_anki(self, questions: list, deck_name: str = "AI Learning") -> int:
        model = mw.col.models.by_name("Basic")
        if not model:
            model = mw.col.models.current()
        deck = mw.col.decks.by_name(deck_name)
        if not deck:
            deck_id = mw.col.decks.add_normal_deck_with_name(deck_name)
        else:
            deck_id = deck["id"]

        count = 0
        for q in questions:
            note = Note(mw.col, model)
            note["Front"] = q.get("sentence_with_blank", "")
            note["Back"] = q.get("full_sentence", "")
            note.note_type()["did"] = deck_id
            mw.col.add_note(note, deck_id)
            count += 1
        return count
