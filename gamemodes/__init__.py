from .manifest import GameControlField, GameModeManifest
from .registry import registry, GameModeRegistry
from .fill_blank import FillBlankMode
from .cloze import ClozeMode
from .translation import TranslationMode
from .word_unscramble import WordUnscrambleMode
from .word_matching import WordMatchingMode
from .story_generator import StoryGeneratorMode
from .sentence_transform import SentenceTransformMode
from .taboo import TabooMode

# Register all modes into dynamic registry
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

for _mode_id, _mode_cls in REGISTRY.items():
    registry.register(_mode_id, _mode_cls)

def get_gamemode(name: str):
    return registry.get(name)

def list_gamemodes() -> list[str]:
    return registry.list_mode_ids()

def list_manifests() -> list[dict]:
    return registry.list_manifests()

def get_mode_limits(name: str):
    return registry.get_limits(name)

__all__ = [
    "REGISTRY",
    "registry",
    "GameModeRegistry",
    "GameModeManifest",
    "GameControlField",
    "get_gamemode",
    "list_gamemodes",
    "list_manifests",
    "get_mode_limits",
    "FillBlankMode",
    "ClozeMode",
    "TranslationMode",
    "WordUnscrambleMode",
    "WordMatchingMode",
    "StoryGeneratorMode",
    "SentenceTransformMode",
    "TabooMode",
]

