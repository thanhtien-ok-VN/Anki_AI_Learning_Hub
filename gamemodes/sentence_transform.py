import re
from typing import Any
from aqt import mw
from anki.notes import Note

from .base import GameModeBase


class SentenceTransformMode(GameModeBase):
    name = "sentence_transform"
    display_name = "Sentence Transformation"
    icon = "🔄"

    FOCUS_OPTIONS = ["voice", "conditional", "reported", "comparative"]

    def render_ui_data(self, raw_result: dict) -> dict:
        questions = raw_result.get("questions", [])
        return {
            "questions": [
                {
                    "original_sentence": q.get("original_sentence", ""),
                    "instruction": q.get("instruction", ""),
                    "hint_word": q.get("hint_word", ""),
                    "expected_answer": q.get("expected_answer", ""),
                    "grammar_rule": q.get("grammar_rule", ""),
                    "focus": q.get("focus", "voice"),
                }
                for q in questions
            ]
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        user_text = str(user_input).strip() if user_input else ""
        expected = str(correct).strip() if correct else ""

        user_norm = re.sub(r'\s+', ' ', user_text.lower()).strip()
        expected_norm = re.sub(r'\s+', ' ', expected.lower()).strip()

        exact_match = user_norm == expected_norm
        keyword_score = 0.0

        if exact_match:
            keyword_score = 1.0
        elif user_norm and expected_norm:
            user_words = set(user_norm.split())
            expected_words = set(expected_norm.split())
            if expected_words:
                overlap = len(user_words & expected_words)
                keyword_score = overlap / len(expected_words)

        is_correct = exact_match or (keyword_score > 0.8 and len(user_norm) > len(expected_norm) * 0.7)

        return {
            "correct": is_correct,
            "score": round(keyword_score, 2),
            "exact_match": exact_match,
            "user_answer": user_text,
            "expected": expected,
            "feedback": "Perfect!" if exact_match else (
                "Close! Minor differences in structure." if is_correct else
                "Review the grammar rule and try again."
            ),
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
            note["Front"] = f"{q.get('instruction', 'Transform:')}\n\n{q.get('original_sentence', '')}"
            note["Back"] = q.get("expected_answer", "")
            note.note_type()["did"] = deck_id
            mw.col.add_note(note, deck_id)
            count += 1
        return count
