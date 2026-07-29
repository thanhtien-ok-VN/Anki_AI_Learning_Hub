GENERIC_GRADER_PROMPT = """You are a language teacher grading a student's answer.

Learning language: {learn_lang}
Game mode: {gamemode}
Student's level: {level}
Question: {question}
Expected answer: {expected}
Student's answer: {user_answer}

Grade the answer considering the student's level. Provide:
1. Whether it's correct (true/false)
2. A score from 0.0 to 1.0
3. Brief explanation of errors (if wrong) or confirmation (if correct)
4. A helpful suggestion for improvement

Respond in JSON format:
{{
    "correct": true/false,
    "score": 0.0-1.0,
    "explanation": "string",
    "suggestion": "string"
}}
"""

FILL_BLANK_GRADER = """You are a language teacher grading a fill-in-the-blank exercise.

Learning language: {learn_lang}
Student's level: {level}
Target word: {target_word}
Meaning: {meaning_vi}
Question: {question}
Expected answer: {expected}
Student's answer: {user_answer}

Explain why the correct answer is right or wrong. Include:
- Semantic meaning of the correct word in context
- Grammar rule involved
- Why the other options are incorrect (consider option types: correct/antonym/grammar_error/semantic_close)

Respond in JSON:
{{
    "correct": true/false,
    "score": 0.0-1.0,
    "semantic": "string",
    "grammar": "string",
    "vocabulary_relation": "string"
}}
"""

TRANSLATION_GRADER = """You are a language teacher grading a translation.

Source ({source_lang}): {source_sentence}
Expected translation ({target_lang}): {reference_translation}
Student's translation: {user_target}

Common mistakes to check: {common_mistakes}

Grade the translation. If wrong, identify specific errors (word choice, grammar, missing parts).
If different but acceptable, explain why both work.
Consider the student's level: {level}

Respond in JSON:
{{
    "correct": true/false,
    "score": 0.0-1.0,
    "errors": ["error1", "error2"],
    "explanation": "string",
    "suggestion": "string"
}}
"""

UNSCRAMBLE_GRADER = """You are a language teacher grading a sentence unscramble exercise.

Correct sentence: {correct_sentence}
Student's sentence: {user_sentence}

If wrong, identify which words are out of order and explain the correct syntax/grammar rule.
Consider level: {level}

Respond in JSON:
{{
    "correct": true/false,
    "score": 0.0-1.0,
    "wrong_words": ["word1", "word2"],
    "grammar_rule": "string",
    "explanation": "string"
}}
"""

TRANSFORM_GRADER = """You are a language teacher grading a sentence transformation.

Instruction/Prompt: {prompt}
Original: {original}
Expected answer: {expected_answer}
Normalized answer: {normalized_answer}
Forbidden words: {forbidden_words}
Acceptable variations: {acceptable_variations}
Student's answer: {user_answer}

If wrong, explain the grammar rule being tested and how to fix it.
Consider level: {level}

Respond in JSON:
{{
    "correct": true/false,
    "score": 0.0-1.0,
    "grammar_rule": "string",
    "explanation": "string",
    "suggestion": "string"
}}
"""

TABOO_GRADER = """You are judging a Taboo word-guessing game.

Target word: {target_word}
Taboo words: {taboo_words}
Sample acceptable phrases: {sample_acceptable_phrases}
Sample forbidden phrases: {sample_forbidden_phrases}
Student's guess: {user_input}

Determine if the guess matches or is semantically close enough.
Consider synonyms, common learner associations.

Respond in JSON:
{{
    "correct": true/false,
    "score": 0.0-1.0,
    "explanation": "string",
    "suggested_words": ["word1", "word2"]
}}
"""


GRADER_PROMPTS = {
    "fill_blank": FILL_BLANK_GRADER,
    "translation": TRANSLATION_GRADER,
    "unscramble": UNSCRAMBLE_GRADER,
    "sentence_transform": TRANSFORM_GRADER,
    "taboo": TABOO_GRADER,
}


def get_grader_prompt(gamemode: str, **kwargs) -> str:
    if gamemode in GRADER_PROMPTS:
        return GRADER_PROMPTS[gamemode].format(**kwargs)
    return GENERIC_GRADER_PROMPT.format(**kwargs)
