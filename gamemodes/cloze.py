from typing import Any

from .base import GameModeBase


class ClozeMode(GameModeBase):
    name = "cloze"
    display_name = "Cloze Paragraph"
    icon = "📖"

    def render_ui_data(self, raw_result: dict) -> dict:
        blanks = raw_result.get("blanks", [])
        return {
            "paragraph_with_blanks": raw_result.get("paragraph_with_blanks", ""),
            "paragraph_full": raw_result.get("paragraph_full", ""),
            "blanks": [
                {
                    "blank_id": b.get("blank_id", i),
                    "correct_word": b.get("correct_word", ""),
                    "options": b.get("options", []),
                    "correct_index": b.get("correct_index", 0),
                    "explanation_short": b.get("explanation_short", ""),
                    "explanation": b.get("explanation", ""),
                }
                for i, b in enumerate(blanks)
            ],
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        user_idx = int(user_input) if user_input is not None else -1
        correct_idx = int(correct) if correct is not None else -1
        return {
            "correct": user_idx == correct_idx,
            "user_index": user_idx,
            "correct_index": correct_idx,
            "points": 1 if user_idx == correct_idx else 0,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        paragraph = data.get("paragraph_full", "") or data.get(
            "paragraph_with_blanks", ""
        )
        front = (data.get("paragraph_with_blanks", "") or "Cloze")[:80] + "..."
        return (front, paragraph)
