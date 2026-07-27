import re
from typing import Any

from .base import GameModeBase


class SentenceTransformMode(GameModeBase):
    name = "sentence_transform"
    display_name = "Sentence Transformation"
    icon = "🔄"

    FOCUS_OPTIONS = ["voice", "conditional", "reported", "comparative"]

    def render_ui_data(self, raw_result: dict) -> dict:
        questions = raw_result.get("questions", [])
        return {
            "questions": [
                {
                    "original_sentence": q.get("original_sentence", ""),
                    "instruction": q.get("instruction", ""),
                    "hint_word": q.get("hint_word", ""),
                    "expected_answer": q.get("expected_answer", ""),
                    "grammar_rule": q.get("grammar_rule", ""),
                    "focus": q.get("focus", "voice"),
                }
                for q in questions
            ]
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        user_text = str(user_input).strip() if user_input else ""
        expected = str(correct).strip() if correct else ""

        user_norm = re.sub(r"\s+", " ", user_text.lower()).strip()
        expected_norm = re.sub(r"\s+", " ", expected.lower()).strip()

        exact_match = user_norm == expected_norm
        keyword_score = 0.0

        if exact_match:
            keyword_score = 1.0
        elif user_norm and expected_norm:
            user_words = user_norm.split()
            expected_words = expected_norm.split()
            n, m = len(user_words), len(expected_words)
            dp = [[0] * (m + 1) for _ in range(n + 1)]
            for i in range(1, n + 1):
                for j in range(1, m + 1):
                    if user_words[i - 1] == expected_words[j - 1]:
                        dp[i][j] = dp[i - 1][j - 1] + 1
                    else:
                        dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
            keyword_score = dp[n][m] / m if m else 0

        is_correct = exact_match or (
            keyword_score > 0.8 and len(user_norm) > len(expected_norm) * 0.7
        )

        return {
            "correct": is_correct,
            "score": round(keyword_score, 2),
            "exact_match": exact_match,
            "user_answer": user_text,
            "expected": expected,
            "feedback": (
                "Perfect!"
                if exact_match
                else (
                    "Close! Minor differences in structure."
                    if is_correct
                    else "Review the grammar rule and try again."
                )
            ),
            "points": 1 if is_correct else 0,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        front = f"{data.get('instruction', 'Transform:')}\n\n{data.get('original_sentence', '')}"
        return (front, data.get("expected_answer", ""))
