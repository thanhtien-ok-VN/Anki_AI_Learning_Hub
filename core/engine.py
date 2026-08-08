import threading
import json
import os
import time
import random
from typing import Any, Optional

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import tooltip

from core.logger import log
from core.language_normalizer import normalize_language_fields
from core.languages import DEFAULT_LEARN_LANG, DEFAULT_UI_LANG, bridge_languages, valid_learn_lang, valid_ui_lang

import re

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ──────────────────────────────────────────────────────────────
# SECTION 1: Module-level helpers
# (clean_json_response, normalize_answer, sanitize_html,
#  sanitize_dict, ADDON_PATH, DEFAULT_SETTINGS, GAME_LIMITS)
# ──────────────────────────────────────────────────────────────

def clean_json_response(raw_text: str) -> str:
    """Strip markdown code blocks and extra text, return pure JSON."""
    if not raw_text or not isinstance(raw_text, str):
        return raw_text or ""
    cleaned = re.sub(r"```(?:json)?", "", raw_text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end+1]
    return cleaned.strip()

def normalize_answer(text: str) -> str:
    """Normalize answer for comparison (used by sentence_transform + translation)."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower().strip()).rstrip(".,!?;:")

def sanitize_html(text: str) -> str:
    """Strips all HTML tags except safe formatting ones: b, i, u, br, p, span, code, hr."""
    if not text or not isinstance(text, str):
        return text or ""
    # 1. Strip dangerous tags completely along with their contents
    text = re.sub(
        r"<(script|iframe|style|link|embed|object|form|input|button)\b[^<]*(?:(?!</\1>)<[^<]*)*</\1>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(
        r"<(script|iframe|style|link|embed|object|form|input|button)\b[^>]*/>?",
        "",
        text,
        flags=re.IGNORECASE
    )
    # 2. Strip inline event attributes like onclick=...
    text = re.sub(r"\s*on\w+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", "", text, flags=re.IGNORECASE)
    # 3. Strip javascript: URIs
    text = re.sub(r"(href|src|action)\s*=\s*[\"']?\s*javascript:[^\"'>]*[\"']?", "", text, flags=re.IGNORECASE)
    # 4. Strip any tag NOT in the whitelist
    whitelist = {"b", "i", "u", "br", "p", "span", "code", "hr"}
    def tag_repl(match):
        tag_name = match.group(1).lower()
        if tag_name in whitelist:
            return match.group(0)
        return ""
    return re.sub(r"<(/?[a-zA-Z0-9]+)(?:\s+[^>]*)?>", tag_repl, text)

def sanitize_dict(val: Any) -> Any:
    """Recursively search for strings and run sanitize_html over them, stripping bad newlines/quotes from dict keys."""
    if isinstance(val, dict):
        cleaned_dict = {}
        for k, v in val.items():
            clean_key = k.strip().strip('"').strip("'").strip() if isinstance(k, str) else k
            cleaned_dict[clean_key] = sanitize_dict(v)
        return cleaned_dict
    elif isinstance(val, list):
        return [sanitize_dict(item) for item in val]
    elif isinstance(val, str):
        return sanitize_html(val)
    return val

from core.settings import SettingsManager, SETTINGS_PATH, DEFAULT_SETTINGS
from core.timer import SessionTimer

GAME_LIMITS = {
    "fill_blank": (1, 10),
    "translation": (1, 10),
    "unscramble": (1, 10),
    "sentence_transform": (1, 10),
    "taboo": (1, 10),
    "cloze": (1, 10),
    "matching": (5, 50),
    "story": (3, 10),
}




# ──────────────────────────────────────────────────────────────
# SECTION 3: AIEngine — Init, API Client, Game Cache
# (Manages GeminiClient, PromptManager, gamemode object cache)
# ──────────────────────────────────────────────────────────────

class AIEngine:
    def __init__(self):
        self.settings = SettingsManager()
        self.timer = SessionTimer()
        self.cancel_event = threading.Event()
        self._api_lock = threading.RLock()
        self._api_client = None
        self._prompt_mgr = None
        self._gamemode_cache = {}

        self.timer.tick.connect(self._on_timer_tick)
        gui_hooks.profile_will_close.append(self._on_profile_close)

    def _new_cancel_event(self) -> threading.Event:
        with self._api_lock:
            self.cancel_event = threading.Event()
            if self._api_client:
                self._api_client.cancel_event = self.cancel_event
            return self.cancel_event

    def cancel_current_task(self):
        self.cancel_event.set()
        log.info("Cancel current task event set")

    def _send_progress(self, text: str):
        if self.cancel_event and self.cancel_event.is_set():
            return
        from aqt import mw
        def update_ui():
            try:
                if hasattr(self, "main_window") and self.main_window and self.main_window._hub_web:
                    js = f"if(window.Bridge && window.Bridge.updateStatus) window.Bridge.updateStatus({json.dumps(text)});"
                    self.main_window._hub_web.eval(js)
            except Exception as e:
                log.error(f"update_ui progress eval failed: {e}")
        mw.taskman.run_on_main(update_ui)


    def _get_api_client(self):
        with self._api_lock:
            if self._api_client is None:
                from core.api_client import GeminiClient

                keys = self.settings.get_active_keys()
                if keys:
                    self._api_client = GeminiClient(
                        keys,
                        self.settings.get("model", "auto"),
                        ui_lang=self.settings.get("ui_lang", "en"),
                        cancel_event=self.cancel_event
                    )
            elif self._api_client and self._api_client.cancel_event is None:
                self._api_client.cancel_event = self.cancel_event
            return self._api_client

    def _reset_api_client(self):
        with self._api_lock:
            self._api_client = None
            self._gamemode_cache.clear()

    def get_prompt_manager(self):
        if self._prompt_mgr is None:
            from core.prompt_manager import PromptManager

            prompts_dir = os.path.join(ADDON_PATH, "prompts")
            self._prompt_mgr = PromptManager(prompts_dir)
        return self._prompt_mgr

    def get_gamemode(self, name: str):
        if name not in self._gamemode_cache:
            from gamemodes import get_gamemode as _get_cls

            cls = _get_cls(name)
            if cls:
                self._gamemode_cache[name] = cls(
                    self._get_api_client(), self.get_prompt_manager()
                )
        return self._gamemode_cache.get(name)

    def start(self):
        self.timer.start()
        if self.settings.has_any_key():
            from core.api_client import GeminiClient

            self._api_client = GeminiClient(
                self.settings.get_active_keys(),
                self.settings.get("model", "auto"),
                ui_lang=self.settings.get("ui_lang", "en"),
                cancel_event=self.cancel_event
            )
        log.info(
            "AIEngine started",
            {
                "has_keys": self.settings.has_any_key(),
                "num_keys": len(self.settings.get_active_keys()),
            },
        )

    def stop(self):
        try:
            elapsed = self.timer.stop()
            self.settings.set("last_session_duration", elapsed)
            from core.logger import flow
            flow(phase="EVENT", message="Anki session stopped", duration_ms=elapsed * 1000 if elapsed else 0)
            log.info("AIEngine stopped", {"session_seconds": elapsed})
        except Exception as e:
            log.error(f"Error stopping AIEngine: {e}")

    def _on_timer_tick(self, seconds: int):
        pass

    def _on_profile_close(self):
        try:
            self.stop()
        except Exception as e:
            log.error(f"Error in _on_profile_close: {e}")

    def handle_js_message(self, message: str) -> dict:
        try:
            msg = json.loads(message)
            action = msg.get("action", "")
            data = msg.get("data", {})
            log.debug(
                f"JS message: {action}",
                {"data_keys": list(data.keys()) if data else None},
            )

            handlers = {
                "generate": self._handle_generate,
                "save_settings": self._handle_save_settings,
                "get_settings": self._handle_get_settings,
                "check_api_key": self._handle_check_api_key,
                "save_to_anki": self._handle_save_to_anki,
                "check_answer": self._handle_check_answer,

                "save_prefs": self._handle_save_prefs,
                "load_prefs": self._handle_load_prefs,
                "test_key": self._handle_test_key,
                "test_all_keys": self._handle_test_all_keys,
                "list_decks": self._handle_list_decks,
                "get_source_models": self._handle_get_source_models,
                "get_source_fields": self._handle_get_source_fields,
                "sample_vocab_pairs": self._handle_sample_vocab_pairs,
                "set_ui_lang": self._handle_set_ui_lang,
                "set_learn_lang": self._handle_set_learn_lang,
                "get_ui_lang": self._handle_get_ui_lang,
                "get_ui_strings": self._handle_get_ui_strings,
                "get_supported_languages": self._handle_get_supported_languages,
                "ai_grade": self._handle_ai_grade,
                "get_hint": self._handle_get_hint,
                "close_hub": self._handle_close_hub,
                "cancel_gen": self._handle_cancel_gen,
                "log_event": self._handle_log_event,
            }
            handler = handlers.get(action)
            if handler:
                result = handler(data)
                # All public bridge results have one stable envelope.  Existing
                # gamemode payloads remain inside data for the SPA.
                if isinstance(result, dict) and "success" in result:
                    if not result.get("success"):
                        err_msg = result.get("message") or "The operation failed."
                        err_code = result.get("error_code") or "E_OPERATION"
                        log.warn(f"Bridge operation failed [{err_code}]: {err_msg}")
                        return {
                            "success": False,
                            "data": result.get("data", {}),
                            "error_code": err_code,
                            "message": err_msg,
                        }
                    return result
                if isinstance(result, dict) and result.get("error"):
                    err_msg = result.get("message") or "The operation failed."
                    err_code = result.get("error_code") or "E_OPERATION"
                    return {
                        "success": False,
                        "data": {},
                        "error_code": err_code,
                        "message": err_msg,
                    }
                return {"success": True, "data": result or {}}
            log.warn(f"Unknown action: {action}")
            return {
                "success": False,
                "data": {},
                "error_code": "E_UNKNOWN",
                "message": f"Unknown action: {action}",
            }
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            log.error(f"handle_js_message error: {e}\n{tb}")
            return {
                "success": False,
                "data": {},
                "error_code": "E_INTERNAL",
                "message": "The AI Hub could not complete this request.",
            }

    # ──────────────────────────────────────────────────────────
    # SECTION 4: Bridge Handlers — Generate & Game
    # (_handle_generate, _handle_check_answer, _handle_ai_grade,
    #  _handle_save_to_anki)
    # ──────────────────────────────────────────────────────────

    def _handle_log_event(self, data: dict = None) -> dict:
        data = data or {}
        event = data.get("event", "unknown")
        game = data.get("game", "")
        extra = data.get("extra") or {}
        log.info(f"User event: {event}", {"game": game, **extra})
        from core.logger import flow
        flow(phase="EVENT", gamemode=game, message=f"User event: {event}", extra=extra)
        return {"logged": True}

    def _handle_cancel_gen(self, data: dict = None) -> dict:
        from core.logger import flow
        flow(phase="EVENT", message="Cancel requested by user via cancel_gen RPC")
        self.cancel_current_task()
        return {"cancelled": True}

    def _handle_generate(self, data: dict) -> dict:
        from core.logger import log, flow, FlowTimer, LogLevel
        from core.schema_registry import get_schema
        self._new_cancel_event()
        data = normalize_language_fields(dict(data or {}))
        gamemode = data.get("gamemode", "fill_blank")

        gm_pre = self.get_gamemode(gamemode)
        if gm_pre and getattr(gm_pre, "is_offline", False) and hasattr(gm_pre, "generate"):
            log.info(f"Generating offline game content for {gamemode}")
            rendered = gm_pre.generate(**data)
            rendered = normalize_language_fields(rendered)
            rendered = sanitize_dict(rendered)
            return self._result(True, rendered)

        # Phase 1: CONNECT
        with FlowTimer("CONNECT", gamemode=gamemode, message="Checking client and API keys") as timer:
            client = self._get_api_client()
            active_keys = self.settings.get_active_keys()
            timer.extra["active_keys_count"] = len(active_keys)
            if not client or not active_keys:
                return {
                    "error": True,
                    "error_code": "E_NO_KEYS",
                    "message": "No API key configured. Set at least one in Settings.",
                }

        # Phase 2: SYSTEM
        with FlowTimer("SYSTEM", gamemode=gamemode, message="Building prompt and parameters") as timer:
            language = valid_learn_lang(data.get("language"), self.settings.get("learn_lang", DEFAULT_LEARN_LANG))
            data["language"] = language
            level = data.get("level", "intermediate")
            topic = data.get("topic", "daily_life")
            minimum, maximum = GAME_LIMITS.get(gamemode, (1, 5))
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
            data.setdefault("source_lang", self.settings.get("ui_lang", "en"))
            data.setdefault("target_lang", language)
            data.setdefault("word_count", 180)
            data.setdefault("question_count", count)
            data.setdefault("target_words", "")
            data.setdefault("focus", "grammar")

            schema = get_schema(gamemode)
            if not schema:
                log.warn(f"No schema for gamemode: {gamemode}")
                return {"error": True, "error_code": "E_NO_SCHEMA", "message": f"Unknown gamemode: {gamemode}"}

            prompt_mgr = self.get_prompt_manager()
            if source_pairs and gamemode == "story" and not data.get("target_words"):
                data = dict(data)
                data["target_words"] = ", ".join(pair["term"] for pair in source_pairs[:count])

            prompt_data = dict(data)
            for key in ("gamemode", "language", "level", "topic", "count", "vocab_pairs"):
                prompt_data.pop(key, None)
            prompt_data["ui_lang"] = self.settings.get("ui_lang", "en")
            prompt_data["feedback_lang"] = self.settings.get("ui_lang", "en")
            prompt = prompt_mgr.get_prompt(
                gamemode=gamemode, language=language, level=level, topic=topic, count=count,
                vocab_pairs=source_pairs, **prompt_data
            )
            timer.extra.update({"language": language, "level": level, "topic": topic, "count": count, "vocab_count": len(source_pairs)})

        # Phase 3: AI
        with FlowTimer("AI", gamemode=gamemode, message="Generating content via Gemini API") as timer:
            result = client.generate_structured(
                prompt=prompt,
                response_schema=schema,
                temperature=self.settings.get("temperature", 0.7),
                progress_callback=self._send_progress,
            )
            timer.extra["key_used"] = result.get("_key_used", "")
            timer.extra["model_used"] = result.get("_model_used", "")

        if result.get("error"):
            log.warn(f"Generate failed: {result.get('error_code', '?')} - {result.get('message', '')[:100]}")
            return result

        # Phase 4: RENDER
        with FlowTimer("RENDER", gamemode=gamemode, message="Validating and rendering response") as timer:
            gm = self.get_gamemode(gamemode)
            key_used = result.get("_key_used", "?")
            model_used = result.get("_model_used", "?")
            
            from core.schema_registry import get_pydantic_model
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

            from core.content_validation import validate_game_result
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

    # ──────────────────────────────────────────────────────────
    # SECTION 5: Bridge Handlers — Settings, UI & Utility
    # (_handle_save_settings, _handle_get_settings,
    #  _handle_set_ui_lang, _handle_get_ui_strings,
    #  _handle_list_decks, _handle_sample_vocab_pairs, etc.)
    # ──────────────────────────────────────────────────────────

    def _handle_save_settings(self, data: dict) -> dict:
        to_update = {}
        for key, value in data.items():
            # Skip masked API keys (user didn't change them)
            if key.startswith("api_key"):
                val_str = str(value or "").strip()
                if not val_str or "*" in val_str or "..." in val_str:
                    continue
            to_update[key] = value

        result = self.settings.set_many(to_update)
        if not result.get("ok"):
            error_code = result.get("error_code", "E_SETTINGS_SAVE")
            return {"success": False, "error_code": error_code, "message": result.get("message", "Save failed")}

        changed = result.get("changed_keys", [])
        if any(k.startswith("api_key") or k == "model" for k in changed):
            self._reset_api_client()
            self._gamemode_cache.clear()
            log.info("API keys/model changed, client+cache reset")
        elif any(k in ("temperature", "learn_lang") for k in changed):
            self._gamemode_cache.clear()
            log.info("Temperature/learn_lang changed, cache cleared")
        if "ui_lang" in changed:
            log.info("UI language changed")
        log.info("Settings saved via bridge", {"changed": changed})
        return {"success": True, "saved": changed}

    def _handle_get_settings(self, data: dict = None) -> dict:
        settings_copy = {
            key: value
            for key, value in self.settings.data.items()
            if not key.startswith("api_key")
        }
        settings_copy["masked_keys"] = self.settings.get_masked_api_keys()
        return settings_copy

    def _handle_check_api_key(self, data: dict = None) -> dict:
        keys = self.settings.get_active_keys()
        from core.api_client import GeminiClient

        return {
            "has_key": bool(keys),
            "key_count": len(keys),
            "keys": [GeminiClient.detect_key_type(k) for k in keys],
        }

    def _handle_test_key(self, data: dict) -> dict:
        cancel_evt = self._new_cancel_event()
        key = data.get("key", "").strip()
        if not key:
            log.warn("test_key called with empty key")
            return {"ok": False, "error": "Empty key"}
        from core.api_client import GeminiClient

        configured_model = self.settings.get("model", "auto")
        client = GeminiClient([key], configured_model, cancel_event=cancel_evt)
        try:
            result = client.test_key(key, progress_callback=self._send_progress)
            log.info(f"test_key result: ok={result.get('ok')} model={result.get('model')}")
            return result
        finally:
            if hasattr(client, "close"):
                client.close()

    def _handle_test_all_keys(self, data: dict = None) -> dict:
        cancel_evt = self._new_cancel_event()
        keys = self.settings.get_api_keys()
        configured_model = self.settings.get("model", "auto")
        from core.api_client import GeminiClient

        results = []
        for idx, key in enumerate(keys):
            if cancel_evt and cancel_evt.is_set():
                log.info(f"test_all_keys cancelled by user before slot {idx+1}/{len(keys)}")
                return {"results": results, "cancelled": True}

            slot = idx + 1
            if not key.strip():
                results.append({"key": slot, "ok": False, "error": "Empty"})
                continue
            client = GeminiClient([key], configured_model, cancel_event=cancel_evt)
            try:
                res = client.test_key_with_waterfall(key, progress_callback=self._send_progress)
                if cancel_evt and cancel_evt.is_set():
                    log.info(f"test_all_keys cancelled by user after slot {slot}/{len(keys)}")
                    results.append(
                        {
                            "key": slot,
                            "ok": False,
                            "model": res.get("model", ""),
                            "error_code": "E_CANCELLED",
                            "error": "Cancelled by user",
                        }
                    )
                    return {"results": results, "cancelled": True}
                results.append(
                    {
                        "key": slot,
                        "ok": res.get("ok", False),
                        "model": res.get("model", ""),
                        "error_code": res.get("error_code", ""),
                        "error": res.get("error", ""),
                        "response": res.get("response", ""),
                    }
                )
            finally:
                if hasattr(client, "close"):
                    client.close()
        log.info(
            f"test_all_keys: {sum(1 for r in results if r['ok'])}/{len(results)} ok"
        )
        return {"results": results}

    def _handle_list_decks(self, data: dict = None) -> dict:
        from core.deck_source import list_decks

        return list_decks()

    def _handle_get_source_models(self, data: dict) -> dict:
        from core.deck_source import list_source_models

        return list_source_models(data.get("deck_id"))

    def _handle_get_source_fields(self, data: dict) -> dict:
        from core.deck_source import list_source_fields

        return list_source_fields(data.get("model_id"))

    def _handle_sample_vocab_pairs(self, data: dict) -> dict:
        self._new_cancel_event()
        from core.deck_source import sample_vocab_pairs

        return sample_vocab_pairs(
            deck_id=data.get("deck_id"),
            model_id=data.get("model_id"),
            term_field=data.get("term_field", ""),
            definition_field=data.get("definition_field", ""),
            limit=data.get("limit", 50),
            excluded_pair_keys=data.get("excluded_pair_keys", []),
            weak_words=data.get("weak_words", []),
        )



    def _handle_set_ui_lang(self, data: dict) -> dict:
        lang = valid_ui_lang(data.get("lang"), self.settings.get("ui_lang", DEFAULT_UI_LANG))
        self.settings.set("ui_lang", lang)
        if self._api_client:
            self._api_client.ui_lang = lang
        self._gamemode_cache.clear()
        log.info(f"UI language set to: {lang}")
        return {"ui_lang": lang, "lang": lang}

    def _handle_set_learn_lang(self, data: dict) -> dict:
        lang = valid_learn_lang(data.get("lang"), self.settings.get("learn_lang", DEFAULT_LEARN_LANG))
        self.settings.set("learn_lang", lang)
        self._gamemode_cache.clear()
        log.info(f"Learning language set to: {lang}")
        return {"learn_lang": lang}

    def _handle_get_ui_lang(self, data: dict = None) -> dict:
        lang = valid_ui_lang(self.settings.get("ui_lang"))
        return {"lang": lang}

    def _handle_get_ui_strings(self, data: dict = None) -> dict:
        lang = valid_ui_lang(self.settings.get("ui_lang"))
        from core.i18n import load_strings

        strings = load_strings(lang)
        return {"strings": strings, "lang": lang}

    def _handle_get_supported_languages(self, data: dict = None) -> dict:
        return bridge_languages()

    def _handle_get_hint(self, data: dict) -> dict:
        from core.hint_manager import HintManager
        gamemode = data.get("gamemode", "fill_blank")
        question_data = data.get("question_data", {})
        hint_level = data.get("hint_level", 1)
        ui_lang = self.settings.get("ui_lang", "en")
        return HintManager.get_hint_data(gamemode, question_data, hint_level, ui_lang)

    def _handle_ai_grade(self, data: dict) -> dict:
        self._new_cancel_event()
        data = normalize_language_fields(dict(data or {}))
        gamemode = data.get("gamemode", "fill_blank")
        learn_lang = valid_learn_lang(self.settings.get("learn_lang"))
        ui_lang = valid_ui_lang(self.settings.get("ui_lang"))
        level = data.get("level", "intermediate")

        from core.languages import get_language_name
        learn_lang_full = get_language_name(learn_lang)
        ui_lang_full = get_language_name(ui_lang)

        from core.logger import flow
        flow(
            phase="GRADER",
            message=f"AI Grade evaluated for gamemode={gamemode}, feedback_lang={ui_lang_full}"
        )

        from core.ai_grader import get_grader_prompt

        common = {"learn_lang": learn_lang_full, "level": level, "feedback_lang": ui_lang_full}
        if gamemode == "fill_blank":
            prompt_data = {
                **common,
                "target_word": data.get("target_word", ""),
                "meaning": data.get("meaning", ""),
                "question": data.get("question", ""),
                "expected": data.get("expected", data.get("target_word", "")),
                "user_answer": data.get("user_answer", ""),
            }
        elif gamemode == "translation":
            prompt_data = {
                **common,
                "source_lang": ui_lang,
                "target_lang": learn_lang,
                "source_sentence": data.get("source_sentence", data.get("source_text", "")),
                "reference_translation": data.get("reference_translation", data.get("expected", "")),
                "user_target": data.get("user_answer", ""),
            }
        elif gamemode == "unscramble":
            prompt_data = {
                **common,
                "correct_sentence": data.get("correct_sentence", data.get("expected", "")),
                "user_sentence": data.get("user_answer", ""),
            }
        elif gamemode == "sentence_transform":
            prompt_data = {
                **common,
                "prompt": data.get("prompt", data.get("instruction", "")),
                "original": data.get("original", ""),
                "expected_answer": data.get("expected_answer", data.get("expected", "")),
                "normalized_answer": data.get("normalized_answer", ""),
                "forbidden_words": data.get("forbidden_words", "None"),
                "acceptable_variations": data.get("acceptable_variations", "None"),
                "user_answer": data.get("user_answer", ""),
            }
        elif gamemode == "taboo":
            prompt_data = {
                **common,
                "target_word": data.get("target_word", data.get("secret_word", "")),
                "meaning": data.get("meaning", ""),
                "taboo_words": data.get("taboo_words", "None"),
                "sample_acceptable_phrases": data.get("sample_acceptable_phrases", "None"),
                "sample_forbidden_phrases": data.get("sample_forbidden_phrases", "None"),
                "user_input": data.get("user_answer", ""),
            }
        else:
            prompt_data = {
                **common,
                "question": data.get("question", ""),
                "expected": data.get("expected", ""),
                "user_answer": data.get("user_answer", ""),
            }
        prompt = get_grader_prompt(gamemode, **prompt_data)

        client = self._get_api_client()
        if not client:
            return {"error": True, "error_code": "E_NO_KEYS", "message": "No API key"}

        result = client.generate_text_result(
            prompt, temperature=0.3, progress_callback=self._send_progress
        )
        if result.get("error"):
            return result
        return sanitize_dict(normalize_language_fields(result))

    def _handle_close_hub(self, data: dict = None) -> dict:
        from aqt import mw
        from core.logger import flow
        flow(phase="EVENT", message="AI Hub closed via bridge RPC")
        if hasattr(mw, "ai_hub_view") and mw.ai_hub_view is not None:
            mw.ai_hub_view.close()
        return {}

    def _handle_save_to_anki(self, data: dict) -> dict:
        gamemode = data.get("gamemode", "fill_blank")
        content = data.get("content", {})
        deck_name = data.get("deck", "AI Learning")
        gm = self.get_gamemode(gamemode)
        if gm and hasattr(gm, "save_to_anki"):
            items = content if isinstance(content, list) else [content]
            count = gm.save_to_anki(items, deck_name)
            log.info(f"Saved {count} cards to deck '{deck_name}' from {gamemode}")
            return {"success": True, "count": count}
        log.warn(f"No save handler for {gamemode}")
        return {
            "error": True,
            "error_code": "E_NO_SAVE_HANDLER",
            "message": f"No save handler for {gamemode}",
        }

    def _handle_check_answer(self, data: dict) -> dict:
        gamemode = data.get("gamemode", "fill_blank")
        user_input = data.get("user_input")
        correct = data.get("correct")
        gm = self.get_gamemode(gamemode)
        if gm and hasattr(gm, "check_answer"):
            result = gm.check_answer(user_input, correct)
            log.debug(f"check_answer: {gamemode} -> {result}")
            return result
        log.warn(f"No check handler for {gamemode}")
        return {
            "error": True,
            "error_code": "E_NO_CHECK_HANDLER",
            "message": f"No check handler for {gamemode}",
        }



    def _handle_save_prefs(self, data: dict) -> dict:
        prefs_path = os.path.join(ADDON_PATH, "user_files", "prefs.json")
        try:
            os.makedirs(os.path.dirname(prefs_path), exist_ok=True)
            with open(prefs_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.debug("Prefs saved to user_files/prefs.json")
            return {"success": True}
        except Exception as e:
            log.error(f"Failed to save prefs: {e}")
            return {"success": False, "message": str(e)}

    def _handle_load_prefs(self, data: dict = None) -> dict:
        prefs_path = os.path.join(ADDON_PATH, "user_files", "prefs.json")
        if os.path.isfile(prefs_path):
            try:
                with open(prefs_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                log.debug("Prefs loaded from user_files/prefs.json")
                return loaded
            except Exception as e:
                log.warn(f"Failed to load prefs: {e}")
        return {}
