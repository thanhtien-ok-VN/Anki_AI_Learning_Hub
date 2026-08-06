# AI Learning Hub — Anki Add-on

> An AI-powered vocabulary learning system for Anki with 8 interactive game modes, powered by Gemini API.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Anki](https://img.shields.io/badge/Anki-2.1.50+-green.svg)](https://apps.ankiweb.net)
[![Gemini](https://img.shields.io/badge/AI-Gemini%20API-orange.svg)](https://ai.google.dev)

## Overview

AI Learning Hub transforms your existing Anki vocabulary decks into interactive AI-powered exercises. Instead of passive flashcard review, practice with 8 distinct game modes that generate personalized exercises from your own vocabulary.

## Features

| Game Mode | Description |
|---|---|
| **Fill in the Blank** | AI generates fill-in-the-blank sentences using your vocabulary |
| **Cloze Paragraph** | Practice words in a coherent paragraph context |
| **Translation** | Translate sentences with AI grading and detailed feedback |
| **Word Unscramble** | Reconstruct scrambled sentences by dragging/clicking words |
| **Word Matching** | Match vocabulary words to their definitions in a 5-slot board |
| **Story Generator** | Read an AI-generated story and answer comprehension questions |
| **Sentence Transform** | Rewrite sentences using different grammatical structures |
| **Taboo** | Describe a word without using forbidden related words |

## Installation

1. **Download** this repository as a ZIP or clone it:
   ```bash
   git clone https://github.com/your-username/AI_Learning_Hub.git
   ```

2. **Copy** the folder to your Anki add-ons directory:
   - **Windows**: `%APPDATA%\Anki2\addons21\AI_Learning_Hub\`
   - **macOS**: `~/Library/Application Support/Anki2/addons21/AI_Learning_Hub/`
   - **Linux**: `~/.local/share/Anki2/addons21/AI_Learning_Hub/`

3. **Restart Anki**. The add-on will appear in the Tools menu.

4. **Configure**: Tools → AI Learning Hub → Settings
   - Enter your [Gemini API Key](https://aistudio.google.com/apikey)
   - Select your learning language and UI language
   - Choose the Anki deck to practice from

## Requirements

- Anki 2.1.50 or newer
- Python 3.9+ (bundled with Anki)
- A free [Gemini API Key](https://aistudio.google.com/apikey)
- No Node.js or npm required — pure Python + vanilla JS

## Project Architecture

For a detailed sitemap of all 16 component groups, refer to [docs/ARCHITECTURE.md](file:///D:/GithubDesktopClone/Anki_AI_Learning_Hub/docs/ARCHITECTURE.md).

```text
AI_Learning_Hub/
├── __init__.py           # [Group 1] Anki add-on entry point & menu setup
├── ui/                   # [Group 1, 2, 13] Qt Presentation Layer & Diagnostics
│   ├── main_window.py   # Anki Qt Tab embedding & async task manager
│   ├── settings_dialog.py # Settings Dialog (Keys, Model, Language, Logs)
│   └── log_viewer.py    # Log Viewer & Diagnostic Bug Report GUI
├── core/                 # [Group 1-6, 8, 10, 11, 13, 14] Domain Core & Bridge
│   ├── engine.py         # AIEngine: JS Bridge Router (~20 Actions, 4-Phase Flow)
│   ├── settings.py       # SettingsManager: persistent JSON storage
│   ├── timer.py          # SessionTimer: elapsed practice time tracking
│   ├── api_client.py     # Backward-compatible alias for llm/gemini.py
│   ├── prompt_manager.py # Prompt loading & placeholder substitution
│   ├── schema_registry.py# Pydantic schemas & Gemini JSON spec generators
│   └── logger.py         # Thread-Safe Ring Buffer & Flow JSONL Logger
├── llm/                  # [Group 7] Provider Abstraction Layer (DIP)
│   ├── base.py           # BaseLLMProvider abstract interface
│   └── gemini.py         # GeminiProvider (Rotation, backoff, waterfalls)
├── gamemodes/            # [Group 9] 8 Interactive Gamemode Handlers
├── prompts/              # [Group 3] System prompt templates (en, zh, common)
├── lang/                 # [Group 3] i18n JSON Catalogs (en.json, vi.json)
└── web/                  # [Group 4, 12, 15] Web SPA Frontend (HTML, CSS, JS)
```
│       ├── utils.js      # i18n, shuffle, debounce, formatTime
│       └── app.js        # Main SPA (8 game renderers, routing, state)
├── lang/
│   ├── en.json           # English UI strings
│   ├── vi.json           # Vietnamese UI strings
│   └── languages.json    # Supported language registry
├── tests/                # Python unit tests (pytest)
└── docs/                 # Detailed documentation
```

For the full data-flow diagram and extension guide, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Supported Languages

**Learning languages**: English, Chinese (Simplified), Japanese, Korean, French, German, Spanish, Italian, Russian, Hindi

**UI languages**: English (en), Vietnamese (vi)

Adding a new language requires only a configuration entry in `core/languages.py` — no code changes.

## Development

This is a pure Python + vanilla JS project. No build step is needed for the web frontend.

```bash
# Run tests
python -m pytest tests/ -v

# Lint Python
python -m py_compile core/*.py gamemodes/*.py

# After editing, copy to Anki add-ons folder to test
robocopy . "%APPDATA%\Anki2\addons21\AI_Learning_Hub" /E /XD .git node_modules
```

## License

MIT License — see [LICENSE](LICENSE) for details.
