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


def get_schema(gamemode: str) -> dict:
    if gamemode in RAW_DICT_SCHEMAS:
        return RAW_DICT_SCHEMAS[gamemode]
    return {}


def get_pydantic_model(gamemode: str):
    return REGISTRY.get(gamemode)


def _pydantic_to_gemini_schema(model) -> dict:
    if not HAS_PYDANTIC or model is None:
        return {}

    schema = model.schema()
    defs = schema.get("$defs", schema.get("definitions", {}))

    def resolve_ref(ref_str: str) -> dict:
        def_name = ref_str.split("/")[-1]
        return defs.get(def_name, {})

    def convert_prop(prop_schema: dict) -> dict:
        if "$ref" in prop_schema:
            prop_schema = resolve_ref(prop_schema["$ref"])

        p_type = prop_schema.get("type", "string")

        if "anyOf" in prop_schema:
            for item in prop_schema["anyOf"]:
                if item.get("type") != "null":
                    return convert_prop(item)
            p_type = "string"

        if p_type == "array":
            items_schema = prop_schema.get("items", {})
            return {
                "type": "ARRAY",
                "items": convert_prop(items_schema)
            }
        elif p_type == "object":
            props = prop_schema.get("properties", {})
            req = prop_schema.get("required", [])
            converted_props = {}
            for k, v in props.items():
                converted_props[k] = convert_prop(v)
            res = {
                "type": "OBJECT",
                "properties": converted_props
            }
            if req:
                res["required"] = req
            return res
        else:
            return {"type": TYPE_MAP.get(p_type, "STRING")}

    props = schema.get("properties", {})
    req = schema.get("required", [])
    converted_props = {}
    for k, v in props.items():
        converted_props[k] = convert_prop(v)

    res = {
        "type": "OBJECT",
        "properties": converted_props
    }
    if req:
        res["required"] = req
    return res


def model_to_gemini_schema(gamemode: str) -> dict:
    if HAS_PYDANTIC and gamemode in REGISTRY:
        try:
            return _pydantic_to_gemini_schema(REGISTRY[gamemode])
        except Exception:
            pass
    return get_schema(gamemode)
