import json
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple, List

from core.api_client import GeminiClient
from core.prompt_manager import PromptManager
from core.schema_registry import get_schema


class GameModeBase(ABC):
    name: str = ""
    display_name: str = ""
    icon: str = ""

    def __init__(self, api_client: GeminiClient, prompt_mgr: PromptManager):
        self.api = api_client
        self.prompts = prompt_mgr

    def generate(self, **kwargs) -> dict:
        from core.schema_registry import get_schema, get_pydantic_model
        schema = get_schema(self.name)
        if not schema:
            return {"error": True, "message": f"No schema for {self.name}"}

        prompt = self.prompts.get_prompt(
            gamemode=self.name,
            **kwargs,
        )

        result = self.api.generate_structured(
            prompt=prompt,
            response_schema=schema,
        )

        if not result.get("error"):
            pydantic_cls = get_pydantic_model(self.name)
            if pydantic_cls:
                try:
                    key_used = result.get("_key_used")
                    model_used = result.get("_model_used")
                    err_code = result.get("error_code")

                    validated = pydantic_cls.model_validate(result)
                    result = validated.model_dump()

                    if key_used: result["_key_used"] = key_used
                    if model_used: result["_model_used"] = model_used
                    if err_code: result["error_code"] = err_code
                except Exception:
                    pass
        return result

    @abstractmethod
    def render_ui_data(self, raw_result: dict) -> dict:
        pass

    @abstractmethod
    def check_answer(self, user_input: Any, correct: Any) -> dict:
        pass

    @abstractmethod
    def _format_anki_note(self, data: dict) -> Tuple[str, str]:
        """Return (front, back) for a single Anki note from game data item."""
        pass



    def save_to_anki(self, items: List[dict], deck_name: str = "AI Learning") -> int:
        from aqt import mw
        from anki.notes import Note

        model = mw.col.models.by_name("Basic")
        if not model:
            model = mw.col.models.current()

        deck = mw.col.decks.by_name(deck_name)
        if not deck:
            deck_id = mw.col.decks.add_normal_deck_with_name(deck_name)
        else:
            deck_id = deck["id"]

        count = 0
        for item in items:
            front, back = self._format_anki_note(item)
            if not front and not back:
                continue
            note = Note(mw.col, model)
            note["Front"] = front
            note["Back"] = back
            note.note_type()["did"] = deck_id
            mw.col.add_note(note, deck_id)
            count += 1

        return count
