import json
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple, List

from core.api_client import GeminiClient
from core.prompt_manager import PromptManager
from core.schema_registry import get_schema
from gamemodes.manifest import GameModeManifest
from llm.base import BaseLLMProvider


class GameModeBase(ABC):
    name: str = ""
    display_name: str = ""
    icon: str = ""
    manifest: Optional[GameModeManifest] = None

    def __init__(self, api_client: Optional[BaseLLMProvider] = None, prompt_mgr: Optional[PromptManager] = None):
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
    def check_answer(self, user_input: Any, correct: Any, hint_level: int = 0) -> dict:
        pass

    @staticmethod
    def build_grading_prompt_data(data: dict, common: dict) -> dict:
        """Build prompt keyword arguments for AI grading."""
        return {
            **common,
            "question": data.get("question", ""),
            "expected": data.get("expected", ""),
            "user_answer": data.get("user_answer", ""),
        }

    @abstractmethod
    def _format_anki_note(self, data: dict) -> Tuple[str, str]:
        """Return (front, back) for a single Anki note from game data item."""
        pass

    def save_to_anki(self, items: List[dict], deck_name: str = "AI Learning") -> int:
        import threading
        from concurrent.futures import Future
        from aqt import mw
        from anki.notes import Note

        if not mw or not getattr(mw, "col", None):
            return 0

        def _do_save() -> int:
            mw.checkpoint("Save AI Learning Cards")

            model = mw.col.models.by_name("Basic")
            if not model:
                model = mw.col.models.current()
            if not model or "flds" not in model:
                return 0

            fields = [f["name"] for f in model.get("flds", [])]
            if not fields:
                return 0

            # Heuristic Field Mapping for custom note types
            front_field = fields[0]
            for f in fields:
                if f.lower() in ("front", "word", "question", "term", "text"):
                    front_field = f
                    break

            back_field = fields[1] if len(fields) > 1 else fields[0]
            for f in fields:
                if f.lower() in ("back", "answer", "meaning", "definition", "translation"):
                    back_field = f
                    break

            deck = mw.col.decks.by_name(deck_name)
            if not deck:
                deck_id = mw.col.decks.add_normal_deck_with_name(deck_name)
            else:
                deck_id = deck["id"]

            # Targeted duplicate scanning: avoid O(D) full deck loading
            clean_candidates = []
            for item in items:
                front, back = self._format_anki_note(item)
                if front or back:
                    clean_front = front.strip().lower()
                    clean_candidates.append((front, back, clean_front))

            existing_fronts = set()
            for front, back, clean_front in clean_candidates:
                if not clean_front:
                    continue
                # Sanitize search term for Anki query to avoid syntax errors
                term_escaped = clean_front.replace('"', '').replace('\\', '').replace('*', '')
                if not term_escaped:
                    continue
                try:
                    matching_nids = mw.col.find_notes(f'did:{deck_id} "{term_escaped}"')
                    for nid in matching_nids:
                        n = mw.col.get_note(nid)
                        existing_val = n[front_field].strip().lower()
                        if existing_val:
                            existing_fronts.add(existing_val)
                except Exception:
                    pass

            count = 0
            for front, back, clean_front in clean_candidates:
                if not front and not back:
                    continue
                if clean_front in existing_fronts:
                    continue

                note = Note(mw.col, model)
                note[front_field] = front
                if len(fields) > 1:
                    note[back_field] = back
                note.note_type()["did"] = deck_id
                mw.col.add_note(note, deck_id)
                existing_fronts.add(clean_front)
                count += 1

            if count > 0:
                mw.reset()

            return count

        if threading.current_thread() is threading.main_thread():
            return _do_save()

        if mw and hasattr(mw, "taskman") and hasattr(mw.taskman, "run_on_main"):
            fut = Future()

            def wrapper():
                try:
                    fut.set_result(_do_save())
                except BaseException as e:
                    fut.set_exception(e)

            mw.taskman.run_on_main(wrapper)
            return fut.result(timeout=10.0)

        return _do_save()
