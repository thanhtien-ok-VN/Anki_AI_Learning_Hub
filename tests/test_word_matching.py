import unittest
from gamemodes.word_matching import WordMatchingMode


class TestWordMatchingMode(unittest.TestCase):
    def setUp(self):
        self.mode = WordMatchingMode()

    def test_default_generation(self):
        result = self.mode.generate(count=8, source="builtin")
        self.assertNotIn("error", result)
        self.assertIn("pairs", result)
        self.assertEqual(len(result["pairs"]), 8)
        self.assertIn("game_id", result)

    def test_custom_count(self):
        result = self.mode.generate(count=5, source="builtin")
        self.assertEqual(len(result["pairs"]), 5)

    def test_vocab_pairs_supplement(self):
        # Pass only 2 pairs, mode should automatically supplement up to count (e.g. 6)
        few_pairs = [
            {"term": "apple", "definition": "a round red or green fruit"},
            {"term": "banana", "definition": "a long yellow fruit"},
        ]
        result = self.mode.generate(count=6, vocab_pairs=few_pairs)
        self.assertNotIn("error", result)
        self.assertEqual(len(result["pairs"]), 6)
        terms = [p["term"] for p in result["pairs"]]
        self.assertIn("apple", terms)
        self.assertIn("banana", terms)

    def test_check_answer_correct(self):
        res = self.mode.check_answer({"pair_id": "pair_1"}, {"pair_id": "pair_1"})
        self.assertTrue(res["correct"])
        self.assertEqual(res["points"], 1)

    def test_check_answer_incorrect(self):
        res = self.mode.check_answer({"pair_id": "pair_1"}, {"pair_id": "pair_2"})
        self.assertFalse(res["correct"])
        self.assertEqual(res["points"], 0)


if __name__ == "__main__":
    unittest.main()
