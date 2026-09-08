import unittest
from core.ai_grader import get_grader_prompt, GRADER_PROMPTS


class TestAIGraderPrompts(unittest.TestCase):
    def test_transform_grader_prompt_structure(self):
        prompt = get_grader_prompt(
            "sentence_transform",
            prompt="Rewrite using passive voice",
            original="The team built the feature.",
            expected_answer="The feature was built by the team.",
            user_answer="The feature built by team.",
            level="intermediate",
            feedback_lang="Vietnamese",
            learn_lang="English",
            hint_level=0,
        )
        self.assertIn("errors", prompt)
        self.assertIn("suggested_answers", prompt)
        self.assertIn("score", prompt)
        self.assertIn("level", prompt)
        self.assertIn("Hint level used by student: 0", prompt)

    def test_all_grader_prompts_render_without_key_error(self):
        common_kwargs = {
            "learn_lang": "English",
            "level": "intermediate",
            "feedback_lang": "Vietnamese",
            "user_answer": "test answer",
            "hint_level": 0,
            "question": "test question",
            "expected": "test expected",
            "target_word": "word",
            "meaning": "meaning",
            "source_lang": "Vietnamese",
            "target_lang": "English",
            "source_sentence": "test source",
            "reference_translation": "test ref",
            "user_target": "test target",
            "correct_sentence": "test correct",
            "user_sentence": "test user",
            "prompt": "test prompt",
            "original": "test original",
            "expected_answer": "test expected",
            "forbidden_words": "none",
            "acceptable_variations": "none",
            "taboo_words": ["a", "b"],
            "sample_acceptable_phrases": ["c"],
            "sample_forbidden_phrases": ["d"],
            "user_input": "guess",
        }
        for mode in GRADER_PROMPTS:
            rendered = get_grader_prompt(mode, **common_kwargs)
            self.assertIsInstance(rendered, str)
            self.assertTrue(len(rendered) > 50)


class TestGradingServicePolymorphism(unittest.TestCase):
    def test_ai_grade_polymorphic_prompt_data(self):
        from unittest.mock import MagicMock
        from core.services.grading_service import GradingService

        service = GradingService()
        mock_client = MagicMock()
        mock_client.generate_text_result.return_value = {
            "score": 10,
            "feedback": "Great job!",
            "errors": [],
        }

        mock_settings = {"ui_lang": "vi", "learn_lang": "en"}

        for gamemode in ["fill_blank", "translation", "unscramble", "sentence_transform", "taboo"]:
            data = {
                "gamemode": gamemode,
                "user_answer": "my answer",
                "expected": "expected answer",
                "hint_level": 1,
            }
            res = service.ai_grade(mock_client, data, mock_settings)
            self.assertFalse(res.get("error"))
            self.assertEqual(res.get("score"), 10)
            mock_client.generate_text_result.assert_called()


if __name__ == "__main__":
    unittest.main()

