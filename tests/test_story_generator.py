import unittest
from core.content_validation import validate_game_result
from gamemodes.story_generator import StoryGeneratorMode


class TestStoryGeneratorMode(unittest.TestCase):
    def setUp(self):
        self.mode = StoryGeneratorMode()

    def test_render_ui_data_standard(self):
        raw = {
            "story": {"title": "Test Title", "content": "Test content", "word_count": 100},
            "questions": [
                {
                    "id": 1,
                    "type": "detail",
                    "question": "What is test?",
                    "options": [
                        {"text": "A", "is_correct": True},
                        {"text": "B", "is_correct": False},
                        {"text": "C", "is_correct": False},
                        {"text": "D", "is_correct": False},
                    ],
                    "explanation": "Exp",
                }
            ],
            "discussion_prompt": "Discuss",
        }
        res = self.mode.render_ui_data(raw)
        self.assertEqual(res["story"]["title"], "Test Title")
        self.assertEqual(len(res["questions"]), 1)
        self.assertEqual(len(res["questions"][0]["options"]), 4)
        self.assertIn("correct_index", res["questions"][0])
        self.assertNotEqual(res["questions"][0]["correct_index"], -1)

    def test_render_ui_data_alternative_keys_and_strings(self):
        raw = {
            "story": "Plain story text",
            "questions": [
                {
                    "type": "main_idea",
                    "question": "Q1",
                    "options": [
                        {"word": "Opt Word A", "is_correct": True},
                        {"option": "Opt Word B", "is_correct": False},
                        "Plain String Option C",
                    ],
                }
            ],
        }
        res = self.mode.render_ui_data(raw)
        q0 = res["questions"][0]
        self.assertEqual(q0["options"][0]["text"], "Opt Word A")
        self.assertEqual(q0["options"][1]["text"], "Opt Word B")
        self.assertEqual(q0["options"][2]["text"], "Plain String Option C")

    def test_check_answer(self):
        opts = [
            {"text": "A", "is_correct": False},
            {"text": "B", "is_correct": True},
        ]
        res_correct = self.mode.check_answer(1, opts)
        self.assertTrue(res_correct["correct"])
        self.assertEqual(res_correct["points"], 1)

        res_wrong = self.mode.check_answer(0, opts)
        self.assertFalse(res_wrong["correct"])
        self.assertEqual(res_wrong["points"], 0)

    def test_validation_normalizes_types_and_strings(self):
        payload = {
            "story": {"title": "Title", "content": "Body"},
            "questions": [
                {
                    "type": "main_idea",
                    "question": "Q1",
                    "options": [
                        {"word": "A", "is_correct": True},
                        "B", "C", "D"
                    ],
                },
                {
                    "type": "vocabulary_context",
                    "question": "Q2",
                    "options": [
                        {"option": "A", "is_correct": False},
                        {"option": "B", "is_correct": True},
                        "C", "D"
                    ],
                },
            ],
        }
        err = validate_game_result("story", payload)
        self.assertEqual(err, {})
        self.assertEqual(payload["questions"][0]["type"], "inference")
        self.assertEqual(payload["questions"][1]["type"], "vocabulary")
        self.assertEqual(payload["questions"][0]["options"][0]["text"], "A")
        self.assertEqual(payload["questions"][0]["options"][1]["text"], "B")

    def test_validation_empty_questions_does_not_error(self):
        payload = {"story": {"title": "Title", "content": "Body"}, "questions": []}
        err = validate_game_result("story", payload)
        self.assertEqual(err, {})


if __name__ == "__main__":
    unittest.main()
