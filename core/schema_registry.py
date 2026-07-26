FILL_BLANK = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sentence_with_blank": {"type": "string"},
                    "full_sentence": {"type": "string"},
                    "blank_word": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "correct_index": {"type": "integer"},
                    "hint": {"type": "string"},
                    "explanation_short": {"type": "string"},
                    "semantic": {"type": "string"},
                    "grammar": {"type": "string"},
                    "vocab_relation": {"type": "string"},
                    "sentence_translation": {"type": "string"},
                    "word_meaning": {"type": "string"},
                    "usage_example": {"type": "string"},
                },
                "required": ["sentence_with_blank", "options", "correct_index"],
            },
        }
    },
    "required": ["questions"],
}

CLOZE = {
    "type": "object",
    "properties": {
        "paragraph_with_blanks": {"type": "string"},
        "paragraph_full": {"type": "string"},
        "sentence_meaning": {"type": "string"},
        "blanks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "blank_id": {"type": "integer"},
                    "correct_word": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "correct_index": {"type": "integer"},
                    "explanation_short": {"type": "string"},
                    "explanation": {"type": "string"},
                    "meaning_in_vietnamese": {"type": "string"},
                },
            },
            "minItems": 1,
            "maxItems": 10,
        },
    },
    "required": ["paragraph_with_blanks", "blanks"],
}

TRANSLATION = {
    "type": "object",
    "properties": {
        "sentences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_text": {"type": "string"},
                    "target_text": {"type": "string"},
                    "vocabulary_highlight": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "word": {"type": "string"},
                                "translation": {"type": "string"},
                                "notes": {"type": "string"},
                            },
                        },
                    },
                    "grammar_notes": {"type": "string"},
                    "detailed_feedback": {
                        "type": "object",
                        "properties": {
                            "word_by_word": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "word": {"type": "string"},
                                        "translation": {"type": "string"},
                                        "notes": {"type": "string"},
                                    },
                                },
                            },
                            "common_mistakes": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "alternative_translations": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "improvement_tips": {"type": "string"},
                        },
                    },
                },
                "required": ["source_text", "target_text"],
            },
        }
    },
    "required": ["sentences"],
}

SENTENCE_UNSCRAMBLE = {
    "type": "object",
    "properties": {
        "sentences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "correct_sentence": {"type": "string"},
                    "hint": {"type": "string"},
                    "translation": {"type": "string"},
                    "sentence_meaning": {"type": "string"},
                    "key_vocab": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "word": {"type": "string"},
                                "meaning": {"type": "string"},
                            },
                        },
                    },
                },
                "required": ["correct_sentence"],
            },
        }
    },
    "required": ["sentences"],
}

STORY = {
    "type": "object",
    "properties": {
        "story": {"type": "string"},
        "target_word_usage": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "word": {"type": "string"},
                    "sentence_used_in": {"type": "string"},
                },
            },
        },
        "comprehension_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "correct_index": {"type": "integer"},
                    "explanation": {"type": "string"},
                },
            },
            "minItems": 1,
            "maxItems": 5,
        },
    },
    "required": ["story", "comprehension_questions"],
}

SENTENCE_TRANSFORM = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original_sentence": {"type": "string"},
                    "instruction": {"type": "string"},
                    "hint_word": {"type": "string"},
                    "expected_answer": {"type": "string"},
                    "grammar_rule": {"type": "string"},
                    "focus": {
                        "type": "string",
                        "enum": ["voice", "conditional", "reported", "comparative"],
                    },
                    "detailed_explanation": {
                        "type": "object",
                        "properties": {
                            "rule_description": {"type": "string"},
                            "step_by_step": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "common_errors": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "comparison": {"type": "string"},
                        },
                    },
                },
                "required": ["original_sentence", "instruction", "expected_answer"],
            },
        }
    },
    "required": ["questions"],
}

TABOO = {
    "type": "object",
    "properties": {
        "rounds": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "secret_word": {"type": "string"},
                    "forbidden_words": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 3,
                        "maxItems": 5,
                    },
                    "ai_description": {"type": "string"},
                    "category": {"type": "string"},
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                    },
                },
                "required": ["secret_word", "forbidden_words"],
            },
        }
    },
    "required": ["rounds"],
}

REGISTRY = {
    "fill_blank": FILL_BLANK,
    "cloze": CLOZE,
    "translation": TRANSLATION,
    "unscramble": SENTENCE_UNSCRAMBLE,
    "story": STORY,
    "sentence_transform": SENTENCE_TRANSFORM,
    "taboo": TABOO,
}


def get_schema(gamemode: str) -> dict:
    return REGISTRY.get(gamemode)


def list_gamemodes() -> list[str]:
    return list(REGISTRY.keys())
