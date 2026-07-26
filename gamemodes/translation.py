from typing import Any
from aqt import mw
from anki.notes import Note

from .base import GameModeBase


class TranslationMode(GameModeBase):
    name = "translation"
    display_name = "AI Translation Practice"
    icon = "🌐"

    def render_ui_data(self, raw_result: dict) -> dict:
        sentences = raw_result.get("sentences", [])
        return {
            "sentences": [
                {
                    "source_text": s.get("source_text", ""),
                    "target_text": s.get("target_text", ""),
                    "vocabulary": s.get("vocabulary_highlight", []),
                    "grammar_notes": s.get("grammar_notes", ""),
                }
                for s in sentences
            ]
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        user_text = str(user_input).strip() if user_input else ""
        target_text = str(correct).strip() if correct else ""
        return {
            "correct": user_text.lower() == target_text.lower(),
            "user_answer": user_text,
            "expected": target_text,
            "points": 1 if user_text.lower() == target_text.lower() else 0,
        }

    def grade_with_ai(self, source_text: str, expected: str, user_text: str, level: str, learn_lang: str) -> dict:
        from core.ai_grader import TRANSLATION_GRADER
        prompt = TRANSLATION_GRADER.format(
            source_lang="Vietnamese",
            target_lang=learn_lang,
            source_text=source_text,
            expected_target=expected,
            user_target=user_text,
            level=level,
        )
        from aqt import mw
        engine = getattr(mw, "ai_engine", None)
        if engine:
            client = engine._get_api_client()
            if client:
                result = client.generate_text(prompt, temperature=0.3)
                if result:
                    import json
                    try:
                        return json.loads(result)
                    except Exception:
                        pass
        return {"correct": False, "score": 0, "explanation": "AI grading unavailable"}

    def save_to_anki(self, sentences: list, deck_name: str = "AI Learning") -> int:
        model = mw.col.models.by_name("Basic")
        if not model:
            model = mw.col.models.current()
        deck = mw.col.decks.by_name(deck_name)
        if not deck:
            deck_id = mw.col.decks.add_normal_deck_with_name(deck_name)
        else:
            deck_id = deck["id"]

        count = 0
        for s in sentences:
            note = Note(mw.col, model)
            note["Front"] = s.get("source_text", "")
            note["Back"] = s.get("target_text", "")
            note.note_type()["did"] = deck_id
            mw.col.add_note(note, deck_id)
            count += 1
        return count
