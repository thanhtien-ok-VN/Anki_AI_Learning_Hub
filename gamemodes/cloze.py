import random
from typing import Any
from .base import GameModeBase

class ClozeMode(GameModeBase):
    name = "cloze"
    display_name = "Cloze Paragraph"
    icon = "📖"

    def render_ui_data(self, raw_result: dict) -> dict:
        blanks = []
        for i, b in enumerate(raw_result.get("blanks", [])):
            options = [b.get("answer", "")]
            # Shuffle options, track correct index
            indices = list(range(len(options)))
            random.shuffle(indices)
            shuffled = [options[j] for j in indices]
            correct_idx = indices.index(0)
            blanks.append({
                "id": b.get("id", f"BLANK_{i+1}"),
                "answer": b.get("answer", ""),
                "meaning": b.get("meaning", b.get("meaning_vi", "")),
                "hint": b.get("hint", ""),
                "options": shuffled,
                "correct_index": correct_idx,
                "explanation": b.get("explanation", ""),
            })
        return {
            "paragraph": raw_result.get("paragraph", ""),
            "blanks": blanks,
            "full_solution_text": raw_result.get("full_solution_text", ""),
            "story_translation": raw_result.get("story_translation", ""),
            "context_summary": raw_result.get("context_summary", ""),
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
        front = (data.get("paragraph", "") or "Cloze")[:80] + "..."
        return (front, data.get("full_solution_text", ""))
