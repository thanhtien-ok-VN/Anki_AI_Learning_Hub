from typing import Any
from .base import GameModeBase


class SentenceTransformMode(GameModeBase):
    name = "sentence_transform"
    display_name = "Sentence Transformation"
    icon = "🔄"

    FOCUS_OPTIONS = ["voice", "conditional", "reported", "comparative"]

    def render_ui_data(self, raw_result: dict) -> dict:
        # Supports both a single dict or questions list wrapper
        questions = raw_result.get("questions", [raw_result])
        return {
            "questions": [
                {
                    "original_sentence": q.get("original", q.get("original_sentence", "")),
                    "instruction": q.get("prompt", q.get("instruction", "")),
                    "expected_answer": q.get("expected_answer", ""),
                    "normalized_answer": q.get("normalized_answer", ""),
                    "acceptable_variations": q.get("acceptable_variations", []),
                    "forbidden_words": q.get("forbidden_words", []),
                    "grammar_rule": q.get("grammar_rule", ""),
                    "common_errors": q.get("common_errors", []),
                }
                for q in questions
            ]
        }

    def check_answer(self, user_input: Any, correct: Any, hint_level: int = 0) -> dict:
        from core.engine import normalize_answer
        user_norm = normalize_answer(str(user_input or ""))
        expected_norm = normalize_answer(str(correct or ""))
        is_correct = user_norm == expected_norm

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
            "score": points * 10.0,
            "exact_match": is_correct,
            "user_answer": str(user_input or ""),
            "expected": str(correct or ""),
            "hint_level": hint_level,
            "feedback": (
                "Perfect!"
                if is_correct
                else "Review the grammar rule and try again."
            ),
            "points": points,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        front = f"{data.get('instruction', 'Transform:')}\n\n{data.get('original_sentence', '')}"
        return (front, data.get("expected_answer", ""))
