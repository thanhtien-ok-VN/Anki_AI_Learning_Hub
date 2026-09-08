"""Internationalization & Localization Service.

Manages UI language, target learning language, and localized string catalogs.
"""
from typing import Any, Dict, Optional
from core.languages import (
    DEFAULT_LEARN_LANG,
    DEFAULT_UI_LANG,
    bridge_languages,
    get_language_name,
    valid_learn_lang,
    valid_ui_lang,
)
from core.i18n import load_strings
from core.logger import log
from core.settings import SettingsManager


class I18nService:
    def __init__(self, settings_manager: Optional[SettingsManager] = None):
        self.settings = settings_manager or SettingsManager()

    def set_ui_lang(self, data: Dict[str, Any]) -> Dict[str, Any]:
        lang = valid_ui_lang(data.get("lang"), self.settings.get("ui_lang", DEFAULT_UI_LANG))
        self.settings.set("ui_lang", lang)
        log.info(f"UI language set to: {lang}")
        return {"ui_lang": lang, "lang": lang}

    def set_learn_lang(self, data: Dict[str, Any]) -> Dict[str, Any]:
        lang = valid_learn_lang(data.get("lang"), self.settings.get("learn_lang", DEFAULT_LEARN_LANG))
        self.settings.set("learn_lang", lang)
        log.info(f"Learning language set to: {lang}")
        return {"learn_lang": lang}

    def get_ui_lang(self) -> Dict[str, Any]:
        lang = valid_ui_lang(self.settings.get("ui_lang"))
        return {"lang": lang}

    def get_ui_strings(self) -> Dict[str, Any]:
        lang = valid_ui_lang(self.settings.get("ui_lang"))
        strings = load_strings(lang)
        return {"strings": strings, "lang": lang}

    def get_supported_languages(self) -> Dict[str, Any]:
        return bridge_languages()
