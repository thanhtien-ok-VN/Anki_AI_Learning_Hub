"""Core Engine Facade & Coordinator.

Orchestrates services, lifecycle hooks, and IPC message dispatching for Anki Desktop.
"""
import json
import os
import threading
from typing import Any, Optional

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import tooltip

from core.logger import log, flow
from core.settings import SettingsManager, SETTINGS_PATH, DEFAULT_SETTINGS
from core.timer import SessionTimer
from core.router import IPCRouter
from core.services import (
    PrefsService,
    I18nService,
    AnkiService,
    GenerationService,
    GradingService,
)
from gamemodes import registry as gamemode_registry, list_manifests
from llm.factory import LLMProviderFactory
from llm.gemini import GeminiProvider
from core.paths import ADDON_PATH, PROMPTS_DIR, USER_FILES_DIR

GAME_LIMITS = gamemode_registry.get_all_limits()


class AIEngine:
    """Central Facade coordinating services, timer, and IPC bridge communication."""

    def __init__(self):
        self.settings = SettingsManager()
        self.timer = SessionTimer()
        self.cancel_event = threading.Event()
        self._api_lock = threading.RLock()
        self._api_client = None
        self._prompt_mgr = None
        self._gamemode_cache = {}

        # Domain Services
        self.prefs_service = PrefsService(self.settings)
        self.i18n_service = I18nService(self.settings)
        self.anki_service = AnkiService()
        self.generation_service = GenerationService()
        self.grading_service = GradingService()

        # IPC Router
        self.router = IPCRouter()
        self._register_routes()

        self.timer.tick.connect(self._on_timer_tick)
        gui_hooks.profile_will_close.append(self._on_profile_close)

    def _register_routes(self) -> None:
        """Register all IPC actions to their respective handlers."""
        routes = {
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
            "list_source_models": self._handle_get_source_models,
            "get_source_fields": self._handle_get_source_fields,
            "list_source_fields": self._handle_get_source_fields,
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
            "get_gamemodes": self._handle_get_gamemodes,
        }
        bg_actions = {
            "generate",
            "test_key",
            "test_all_keys",
            "ai_grade",
            "sample_vocab_pairs",
            "get_source_models",
            "list_source_models",
            "get_source_fields",
            "list_source_fields",
        }
        for action, handler in routes.items():
            mode = "background" if action in bg_actions else "main"
            self.router.register_handler(
                action,
                lambda data, act=action: getattr(self, f"_handle_{act}")(data),
                execution_mode=mode,
            )

    def handle_js_message(self, message: str) -> dict:
        """Entry point for incoming IPC bridge messages."""
        return self.router.dispatch(message)

    @staticmethod
    def _result(
        success_or_data: Any,
        data_if_success: Optional[dict] = None,
        code: Optional[str] = None,
        message: Optional[str] = None,
    ) -> dict:
        """Legacy helper preserving backward compatibility for response envelopes."""
        if isinstance(success_or_data, bool):
            ok = success_or_data
            payload = data_if_success or {}
        else:
            ok = True
            payload = success_or_data or {}

        if not ok:
            err_code = code or "E_OPERATION"
            err_msg = message or "The operation failed."
            return {
                "success": False,
                "data": payload,
                "error_code": err_code,
                "message": err_msg,
            }

        res = {"success": True, "data": payload}
        if code:
            res["error_code"] = code
        if message:
            res["message"] = message
        return res

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
                keys = self.settings.get_active_keys()
                if keys:
                    self._api_client = LLMProviderFactory.create(
                        "gemini",
                        settings={
                            "keys": keys,
                            "model": self.settings.get("model", "auto"),
                            "ui_lang": self.settings.get("ui_lang", "en"),
                        },
                        cancel_event=self.cancel_event,
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
            cls = gamemode_registry.get(name)
            if cls:
                self._gamemode_cache[name] = cls(
                    self._get_api_client(), self.get_prompt_manager()
                )
        return self._gamemode_cache.get(name)

    def start(self):
        self.timer.start()
        if self.settings.has_any_key():
            self._api_client = LLMProviderFactory.create(
                "gemini",
                settings={
                    "keys": self.settings.get_active_keys(),
                    "model": self.settings.get("model", "auto"),
                    "ui_lang": self.settings.get("ui_lang", "en"),
                },
                cancel_event=self.cancel_event,
            )
        log.info(
            "AIEngine started",
            {
                "has_keys": self.settings.has_any_key(),
                "num_keys": len(self.settings.get_active_keys()),
            },
        )

    def stop(self):
        self.timer.stop()
        gui_hooks.profile_will_close.remove(self._on_profile_close)
        log.info("AIEngine stopped")

    def _on_timer_tick(self, seconds: int):
        mins = seconds // 60
        if mins > 0 and seconds % 60 == 0:
            tooltip(f"AI Learning Hub: {mins} min session")

    def _on_profile_close(self):
        self.stop()

    # ──────────────────────────────────────────────────────────
    # Handlers delegating to Service Layer
    # ──────────────────────────────────────────────────────────

    def _handle_log_event(self, data: dict = None) -> dict:
        data = data or {}
        event = data.get("event", "unknown")
        game = data.get("game", "")
        extra = data.get("extra") or {}
        log.info(f"User event: {event}", {"game": game, **extra})
        flow(phase="EVENT", gamemode=game, message=f"User event: {event}", extra=extra)
        return {"logged": True}

    def _handle_cancel_gen(self, data: dict = None) -> dict:
        flow(phase="EVENT", message="Cancel requested by user via cancel_gen RPC")
        self.cancel_current_task()
        return {"cancelled": True}

    def _handle_get_gamemodes(self, data: dict = None) -> dict:
        return {"gamemodes": list_manifests()}

    def _handle_generate(self, data: dict) -> dict:
        cancel_evt = self._new_cancel_event()
        return self.generation_service.generate(
            data=data,
            api_client=self._get_api_client(),
            prompt_mgr=self.get_prompt_manager(),
            gamemode_resolver=self.get_gamemode,
            settings=self.settings,
            cancel_event=cancel_evt,
            progress_callback=self._send_progress,
        )

    def _handle_save_settings(self, data: dict) -> dict:
        to_update = {}
        for key, value in data.items():
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

        return {"saved": True, "changed_keys": changed}

    def _handle_get_settings(self, data: dict = None) -> dict:
        return self.prefs_service.get_settings()

    def _handle_check_api_key(self, data: dict = None) -> dict:
        return self.prefs_service.check_api_key()

    def _handle_test_key(self, data: dict) -> dict:
        return self.prefs_service.test_key(data, self._new_cancel_event(), self._send_progress)

    def _handle_test_all_keys(self, data: dict = None) -> dict:
        return self.prefs_service.test_all_keys(self._new_cancel_event(), self._send_progress)

    def _handle_list_decks(self, data: dict = None) -> dict:
        return self.anki_service.list_decks()

    def _handle_get_source_models(self, data: dict) -> dict:
        return self.anki_service.get_source_models(data)

    def _handle_get_source_fields(self, data: dict) -> dict:
        return self.anki_service.get_source_fields(data)

    def _handle_sample_vocab_pairs(self, data: dict) -> dict:
        return self.anki_service.sample_vocab_pairs(data, self._new_cancel_event())

    def _handle_save_to_anki(self, data: dict) -> dict:
        gamemode = data.get("gamemode", "fill_blank")
        return self.anki_service.save_to_anki(self.get_gamemode(gamemode), data)

    def _handle_check_answer(self, data: dict) -> dict:
        gamemode = data.get("gamemode", "fill_blank")
        return self.grading_service.check_answer(self.get_gamemode(gamemode), data)

    def _handle_get_hint(self, data: dict) -> dict:
        return self.grading_service.get_hint(data, self.settings.get("ui_lang", "en"))

    def _handle_ai_grade(self, data: dict) -> dict:
        self._new_cancel_event()
        return self.grading_service.ai_grade(
            api_client=self._get_api_client(),
            data=data,
            settings=self.settings,
            progress_callback=self._send_progress,
        )

    def _handle_set_ui_lang(self, data: dict) -> dict:
        return self.i18n_service.set_ui_lang(data)

    def _handle_set_learn_lang(self, data: dict) -> dict:
        res = self.i18n_service.set_learn_lang(data)
        self._gamemode_cache.clear()
        return res

    def _handle_get_ui_lang(self, data: dict = None) -> dict:
        return self.i18n_service.get_ui_lang()

    def _handle_get_ui_strings(self, data: dict = None) -> dict:
        return self.i18n_service.get_ui_strings()

    def _handle_get_supported_languages(self, data: dict = None) -> dict:
        return self.i18n_service.get_supported_languages()

    def _handle_save_prefs(self, data: dict) -> dict:
        return self.prefs_service.save_prefs(data)

    def _handle_load_prefs(self, data: dict = None) -> dict:
        return self.prefs_service.load_prefs()

    def _handle_close_hub(self, data: dict = None) -> dict:
        from aqt import mw
        flow(phase="EVENT", message="AI Hub closed via bridge RPC")
        if hasattr(mw, "ai_hub_view") and mw.ai_hub_view is not None:
            mw.ai_hub_view.close()
        return {}
