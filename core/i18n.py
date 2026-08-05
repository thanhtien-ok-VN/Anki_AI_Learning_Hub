import json
import os

from core.languages import valid_ui_lang

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANG_DIR = os.path.join(ADDON_PATH, "lang")

DEFAULT_LANG = "en"
_cache = {}


def load_strings(lang: str) -> dict:
    lang = valid_ui_lang(lang)
    if lang in _cache:
        return _cache[lang]
    path = os.path.join(LANG_DIR, f"{lang}.json")
    if not os.path.isfile(path):
        path = os.path.join(LANG_DIR, f"{DEFAULT_LANG}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            strings = json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        strings = {}
    _cache[lang] = strings
    return strings


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    strings = load_strings(lang)
    text = strings.get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
