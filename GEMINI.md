# Gemini Agent Configuration & Guidelines

Please refer to [.agents/AGENTS.md](.agents/AGENTS.md) for full workspace rules, architecture maps, and skill triggers.

## Quick Reference
- **Core Architecture**: 3-Tier Anki Add-on (Vanilla JS SPA ↔ PyCmd Async Bridge ↔ Python Core Engine).
- **AI Engine**: 6-Tier Waterfall (`gemini-3.5-flash-lite`, `gemini-flash-lite-latest`, `gemini-3.5-flash`, `gemini-3.6-flash`, `gemini-3.1-flash-lite`, `gemini-3-flash-preview`).
- **Tests**: `python -B -m unittest discover -s tests -p "test_*.py" -v` (65/65 PASS required).
- **Packaging**: `python scripts/build_addon.py` -> `dist/AI_Learning_Hub.ankiaddon` and `.zip`.
- **Sync**: Copy to `%APPDATA%\Anki2\addons21\AI_Learning_Hub\`.
