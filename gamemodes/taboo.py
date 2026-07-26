from typing import Any
from aqt import mw
from anki.notes import Note

from .base import GameModeBase


class TabooMode(GameModeBase):
    name = "taboo"
    display_name = "AI Taboo"
    icon = "🚫"

    def render_ui_data(self, raw_result: dict) -> dict:
        rounds = raw_result.get("rounds", [])
        return {
            "rounds": [
                {
                    "secret_word": r.get("secret_word", ""),
                    "forbidden_words": r.get("forbidden_words", []),
                    "ai_description": r.get("ai_description", ""),
                    "category": r.get("category", ""),
                    "difficulty": r.get("difficulty", "medium"),
                }
                for r in rounds
            ]
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        guess = str(user_input).strip().lower() if user_input else ""
        word = str(correct).strip().lower() if correct else ""
        is_correct = guess == word

        return {
            "correct": is_correct,
            "guess": user_input,
            "secret_word": correct,
            "feedback": "Correct!" if is_correct else f"The word was: {correct}",
            "points": 1 if is_correct else 0,
        }

    def generate_ai_guess(self, description: str, language: str = "en") -> str:
        if not self.api:
            return ""
        prompt = (
            f"Guess the word being described. Language: {language}.\n"
            f"Description: {description}\n"
            f"Reply with ONLY the word, nothing else."
        )
        result = self.api.generate_text(prompt)
        return result or ""

    def save_to_anki(self, rounds: list, deck_name: str = "AI Learning") -> int:
        model = mw.col.models.by_name("Basic")
        if not model:
            model = mw.col.models.current()
        deck = mw.col.decks.by_name(deck_name)
        if not deck:
            deck_id = mw.col.decks.add_normal_deck_with_name(deck_name)
        else:
            deck_id = deck["id"]

        count = 0
        for r in rounds:
            note = Note(mw.col, model)
            forbidden = ", ".join(r.get("forbidden_words", []))
            note["Front"] = f"Taboo: {r.get('secret_word', '')}\nCannot say: {forbidden}"
            note["Back"] = r.get("ai_description", "")
            note.note_type()["did"] = deck_id
            mw.col.add_note(note, deck_id)
            count += 1
        return count
