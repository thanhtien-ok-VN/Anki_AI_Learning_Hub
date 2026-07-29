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
        meaning_vi: str
        full_translation: str
        options: List[FillBlankOption]  # exactly 4
        explanation: str
        grammar_note: Optional[str] = None

    class FillBlankSchema(BaseModel):
        questions: List[FillBlankQuestion]

    # ===================== 2. CLOZE =====================
    class ClozeBlank(BaseModel):
        id: str                    # "BLANK_1", "BLANK_2"
        answer: str
        meaning_vi: str
        hint: str
        distractors: List[str]
        explanation: str

    class ClozeSchema(BaseModel):
        paragraph: str
        blanks: List[ClozeBlank]
        full_solution_text: str
        story_translation: str
        context_summary: str

    # ===================== 3. TRANSLATION =====================
    class AltTranslation(BaseModel):
        text: str
        note: str

    class KeyVocab(BaseModel):
        source: str
        target: str
        note: str

    class CommonMistake(BaseModel):
        wrong: str
        error_type: str
        correction: str

    class TranslationSchema(BaseModel):
        source_sentence: str
        target_language: str
        reference_translation: str
        alternative_translations: List[AltTranslation]
        key_vocabulary: List[KeyVocab]
        common_mistakes: List[CommonMistake]
        grading_rubric: str

    # ===================== 4. UNSCRAMBLE =====================
    class UnscrambleVocab(BaseModel):
        word: str
        meaning_vi: str

    class UnscrambleSentence(BaseModel):
        correct_sentence: str
        meaning_vi: str
        hint: str
        key_vocabulary: List[UnscrambleVocab]
        difficulty_reason: str
        grammar_note: str

    class UnscrambleSchema(BaseModel):
        questions: List[UnscrambleSentence]

    # ===================== 6. STORY =====================
    class HighlightedVocab(BaseModel):
        word: str
        meaning_vi: str
        context_meaning: str

    class StoryContent(BaseModel):
        title: str
        content: str
        word_count: int
        highlighted_vocab: List[HighlightedVocab]
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

    class StorySchema(BaseModel):
        story: StoryContent
        questions: List[StoryQuestion]
        discussion_prompt: str

    # ===================== 7. SENTENCE TRANSFORM =====================
    class AcceptableVariation(BaseModel):
        text: str
        note: str

    class CommonError(BaseModel):
        error: str
        feedback: str

    class SentenceTransformQuestion(BaseModel):
        original: str
        prompt: str
        expected_answer: str
        normalized_answer: str
        acceptable_variations: List[AcceptableVariation]
        forbidden_words: List[str]
        grammar_rule: str
        common_errors: List[CommonError]

    class SentenceTransformSchema(BaseModel):
        questions: List[SentenceTransformQuestion]

    # ===================== 8. TABOO =====================
    class TabooRound(BaseModel):
        target_word: str
        meaning_vi: str
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

# ===================== GEMINI SCHEMA CONVERTER =====================
TYPE_MAP = {
    "string": "STRING",
    "integer": "INTEGER",
    "number": "NUMBER",
    "boolean": "BOOLEAN",
    "array": "ARRAY",
    "object": "OBJECT",
}

# Raw Dict Schemas Fallback when Pydantic is not installed
RAW_DICT_SCHEMAS = {
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
                        "meaning_vi": {"type": "STRING"},
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
                        "grammar_note": {"type": "STRING"}
                    },
                    "required": ["sentence", "target_word", "meaning_vi", "full_translation", "options", "explanation"]
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
                        "meaning_vi": {"type": "STRING"},
                        "hint": {"type": "STRING"},
                        "distractors": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "explanation": {"type": "STRING"}
                    },
                    "required": ["id", "answer", "meaning_vi", "hint", "distractors", "explanation"]
                }
            },
            "full_solution_text": {"type": "STRING"},
            "story_translation": {"type": "STRING"},
            "context_summary": {"type": "STRING"}
        },
        "required": ["paragraph", "blanks", "full_solution_text", "story_translation", "context_summary"]
    },
    "translation": {
        "type": "OBJECT",
        "properties": {
            "source_sentence": {"type": "STRING"},
            "target_language": {"type": "STRING"},
            "reference_translation": {"type": "STRING"},
            "alternative_translations": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {"type": "STRING"},
                        "note": {"type": "STRING"}
                    },
                    "required": ["text", "note"]
                }
            },
            "key_vocabulary": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "source": {"type": "STRING"},
                        "target": {"type": "STRING"},
                        "note": {"type": "STRING"}
                    },
                    "required": ["source", "target", "note"]
                }
            },
            "common_mistakes": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "wrong": {"type": "STRING"},
                        "error_type": {"type": "STRING"},
                        "correction": {"type": "STRING"}
                    },
                    "required": ["wrong", "error_type", "correction"]
                }
            },
            "grading_rubric": {"type": "STRING"}
        },
        "required": ["source_sentence", "target_language", "reference_translation", "alternative_translations", "key_vocabulary", "common_mistakes", "grading_rubric"]
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
                        "meaning_vi": {"type": "STRING"},
                        "hint": {"type": "STRING"},
                        "key_vocabulary": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "word": {"type": "STRING"},
                                    "meaning_vi": {"type": "STRING"}
                                },
                                "required": ["word", "meaning_vi"]
                            }
                        },
                        "difficulty_reason": {"type": "STRING"},
                        "grammar_note": {"type": "STRING"}
                    },
                    "required": ["correct_sentence", "meaning_vi", "hint", "key_vocabulary", "difficulty_reason", "grammar_note"]
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
                    "highlighted_vocab": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "word": {"type": "STRING"},
                                "meaning_vi": {"type": "STRING"},
                                "context_meaning": {"type": "STRING"}
                            },
                            "required": ["word", "meaning_vi", "context_meaning"]
                        }
                    },
                    "full_translation": {"type": "STRING"}
                },
                "required": ["title", "content", "word_count", "highlighted_vocab", "full_translation"]
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
                        "evidence_quote": {"type": "STRING"}
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
                        "acceptable_variations": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "text": {"type": "STRING"},
                                    "note": {"type": "STRING"}
                                },
                                "required": ["text", "note"]
                            }
                        },
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
                    "required": ["original", "prompt", "expected_answer", "normalized_answer", "acceptable_variations", "forbidden_words", "grammar_rule", "common_errors"]
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
                        "meaning_vi": {"type": "STRING"},
                        "taboo_words": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "clue": {"type": "STRING"},
                        "difficulty_level": {"type": "STRING"},
                        "sample_acceptable_phrases": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "sample_forbidden_phrases": {"type": "ARRAY", "items": {"type": "STRING"}}
                    },
                    "required": ["target_word", "meaning_vi", "taboo_words", "clue", "difficulty_level", "sample_acceptable_phrases", "sample_forbidden_phrases"]
                }
            }
        },
        "required": ["rounds"]
    }
}

def model_to_gemini_schema(model_class) -> dict:
    """Convert Pydantic BaseModel -> Gemini response_schema dict."""
    if not HAS_PYDANTIC or not hasattr(model_class, "model_json_schema"):
        return {}
    schema = model_class.model_json_schema()
    defs = schema.get("$defs", {})

    def convert(props):
        out = {}
        for name, prop in props.items():
            ref = prop.get("$ref", "")
            if ref:
                prop = defs.get(ref.split("/")[-1], prop)

            if prop.get("type") == "array":
                items = prop.get("items", {})
                iref = items.get("$ref", "")
                if iref:
                    idef = defs.get(iref.split("/")[-1], {})
                    out[name] = {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": convert(idef.get("properties", {})),
                            "required": list(idef.get("required", [])),
                        },
                    }
                else:
                    out[name] = {
                        "type": "ARRAY",
                        "items": {"type": TYPE_MAP.get(items.get("type", "string"), "STRING")},
                    }
            elif prop.get("properties"):
                out[name] = {
                    "type": "OBJECT",
                    "properties": convert(prop["properties"]),
                    "required": list(prop.get("required", [])),
                }
            else:
                out[name] = {"type": TYPE_MAP.get(prop.get("type", "string"), "STRING")}
        return out

    return {
        "type": "OBJECT",
        "properties": convert(schema.get("properties", {})),
        "required": list(schema.get("required", [])),
    }

def get_schema(gamemode: str) -> Optional[dict]:
    if HAS_PYDANTIC and gamemode in REGISTRY:
        cls = REGISTRY.get(gamemode)
        return model_to_gemini_schema(cls) if cls else None
    return RAW_DICT_SCHEMAS.get(gamemode)

def get_pydantic_model(gamemode: str):
    return REGISTRY.get(gamemode) if HAS_PYDANTIC else None

def list_gamemodes() -> list[str]:
    return list(RAW_DICT_SCHEMAS.keys())
