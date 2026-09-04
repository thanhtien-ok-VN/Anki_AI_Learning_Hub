from .fill_blank import FillBlankMode
from .cloze import ClozeMode
from .translation import TranslationMode
from .word_unscramble import WordUnscrambleMode
from .word_matching import WordMatchingMode
from .story_generator import StoryGeneratorMode
from .sentence_transform import SentenceTransformMode
from .taboo import TabooMode

REGISTRY = {
    "fill_blank": FillBlankMode,
    "cloze": ClozeMode,
    "translation": TranslationMode,
    "unscramble": WordUnscrambleMode,
    "matching": WordMatchingMode,
    "story": StoryGeneratorMode,
    "sentence_transform": SentenceTransformMode,
    "taboo": TabooMode,
}

def get_gamemode(name: str):
    cls = REGISTRY.get(name)
    if cls:
        return cls
    return None

def list_gamemodes() -> list[str]:
    return list(REGISTRY.keys())
