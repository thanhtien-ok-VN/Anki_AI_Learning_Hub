from typing import Any
from .base import GameModeBase
from gamemodes.manifest import GameModeManifest

class TranslationMode(GameModeBase):
    name = "translation"
    display_name = "AI Translation Practice"
    icon = "🌐"
    manifest = GameModeManifest(
        id="translation",
        icon="🌐",
        title_key="translation.title",
        default_title="Translation",
        desc_key="translation.desc",
        default_desc="Translate sentences and get AI grading",
        min_items=1,
        max_items=1,
        default_items=1,
        requires_anki_cards=False,
    )

    def render_ui_data(self, raw_result: dict) -> dict:
        return {
            "source_sentence": raw_result.get("source_sentence", ""),
            "reference_translation": raw_result.get("reference_translation", ""),
            "alternative_translations": raw_result.get("alternative_translations", []),
            "grading_rubric": raw_result.get("grading_rubric", ""),
        }

    def check_answer(self, user_input: Any, correct: Any, hint_level: int = 0) -> dict:
        from core.sanitizer import normalize_answer
        user_norm = normalize_answer(str(user_input or ""))
        target_norm = normalize_answer(str(correct or ""))
        return {
            "correct": user_norm == target_norm,
            "user_answer": str(user_input or ""),
            "expected": str(correct or ""),
            "points": 1 if user_norm == target_norm else 0,
        }

    @staticmethod
    def build_grading_prompt_data(data: dict, common: dict) -> dict:
        return {
            **common,
            "source_lang": common.get("feedback_lang", ""),
            "target_lang": common.get("learn_lang", ""),
            "source_sentence": data.get("source_sentence", data.get("source_text", "")),
            "reference_translation": data.get("reference_translation", data.get("expected", "")),
            "user_target": data.get("user_answer", ""),
        }

    def _format_anki_note(self, data: dict) -> tuple:
        return (data.get("source_sentence", ""), data.get("reference_translation", ""))
