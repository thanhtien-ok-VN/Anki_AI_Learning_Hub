from typing import Any
from .base import GameModeBase

class TranslationMode(GameModeBase):
    name = "translation"
    display_name = "AI Translation Practice"
    icon = "🌐"

    def render_ui_data(self, raw_result: dict) -> dict:
        return {
            "source_sentence": raw_result.get("source_sentence", ""),
            "reference_translation": raw_result.get("reference_translation", ""),
            "alternative_translations": raw_result.get("alternative_translations", []),
            "grading_rubric": raw_result.get("grading_rubric", ""),
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        from core.engine import normalize_answer
        user_norm = normalize_answer(str(user_input or ""))
        target_norm = normalize_answer(str(correct or ""))
        return {
            "correct": user_norm == target_norm,
            "user_answer": str(user_input or ""),
            "expected": str(correct or ""),
            "points": 1 if user_norm == target_norm else 0,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        return (data.get("source_sentence", ""), data.get("reference_translation", ""))
