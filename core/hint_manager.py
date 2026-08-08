from typing import Dict, Any, Optional
from core.logger import flow
from core.languages import get_language_name
from core.i18n import t


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

        # Multiplier map: L0=1.0, L1=0.75, L2=0.50, L3+=0.0
        if hint_level <= 0:
            multiplier = 1.0
            penalty_pct = 0
        elif hint_level == 1:
            multiplier = 0.75
            penalty_pct = 25
        elif hint_level == 2:
            multiplier = 0.50
            penalty_pct = 50
        else:
            multiplier = 0.0
            penalty_pct = 100

        res = {
            "gamemode": gamemode,
            "hint_level": hint_level,
            "ui_lang": ui_lang,
            "hint_title": "",
            "content": "",
            "penalty": hint_level >= 3,
            "is_penalty": hint_level > 0,
            "score_multiplier": multiplier,
            "penalty_percent": penalty_pct,
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
            res["hint_title"] = t("hint.level_1", lang=ui_lang)
            if grammar_rule:
                res["content"] = f"Grammar Rule: {grammar_rule}"
            elif target_word:
                res["content"] = f"{t('hint.word_length', lang=ui_lang)}: {len(target_word)} characters"
            else:
                res["content"] = t("hint.structure_tip", lang=ui_lang)
        elif hint_level == 2:
            # Level 2: First letter / Contextual meaning hint
            res["hint_title"] = t("hint.level_2", lang=ui_lang)
            hints = []
            if target_word:
                hints.append(f"First letter: '{target_word[0].upper()}'")
            if meaning:
                hints.append(f"Meaning: {meaning}")
            res["content"] = " | ".join(hints) if hints else "Analyze context carefully."
        elif hint_level >= 3:
            # Level 3: Full Answer & Score Penalty
            res["hint_title"] = t("hint.level_3", lang=ui_lang)
            res["content"] = f"Answer: {target_word}" if target_word else "Solution revealed."

        return res
