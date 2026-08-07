import unittest
import json

from core.language_normalizer import normalize_language_fields
from core.languages import (
    DEFAULT_LEARN_LANG,
    DEFAULT_UI_LANG,
    LEARN_LANGUAGE_CODES,
    UI_LANGUAGES,
    bridge_languages,
    valid_learn_lang,
    valid_ui_lang,
)
from core.prompt_manager import PromptManager
import os


class LanguageContractTests(unittest.TestCase):
    def test_registry_has_the_supported_axes(self):
        self.assertEqual(DEFAULT_UI_LANG, "en")
        self.assertEqual(DEFAULT_LEARN_LANG, "en")
        self.assertEqual(set(UI_LANGUAGES), {"en", "vi"})
        self.assertEqual(len(LEARN_LANGUAGE_CODES), 10)
        self.assertEqual(bridge_languages()["learn_languages"][0]["code"], "en")

    def test_invalid_codes_keep_the_previous_valid_value(self):
        self.assertEqual(valid_ui_lang("xx", "vi"), "vi")
        self.assertEqual(valid_learn_lang("vi", "ja"), "ja")

    def test_legacy_locale_fields_are_non_destructively_normalized(self):
        result = normalize_language_fields({"meaning_vi": "nghĩa", "items": [{"reason_vi": "lý do"}]})
        self.assertEqual(result["meaning"], "nghĩa")
        self.assertEqual(result["items"][0]["reason"], "lý do")
        self.assertEqual(normalize_language_fields({"meaning": "new", "meaning_vi": "old"})["meaning"], "new")

    def test_common_prompts_resolve_for_every_learning_language(self):
        root = os.path.dirname(os.path.dirname(__file__))
        manager = PromptManager(os.path.join(root, "prompts"))
        for code in LEARN_LANGUAGE_CODES:
            prompt = manager.get_prompt("fill_blank", language=code, ui_lang="vi", count=1)
            self.assertNotIn("{learn_lang}", prompt)
            self.assertNotIn("{ui_lang}", prompt)

    def test_ui_locale_catalogs_have_identical_keys(self):
        root = os.path.dirname(os.path.dirname(__file__))
        with open(os.path.join(root, "lang", "en.json"), encoding="utf-8") as handle:
            english = json.load(handle)
        with open(os.path.join(root, "lang", "vi.json"), encoding="utf-8") as handle:
            vietnamese = json.load(handle)
        self.assertEqual(set(english), set(vietnamese))


if __name__ == "__main__":
    unittest.main()
