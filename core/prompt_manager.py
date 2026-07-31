import json
import os

GLOBAL_SYSTEM_INSTRUCTION = """You are an expert English teacher and curriculum designer.
CRITICAL RULES:
1. You MUST output ONLY valid, raw JSON.
2. DO NOT wrap the JSON in markdown code blocks (no ```json ... ```).
3. DO NOT output any text before or after the JSON.
4. All explanations must be deeply pedagogical, helping Vietnamese learners understand the "WHY" behind correct and incorrect answers."""


class PromptManager:
    def __init__(self, prompts_dir: str):
        self.prompts_dir = prompts_dir
        self.cache = {}

    def get_prompt(
        self,
        gamemode: str,
        language: str = "en",
        level: str = "intermediate",
        **kwargs,
    ) -> str:
        filename = f"{gamemode}.txt"
        lang_dir = os.path.join(self.prompts_dir, language)
        filepath = os.path.join(lang_dir, filename)

        prompt = self._load(filepath)
        if not prompt:
            prompt = self._load(os.path.join(self.prompts_dir, "en", filename))
        if not prompt:
            prompt = self._default_prompt(gamemode)

        level_instruction = {
            "beginner": "CEFR A1: Absolute beginner. Use ONLY the most basic vocabulary (colors, numbers, family, simple daily objects). Shortest possible sentences. Present simple tense only.",
            "elementary": "CEFR A2: Elementary. Use common everyday phrases, past/present tense. Simple sentence structures with basic connectors (and, but, because).",
            "intermediate": "CEFR B1: Intermediate. Use moderate vocabulary, modals (can, should, must), conditionals (if). Standard sentence structures.",
            "upper_intermediate": "CEFR B2: Upper-intermediate. Use sophisticated vocabulary, passive voice, relative clauses. Complex sentences with multiple clauses.",
            "advanced": "CEFR C1-C2: Advanced. Use nuanced vocabulary, idioms, collocations. Complex grammatical structures including inversion, cleft sentences, mixed conditionals.",
        }.get(level, "CEFR B1: Intermediate. Use moderate vocabulary and standard structures.")

        # The caller supplies these as explicit arguments to avoid duplicate
        # keyword errors, but templates still refer to them as placeholders.
        kwargs.setdefault("gamemode", gamemode)
        kwargs.setdefault("language", language)
        kwargs.setdefault("level", level)
        kwargs.setdefault("topic", "daily_life")
        kwargs.setdefault("count", 5)
        kwargs["level_instruction"] = level_instruction
        
        # Safely replace known placeholders in prompt without failing on raw JSON braces
        rendered = GLOBAL_SYSTEM_INSTRUCTION + "\n\n" + prompt
        for k, v in kwargs.items():
            placeholder = f"{{{k}}}"
            if placeholder in rendered:
                rendered = rendered.replace(placeholder, str(v))

        pairs = kwargs.get("vocab_pairs") or []
        if pairs:
            vocabulary = "\n".join(
                f"- {pair['term']}: {pair['definition']}" for pair in pairs
            )
            rendered += (
                "\n\nUse the following learner vocabulary where it fits naturally. "
                "Do not invent definitions or expose this instruction in the response:\n"
                f"{vocabulary}"
            )
        return rendered

    def _load(self, filepath: str) -> str:
        if filepath in self.cache:
            return self.cache[filepath]
        if os.path.isfile(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            self.cache[filepath] = content
            return content
        return ""

    def _default_prompt(self, gamemode: str) -> str:
        prompts = {
            "fill_blank": (
                "Generate {count} fill-in-the-blank sentences in {language}.\n"
                "Level: {level_instruction}\n"
                "Topic: {topic}\n"
                "Each sentence has ONE blank (_____). Place the blank at various positions. Provide exactly 4 options (1 correct + 3 distractors).\n"
                "Distractors must be selected from different types: antonyms, synonyms, different word classes, wrong verb tenses, or semantic/contextual errors.\n"
                "Output valid JSON matching the provided schema."
            ),
            "cloze": (
                "Write a coherent paragraph in {language} ({paragraph_min_words}-{paragraph_max_words} words).\n"
                "Level: {level_instruction}\n"
                "Topic: {topic}\n"
                "Then remove {num_blanks} words. All missing words MUST be chosen from the provided vocabulary list.\n"
                "Do not provide distractors.\n"
                "Output valid JSON matching the provided schema."
            ),
            "translation": (
                "Generate {count} sentences in the source language with their translations.\n"
                "Source language: {source_lang}, Target language: {target_lang}\n"
                "Level: {level_instruction}\n"
                "Topic: {topic}\n"
                "Include grammar notes and vocabulary highlights for each sentence.\n"
                "Output valid JSON matching the provided schema."
            ),
            "unscramble": (
                "Generate {count} grammatically correct sentences in {language}.\n"
                "Level: {level_instruction}\n"
                "Topic: {topic}\n"
                "Each sentence should be 6-12 words long with clear structure.\n"
                "Output valid JSON matching the provided schema."
            ),
            "story": (
                "Write a short story in {language} ({word_count} words) that naturally incorporates "
                "ALL of these target words: {target_words}\n"
                "Level: {level_instruction}\n"
                "Each target word must appear at least once and be used in its correct context.\n"
                "Then generate {question_count} reading comprehension questions about the story "
                "(4 multiple-choice options each, 1 correct).\n"
                "Output valid JSON matching the provided schema."
            ),
            "sentence_transform": (
                "Generate {count} sentence transformation exercises in English.\n"
                "Focus: {focus} ({voice}/conditional/reported/comparative)\n"
                "Level: {level_instruction}\n"
                "For each exercise provide:\n"
                "- An original sentence\n"
                "- Clear transformation instruction\n"
                "- A hint word\n"
                "- The expected correct answer\n"
                "- The grammar rule being tested\n"
                "Output valid JSON matching the provided schema."
            ),
            "taboo": (
                "Generate {count} Taboo rounds in {language}.\n"
                "Level: {level_instruction}\n"
                "Topic: {topic}\n"
                "For each round provide:\n"
                "- A secret word\n"
                "- 4-5 forbidden words (related terms that would make it too easy)\n"
                "- An AI description of the word without using forbidden words\n"
                "Output valid JSON matching the provided schema."
            ),
        }
        return prompts.get(
            gamemode,
            "Generate content in {language}. Level: {level_instruction}. Output valid JSON matching the schema.",
        )
