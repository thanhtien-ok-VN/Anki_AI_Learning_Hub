"""Generation Service.

Orchestrates the 4-phase AI generation pipeline (Connect, System, AI, Render),
enforcing schemas, prompt compilation, and validation.
"""
import random
import threading
from typing import Any, Callable, Dict, Optional
from core.languages import (
    DEFAULT_LEARN_LANG,
    get_language_name,
    valid_learn_lang,
)
from core.language_normalizer import normalize_language_fields
from core.sanitizer import sanitize_dict
from core.logger import log, flow, FlowTimer
from core.schema_registry import get_schema, get_pydantic_model
from core.content_validation import validate_game_result
from gamemodes import registry as gamemode_registry


class GenerationService:
    def generate(
        self,
        data: Dict[str, Any],
        api_client: Any,
        prompt_mgr: Any,
        gamemode_resolver: Callable[[str], Any],
        settings: Any,
        cancel_event: Optional[threading.Event] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        data = normalize_language_fields(dict(data or {}))
        gamemode = data.get("gamemode", "fill_blank")

        # 0. Offline Game Short-Circuit
        gm_pre = gamemode_resolver(gamemode)
        if gm_pre and getattr(gm_pre, "is_offline", False) and hasattr(gm_pre, "generate"):
            log.info(f"Generating offline game content for {gamemode}")
            try:
                rendered = gm_pre.generate(**data)
                if isinstance(rendered, dict) and rendered.get("error"):
                    return {
                        "success": False,
                        "data": {},
                        "error_code": rendered.get("error_code", "E_OFFLINE_GEN"),
                        "message": rendered.get("message", "Offline generation failed"),
                    }
                rendered = normalize_language_fields(rendered)
                rendered = sanitize_dict(rendered)
                return {
                    "success": True,
                    "data": rendered,
                }
            except Exception as e:
                log.exception(f"Offline game generation error for {gamemode}: {e}")
                return {
                    "success": False,
                    "data": {},
                    "error_code": "E_OFFLINE_GEN",
                    "message": f"Offline generation failed: {str(e)}",
                }

        # Phase 1: CONNECT
        with FlowTimer("CONNECT", gamemode=gamemode, message="Checking client and API keys") as timer:
            active_keys = settings.get_active_keys()
            timer.extra["active_keys_count"] = len(active_keys)
            if not api_client or not active_keys:
                return {
                    "error": True,
                    "error_code": "E_NO_KEYS",
                    "message": "No API key configured. Set at least one in Settings.",
                }

        # Phase 2: SYSTEM
        with FlowTimer("SYSTEM", gamemode=gamemode, message="Building prompt and parameters") as timer:
            language = valid_learn_lang(data.get("language"), settings.get("learn_lang", DEFAULT_LEARN_LANG))
            data["language"] = language
            level = data.get("level", "intermediate")
            topic = data.get("topic", "daily_life")
            minimum, maximum = gamemode_registry.get_limits(gamemode)
            count = max(minimum, min(int(data.get("count", minimum)), maximum))
            data["count"] = count
            source_pairs = data.get("vocab_pairs") or []
            if gamemode == "cloze":
                num_blanks = max(1, min(int(data.get("num_blanks") or 5), len(source_pairs) or 5, 10))
                data["num_blanks"] = num_blanks
                effective = num_blanks
            else:
                effective = count

            if gamemode == "translation":
                TRANSLATION_SENTENCE_TYPES = [
                    "passive voice", "conditional (if + would)", "present perfect vs past simple",
                    "comparative / superlative", "relative clause (who/which/that)",
                    "complex sentence with because/although/while", "modal verbs (can, should, must, might)",
                    "common idiom or phrasal verb", "reported speech", "negative + tag/question structure",
                ]
                data["sentence_type"] = random.choice(TRANSLATION_SENTENCE_TYPES)

            if gamemode == "unscramble":
                UNSCRAMBLE_SENTENCE_TYPES = [
                    "passive voice", "conditional (if + would)", "relative clause (who/which/that)",
                    "comparative / superlative", "reported speech", "modal verbs (can, should, must, might)",
                    "common idiom or phrasal verb", "present perfect vs past simple", "imperative sentence",
                    "question structure (why/how/tag)", "complex sentence with because/although/while",
                    "gerund as subject or object",
                ]
                sampled_types = random.sample(UNSCRAMBLE_SENTENCE_TYPES, min(count, len(UNSCRAMBLE_SENTENCE_TYPES)))
                data["sentence_types"] = ", ".join(sampled_types)

            if source_pairs:
                needed = min(effective, len(source_pairs))
                data["vocab_pairs"] = random.sample(source_pairs, needed) if needed else []
                data["blank_words"] = ", ".join(p["term"] for p in data["vocab_pairs"])

            data.setdefault("paragraph_min_words", 80)
            data.setdefault("paragraph_max_words", 140)
            data.setdefault("num_blanks", min(5, int(count)))
            data.setdefault("source_lang", get_language_name(settings.get("ui_lang", "en")))
            data.setdefault("target_lang", get_language_name(language))
            data.setdefault("word_count", 180)
            data.setdefault("question_count", count)
            data.setdefault("target_words", "")
            data.setdefault("focus", "grammar")

            schema = get_schema(gamemode)
            if not schema:
                log.warn(f"No schema for gamemode: {gamemode}")
                return {"error": True, "error_code": "E_NO_SCHEMA", "message": f"Unknown gamemode: {gamemode}"}

            if source_pairs and gamemode == "story" and not data.get("target_words"):
                data = dict(data)
                data["target_words"] = ", ".join(pair["term"] for pair in source_pairs[:count])

            prompt_data = dict(data)
            for key in ("gamemode", "language", "level", "topic", "count", "vocab_pairs"):
                prompt_data.pop(key, None)
            prompt_data["ui_lang"] = settings.get("ui_lang", "en")
            prompt_data["feedback_lang"] = settings.get("ui_lang", "en")
            prompt = prompt_mgr.get_prompt(
                gamemode=gamemode, language=language, level=level, topic=topic, count=count,
                vocab_pairs=source_pairs, **prompt_data
            )
            timer.extra.update({"language": language, "level": level, "topic": topic, "count": count, "vocab_count": len(source_pairs)})

        # Phase 3: AI
        with FlowTimer("AI", gamemode=gamemode, message="Generating content via LLM") as timer:
            result = api_client.generate_structured(
                prompt=prompt,
                response_schema=schema,
                temperature=settings.get("temperature", 0.7),
                progress_callback=progress_callback,
            )
            timer.extra["key_used"] = result.get("_key_used", "")
            timer.extra["model_used"] = result.get("_model_used", "")

        if result.get("error"):
            log.warn(f"Generate failed: {result.get('error_code', '?')} - {result.get('message', '')[:100]}")
            return result

        # Phase 4: RENDER
        with FlowTimer("RENDER", gamemode=gamemode, message="Validating and rendering response") as timer:
            gm = gamemode_resolver(gamemode)
            key_used = result.get("_key_used", "?")
            model_used = result.get("_model_used", "?")

            pydantic_cls = get_pydantic_model(gamemode)
            if pydantic_cls:
                try:
                    err_code = result.get("error_code")
                    validated = pydantic_cls.model_validate(result)
                    result = validated.model_dump()
                    result["_key_used"] = key_used
                    result["_model_used"] = model_used
                    if err_code:
                        result["error_code"] = err_code
                except Exception as e:
                    log.warn(f"Pydantic validation failed for {gamemode}: {e}")

            validation = validate_game_result(gamemode, result, count)
            if validation.get("error"):
                return {
                    "error": True,
                    "error_code": "E_AI_CONTENT",
                    "message": validation["error"],
                }

            result = normalize_language_fields(result)
            if gm:
                rendered = gm.render_ui_data(result)
                if rendered:
                    result = rendered

            result = sanitize_dict(normalize_language_fields(result))
            timer.extra["status"] = "OK"

        return result
