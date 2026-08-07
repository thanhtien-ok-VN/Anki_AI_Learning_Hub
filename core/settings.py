import json
import os
import threading
import time
from typing import Any
from core.logger import log
from core.languages import DEFAULT_LEARN_LANG, DEFAULT_UI_LANG, valid_learn_lang, valid_ui_lang

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(ADDON_PATH, "user_files", "settings.json")

DEFAULT_SETTINGS = {
    "api_key1": "",
    "api_key2": "",
    "api_key3": "",
    "api_key4": "",
    "api_key5": "",
    "api_key6": "",
    "api_key7": "",
    "api_key8": "",
    "api_key9": "",
    "api_key10": "",
    "model": "auto",
    "temperature": 0.7,
    "ui_lang": DEFAULT_UI_LANG,
    "learn_lang": DEFAULT_LEARN_LANG,
    "window_width": 960,
    "window_height": 700,
}

_ALLOWED_FIELDS = frozenset(DEFAULT_SETTINGS.keys())
_API_KEY_FIELDS = frozenset(f"api_key{i}" for i in range(1, 11))

class SettingsManager:
    def __init__(self, settings_path: str = SETTINGS_PATH):
        self._path = settings_path
        self._lock = threading.RLock()
        self._settings = dict(DEFAULT_SETTINGS)
        self._load()

    @property
    def path(self) -> str:
        """Backward-compatible path accessor."""
        return self._path

    @property
    def data(self) -> dict:
        """Backward-compatible data accessor used by engine.py."""
        return self._settings

    @data.setter
    def data(self, value: dict):
        """Backward-compatible data setter used by tests."""
        self._settings = value

    def _backup_corrupt(self):
        try:
            timestamp = int(time.time())
            backup_path = self._path.replace(".json", f".corrupt.{timestamp}.json")
            os.rename(self._path, backup_path)
            log.warn(f"Corrupt settings backed up to {os.path.basename(backup_path)}")
        except Exception as e:
            log.error(f"Failed to backup corrupt settings: {e}")

    def _load(self):
        with self._lock:
            if not os.path.exists(self._path):
                return

            try:
                with open(self._path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                log.error("Settings file is corrupt. Loading defaults.")
                self._backup_corrupt()
                self._settings = dict(DEFAULT_SETTINGS)
                return
            except Exception as e:
                log.error(f"Failed to load settings: {e}")
                return

            # Legacy migration
            if "api_key" in data and isinstance(data["api_key"], str):
                if not data.get("api_key1"):
                    data["api_key1"] = data["api_key"]
            
            data.pop("api_key", None)
            data.pop("api_key_count", None)

            for key, value in data.items():
                if key in _ALLOWED_FIELDS:
                    if key == "ui_lang":
                        value = valid_ui_lang(value)
                    elif key == "learn_lang":
                        value = valid_learn_lang(value)
                    elif key in _API_KEY_FIELDS and isinstance(value, str):
                        value = value.strip()
                    self._settings[key] = value

    def _save(self) -> bool:
        with self._lock:
            try:
                tmp_path = self._path + ".tmp"
                os.makedirs(os.path.dirname(self._path), exist_ok=True)
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    data_to_save = {k: v for k, v in self._settings.items() if k in _ALLOWED_FIELDS}
                    json.dump(data_to_save, f, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, self._path)
                return True
            except Exception as e:
                log.error(f"Failed to save settings: {e}")
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                return False

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> dict:
        return self.set_many({key: value})

    def set_many(self, items: dict) -> dict:
        with self._lock:
            changed_keys = []
            ignored_keys = []
            
            for key, value in items.items():
                if key not in _ALLOWED_FIELDS:
                    ignored_keys.append(key)
                    continue
                
                # Validation
                if key == "temperature":
                    if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                        return {"ok": False, "error_code": "E_VALIDATION", "message": f"Invalid temperature: {value}"}
                elif key == "ui_lang":
                    validated = valid_ui_lang(value)
                    if validated != value:
                        return {"ok": False, "error_code": "E_VALIDATION", "message": f"Invalid ui_lang: {value}"}
                    value = validated
                elif key == "learn_lang":
                    validated = valid_learn_lang(value)
                    if validated != value:
                        return {"ok": False, "error_code": "E_VALIDATION", "message": f"Invalid learn_lang: {value}"}
                    value = validated
                elif key == "model":
                    if not isinstance(value, str) or not value.strip():
                        return {"ok": False, "error_code": "E_VALIDATION", "message": "Invalid model"}
                elif key in _API_KEY_FIELDS:
                    if not isinstance(value, str):
                        return {"ok": False, "error_code": "E_VALIDATION", "message": f"Invalid API key type for {key}"}
                    value = value.strip()
                elif key in ["window_width", "window_height"]:
                    if not isinstance(value, int) or value <= 0:
                        return {"ok": False, "error_code": "E_VALIDATION", "message": f"Invalid {key}"}

                if self._settings.get(key) != value:
                    self._settings[key] = value
                    changed_keys.append(key)

            if changed_keys:
                if not self._save():
                    return {"ok": False, "error_code": "E_SETTINGS_SAVE", "message": "Failed to save settings to disk"}

            return {"ok": True, "changed_keys": changed_keys, "ignored_keys": ignored_keys}

    def get_api_keys(self) -> list[str]:
        with self._lock:
            return [self._settings.get(f"api_key{i}", "") for i in range(1, 11)]

    def get_active_keys(self) -> list[str]:
        return [k for k in self.get_api_keys() if k]

    def get_masked_api_keys(self) -> list[str]:
        masked = []
        for k in self.get_api_keys():
            if not k:
                masked.append("")
            elif len(k) <= 12:
                if len(k) >= 6:
                    masked.append(f"{k[:2]}****{k[-2:]}")
                else:
                    masked.append("****")
            else:
                masked.append(f"{k[:4]}...{k[-4:]}")
        return masked

    def has_any_key(self) -> bool:
        return bool(self.get_active_keys())
