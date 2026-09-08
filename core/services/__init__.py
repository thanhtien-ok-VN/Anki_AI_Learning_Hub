"""Service Layer Package for Anki AI Learning Hub.

Decomposes the core engine god object into dedicated domain services:
- PrefsService: Settings, keys, and preferences persistence.
- I18nService: Internationalization, locale catalogs, and language switches.
- AnkiService: Anki Desktop collection access, sampling, and card saving.
- GenerationService: LLM orchestration and game generation workflow.
- GradingService: Polymorphic answer checking, AI grading, and hint management.
"""
from .prefs_service import PrefsService
from .i18n_service import I18nService
from .anki_service import AnkiService
from .generation_service import GenerationService
from .grading_service import GradingService

__all__ = [
    "PrefsService",
    "I18nService",
    "AnkiService",
    "GenerationService",
    "GradingService",
]
