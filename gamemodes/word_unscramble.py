import random
from typing import Any
from aqt import mw
from anki.notes import Note

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
        sentences = raw_result.get("sentences", [])
        return {
            "questions": [
                {
                    "correct_sentence": s.get("correct_sentence", ""),
                    "shuffled_words": self.fisher_yates_shuffle(
                        s.get("correct_sentence", "").split()
                    ),
                    "hint": s.get("hint", ""),
                    "translation": s.get("translation", ""),
                    "word_count": len(s.get("correct_sentence", "").split()),
                }
                for s in sentences
            ]
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        user_str = " ".join(user_input) if isinstance(user_input, list) else str(user_input)
        correct_str = str(correct) if correct else ""
        norm_user = " ".join(user_str.strip().split()).lower()
        norm_correct = " ".join(correct_str.strip().split()).lower()
        is_correct = norm_user == norm_correct

        user_words = norm_user.split()
        correct_words = norm_correct.split()
        correct_positions = sum(
            1 for i, w in enumerate(user_words)
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

    def save_to_anki(self, questions: list, deck_name: str = "AI Learning") -> int:
        model = mw.col.models.by_name("Basic")
        if not model:
            model = mw.col.models.current()
        deck = mw.col.decks.by_name(deck_name)
        if not deck:
            deck_id = mw.col.decks.add_normal_deck_with_name(deck_name)
        else:
            deck_id = deck["id"]

        count = 0
        for q in questions:
            note = Note(mw.col, model)
            note["Front"] = f"Unscramble: {' '.join(self.fisher_yates_shuffle(q.get('correct_sentence', '').split()))}"
            note["Back"] = q.get("correct_sentence", "")
            note.note_type()["did"] = deck_id
            mw.col.add_note(note, deck_id)
            count += 1
        return count
