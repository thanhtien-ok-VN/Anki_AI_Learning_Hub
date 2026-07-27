from typing import Any

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
        if result:
            result = result.strip().strip('"\'.,!?').strip()
            for prefix in ["I think the word is ", "The word is ", "My guess is ", "It's ", "Is it "]:
                if result.lower().startswith(prefix.lower()):
                    result = result[len(prefix):].strip().strip('"\'.,!?').strip()
                    break
        return result or ""

    def _format_anki_note(self, data: dict) -> tuple:
        forbidden = ", ".join(data.get("forbidden_words", []))
        front = f"Taboo: {data.get('secret_word', '')}\nCannot say: {forbidden}"
        return (front, data.get("ai_description", ""))
