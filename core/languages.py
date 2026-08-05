SUPPORTED_LANGUAGES = [
    {"code": "en", "names": {"en": "English", "vi": "Tiếng Anh"}, "native": "English"},
    {"code": "zh", "names": {"en": "Chinese", "vi": "Tiếng Trung"}, "native": "中文"},
    {"code": "ja", "names": {"en": "Japanese", "vi": "Tiếng Nhật"}, "native": "日本語"},
    {"code": "ko", "names": {"en": "Korean", "vi": "Tiếng Hàn"}, "native": "한국어"},
    {"code": "fr", "names": {"en": "French", "vi": "Tiếng Pháp"}, "native": "Français"},
    {"code": "de", "names": {"en": "German", "vi": "Tiếng Đức"}, "native": "Deutsch"},
    {"code": "es", "names": {"en": "Spanish", "vi": "Tiếng Tây Ban Nha"}, "native": "Español"},
    {"code": "it", "names": {"en": "Italian", "vi": "Tiếng Ý"}, "native": "Italiano"},
    {"code": "ru", "names": {"en": "Russian", "vi": "Tiếng Nga"}, "native": "Русский"},
    {"code": "hi", "names": {"en": "Hindi", "vi": "Tiếng Ấn Độ"}, "native": "हिन्दी"},
]

def get_language_name(code: str) -> str:
    mapping = {
        "en": "English",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "it": "Italian",
        "ru": "Russian",
        "hi": "Hindi",
        "vi": "Vietnamese",
    }
    return mapping.get(code.lower(), "English")
