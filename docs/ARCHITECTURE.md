# AI Learning Hub — Complete System Architecture & Component Map

Document version: 2.0 | Last updated: 2026-08-07

This document provides a comprehensive architectural sitemap and component responsibilities matrix for the `Anki_AI_Learning_Hub` add-on codebase.

---

## 🗺️ COMPONENT MAP (16 SYSTEM GROUPS)

```
Anki_AI_Learning_Hub/
├── __init__.py                  # [Group 1] Anki Integration & Lifecycle Entry Point
├── ui/                          # [Group 1, 2, 13] Presentation Layer
│   ├── main_window.py           # Anki Tab Embedding & Async Worker Manager
│   ├── settings_dialog.py       # Qt Config Dialog & Key Manager
│   └── log_viewer.py            # System Log & Diagnostics GUI
├── core/                        # [Group 1, 2, 3, 5, 6, 8, 10, 11, 13, 14] Core Domain & Bridge Services
│   ├── engine.py                # AIEngine Facade & JS Bridge Router (~20 Actions)
│   ├── settings.py              # SettingsManager & Persistent JSON Storage
│   ├── timer.py                 # SessionTimer (Elapsed Time Signals)
│   ├── api_client.py            # Backward-compatible LLM Client Alias
│   ├── prompt_manager.py        # Template Prompt Loader & Placeholder Resolution
│   ├── schema_registry.py       # Pydantic Schemas & Gemini JSON Spec Generators
│   ├── content_validation.py    # AI Exercise Structure Validation Rules
│   ├── deck_source.py           # Anki Deck Vocabulary Reader & Weak-Word Sampler
│   ├── ai_grader.py             # Pedagogical AI Feedback Prompts
│   ├── languages.py             # Supported Language Definitions
│   ├── i18n.py                  # Catalog Loader (lang/*.json)
│   ├── language_normalizer.py    # Legacy Schema Field Harmonizer
│   ├── error_suppressor.py      # Anki Timeout Exception Interceptor
│   ├── task_results.py          # Future Task Result Resolver
│   └── logger.py                # Structured Flow JSONL Logger & Memory Ring Buffer
├── llm/                         # [Group 7] AI / LLM Provider Layer (DIP)
│   ├── base.py                  # BaseLLMProvider (Abstract Base Class)
│   └── gemini.py                # GeminiProvider (Rotation, Backoff, Waterfalls)
├── gamemodes/                   # [Group 9, 10, 11] Gamemode Domain Layer (8 Modes)
│   ├── base.py                  # GameModeBase (Anki Card Generator)
│   ├── fill_blank.py            # Fill-in-the-Blank Mode
│   ├── cloze.py                 # Contextual Cloze Mode
│   ├── translation.py           # Translation Practice Mode
│   ├── word_unscramble.py       # Sentence Order Mode
│   ├── word_matching.py         # Term-Definition Matcher (Offline)
│   ├── story_generator.py       # Reading Comprehension Story Mode
│   ├── sentence_transform.py    # Grammar Transformation Mode
│   └── taboo.py                 # Taboo Word Guessing Game Mode
├── prompts/                     # [Group 3] System Prompt Templates
│   ├── common/                  # Shared Directives
│   ├── en/                      # English Learning Templates
│   └── zh/                      # Chinese Learning Templates
├── lang/                        # [Group 3] i18n Catalogs
│   ├── en.json                  # English UI String Catalog
│   ├── vi.json                  # Vietnamese UI String Catalog
│   └── languages.json           # 10 Supported Learning Languages Registry
└── web/                         # [Group 4, 12, 15] Web SPA Frontend
    ├── index.html               # SPA Container
    ├── css/style.css            # Responsive Glassmorphism Styling
    └── js/
        ├── app.js               # Route Manager & Renderer
        ├── bridge.js            # PyCmd Async RPC Layer
        └── utils.js             # Front-end Helper Functions
```

---

## 📑 DETAILED COMPONENT GROUPS MATRIX

### GROUP 1. Anki Integration & Lifecycle Entry Point
- [`__init__.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/__init__.py): Registers `open_hub()`, `open_settings()`, `init_addon()`, Anki menu entries, and Anki Browser context menu hooks.
- [`ui/main_window.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/ui/main_window.py): `AIHubView` embeds WebView as a native Anki Qt Tab (`embed()`, `focus()`, `is_closed()`).
- [`core/error_suppressor.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/error_suppressor.py): Suppresses known transient Anki Qt timeout exceptions.
- [`core/task_results.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/task_results.py): Unwraps async background task futures across Anki versions.

### GROUP 2. Settings & Configuration Management
- [`core/settings.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/settings.py): `SettingsManager` loads and saves `user_files/settings.json`. Handles dynamic API key retrieval, active filtering, and security masking.
- [`ui/settings_dialog.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/ui/settings_dialog.py): Qt configuration GUI dialog for keys, models, temperature, language, and diagnostics.
- [`core/engine.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/engine.py): Bridge handlers: `_handle_save_settings`, `_handle_get_settings`, `_handle_test_key`, etc.
- [`core/constants.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/constants.py): Model chains, waterfall mappings, rate limit backoff constants.

### GROUP 3. Internationalization (i18n) & Prompt Loading
- [`core/languages.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/languages.py): Registry of 10 supported learning languages.
- [`core/i18n.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/i18n.py): Catalog strings loader with caching (`load_strings()`, `t()`).
- [`core/language_normalizer.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/language_normalizer.py): Harmonizes legacy AI schema fields (`meaning_vi` -> `meaning`).
- [`web/js/utils.js`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/web/js/utils.js): Front-end `Utils.i18n` and DOM translation interpolation.

### GROUP 4. Single Page Application (SPA Frontend)
- [`web/index.html`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/web/index.html): Clean HTML5 shell.
- [`web/css/style.css`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/web/css/style.css): Modern glassmorphism dark/light visual theme.
- [`web/js/app.js`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/web/js/app.js): Route controller (`nav()`, `home()`, `game()`, `render()`), timer lifecycle manager (`disposeCurrentGame()`).
- [`web/js/bridge.js`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/web/js/bridge.js): Async PyCmd RPC bridge sending JSON envelopes.

### GROUP 5. Bridge Message Routing
- [`core/engine.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/engine.py): `handle_js_message()` dispatches ~20 RPC actions. Handles `log_event`, `cancel_gen`, `close_hub`.
- [`ui/main_window.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/ui/main_window.py): Thread worker routing via `mw.taskman.run_in_background()`.

### GROUP 6. Question Generation Pipeline (Core Engine)
- [`core/engine.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/engine.py): `_handle_generate()` orchestrates the 4-phase generation pipeline (`CONNECT` -> `SYSTEM` -> `AI` -> `RENDER`).
- [`core/prompt_manager.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/prompt_manager.py): Builds structured instructions from `prompts/{lang}/{gamemode}.txt`.
- [`core/schema_registry.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/schema_registry.py): Pydantic schemas and Gemini JSON schema generators.
- [`core/content_validation.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/content_validation.py): Enforces exercise option counts and answer consistency.

### GROUP 7. AI / LLM Provider Layer (Gemini REST API)
- [`llm/base.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/llm/base.py): Abstract base class `BaseLLMProvider`.
- [`llm/gemini.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/llm/gemini.py): `GeminiProvider` implementing exponential backoff, key rotation, model waterfall fallback, and user cancellation checks.

### GROUP 8. Anki Deck & Vocabulary Integration
- [`core/deck_source.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/deck_source.py): Reads user's Anki collection, extracts target note fields, and samples vocabulary (prioritizing weak words).

### GROUP 9. 8 Interactive Gamemodes
1. **Fill in the Blank**: `gamemodes/fill_blank.py`
2. **Cloze Passage**: `gamemodes/cloze.py`
3. **Translation Practice**: `gamemodes/translation.py`
4. **Word Unscramble**: `gamemodes/word_unscramble.py`
5. **Word Matching**: `gamemodes/word_matching.py` (Offline local generation supported)
6. **Story Generator**: `gamemodes/story_generator.py`
7. **Sentence Transform**: `gamemodes/sentence_transform.py`
8. **Taboo Word Game**: `gamemodes/taboo.py`

### GROUP 10. Pedagogical AI Grading
- [`core/ai_grader.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/ai_grader.py): `GRADER_PROMPTS` generating detailed grammatical, semantic, and error feedback in user's UI language.

### GROUP 11. Anki Flashcard Export
- [`gamemodes/base.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/gamemodes/base.py): `save_to_anki()` creates Anki checkpoint for Undo, checks duplicate notes, and inserts cards directly into collection.

### GROUP 12. History & Performance Analytics
- [`web/js/app.js`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/web/js/app.js): Session storage history management and Matching game accuracy statistics.

### GROUP 13. System Observability & Logging
- [`core/logger.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/logger.py): Thread-safe in-memory ring buffer (`collections.deque`), structured JSONL flow logger (`ai_hub_flow.jsonl`), and `FlowTimer`.
- [`ui/log_viewer.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/ui/log_viewer.py): LogViewerDialog with monospace log viewer, real-time QLineEdit keyword search, multi-filter algorithm, log counter (`Showing X of Y logs`), 1-click Diagnostic Bug Report generation, and multi-tier Anki version detection.

### GROUP 14. Session & Timer Management
- [`core/timer.py`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/core/timer.py): `SessionTimer` tracking total practice time and emitting Qt tick signals.

### GROUP 15. SPA State & Navigation
- [`web/js/app.js`](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/web/js/app.js): Route state manager, preferences persistence, request abort controller.

### GROUP 16. Automated Test Suite
- `tests/test_logger.py`: Main log tests.
- `tests/test_flow_logger.py`: Thread-safety ring buffer and masking security unit tests.
- `tests/test_api_client.py`: Gemini client error handling tests.
- `tests/test_languages.py`: Language registry tests.
