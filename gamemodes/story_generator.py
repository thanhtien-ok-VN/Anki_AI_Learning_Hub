from typing import Any

from .base import GameModeBase


class StoryGeneratorMode(GameModeBase):
    name = "story"
    display_name = "Story Generator"
    icon = "📚"

    def render_ui_data(self, raw_result: dict) -> dict:
        return {
            "story": raw_result.get("story", ""),
            "target_word_usage": raw_result.get("target_word_usage", []),
            "comprehension_questions": raw_result.get("comprehension_questions", []),
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        selected = int(user_input) if user_input is not None else -1
        correct_idx = int(correct)
        return {
            "correct": selected == correct_idx,
            "selected": selected,
            "correct_index": correct_idx,
            "points": 1 if selected == correct_idx else 0,
        }

    def check_all_answers(self, answers: list[dict]) -> dict:
        total = len(answers)
        correct = 0
        details = []
        for ans in answers:
            result = self.check_answer(ans.get("selected"), ans.get("correct_index"))
            if result["correct"]:
                correct += 1
            details.append(result)
        return {
            "correct": correct,
            "total": total,
            "percentage": round((correct / total) * 100) if total else 0,
            "details": details,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        return ("AI Story: Read & Comprehend", data.get("story", ""))
