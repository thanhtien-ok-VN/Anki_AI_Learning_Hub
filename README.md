# AI Learning Hub — Anki Add-on

> An AI-powered vocabulary learning system for Anki with 8 interactive game modes, powered by Google Gemini API.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Anki](https://img.shields.io/badge/Anki-2.1.50~25.05+-green.svg)](https://apps.ankiweb.net)
[![Gemini](https://img.shields.io/badge/AI-Google%20Gemini%20API-orange.svg)](https://ai.google.dev)
[![Tests](https://img.shields.io/badge/Tests-65%2F65%20PASS-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Overview

**AI Learning Hub** transforms your passive Anki flashcard review into an engaging, interactive learning experience. Utilizing cutting-edge Google Gemini AI, the add-on automatically generates context-rich exercises, provides 5-field granular error analysis, offers multi-tier hints, and supports full multilingual learning (English & Chinese target languages with English & Vietnamese UI).

---

## Key Features & 8 Game Modes

| Gamemode | Mode Type | Key Features & Description |
|---|---|---|
| **✏️ Fill in the Blank** | AI Online | Interactive Blank Pills, auto-masking target words in context sentences |
| **📖 Cloze Test** | AI Online | Contextual topic paragraphs with multiple missing blank positions (`[BLANK_1]`, `[BLANK_2]`) |
| **🌐 Sentence Translation** | AI Online | 0–10 score, 5-field granular error analysis (Name, Wrong, Reason, Suggestion, Rationale) |
| **🧩 Word Unscramble** | AI Online | Reconstruct scrambled word tiles into grammatically correct sentences |
| **📚 Story Generator** | AI Online | CEFR A1–C2 level reading passages with 4-choice comprehension questions |
| **🔄 Sentence Transformation** | AI Online | Rewrite sentences with 4-block feedback & common/advanced suggestions |
| **🚫 Taboo Word Guessing** | AI Online | Guess target words from AI clues without using forbidden (Taboo) words |
| **🔗 Word Matching** | **100% Offline** | Instant 5-slot matching board extracted from user's Anki deck (no API needed) |

### 💡 Pedagogical Multi-Tier Hint System
- **Level 1 (Grammar Rule):** Provides the underlying grammatical structure or rule.
- **Level 2 (First Letter & Meaning):** Reveals the first letter of the target word and its contextual meaning.
- **Level 3 (Full Solution):** Reveals the complete correct solution.
- **Tiered Score Penalty:** Automatically calculates tiered score deductions (L0: 100%, L1: 75%, L2: 50%, L3: 0%) to encourage active recall.

---

## Quickstart & Setup Guide

### 1. Installation
- **Option A (Via AnkiWeb Code):** In Anki Desktop, go to **Tools** ➔ **Add-ons** ➔ **Get Add-ons...** ➔ Enter Code ➔ Click **OK**.
- **Option B (Via File):** In Anki Desktop, go to **Tools** ➔ **Add-ons** ➔ **Install from file...** ➔ Select `AI_Learning_Hub.ankiaddon`.

### 2. Gemini API Key Configuration
1. Obtain a free API Key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Launch **Tools** ➔ **🚀 AI Learning Hub...** ➔ Click **⚙️ Settings** (top-right).
3. Paste your API Key starting with `AQ...` (one key per line for automatic failover/rotation).
4. Click **🧪 Test All Keys** to verify API connectivity.
5. Select your preferred **Learning Language** (e.g. `English`, `Chinese (Mandarin)`) and **UI Language** (`English`, `Vietnamese`).
6. Select your target **Anki Deck Source** to import vocabulary.

---

## Project Architecture & Directory Structure

For complete component sitemaps and domain matrix, refer to [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```text
Anki_AI_Learning_Hub/
├── __init__.py           # Anki add-on entry point & menu setup
├── manifest.json         # AnkiWeb strict add-on package specification
├── config.json           # Native Anki configuration schema
├── config.md             # Native Anki in-app documentation guide
├── core/                 # Engine, Settings, Prompts, Schema Registry, i18n, Logger
├── gamemodes/            # 8 Interactive Gamemode implementations
├── llm/                  # Gemini provider abstraction & waterfall rotation
├── lang/                 # Multilingual UI catalogs (en.json, vi.json, languages.json)
├── prompts/              # System prompt templates (en/, zh/, common/)
├── ui/                   # Qt Presentation Layer & Diagnostic Log Viewer
├── web/                  # Web SPA Frontend (HTML5, CSS3, Vanilla JS)
├── scripts/              # Automated packaging script (build_addon.py)
├── tests/                # Standalone unit test suite (65 unit tests)
├── docs/                 # System architecture, guide & AnkiWeb descriptions
└── dist/                 # Release packages (AI_Learning_Hub.ankiaddon & .zip)
```

---

## Development & Testing

This project requires **Python 3.9+** and standard Anki Desktop. No Node.js build step is required for the web frontend.

```bash
# 1. Run full unit test suite (65 tests)
python -m unittest discover -s tests -p "test_*.py" -v

# 2. Rebuild distribution packages (.ankiaddon and .zip)
python scripts/build_addon.py
```

---

## Documentation Links

- [System Architecture (docs/ARCHITECTURE.md)](docs/ARCHITECTURE.md)
- [AnkiWeb Description (English)](docs/ANKIWEB_DESCRIPTION_EN.md)
- [AnkiWeb Description (Vietnamese)](docs/ANKIWEB_DESCRIPTION.md)

---

## License

MIT License — see [LICENSE](LICENSE) for details. Copyright (c) 2026 Cornok.
