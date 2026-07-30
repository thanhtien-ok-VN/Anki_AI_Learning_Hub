from typing import Any, List
from .base import GameModeBase

class FillBlankMode(GameModeBase):
    name = "fill_blank"
    display_name = "Fill in the Blank"
    icon = "✍️"

    def render_ui_data(self, raw_result: dict) -> dict:
        questions = raw_result.get("questions", [raw_result])
        return {
            "questions": [
                {
                    "sentence": q.get("sentence", ""),
                    "target_word": q.get("target_word", ""),
                    "meaning_vi": q.get("meaning_vi", ""),
                    "full_translation": q.get("full_translation", ""),
                    "options": [
                        {
                            "word": o.get("word", ""),
                            "is_correct": o.get("is_correct", False),
                            "type": o.get("type", ""),
                            "reason": o.get("reason", ""),
                        }
                        for o in q.get("options", [])
                    ],
                    "explanation": q.get("explanation", ""),
                    "grammar_note": q.get("grammar_note", ""),
                    "user_definition": q.get("user_definition", ""),
                }
                for q in questions
            ]
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        selected_idx = int(user_input) if user_input is not None else -1
        correct_idx = -1
        options = correct if isinstance(correct, list) else []
        for i, opt in enumerate(options):
            if opt.get("is_correct"):
                correct_idx = i
                break
        is_correct = selected_idx == correct_idx
        return {
            "correct": is_correct,
            "selected_index": selected_idx,
            "correct_index": correct_idx,
            "points": 1 if is_correct else 0,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        return (data.get("sentence", ""), data.get("full_translation", ""))
