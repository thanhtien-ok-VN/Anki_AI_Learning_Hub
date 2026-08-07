import unittest
from core.schema_registry import get_schema, get_pydantic_model

AI_GAMEMODES = [
    "fill_blank",
    "cloze",
    "translation",
    "taboo",
    "story",
    "unscramble",
    "sentence_transform"
]


class TestSchemaRegistry(unittest.TestCase):
    def test_schemas_exist_for_ai_gamemodes(self):
        for gm in AI_GAMEMODES:
            schema = get_schema(gm)
            self.assertIsNotNone(schema, f"Schema missing for gamemode: {gm}")
            self.assertIsInstance(schema, dict, f"Schema for {gm} should be a dict")

    def test_pydantic_models_exist_for_ai_gamemodes(self):
        for gm in AI_GAMEMODES:
            model_cls = get_pydantic_model(gm)
            self.assertIsNotNone(model_cls, f"Pydantic model missing for gamemode: {gm}")

    def test_fill_blank_schema_validation(self):
        model_cls = get_pydantic_model("fill_blank")
        valid_payload = {
            "questions": [
                {
                    "sentence": "The dog ___ loudly.",
                    "target_word": "barked",
                    "meaning": "sủa",
                    "full_translation": "Con chó sủa to.",
                    "options": [
                        {"word": "barked", "is_correct": True, "type": "correct", "reason": "Right"},
                        {"word": "slept", "is_correct": False, "type": "wrong_context", "reason": "Wrong"}
                    ],
                    "explanation": "Correct",
                    "grammar_note": "Past tense"
                }
            ]
        }
        validated = model_cls.model_validate(valid_payload)
        self.assertEqual(len(validated.questions), 1)
        self.assertEqual(validated.questions[0].target_word, "barked")


if __name__ == '__main__':
    unittest.main()
