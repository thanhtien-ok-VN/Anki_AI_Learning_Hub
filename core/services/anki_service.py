"""Anki Desktop Collection & Storage Service.

Encapsulates all interactions with Anki's SQLite database, SRS collection,
and deck models with thread safety and bounded memory hydration.
"""
from typing import Any, Dict, List, Optional
from core.logger import log
from core.deck_source import (
    list_decks,
    list_source_models,
    list_source_fields,
    sample_vocab_pairs,
)


class AnkiService:
    def list_decks(self) -> Dict[str, Any]:
        return list_decks()

    def get_source_models(self, data: Dict[str, Any]) -> Dict[str, Any]:
        deck_id = data.get("deck_id")
        return list_source_models(deck_id)

    def get_source_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        model_id = data.get("model_id")
        return list_source_fields(model_id)

    def sample_vocab_pairs(
        self,
        data: Dict[str, Any],
        cancel_event: Optional[Any] = None,
    ) -> Dict[str, Any]:
        raw_did = data.get("deck_id")
        try:
            deck_id = int(raw_did) if raw_did is not None else None
        except (ValueError, TypeError):
            deck_id = None

        raw_mid = data.get("model_id")
        try:
            model_id = int(raw_mid) if raw_mid is not None else None
        except (ValueError, TypeError):
            model_id = None

        term_field = str(data.get("term_field") or "").strip()
        definition_field = str(
            data.get("definition_field") or data.get("def_field") or ""
        ).strip()
        limit = int(data.get("limit") or 20)
        excluded = list(data.get("excluded_pair_keys") or [])
        weak_words = list(data.get("weak_words") or [])

        return sample_vocab_pairs(
            deck_id=deck_id,
            model_id=model_id,
            term_field=term_field,
            definition_field=definition_field,
            limit=limit,
            excluded_pair_keys=excluded,
            weak_words=weak_words,
        )

    def save_to_anki(self, gamemode_obj: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        gamemode = data.get("gamemode", "fill_blank")
        content = data.get("content", {})
        deck_name = data.get("deck", "AI Learning")

        if gamemode_obj and hasattr(gamemode_obj, "save_to_anki"):
            items = content if isinstance(content, list) else [content]
            count = gamemode_obj.save_to_anki(items, deck_name)
            log.info(f"Saved {count} cards to deck '{deck_name}' from {gamemode}")
            return {"success": True, "count": count}

        log.warn(f"No save handler for {gamemode}")
        return {
            "error": True,
            "error_code": "E_NO_SAVE_HANDLER",
            "message": f"No save handler for {gamemode}",
        }
