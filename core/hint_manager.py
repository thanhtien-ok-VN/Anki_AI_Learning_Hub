from typing import Dict, Any, Optional
from core.logger import flow
from core.languages import get_language_name


class HintManager:
    """Centralized Backend Hint Manager supporting 3-Tier Multilingual Hints across 8 Gamemodes."""

    @staticmethod
    def get_hint_data(
        gamemode: str,
        question_data: Dict[str, Any],
        hint_level: int,
        ui_lang: str = "en"
    ) -> Dict[str, Any]:
        ui_lang_name = get_language_name(ui_lang)
        flow(
            phase="HINT",
            message=f"Hint requested: gamemode={gamemode}, hint_level={hint_level}, ui_lang={ui_lang_name}"
        )

        res = {
            "gamemode": gamemode,
            "hint_level": hint_level,
            "ui_lang": ui_lang,
            "hint_title": "",
            "content": "",
            "penalty": False
        }

        target_word = (
            question_data.get("target_word") or
            question_data.get("answer") or
            question_data.get("expected_answer") or
            question_data.get("correct_sentence") or
            ""
        )
        meaning = (
            question_data.get("meaning") or
            question_data.get("full_translation") or
            ""
        )
        grammar_rule = question_data.get("grammar_note") or question_data.get("grammar_rule") or ""

        if hint_level == 1:
            # Level 1: Structure / Part of Speech hint
            res["hint_title"] = "Level 1: Structure & Grammar"
            if grammar_rule:
                res["content"] = f"Grammar Rule: {grammar_rule}"
            elif target_word:
                res["content"] = f"Word length: {len(target_word)} characters"
            else:
                res["content"] = "Pay attention to sentence structure and context."
        elif hint_level == 2:
            # Level 2: First letter / Contextual meaning hint
            res["hint_title"] = "Level 2: First Character & Meaning"
            hints = []
            if target_word:
                hints.append(f"First letter: '{target_word[0].upper()}'")
            if meaning:
                hints.append(f"Meaning: {meaning}")
            res["content"] = " | ".join(hints) if hints else "Analyze context carefully."
        elif hint_level >= 3:
            # Level 3: Full Answer & Score Penalty
            res["hint_title"] = "Level 3: Correct Answer (0 Points)"
            res["content"] = f"Answer: {target_word}" if target_word else "Solution revealed."
            res["penalty"] = True

        return res
