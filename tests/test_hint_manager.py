import sys
import unittest
from unittest.mock import MagicMock

# Mock aqt dependencies for standalone execution
sys.modules['aqt'] = MagicMock()
sys.modules['aqt.qt'] = MagicMock()
sys.modules['aqt.gui_hooks'] = MagicMock()
sys.modules['aqt.utils'] = MagicMock()

from core.hint_manager import HintManager
from gamemodes.taboo import TabooMode
from gamemodes.sentence_transform import SentenceTransformMode


class HintManagerAndGamemodesScoringTests(unittest.TestCase):
    def test_hint_manager_multipliers(self):
        qdata = {"target_word": "apple", "meaning": "fruit", "grammar_note": "noun"}

        # Level 0
        h0 = HintManager.get_hint_data("fill_blank", qdata, hint_level=0)
        self.assertEqual(h0["score_multiplier"], 1.0)
        self.assertEqual(h0["penalty_percent"], 0)
        self.assertFalse(h0["is_penalty"])

        # Level 1
        h1 = HintManager.get_hint_data("fill_blank", qdata, hint_level=1)
        self.assertEqual(h1["score_multiplier"], 0.75)
        self.assertEqual(h1["penalty_percent"], 25)
        self.assertTrue(h1["is_penalty"])

        # Level 2
        h2 = HintManager.get_hint_data("fill_blank", qdata, hint_level=2)
        self.assertEqual(h2["score_multiplier"], 0.50)
        self.assertEqual(h2["penalty_percent"], 50)
        self.assertTrue(h2["is_penalty"])

        # Level 3
        h3 = HintManager.get_hint_data("fill_blank", qdata, hint_level=3)
        self.assertEqual(h3["score_multiplier"], 0.0)
        self.assertEqual(h3["penalty_percent"], 100)
        self.assertTrue(h3["penalty"])

    def test_taboo_check_answer_tiered_penalties(self):
        taboo = TabooMode(MagicMock(), MagicMock())

        # L0
        r0 = taboo.check_answer("apple", "apple", hint_level=0)
        self.assertTrue(r0["correct"])
        self.assertEqual(r0["points"], 1.0)

        # L1
        r1 = taboo.check_answer("apple", "apple", hint_level=1)
        self.assertTrue(r1["correct"])
        self.assertEqual(r1["points"], 0.75)

        # L2
        r2 = taboo.check_answer("apple", "apple", hint_level=2)
        self.assertTrue(r2["correct"])
        self.assertEqual(r2["points"], 0.50)

        # L3
        r3 = taboo.check_answer("apple", "apple", hint_level=3)
        self.assertTrue(r3["correct"])
        self.assertEqual(r3["points"], 0.0)

    def test_sentence_transform_check_answer_tiered_penalties(self):
        st = SentenceTransformMode(MagicMock(), MagicMock())

        # L0
        r0 = st.check_answer("She is happy.", "She is happy.", hint_level=0)
        self.assertTrue(r0["correct"])
        self.assertEqual(r0["points"], 1.0)
        self.assertEqual(r0["score"], 10.0)

        # L1
        r1 = st.check_answer("She is happy.", "She is happy.", hint_level=1)
        self.assertTrue(r1["correct"])
        self.assertEqual(r1["points"], 0.75)
        self.assertEqual(r1["score"], 7.5)

        # L2
        r2 = st.check_answer("She is happy.", "She is happy.", hint_level=2)
        self.assertTrue(r2["correct"])
        self.assertEqual(r2["points"], 0.50)
        self.assertEqual(r2["score"], 5.0)

        # L3
        r3 = st.check_answer("She is happy.", "She is happy.", hint_level=3)
        self.assertTrue(r3["correct"])
        self.assertEqual(r3["points"], 0.0)
        self.assertEqual(r3["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
