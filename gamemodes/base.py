import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from core.api_client import GeminiClient
from core.prompt_manager import PromptManager
from core.schema_registry import get_schema


class GameModeBase(ABC):
    name: str = ""
    display_name: str = ""
    icon: str = ""
    supported_languages: list = ["en", "zh"]

    def __init__(self, api_client: GeminiClient, prompt_mgr: PromptManager):
        self.api = api_client
        self.prompts = prompt_mgr

    def generate(self, **kwargs) -> dict:
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
        return result

    @abstractmethod
    def render_ui_data(self, raw_result: dict) -> dict:
        pass

    @abstractmethod
    def check_answer(self, user_input: Any, correct: Any) -> dict:
        pass

    def save_context(self, data: dict) -> dict:
        return {"gamemode": self.name, "data": data}

    def load_context(self, ctx: dict) -> Optional[dict]:
        raw = ctx.get("data", {}).get("result") if ctx else None
        if raw:
            return self.render_ui_data(raw)
        return None
