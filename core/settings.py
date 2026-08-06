import json
import os
from typing import Any
from core.logger import log
from core.languages import DEFAULT_LEARN_LANG, DEFAULT_UI_LANG, valid_learn_lang, valid_ui_lang

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(ADDON_PATH, "user_files", "settings.json")

DEFAULT_SETTINGS = {
    "api_key": "",
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
    "api_key_count": 3,
    "model": "auto",
    "temperature": 0.7,
    "ui_lang": DEFAULT_UI_LANG,
    "learn_lang": DEFAULT_LEARN_LANG,
    "window_width": 960,
    "window_height": 700,
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
                self.data["ui_lang"] = valid_ui_lang(self.data.get("ui_lang"))
                self.data["learn_lang"] = valid_learn_lang(self.data.get("learn_lang"))
                log.debug(f"Settings loaded from {self.path}", {"key_count": len(self.data)})
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

    def set_many(self, items: dict):
        changed = False
        for key, value in items.items():
            old = self.data.get(key)
            if old != value:
                self.data[key] = value
                changed = True
                log.info(f"Setting changed: {key}", {"old": old, "new": value})
        if changed:
            self.save()

    def get_api_keys(self) -> list[str]:
        keys = []
        for i in range(1, 11):
            val = self.get(f"api_key{i}", "").strip()
            keys.append(val)
        
        if not keys[0]:
            old_key = self.get("api_key", "").strip()
            if old_key:
                keys[0] = old_key
        if not keys[1]:
            old_key2 = self.get("api_key2", "").strip()
            if old_key2:
                keys[1] = old_key2
        if not keys[2]:
            old_key3 = self.get("api_key3", "").strip()
            if old_key3:
                keys[2] = old_key3
        return keys

    def get_active_keys(self) -> list[str]:
        """Return list of valid, non-empty API keys with whitespace stripped."""
        raw_keys = self.get_api_keys()
        return [k.strip() for k in raw_keys if isinstance(k, str) and k.strip()]

    def get_masked_api_keys(self) -> list[str]:
        """Return masked strings for active non-empty API keys only."""
        active = self.get_active_keys()
        masked = []
        for k in active:
            if len(k) <= 12:
                masked.append(f"{k[:2]}****{k[-2:]}" if len(k) >= 6 else "****")
            else:
                masked.append(f"{k[:4]}...{k[-4:]}")
        return masked

    def has_any_key(self) -> bool:
        return bool(self.get_active_keys())
