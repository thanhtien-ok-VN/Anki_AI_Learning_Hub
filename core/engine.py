import json
import os
import time
from typing import Any, Optional

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import tooltip

from core.logger import log

import re

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

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(ADDON_PATH, "user_files", "settings.json")

DEFAULT_SETTINGS = {
    "api_key": "",
    "api_key2": "",
    "api_key3": "",
    "model": "auto",
    "temperature": 0.7,
    "ui_lang": "vi",
    "learn_lang": "en",
    "window_width": 960,
    "window_height": 700,
}

GAME_LIMITS = {
    "fill_blank": (1, 5),
    "translation": (1, 5),
    "unscramble": (1, 5),
    "sentence_transform": (1, 5),
    "taboo": (1, 5),
    "cloze": (1, 5),
    "matching": (3, 12),
    "story": (3, 5),
}


class SettingsManager:
    def __init__(self, path: str = SETTINGS_PATH):
        self.path = path
        self.data: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self._load()

    def _load(self):
        if os.path.isfile(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
                log.debug(
                    f"Settings loaded from {self.path}", {"key_count": len(self.data)}
                )
            except Exception as e:
                log.warn(f"Failed to load settings: {e}")

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        log.debug("Settings saved")

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value):
        old = self.data.get(key)
        self.data[key] = value
        self.save()
        if old != value:
            log.info(f"Setting changed: {key}", {"old": old, "new": value})

    def get_api_keys(self) -> list[str]:
        return [
            self.get("api_key", "").strip(),
            self.get("api_key2", "").strip(),
            self.get("api_key3", "").strip(),
        ]

    def get_active_keys(self) -> list[str]:
        return [k for k in self.get_api_keys() if k]

    def has_any_key(self) -> bool:
        return bool(self.get_active_keys())


class SessionTimer(QObject):
    tick = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.start_time: Optional[float] = None
        self._qtimer = QTimer()
        self._qtimer.timeout.connect(self._on_tick)
        self._enabled = True

    def start(self):
        self.start_time = time.time()
        if self._enabled:
            self._qtimer.start(1000)

    def stop(self):
        self._qtimer.stop()
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.start_time = None
            return elapsed
        return 0

    def toggle(self, enabled: bool):
        self._enabled = enabled
        if enabled and self.start_time:
            self._qtimer.start(1000)
        else:
            self._qtimer.stop()

    def elapsed_seconds(self) -> int:
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0

    def _on_tick(self):
        if self.start_time:
            self.tick.emit(self.elapsed_seconds())


class AIEngine:
    def __init__(self):
        self.settings = SettingsManager()
        self.timer = SessionTimer()
        self._api_client = None
        self._prompt_mgr = None
        self._gamemode_cache = {}

        self.timer.tick.connect(self._on_timer_tick)
        gui_hooks.profile_will_close.append(self._on_profile_close)

    def _send_progress(self, text: str):
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
        if self._api_client is None:
            from core.api_client import GeminiClient

            keys = self.settings.get_active_keys()
            if keys:
                self._api_client = GeminiClient(
                    keys, self.settings.get("model", "auto")
                )
        return self._api_client

    def _reset_api_client(self):
        self._api_client = None

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
                "get_ui_lang": self._handle_get_ui_lang,
                "get_ui_strings": self._handle_get_ui_strings,
                "ai_grade": self._handle_ai_grade,
                "close_hub": self._handle_close_hub,
            }
            handler = handlers.get(action)
            if handler:
                result = handler(data)
                # All public bridge results have one stable envelope.  Existing
                # gamemode payloads remain inside data for the SPA.
                if isinstance(result, dict) and "success" in result:
                    if not result.get("success"):
                        log.warn(
                            f"Bridge operation failed: {result.get('message', '')}"
                        )
                        return {
                            "success": False,
                            "data": {},
                            "error_code": result.get("error_code", "E_OPERATION"),
                            "message": "The AI Hub could not complete this request.",
                        }
                    return result
                if isinstance(result, dict) and result.get("error"):
                    return {
                        "success": False,
                        "data": {},
                        "error_code": result.get("error_code", "E_OPERATION"),
                        "message": result.get("message", "The operation failed."),
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

    def _handle_generate(self, data: dict) -> dict:
        data = dict(data or {})
        gamemode = data.get("gamemode", "fill_blank")
        language = data.get("language", self.settings.get("learn_lang", "en"))
        level = data.get("level", "intermediate")
        topic = data.get("topic", "daily_life")
        minimum, maximum = GAME_LIMITS.get(gamemode, (1, 5))
        count = max(minimum, min(int(data.get("count", minimum)), maximum))
        data["count"] = count
        # SPA callers only need to provide the common controls.  These defaults
        # satisfy each prompt template without making UI routes template-aware.
        data.setdefault("paragraph_min_words", 80)
        data.setdefault("paragraph_max_words", 140)
        data.setdefault("num_blanks", min(5, int(count)))
        data.setdefault("source_lang", "vi")
        data.setdefault("target_lang", language)
        data.setdefault("word_count", 180)
        data.setdefault("question_count", 3)
        data.setdefault("target_words", "")
        data.setdefault("focus", "grammar")
        data.setdefault("voice", "active/passive")
        data.setdefault("conditional", "conditional")
        data.setdefault("reported", "reported speech")
        data.setdefault("comparative", "comparative")

        log.info(
            f"Generate: {gamemode}",
            {"language": language, "level": level, "topic": topic, "count": count},
        )

        gm = self.get_gamemode(gamemode)
        if gm and getattr(gm, "is_offline", False):
            log.info(f"{gamemode} is offline mode, generating locally")
            return gm.generate(**data)

        from core.schema_registry import get_schema

        schema = get_schema(gamemode)
        if not schema:
            log.warn(f"No schema for gamemode: {gamemode}")
            return {
                "error": True,
                "error_code": "E_NO_SCHEMA",
                "message": f"Unknown gamemode: {gamemode}",
            }

        prompt_mgr = self.get_prompt_manager()
        source_pairs = data.get("vocab_pairs") or []
        if source_pairs and gamemode == "story" and not data.get("target_words"):
            data = dict(data)
            data["target_words"] = ", ".join(
                pair["term"] for pair in source_pairs[:count]
            )
        # Do not pass the common arguments twice: they are already explicit
        # parameters of get_prompt(), while the SPA also stores them in data.
        prompt_data = dict(data)
        for key in ("gamemode", "language", "level", "topic", "count", "vocab_pairs"):
            prompt_data.pop(key, None)
        prompt = prompt_mgr.get_prompt(
            gamemode=gamemode,
            language=language,
            level=level,
            topic=topic,
            count=count,
            vocab_pairs=source_pairs,
            **prompt_data,
        )

        client = self._get_api_client()
        if not client:
            log.warn("No API client available")
            return {
                "error": True,
                "error_code": "E_NO_KEYS",
                "message": "No API key configured. Set at least one in Settings.",
            }

        result = client.generate_structured(
            prompt=prompt,
            response_schema=schema,
            temperature=self.settings.get("temperature", 0.7),
            progress_callback=self._send_progress,
        )

        if result.get("error"):
            log.warn(
                f"Generate failed: {result.get('error_code', '?')} - {result.get('message', '')[:100]}"
            )
            return result
        else:
            key_used = result.get("_key_used", "?")
            model_used = result.get("_model_used", "?")
            log.info(f"Generate OK: {key_used} / {model_used}")
            
            # Pydantic model validation
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
                    # Keep raw result as fallback rather than failing
                    pass

        if not result.get("error"):
            from core.content_validation import validate_game_result

            validation = validate_game_result(gamemode, result, count)
            if validation.get("error"):
                return {
                    "error": True,
                    "error_code": "E_AI_CONTENT",
                    "message": validation["error"],
                }

        # Ánh xạ định nghĩa từ Anki deck của người dùng vào câu hỏi Fill in the Blank
        if gamemode == "fill_blank" and not result.get("error"):
            vocab_map = {}
            for p in source_pairs:
                term = p.get("term", "").strip().lower()
                defn = p.get("definition", "").strip()
                if term and defn:
                    vocab_map[term] = defn
                    
            if "questions" in result:
                for q in result["questions"]:
                    target = q.get("target_word", "").strip().lower()
                    matched_def = vocab_map.get(target)
                    if not matched_def:
                        # Khớp tương đối nếu từ ghép hoặc chứa từ khóa
                        for term, defn in vocab_map.items():
                            if term == target or (len(term) > 3 and term in target) or (len(target) > 3 and target in term):
                                matched_def = defn
                                break
                    q["user_definition"] = matched_def if matched_def else q.get("meaning_vi", "")

        if gm and not result.get("error"):
            rendered = gm.render_ui_data(result)
            if rendered:
                result = rendered


        # Recursively sanitize all HTML content in result before returning
        result = sanitize_dict(result)
        return result

    def _handle_save_settings(self, data: dict) -> dict:
        changed_keys = []
        for key, value in data.items():
            self.settings.set(key, value)
            changed_keys.append(key)
        if any(k.startswith("api_key") for k in data):
            self._reset_api_client()
            self._gamemode_cache.clear()
            log.info("API keys changed, client+cache reset")
        log.info("Settings saved via JS", {"keys": changed_keys})
        return {"saved": changed_keys}

    def _handle_get_settings(self, data: dict = None) -> dict:
        # API keys never cross the Python/JS bridge.
        return {
            key: value
            for key, value in self.settings.data.items()
            if not key.startswith("api_key")
        }

    def _handle_check_api_key(self, data: dict = None) -> dict:
        keys = self.settings.get_active_keys()
        from core.api_client import GeminiClient

        return {
            "has_key": bool(keys),
            "key_count": len(keys),
            "keys": [GeminiClient.detect_key_type(k) for k in keys],
        }

    def _handle_test_key(self, data: dict) -> dict:
        key = data.get("key", "").strip()
        if not key:
            log.warn("test_key called with empty key")
            return {"ok": False, "error": "Empty key"}
        from core.api_client import GeminiClient

        client = GeminiClient([key], "auto")
        result = client.test_key(key)
        log.info(f"test_key result: ok={result.get('ok')} model={result.get('model')}")
        if hasattr(client, "close"):
            client.close()
        return result

    def _handle_test_all_keys(self, data: dict = None) -> dict:
        keys = self.settings.get_api_keys()
        from core.api_client import GeminiClient

        results = []
        for idx, key in enumerate(keys):
            if not key.strip():
                results.append({"key": idx + 1, "ok": False, "error": "Empty"})
                continue
            client = GeminiClient([key], "auto")
            res = client.test_key_with_waterfall(key)
            results.append(
                {
                    "key": idx + 1,
                    "ok": res.get("ok", False),
                    "model": res.get("model", ""),
                    "error_code": res.get("error_code", ""),
                    "error": res.get("error", ""),
                    "response": res.get("response", ""),
                }
            )
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
        lang = data.get("lang", "vi")
        self.settings.set("ui_lang", lang)
        log.info(f"UI language set to: {lang}")
        return {"lang": lang}

    def _handle_get_ui_lang(self, data: dict = None) -> dict:
        lang = self.settings.get("ui_lang", "vi")
        return {"lang": lang}

    def _handle_get_ui_strings(self, data: dict = None) -> dict:
        lang = self.settings.get("ui_lang", "vi")
        from core.i18n import load_strings

        strings = load_strings(lang)
        return {"strings": strings, "lang": lang}

    def _handle_ai_grade(self, data: dict) -> dict:
        gamemode = data.get("gamemode", "fill_blank")
        learn_lang = self.settings.get("learn_lang", "en")
        level = data.get("level", "intermediate")

        from core.ai_grader import get_grader_prompt

        common = {"learn_lang": learn_lang, "level": level}
        if gamemode == "fill_blank":
            prompt_data = {
                **common,
                "target_word": data.get("target_word", ""),
                "meaning_vi": data.get("meaning_vi", ""),
                "question": data.get("question", ""),
                "expected": data.get("expected", data.get("target_word", "")),
                "user_answer": data.get("user_answer", ""),
            }
        elif gamemode == "translation":
            prompt_data = {
                **common,
                "source_lang": "Vietnamese",
                "target_lang": learn_lang,
                "source_sentence": data.get("source_sentence", data.get("source_text", "")),
                "reference_translation": data.get("reference_translation", data.get("expected", "")),
                "user_target": data.get("user_answer", ""),
                "common_mistakes": data.get("common_mistakes", "None provided"),
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
        return sanitize_dict(result)

    def _handle_close_hub(self, data: dict = None) -> dict:
        from aqt import mw

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
