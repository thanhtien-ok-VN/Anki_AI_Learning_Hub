from pydantic import BaseModel
from typing import List, Optional

# ===================== 1. FILL BLANK =====================
class FillBlankOption(BaseModel):
    word: str
    is_correct: bool
    type: str          # "correct"|"antonym"|"grammar_error"|"semantic_close"
    reason: Optional[str] = None

class FillBlankSchema(BaseModel):
    sentence: str
    target_word: str
    meaning_vi: str
    full_translation: str
    options: List[FillBlankOption]  # exactly 4
    explanation: str
    grammar_note: Optional[str] = None

# ===================== 2. CLOZE =====================
class ClozeBlank(BaseModel):
    id: str                    # "BLANK_1", "BLANK_2"
    answer: str
    meaning_vi: str
    hint: str
    distractors: List[str]     # exactly 3
    explanation: str

class ClozeSchema(BaseModel):
    paragraph: str             # contains [BLANK_1], [BLANK_2]
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

# ===================== 4. WORD UNSCRAMBLE (sentence-based) =====================
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
    sentences: List[UnscrambleSentence]

# ===================== 5. WORD MATCHING (click-pair / pair_id) =====================
class MatchItem(BaseModel):
    id: str
    content: str
    type: str        # "term"|"definition"
    pair_id: str

class MatchConfig(BaseModel):
    total_pairs: int
    time_limit_sec: int

class MatchMetadata(BaseModel):
    topic: str
    level: str

class WordMatchingSchema(BaseModel):
    game_id: str
    items: List[MatchItem]
    config: MatchConfig
    metadata: MatchMetadata

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
    type: str            # "detail"|"inference"|"vocabulary"
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

class SentenceTransformSchema(BaseModel):
    original: str
    prompt: str
    expected_answer: str
    normalized_answer: str
    acceptable_variations: List[AcceptableVariation]
    forbidden_words: List[str]
    grammar_rule: str
    common_errors: List[CommonError]

# ===================== 8. TABOO =====================
class TabooSchema(BaseModel):
    target_word: str
    meaning_vi: str
    taboo_words: List[str]       # exactly 5
    clue: str
    difficulty_level: str        # "Easy"|"Medium"|"Hard"
    sample_acceptable_phrases: List[str]
    sample_forbidden_phrases: List[str]

# ===================== IMPORTANT: Schema → Gemini Dict Converter =====================
TYPE_MAP = {
    "string": "STRING",
    "integer": "INTEGER",
    "number": "NUMBER",
    "boolean": "BOOLEAN",
    "array": "ARRAY",
    "object": "OBJECT",
}

def model_to_gemini_schema(model_class) -> dict:
    """Convert Pydantic BaseModel -> Gemini response_schema dict."""
    schema = model_class.model_json_schema()
    defs = schema.get("$defs", {})

    def convert(props):
        out = {}
        for name, prop in props.items():
            # Resolve $ref
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

# ===================== REGISTRY =====================
REGISTRY = {
    "fill_blank": FillBlankSchema,
    "cloze": ClozeSchema,
    "translation": TranslationSchema,
    "unscramble": UnscrambleSchema,
    "matching": WordMatchingSchema,
    "story": StorySchema,
    "sentence_transform": SentenceTransformSchema,
    "taboo": TabooSchema,
}

def get_schema(gamemode: str) -> Optional[dict]:
    cls = REGISTRY.get(gamemode)
    return model_to_gemini_schema(cls) if cls else None

def get_pydantic_model(gamemode: str):
    return REGISTRY.get(gamemode)

def list_gamemodes() -> list[str]:
    return list(REGISTRY.keys())
