# AI Learning Hub Configuration Guide

Welcome to **AI Learning Hub for Anki**!

## How to Configure

1. **Gemini API Keys**:
   - Obtain your free Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey).
   - Enter your key in `api_key1` (e.g., `"AQ..."`). You can add up to 10 keys for automatic rotation and failover.
   - Alternatively, launch **Tools -> 🚀 AI Learning Hub...** and click **⚙️ Settings** to manage keys interactively.

2. **UI & Learning Languages**:
   - `ui_lang`: Set to `"en"` for English UI, or `"vi"` for Vietnamese UI.
   - `learn_lang`: Set to `"en"` for English target content, or `"zh"` for Chinese target content.

3. **Model & Temperature**:
   - `model`: Set to `"auto"` (Recommended for automatic multi-tier waterfall failover) or select a specific model:
     - `gemini-3.5-flash-lite`: Fastest (0.93s, 100%) — Ideal for rapid batch exercise generation.
     - `gemini-flash-lite-latest`: Sub-second ultra-fast fallback (<1s).
     - `gemini-3.5-flash`: Deep academic phrasing and advanced vocabulary (B2–C2 / Story generator).
     - `gemini-3.6-flash`: High-level logical reasoning for pedagogical grading and error verification.
     - `gemini-3.1-flash-lite`: Tier-2 reliable fallback.
     - `gemini-3-flash-preview`: Tier-3 fast backup.
   - `temperature`: Default `0.7` for balanced creativity and accuracy.
