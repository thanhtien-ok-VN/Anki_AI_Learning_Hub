import re
from typing import Any, List
from .base import GameModeBase


class FillBlankMode(GameModeBase):
    name = "fill_blank"
    display_name = "Fill in the Blank"
    icon = "✍️"

    def render_ui_data(self, raw_result: dict) -> dict:
        import random

        questions = raw_result.get("questions", [raw_result])
        rendered_questions = []
        for q in questions:
            sentence = q.get("sentence", "").strip()
            target_word = q.get("target_word", "").strip()

            # Auto-masking: calculate sentence_with_blank
            sentence_with_blank = sentence
            blank_patterns = [r"______+", r"___+", r"\[BLANK\]", r"\(\.\.\.\)", r"____+"]
            has_blank = any(re.search(pat, sentence, re.IGNORECASE) for pat in blank_patterns)

            if has_blank:
                # Standardize existing blank placeholders to ______
                for pat in blank_patterns:
                    sentence_with_blank = re.sub(pat, "______", sentence_with_blank, flags=re.IGNORECASE)
            elif target_word:
                # Replace first occurrence of target_word with ______ (case-insensitive)
                pattern = r"\b" + re.escape(target_word) + r"\b"
                if re.search(pattern, sentence, re.IGNORECASE):
                    sentence_with_blank = re.sub(pattern, "______", sentence, count=1, flags=re.IGNORECASE)
                elif re.search(re.escape(target_word), sentence, re.IGNORECASE):
                    sentence_with_blank = re.sub(re.escape(target_word), "______", sentence, count=1, flags=re.IGNORECASE)
                else:
                    sentence_with_blank = f"{sentence} ( ______ )"
            else:
                sentence_with_blank = f"{sentence} ( ______ )"

            options = [
                {
                    "word": o.get("word", ""),
                    "is_correct": o.get("is_correct", False),
                    "type": o.get("type", ""),
                    "reason": o.get("reason", ""),
                }
                for o in q.get("options", [])
            ]

            # Xáo trộn options ngẫu nhiên
            indices = list(range(len(options)))
            random.shuffle(indices)
            shuffled_options = [options[j] for j in indices]

            # Tính correct_index mới sau khi xáo trộn
            correct_index = -1
            for idx, opt in enumerate(shuffled_options):
                if opt["is_correct"]:
                    correct_index = idx
                    break

            rendered_questions.append(
                {
                    "sentence": sentence,
                    "sentence_with_blank": sentence_with_blank,
                    "target_word": target_word,
                    "meaning": q.get("meaning", ""),
                    "full_translation": q.get("full_translation", ""),
                    "options": shuffled_options,
                    "correct_index": correct_index,
                    "explanation": q.get("explanation", ""),
                    "grammar_note": q.get("grammar_note", ""),
                    "user_definition": q.get("user_definition", ""),
                }
            )

        return {"questions": rendered_questions}

    def check_answer(self, user_input: Any, correct: Any, hint_level: int = 0) -> dict:
        selected_idx = int(user_input) if user_input is not None else -1
        correct_idx = -1
        options = correct if isinstance(correct, list) else []
        for i, opt in enumerate(options):
            if opt.get("is_correct"):
                correct_idx = i
                break
        is_correct = selected_idx == correct_idx

        # Calculate points with hint penalty
        if not is_correct:
            points = 0.0
        elif hint_level == 0:
            points = 1.0
        elif hint_level == 1:
            points = 0.75
        elif hint_level == 2:
            points = 0.50
        else:
            points = 0.0

        return {
            "correct": is_correct,
            "selected_index": selected_idx,
            "correct_index": correct_idx,
            "hint_level": hint_level,
            "points": points,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        return (data.get("sentence_with_blank", data.get("sentence", "")), data.get("full_translation", ""))
