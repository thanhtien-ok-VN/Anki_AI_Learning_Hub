from typing import Any
from aqt import mw
from anki.notes import Note

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

    def save_to_anki(self, story: str, deck_name: str = "AI Learning") -> int:
        model = mw.col.models.by_name("Basic")
        if not model:
            model = mw.col.models.current()
        deck = mw.col.decks.by_name(deck_name)
        if not deck:
            deck_id = mw.col.decks.add_normal_deck_with_name(deck_name)
        else:
            deck_id = deck["id"]

        note = Note(mw.col, model)
        note["Front"] = "AI Story: Read & Comprehend"
        note["Back"] = story
        note.note_type()["did"] = deck_id
        mw.col.add_note(note, deck_id)
        return 1
