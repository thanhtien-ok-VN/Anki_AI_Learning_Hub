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


if __name__ == "__main__":
    unittest.main()
