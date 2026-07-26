from typing import Any

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

    def _format_anki_note(self, data: dict) -> tuple:
        return (data.get("sentence_with_blank", ""), data.get("full_sentence", ""))
