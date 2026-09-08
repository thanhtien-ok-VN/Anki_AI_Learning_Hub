"""Preferences & Settings Service.

Manages persistent user preferences, API keys, and settings validation.
"""
import json
import os
from typing import Any, Callable, Dict, List, Optional
from core.logger import log
from core.settings import SettingsManager, SETTINGS_PATH
from core.paths import PATHS, PathConfig


class PrefsService:
    def __init__(
        self,
        settings_manager: Optional[SettingsManager] = None,
        paths: Optional[PathConfig] = None,
    ):
        self.settings = settings_manager or SettingsManager()
        self.paths = paths or PATHS

    def _get_prefs_path(self) -> str:
        import sys
        engine = sys.modules.get("core.engine")
        if engine and hasattr(engine, "ADDON_PATH") and engine.ADDON_PATH != self.paths.addon_root:
            return os.path.join(engine.ADDON_PATH, "user_files", "prefs.json")
        return self.paths.prefs_path

    def get_settings(self) -> Dict[str, Any]:
        settings_copy = {
            key: value
            for key, value in self.settings.get_all().items()
            if not key.startswith("api_key")
        }
        settings_copy["masked_keys"] = self.settings.get_masked_api_keys()
        return settings_copy

    def save_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        changed = {}
        for key, value in data.items():
            if key in ("api_keys", "keys"):
                self.settings.set_api_keys(value)
                changed["keys"] = len(value) if isinstance(value, list) else 1
            else:
                self.settings.set(key, value)
                changed[key] = value

        self.settings.save()
        log.info(f"Settings saved: {list(changed.keys())}")
        from core.logger import flow
        flow(phase="SYSTEM", message="Settings saved", extra={"keys": list(changed.keys())})
        return {"saved": True, "changed": changed}

    def check_api_key(self) -> Dict[str, Any]:
        from core.api_client import GeminiClient
        keys = self.settings.get_active_keys()
        return {
            "has_key": bool(keys),
            "key_count": len(keys),
            "keys": [GeminiClient.detect_key_type(k) for k in keys],
        }

    def test_key(
        self,
        data: Dict[str, Any],
        cancel_event: Optional[Any] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        key = data.get("key", "").strip()
        if not key:
            log.warn("test_key called with empty key")
            return {"ok": False, "error": "Empty key"}

        from core.api_client import GeminiClient
        configured_model = self.settings.get("model", "auto")
        client = GeminiClient([key], configured_model, cancel_event=cancel_event)
        try:
            result = client.test_key(key, progress_callback=progress_callback)
            log.info(f"test_key result: ok={result.get('ok')} model={result.get('model')}")
            return result
        finally:
            if hasattr(client, "close"):
                client.close()

    def test_all_keys(
        self,
        cancel_event: Optional[Any] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        from core.api_client import GeminiClient
        keys = self.settings.get_api_keys()
        configured_model = self.settings.get("model", "auto")
        results = []

        for idx, key in enumerate(keys):
            if cancel_event and cancel_event.is_set():
                log.info(f"test_all_keys cancelled by user before slot {idx+1}/{len(keys)}")
                return {"results": results, "cancelled": True}

            slot = idx + 1
            if not key.strip():
                results.append({"key": slot, "ok": False, "error": "Empty"})
                continue

            client = GeminiClient([key], configured_model, cancel_event=cancel_event)
            try:
                res = client.test_key_with_waterfall(key, progress_callback=progress_callback)
                if cancel_event and cancel_event.is_set():
                    log.info(f"test_all_keys cancelled by user after slot {slot}/{len(keys)}")
                    results.append({
                        "key": slot,
                        "ok": False,
                        "model": res.get("model", ""),
                        "error_code": "E_CANCELLED",
                        "error": "Cancelled by user",
                    })
                    return {"results": results, "cancelled": True}
                results.append({
                    "key": slot,
                    "ok": res.get("ok", False),
                    "model": res.get("model", ""),
                    "error_code": res.get("error_code", ""),
                    "error": res.get("error", ""),
                    "response": res.get("response", ""),
                })
            finally:
                if hasattr(client, "close"):
                    client.close()

        log.info(f"test_all_keys: {sum(1 for r in results if r['ok'])}/{len(results)} ok")
        return {"results": results}

    def load_prefs(self) -> Dict[str, Any]:
        prefs_path = self._get_prefs_path()
        if os.path.isfile(prefs_path):
            try:
                with open(prefs_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.warn(f"Failed to load prefs.json: {e}")
        return {}

    def save_prefs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {"success": False, "message": "Invalid prefs data"}
        prefs_path = self._get_prefs_path()
        tmp_path = prefs_path + ".tmp"
        try:
            os.makedirs(os.path.dirname(prefs_path), exist_ok=True)
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, prefs_path)
            return {"success": True}
        except Exception as e:
            log.error(f"Failed to save prefs.json: {e}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return {"success": False, "message": str(e)}
