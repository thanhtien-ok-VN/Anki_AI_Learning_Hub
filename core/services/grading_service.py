"""Grading & Evaluation Service.

Orchestrates answer verification, hint deduction, and pedagogical AI grading.
"""
from typing import Any, Callable, Dict, Optional
from core.languages import get_language_name, valid_learn_lang, valid_ui_lang
from core.language_normalizer import normalize_language_fields
from core.sanitizer import sanitize_dict
from core.hint_manager import HintManager
from core.ai_grader import get_grader_prompt
from core.logger import log, flow


class GradingService:
    def check_answer(self, gamemode_obj: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        user_input = data.get("user_input", "")
        correct = data.get("correct", "")
        hint_level = int(data.get("hint_level", 0))

        if gamemode_obj and hasattr(gamemode_obj, "check_answer"):
            res = gamemode_obj.check_answer(user_input, correct, hint_level=hint_level)
            return res

        return {
            "correct": str(user_input).strip().lower() == str(correct).strip().lower(),
            "user_answer": str(user_input),
            "expected": str(correct),
        }

    def get_hint(self, data: Dict[str, Any], ui_lang: str = "en") -> Dict[str, Any]:
        gamemode = data.get("gamemode", "fill_blank")
        question_data = data.get("question_data", {})
        hint_level = data.get("hint_level", 1)
        return HintManager.get_hint_data(gamemode, question_data, hint_level, ui_lang)

    def ai_grade(
        self,
        api_client: Any,
        data: Dict[str, Any],
        settings: Any,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        data = normalize_language_fields(dict(data or {}))
        gamemode = data.get("gamemode", "fill_blank")
        learn_lang = valid_learn_lang(settings.get("learn_lang"))
        ui_lang = valid_ui_lang(settings.get("ui_lang"))
        level = data.get("level", "intermediate")

        learn_lang_full = get_language_name(learn_lang)
        ui_lang_full = get_language_name(ui_lang)

        flow(
            phase="GRADER",
            message=f"AI Grade evaluated for gamemode={gamemode}, feedback_lang={ui_lang_full}"
        )

        hint_level = data.get("hint_level", 0)
        common = {
            "learn_lang": learn_lang_full,
            "level": level,
            "feedback_lang": ui_lang_full,
            "hint_level": hint_level,
        }

        from gamemodes import registry as gamemode_registry
        mode_obj = gamemode_registry.get(gamemode)
        if mode_obj and hasattr(mode_obj, "build_grading_prompt_data"):
            prompt_data = mode_obj.build_grading_prompt_data(data, common)
        else:
            prompt_data = {
                **common,
                "question": data.get("question", ""),
                "expected": data.get("expected", ""),
                "user_answer": data.get("user_answer", ""),
            }

        prompt = get_grader_prompt(gamemode, **prompt_data)

        if not api_client:
            return {"error": True, "error_code": "E_NO_KEYS", "message": "No API key"}

        result = api_client.generate_text_result(
            prompt, temperature=0.3, progress_callback=progress_callback
        )
        if result.get("error"):
            return result
        return sanitize_dict(normalize_language_fields(result))
