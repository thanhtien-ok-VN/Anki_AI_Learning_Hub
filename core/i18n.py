import json
import os

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANG_DIR = os.path.join(ADDON_PATH, "lang")

DEFAULT_LANG = "vi"
_cache = {}


def load_strings(lang: str) -> dict:
    if lang in _cache:
        return _cache[lang]
    path = os.path.join(LANG_DIR, f"{lang}.json")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            strings = json.load(f)
    else:
        path = os.path.join(LANG_DIR, f"{DEFAULT_LANG}.json")
        with open(path, "r", encoding="utf-8") as f:
            strings = json.load(f)
    _cache[lang] = strings
    return strings


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    strings = load_strings(lang)
    text = strings.get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
