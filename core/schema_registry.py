from typing import List, Optional

try:
    from pydantic import BaseModel
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object

if HAS_PYDANTIC:
    # ===================== 1. FILL BLANK =====================
    class FillBlankOption(BaseModel):
        word: str
        is_correct: bool
        type: str          # "correct"|"antonym"|"grammar_error"|"semantic_close"
        reason: Optional[str] = None

    class FillBlankQuestion(BaseModel):
        sentence: str
        target_word: str
        meaning: str
        full_translation: str
        options: List[FillBlankOption]  # exactly 4
        explanation: str
        grammar_note: Optional[str] = None
        user_definition: Optional[str] = None

    class FillBlankSchema(BaseModel):
        questions: List[FillBlankQuestion]

    # ===================== 2. CLOZE =====================
    class ClozeBlank(BaseModel):
        id: str                    # "BLANK_1", "BLANK_2"
        answer: str
        meaning: str
        distractors: List[str] = []
        explanation: str

    class ClozeSchema(BaseModel):
        paragraph: str
        blanks: List[ClozeBlank]
        full_solution_text: str
        story_translation: str

    # ===================== 3. TRANSLATION =====================
    class TranslationSchema(BaseModel):
        source_sentence: str
        target_language: str
        reference_translation: str
        grading_rubric: str

    # ===================== 4. UNSCRAMBLE =====================
    class UnscrambleVocab(BaseModel):
        word: str
        meaning: str

    class UnscrambleSentence(BaseModel):
        correct_sentence: str
        meaning: str
        hint: str
        key_vocabulary: List[UnscrambleVocab]
        difficulty_reason: str
        grammar_note: str
        core_structure: str

    class UnscrambleSchema(BaseModel):
        questions: List[UnscrambleSentence]

    # ===================== 6. STORY =====================
    class HighlightedVocab(BaseModel):
        word: str
        meaning: str
        context_meaning: str

    class StoryContent(BaseModel):
        title: str
        content: str
        word_count: int
        full_translation: str

    class StoryQuestionOption(BaseModel):
        text: str
        is_correct: bool

    class StoryQuestion(BaseModel):
        id: int
        type: str
        question: str
        options: List[StoryQuestionOption]
        explanation: str
        evidence_quote: str
        target_word: Optional[str] = None

    class StorySchema(BaseModel):
        story: StoryContent
        questions: List[StoryQuestion]
        discussion_prompt: str

    # ===================== 7. SENTENCE TRANSFORM =====================
    class CommonError(BaseModel):
        error: str
        feedback: str

    class SentenceTransformQuestion(BaseModel):
        original: str
        prompt: str
        expected_answer: str
        normalized_answer: str
        forbidden_words: List[str]
        grammar_rule: str
        common_errors: List[CommonError]

    class SentenceTransformSchema(BaseModel):
        questions: List[SentenceTransformQuestion]

    # ===================== 8. TABOO =====================
    class TabooRound(BaseModel):
        target_word: str
        meaning: str
        phonetic: Optional[str] = None
        taboo_words: List[str]
        clue: str
        difficulty_level: str
        sample_acceptable_phrases: List[str]
        sample_forbidden_phrases: List[str]

    class TabooSchema(BaseModel):
        rounds: List[TabooRound]

    REGISTRY = {
        "fill_blank": FillBlankSchema,
        "cloze": ClozeSchema,
        "translation": TranslationSchema,
        "unscramble": UnscrambleSchema,
        "story": StorySchema,
        "sentence_transform": SentenceTransformSchema,
        "taboo": TabooSchema,
    }
else:
    REGISTRY = {}

try:
    from core.schema_compiler import compile_model_to_gemini_schema
except ImportError:
    compile_model_to_gemini_schema = None

CANONICAL_SCHEMAS = {
    "fill_blank": {
        "type": "OBJECT",
        "properties": {
            "questions": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "sentence": {"type": "STRING"},
                        "target_word": {"type": "STRING"},
                        "meaning": {"type": "STRING"},
                        "full_translation": {"type": "STRING"},
                        "options": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "word": {"type": "STRING"},
                                    "is_correct": {"type": "BOOLEAN"},
                                    "type": {"type": "STRING"},
                                    "reason": {"type": "STRING"}
                                },
                                "required": ["word", "is_correct", "type"]
                            }
                        },
                        "explanation": {"type": "STRING"},
                        "grammar_note": {"type": "STRING"},
                        "user_definition": {"type": "STRING"}
                    },
                    "required": ["sentence", "target_word", "meaning", "full_translation", "options", "explanation"]
                }
            }
        },
        "required": ["questions"]
    },
    "cloze": {
        "type": "OBJECT",
        "properties": {
            "paragraph": {"type": "STRING"},
            "blanks": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {"type": "STRING"},
                        "answer": {"type": "STRING"},
                        "meaning": {"type": "STRING"},
                        "distractors": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "explanation": {"type": "STRING"}
                    },
                    "required": ["id", "answer", "meaning", "explanation"]
                }
            },
            "full_solution_text": {"type": "STRING"},
            "story_translation": {"type": "STRING"}
        },
        "required": ["paragraph", "blanks", "full_solution_text", "story_translation"]
    },
    "translation": {
        "type": "OBJECT",
        "properties": {
            "source_sentence": {"type": "STRING"},
            "target_language": {"type": "STRING"},
            "reference_translation": {"type": "STRING"},
            "grading_rubric": {"type": "STRING"}
        },
        "required": ["source_sentence", "target_language", "reference_translation", "grading_rubric"]
    },
    "unscramble": {
        "type": "OBJECT",
        "properties": {
            "questions": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "correct_sentence": {"type": "STRING"},
                        "meaning": {"type": "STRING"},
                        "hint": {"type": "STRING"},
                        "key_vocabulary": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "word": {"type": "STRING"},
                                    "meaning": {"type": "STRING"}
                                },
                                "required": ["word", "meaning"]
                            }
                        },
                        "difficulty_reason": {"type": "STRING"},
                        "grammar_note": {"type": "STRING"},
                        "core_structure": {"type": "STRING"}
                    },
                    "required": ["correct_sentence", "meaning", "hint", "key_vocabulary", "difficulty_reason", "grammar_note", "core_structure"]
                }
            }
        },
        "required": ["questions"]
    },
    "story": {
        "type": "OBJECT",
        "properties": {
            "story": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "content": {"type": "STRING"},
                    "word_count": {"type": "INTEGER"},
                    "full_translation": {"type": "STRING"}
                },
                "required": ["title", "content", "word_count", "full_translation"]
            },
            "questions": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {"type": "INTEGER"},
                        "type": {"type": "STRING"},
                        "question": {"type": "STRING"},
                        "options": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "text": {"type": "STRING"},
                                    "is_correct": {"type": "BOOLEAN"}
                                },
                                "required": ["text", "is_correct"]
                            }
                        },
                        "explanation": {"type": "STRING"},
                        "evidence_quote": {"type": "STRING"},
                        "target_word": {"type": "STRING"}
                    },
                    "required": ["id", "type", "question", "options", "explanation", "evidence_quote"]
                }
            },
            "discussion_prompt": {"type": "STRING"}
        },
        "required": ["story", "questions", "discussion_prompt"]
    },
    "sentence_transform": {
        "type": "OBJECT",
        "properties": {
            "questions": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "original": {"type": "STRING"},
                        "prompt": {"type": "STRING"},
                        "expected_answer": {"type": "STRING"},
                        "normalized_answer": {"type": "STRING"},
                        "forbidden_words": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "grammar_rule": {"type": "STRING"},
                        "common_errors": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "error": {"type": "STRING"},
                                    "feedback": {"type": "STRING"}
                                },
                                "required": ["error", "feedback"]
                            }
                        }
                    },
                    "required": ["original", "prompt", "expected_answer", "forbidden_words", "grammar_rule"]
                }
            }
        },
        "required": ["questions"]
    },
    "taboo": {
        "type": "OBJECT",
        "properties": {
            "rounds": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "target_word": {"type": "STRING"},
                        "meaning": {"type": "STRING"},
                        "phonetic": {"type": "STRING"},
                        "taboo_words": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "clue": {"type": "STRING"},
                        "difficulty_level": {"type": "STRING"},
                        "sample_acceptable_phrases": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "sample_forbidden_phrases": {"type": "ARRAY", "items": {"type": "STRING"}}
                    },
                    "required": ["target_word", "meaning", "taboo_words", "clue", "sample_acceptable_phrases", "sample_forbidden_phrases"]
                }
            }
        },
        "required": ["rounds"]
    }
}

RAW_DICT_SCHEMAS = CANONICAL_SCHEMAS


def get_schema(gamemode: str) -> dict:
    """Returns the Gemini OpenAPI JSON schema for the specified gamemode."""
    if gamemode in CANONICAL_SCHEMAS:
        return CANONICAL_SCHEMAS[gamemode]
    model = REGISTRY.get(gamemode)
    if model and compile_model_to_gemini_schema:
        try:
            return compile_model_to_gemini_schema(model)
        except Exception:
            pass
    return {}


def get_pydantic_model(gamemode: str):
    """Returns the Pydantic model class for the specified gamemode."""
    return REGISTRY.get(gamemode)


def model_to_gemini_schema(gamemode: str) -> dict:
    """Convenience alias for get_schema."""
    return get_schema(gamemode)

