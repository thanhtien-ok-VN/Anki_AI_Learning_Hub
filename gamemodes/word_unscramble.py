import random
from typing import Any
from .base import GameModeBase

class WordUnscrambleMode(GameModeBase):
    name = "unscramble"
    display_name = "Word Unscramble"
    icon = "🧩"

    def fisher_yates_shuffle(self, words: list[str]) -> list[str]:
        arr = list(words)
        for i in range(len(arr) - 1, 0, -1):
            j = random.randint(0, i)
            arr[i], arr[j] = arr[j], arr[i]
        return arr

    def render_ui_data(self, raw_result: dict) -> dict:
        sentences = raw_result.get("questions", raw_result.get("sentences", []))
        return {
            "questions": [
                {
                    "correct_sentence": s.get("correct_sentence", ""),
                    "shuffled_words": self.fisher_yates_shuffle(
                        s.get("correct_sentence", "").split()
                    ),
                    "hint": s.get("hint", ""),
                    "meaning_vi": s.get("meaning_vi", ""),
                    "key_vocabulary": s.get("key_vocabulary", []),
                    "difficulty_reason": s.get("difficulty_reason", ""),
                    "grammar_note": s.get("grammar_note", ""),
                    "core_structure": s.get("core_structure", ""),
                    "word_count": len(s.get("correct_sentence", "").split()),
                }
                for s in sentences
            ]
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        user_str = (
            " ".join(user_input) if isinstance(user_input, list) else str(user_input)
        )
        correct_str = str(correct) if correct else ""
        norm_user = " ".join(user_str.strip().split()).lower()
        norm_correct = " ".join(correct_str.strip().split()).lower()
        is_correct = norm_user == norm_correct

        user_words = norm_user.split()
        correct_words = norm_correct.split()
        correct_positions = sum(
            1
            for i, w in enumerate(user_words)
            if i < len(correct_words) and w == correct_words[i]
        )

        return {
            "correct": is_correct,
            "user_sentence": user_str,
            "expected": correct_str,
            "correct_positions": correct_positions,
            "total_positions": len(correct_words),
            "points": 1 if is_correct else 0,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        shuffled = data.get("shuffled_words")
        if isinstance(shuffled, list):
            shuffled = " ".join(shuffled)
        else:
            shuffled = " ".join(
                self.fisher_yates_shuffle(data.get("correct_sentence", "").split())
            )
        return (f"Unscramble: {shuffled}", data.get("correct_sentence", ""))
