import sys
import unittest
from unittest.mock import MagicMock

# Mock aqt dependencies for standalone execution
sys.modules['aqt'] = MagicMock()
sys.modules['aqt.qt'] = MagicMock()
sys.modules['aqt.gui_hooks'] = MagicMock()
sys.modules['aqt.utils'] = MagicMock()

from gamemodes.fill_blank import FillBlankMode
from core.prompt_manager import PromptManager


class FillBlankLogicTests(unittest.TestCase):
    def setUp(self):
        self.mode = FillBlankMode(MagicMock(), MagicMock())

    def test_auto_masking_pre_existing_blank(self):
        """Test sentence that already has a blank placeholder."""
        raw = {
            "questions": [
                {
                    "sentence": "The cat sat on the ______.",
                    "target_word": "mat",
                    "options": [{"word": "mat", "is_correct": True}],
                }
            ]
        }
        res = self.mode.render_ui_data(raw)
        q = res["questions"][0]
        self.assertEqual(q["sentence_with_blank"], "The cat sat on the ______.")

    def test_auto_masking_standardize_placeholders(self):
        """Test standardizing ___ or [BLANK] placeholders."""
        raw = {
            "questions": [
                {
                    "sentence": "She went to the [BLANK] yesterday.",
                    "target_word": "market",
                    "options": [{"word": "market", "is_correct": True}],
                }
            ]
        }
        res = self.mode.render_ui_data(raw)
        q = res["questions"][0]
        self.assertEqual(q["sentence_with_blank"], "She went to the ______ yesterday.")

    def test_auto_masking_missing_blank_with_target_word(self):
        """Test sentence with missing blank where target_word is present."""
        raw = {
            "questions": [
                {
                    "sentence": "Da Nang is a beautiful city.",
                    "target_word": "beautiful",
                    "options": [{"word": "beautiful", "is_correct": True}],
                }
            ]
        }
        res = self.mode.render_ui_data(raw)
        q = res["questions"][0]
        self.assertEqual(q["sentence_with_blank"], "Da Nang is a ______ city.")

    def test_auto_masking_case_insensitive_target_word(self):
        """Test case-insensitive auto-masking for target_word."""
        raw = {
            "questions": [
                {
                    "sentence": "Abandoned projects usually fail.",
                    "target_word": "abandoned",
                    "options": [{"word": "abandoned", "is_correct": True}],
                }
            ]
        }
        res = self.mode.render_ui_data(raw)
        q = res["questions"][0]
        self.assertEqual(q["sentence_with_blank"], "______ projects usually fail.")

    def test_hint_scoring_penalties(self):
        """Test hint level penalty score deductions."""
        correct_opts = [{"word": "mat", "is_correct": True}, {"word": "dog", "is_correct": False}]

        # Level 0: Full points (1.0)
        c0 = self.mode.check_answer(user_input=0, correct=correct_opts, hint_level=0)
        self.assertTrue(c0["correct"])
        self.assertEqual(c0["points"], 1.0)

        # Level 1: 25% penalty (0.75)
        c1 = self.mode.check_answer(user_input=0, correct=correct_opts, hint_level=1)
        self.assertTrue(c1["correct"])
        self.assertEqual(c1["points"], 0.75)

        # Level 2: 50% penalty (0.50)
        c2 = self.mode.check_answer(user_input=0, correct=correct_opts, hint_level=2)
        self.assertTrue(c2["correct"])
        self.assertEqual(c2["points"], 0.50)

        # Level 3: 100% penalty (0.0)
        c3 = self.mode.check_answer(user_input=0, correct=correct_opts, hint_level=3)
        self.assertTrue(c3["correct"])
        self.assertEqual(c3["points"], 0.0)

        # Incorrect answer: 0.0
        cw = self.mode.check_answer(user_input=1, correct=correct_opts, hint_level=0)
        self.assertFalse(cw["correct"])
        self.assertEqual(cw["points"], 0.0)

    def test_prompt_manager_language_priority(self):
        """Test that PromptManager prioritizes language-specific prompt over common prompt."""
        pm = PromptManager("prompts")
        # Requesting 'en' prompt should resolve prompts/en/fill_blank.txt
        p_en = pm.get_prompt("fill_blank", language="en")
        self.assertIn("Generate a fill-in-the-blank exercise for a", p_en)

        # Requesting 'zh' prompt should resolve prompts/zh/fill_blank.txt
        p_zh = pm.get_prompt("fill_blank", language="zh")
        self.assertIn("Generate a fill-in-the-blank Chinese", p_zh)


if __name__ == "__main__":
    unittest.main()
