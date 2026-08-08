"""The single language registry shared by every Python-facing subsystem."""

import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_UI_LANG = "en"
DEFAULT_LEARN_LANG = "en"

with open(os.path.join(_ROOT, "lang", "languages.json"), "r", encoding="utf-8") as _handle:
    _REGISTRY = json.load(_handle)

UI_LANGUAGES = tuple(_REGISTRY["ui_languages"])
SUPPORTED_LANGUAGES = tuple(_REGISTRY["learn_languages"])
LEARN_LANGUAGE_CODES = frozenset(item["code"] for item in SUPPORTED_LANGUAGES)
_ALL_LANGUAGE_NAMES = {item["code"]: item["names"]["en"] for item in SUPPORTED_LANGUAGES}
_ALL_LANGUAGE_NAMES["vi"] = "Vietnamese"
_ALL_LANGUAGE_NAMES["zh"] = "Chinese (Mandarin)"

def valid_ui_lang(value: object, fallback: str = DEFAULT_UI_LANG) -> str:
    return value if isinstance(value, str) and value in UI_LANGUAGES else fallback

def valid_learn_lang(value: object, fallback: str = DEFAULT_LEARN_LANG) -> str:
    return value if isinstance(value, str) and value in LEARN_LANGUAGE_CODES else fallback

def get_language_name(code: str) -> str:
    return _ALL_LANGUAGE_NAMES.get(str(code).lower(), "English")

def bridge_languages() -> dict:
    return {"ui_languages": list(UI_LANGUAGES), "learn_languages": [dict(item) for item in SUPPORTED_LANGUAGES]}
