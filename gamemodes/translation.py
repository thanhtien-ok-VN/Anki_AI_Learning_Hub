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

    def grade_with_ai(
        self,
        source_text: str,
        expected: str,
        user_text: str,
        level: str,
        learn_lang: str,
        source_lang: str = "Vietnamese",
    ) -> dict:
        from core.ai_grader import TRANSLATION_GRADER

        prompt = TRANSLATION_GRADER.format(
            source_lang=source_lang,
            target_lang=learn_lang,
            source_text=source_text,
            expected_target=expected,
            user_target=user_text,
            level=level,
        )
        if self.api:
            result = self.api.generate_text(prompt, temperature=0.3)
            if result:
                import json

                try:
                    return json.loads(result)
                except Exception:
                    pass
        return {"correct": False, "score": 0, "explanation": "AI grading unavailable"}

    def _format_anki_note(self, data: dict) -> tuple:
        return (data.get("source_sentence", ""), data.get("reference_translation", ""))
