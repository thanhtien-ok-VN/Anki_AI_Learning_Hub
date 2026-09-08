# 🚀 AI Learning Hub for Anki
### 8 Gamified AI-Powered Language Learning Games (Powered by Google Gemini API)

**Anki AI Learning Hub** transforms your passive flashcard review into an engaging, interactive learning experience. Utilizing cutting-edge Google Gemini AI, the add-on automatically generates context-rich exercises, provides 5-field granular error analysis, offers 3-tier progressive hints, and supports full multilingual learning (English & Chinese target languages with English & Vietnamese UI).

---

## 🌟 Key Highlights & Architecture
- **⚡ Zero-Dependency Native Architecture:** Built with pure Python canonical OpenAPI schemas. Does NOT require external packages like `pydantic`. Runs 100% reliably out-of-the-box on any Anki Desktop installation!
- **🤖 Intelligent 6-Tier AI Model Engine (Auto Waterfall):** Extreme failover resilience against API rate limits and model outages with multi-key rotation and exponential backoff.
- **🌐 1-Click Header Language Switcher (VI / EN):** Seamlessly toggle between Vietnamese and English interfaces directly from the top bar with instant DOM updates.
- **🚀 Fast-Path SQLite Engine:** High-speed vocabulary sampling without loading thousands of notes into RAM. Smart deduplication and 30% quota priority for weak/lapse cards.
- **🎨 Modern Glassmorphism UI:** Responsive, polished interface designed specifically for Anki Desktop's dark and light themes.
- **📥 1-Click Save to Anki:** Export generated sentences and new vocabulary directly back into your Anki collection.

---

## 🤖 Intelligent 6-Tier AI Model Engine (Auto Waterfall)
The add-on features an advanced multi-tier model rotation system designed for maximum speed, zero quota lockouts, and deep academic accuracy:

- 🥇 **gemini-3.5-flash-lite** — Ultra-fast primary tier for instant generation and quiz compilation.
- 🥇 **gemini-flash-lite-latest** — Latest stable flash-lite fallback for high-throughput generation.
- 🥈 **gemini-3.5-flash** — Balanced reasoning tier for nuanced grammar and reading tasks.
- 🧠 **gemini-3.6-flash** — Deep academic reasoning for complex translations and story comprehension.
- 🛡️ **gemini-3.1-flash-lite** — High-reliability failover tier.
- 🛡️ **gemini-3-flash-preview** — Ultimate safety net ensuring zero downtime.

*Supports automatic key rotation: Add multiple free Gemini API keys (one per line) for seamless round-robin load balancing!*

---

## 📌 Step-by-Step Setup Guide

### 1️⃣ Step 1: Install the Add-on in Anki
1. Open Anki Desktop on your computer.
2. On the top menu bar, navigate to **Tools ➔ Add-ons** (or press `Ctrl + Shift + A` on Windows / `Cmd + Shift + A` on Mac).
3. **Install via AnkiWeb Code:** Click **Get Add-ons...** ➔ Paste the add-on code ➔ Click **OK**.
4. **Install via File (.ankiaddon):** Click **Install from file...** ➔ Select the `AI_Learning_Hub.ankiaddon` file.
5. Restart Anki to complete activation.

### 2️⃣ Step 2: Get a Free Gemini API Key (Google AI Studio)
The add-on connects directly to Google Gemini AI to generate dynamic exercises. You can obtain a **100% free API Key** in less than 1 minute:
1. Visit Google AI Studio: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account (Gmail).
3. Click the **Create API key** button.
4. Select or create a project ➔ Google will display your API Key string starting with `AIzaSy...`
5. Click **Copy** to copy your API key to clipboard.

🎥 **Video Tutorial: How to Get Free Gemini API Key:**  
[Watch Step-by-Step Video Guide](https://drive.google.com/file/d/1VznGDIv_XdqI7MnVydXh9ubTv7gOZF9O/view?usp=sharing)

### 3️⃣ Step 3: Add API Key & Run Connection Test
1. In Anki, navigate to **Tools ➔ 🚀 AI Learning Hub...** (or press `Ctrl + H` / `Cmd + H`).
2. Once the Hub opens, click the **⚙️ Settings** button at the top right corner.
3. In the **Gemini API Keys** box, paste your API Key (one key per line if you have multiple keys for automatic load balancing).
4. Click **🧪 Test All Keys**:
   - 🟢 **Active (OK):** Your key is valid and ready to use!
   - 🔴 **Error:** Double check if any characters were missed during copy.
5. Click **💾 Save Settings** to store your key securely.

### 4️⃣ Step 4: Configure Learning Language & Anki Deck Source
- **Learning Language:** Select your target language (e.g., English, Chinese (Mandarin)). Generated exercises will be 100% aligned with this language.
- **UI & Feedback Language:** Choose English or Vietnamese, or toggle on-the-fly with the **🌐 VI / EN** header button. Interface labels, hint titles, and AI error explanations adapt dynamically.
- **Model Selection:** Leave on `auto` for smart 6-tier waterfall failover, or pin a specific Gemini model of your choice.
- **Anki Deck Source:** Select any vocabulary deck and note type from your collection. The fast-path SQLite engine extracts word pairs directly from your cards with 30% quota priority for weak/lapse cards!

### 5️⃣ Step 5: Practice Across 8 AI Game Modes
Choose any of the 8 game modes from the dashboard to begin practicing:

1. ✏️ **Fill in the Blank (Điền từ vào chỗ trống):** Fill missing target words in context-rich sentences. Interactive blank pills allow smooth answer selection with 4 smart distractors and CEFR-tailored options.
2. 📖 **Cloze Test (Đoạn văn đục lỗ):** Read coherent topic paragraphs and complete multiple blank positions (`[BLANK_1]`, `[BLANK_2]`...) using an interactive Word Bank and inline dropdowns.
3. 🌐 **Sentence Translation (Dịch câu đa ngữ):** Translate sentences between your native language and target language. AI grades 0–10 and details 5 granular error fields (*Category, Incorrect segment, Reason, Suggestion, Rationale*).
4. 🧩 **Sentence Unscramble (Sắp xếp câu):** Reorder scrambled word tiles into grammatically correct sentences with click or drag-and-drop ordering.
5. 📚 **Story Generator (Kể chuyện & Đọc hiểu):** AI generates level-tailored reading passages (CEFR A1–C2) incorporating your deck vocabulary, followed by 4-choice reading comprehension questions.
6. 🔄 **Sentence Transformation (Viết lại câu):** Rewrite sentences according to grammar prompts (*Passive Voice, Conditionals, Reported Speech, Inversion*). Provides unified 4-block feedback with common & advanced suggestions.
7. 🚫 **Taboo Word Guessing (Đoán từ cấm):** Guess target words from AI descriptions without using 5 forbidden (Taboo) buzzwords.
8. 🔗 **Word Matching (Nối từ vựng - 100% Offline):** Match terms and definitions extracted from your Anki deck on a 5x5 board. Operates 100% offline without API calls, tracking streaks and fastest completion speeds!

---

## 💡 Multi-Tier Hint System & Exercise History
- **💡 Multi-Tier Progressive Hints:** 3-tier progressive hints:
  - **Level 1 (75% Score):** Grammar Rule, Part of Speech & Definition.
  - **Level 2 (50% Score):** First Letter, Word Length & Context Clue.
  - **Level 3 (0% Score):** Full Solution & In-depth Explanation.
  - *Automatically calculates tiered score penalties (100% ➔ 75% ➔ 50% ➔ 0%) to encourage active recall.*
- **📜 Exercise History & Analytics:** Review detailed past exercise attempts, scores, hint penalty badges, and AI explanations anytime.
- **📥 1-Click Save to Anki:** Easily export new vocabulary, context sentences, and explanations directly into your Anki decks as new cards.

---

<p align="center"><b>AI Learning Hub — Elevate Your Anki Learning Experience with Artificial Intelligence 🚀</b></p>
