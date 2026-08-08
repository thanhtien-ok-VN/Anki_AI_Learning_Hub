import json
import os
from core.logger import flow

GLOBAL_SYSTEM_INSTRUCTION = """You are an expert language teacher and curriculum designer.
CRITICAL RULES:
1. You MUST output ONLY valid, raw JSON.
2. DO NOT wrap the JSON in markdown code blocks (no ```json ... ```).
3. DO NOT output any text before or after the JSON.
4. All explanations must be deeply pedagogical, helping learners understand the "WHY" behind correct and incorrect answers."""


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
        # Language-specific prompt takes priority over common/en fallback
        filepath = os.path.join(self.prompts_dir, language, filename)
        prompt = self._load(filepath)
        if not prompt:
            prompt = self._load(os.path.join(self.prompts_dir, "common", filename))
        if not prompt:
            prompt = self._load(os.path.join(self.prompts_dir, "en", filename))
        if not prompt:
            prompt = self._default_prompt(gamemode)

        global_path = os.path.join(self.prompts_dir, "common", "global_system_instruction.txt")
        global_instruction = self._load(global_path) or GLOBAL_SYSTEM_INSTRUCTION

        level_instruction = {
            "beginner": "CEFR A1: Absolute beginner. Use ONLY the most basic vocabulary (colors, numbers, family, simple daily objects). Shortest possible sentences. Present simple tense only.",
            "elementary": "CEFR A2: Elementary. Use common everyday phrases, past/present tense. Simple sentence structures with basic connectors (and, but, because).",
            "intermediate": "CEFR B1: Intermediate. Use moderate vocabulary, modals (can, should, must), conditionals (if). Standard sentence structures.",
            "upper_intermediate": "CEFR B2: Upper-intermediate. Use sophisticated vocabulary, passive voice, relative clauses. Complex sentences with multiple clauses.",
            "advanced": "CEFR C1-C2: Advanced. Use nuanced vocabulary, idioms, collocations. Complex grammatical structures including inversion, cleft sentences, mixed conditionals.",
        }.get(level, "CEFR B1: Intermediate. Use moderate vocabulary and standard structures.")

        kwargs.setdefault("gamemode", gamemode)
        kwargs.setdefault("language", language)
        kwargs.setdefault("level", level)
        kwargs.setdefault("topic", "daily_life")
        kwargs.setdefault("count", 5)
        kwargs["level_instruction"] = level_instruction
        
        from core.languages import get_language_name
        learn_lang_name = get_language_name(language)
        kwargs["learn_lang"] = learn_lang_name
        if "ui_lang" in kwargs:
            kwargs["ui_lang"] = get_language_name(kwargs["ui_lang"])
        else:
            kwargs["ui_lang"] = "English"
            
        if "feedback_lang" in kwargs:
            kwargs["feedback_lang"] = get_language_name(kwargs["feedback_lang"])

        flow(
            phase="PROMPT",
            message=f"Prompt rendered for gamemode={gamemode}, learn_lang={learn_lang_name}, ui_lang={kwargs.get('ui_lang')}"
        )

        rendered = global_instruction + "\n\n" + prompt
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
                "Generate {count} fill-in-the-blank sentences in {learn_lang}.\n"
                "Level: {level_instruction}\n"
                "Topic: {topic}\n"
                "Each sentence has ONE blank (_____). Provide exactly 4 options (1 correct + 3 distractors).\n"
                "Output valid JSON matching the provided schema."
            ),
            "cloze": (
                "Write a coherent paragraph in {learn_lang} under 400 words.\n"
                "Level: {level_instruction}\n"
                "Topic: {topic}\n"
                "Remove {num_blanks} words: {blank_words}.\n"
                "Output valid JSON matching the provided schema."
            ),
            "translation": (
                "Generate {count} sentences in the source language with their translations.\n"
                "Source language: {source_lang}, Target language: {target_lang}\n"
                "Level: {level_instruction}\n"
                "Topic: {topic}\n"
                "Output valid JSON matching the provided schema."
            ),
            "unscramble": (
                "Generate exactly {count} grammatically correct sentences in {learn_lang}.\n"
                "Level: {level_instruction}\n"
                "Topic: {topic}\n"
                "Output valid JSON matching the provided schema."
            ),
            "story": (
                "Write a reading passage in {learn_lang} under 400 words.\n"
                "Level: {level_instruction}\n"
                "Generate comprehension questions with balanced 4 options.\n"
                "Output valid JSON matching the provided schema."
            ),
            "sentence_transform": (
                "Generate {count} sentence transformation exercises in {learn_lang}.\n"
                "Focus: {focus}\n"
                "Output valid JSON matching the provided schema."
            ),
            "taboo": (
                "Generate {count} Taboo rounds in {learn_lang}.\n"
                "Topic: {topic}\n"
                "Output valid JSON matching the provided schema."
            ),
        }
        return prompts.get(
            gamemode,
            "Generate content in {learn_lang}. Support fields must be in {ui_lang}. Level: {level_instruction}. Output valid JSON matching the schema.",
        )
