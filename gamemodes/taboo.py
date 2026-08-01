from typing import Any
from .base import GameModeBase

class TabooMode(GameModeBase):
    name = "taboo"
    display_name = "AI Taboo"
    icon = "🚫"

    def render_ui_data(self, raw_result: dict) -> dict:
        rounds = raw_result.get("rounds", [raw_result])
        return {
            "rounds": [
                {
                    "target_word": r.get("target_word", ""),
                    "meaning_vi": r.get("meaning_vi", ""),
                    "phonetic": r.get("phonetic", ""),
                    "taboo_words": r.get("taboo_words", []),
                    "clue": r.get("clue", ""),
                    "difficulty_level": r.get("difficulty_level", "medium"),
                    "sample_acceptable_phrases": r.get("sample_acceptable_phrases", []),
                    "sample_forbidden_phrases": r.get("sample_forbidden_phrases", []),
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
            "target_word": correct,
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
        taboo = ", ".join(data.get("taboo_words", []))
        front = f"Taboo: {data.get('target_word', '')}\nCannot say: {taboo}"
        return (front, data.get("clue", ""))
