# 📐 Phân tích Kiến trúc Hệ thống — AI Learning Hub

> **Phiên bản:** 0.1.0 · **Loại:** Anki Add-on · **Ngôn ngữ:** Python + Vanilla JS (SPA) · **AI Backend:** Gemini API

---

## 1. 🎯 Tổng quan Hệ thống (System Overview)

### Mục đích cốt lõi
**AI Learning Hub** là một add-on cho Anki (phần mềm học qua thẻ ghi nhớ), tích hợp 8 game mode tương tác sử dụng **Gemini API** để giúp người dùng học ngoại ngữ trực tiếp từ bộ thẻ có sẵn.

### Bài toán giải quyết
- Người học ngoại ngữ cần **thực hành chủ động** (không chỉ đọc thẻ thụ động) nhưng thiếu bạn đồng hành / giáo viên.
- Cần **cá nhân hóa** nội dung luyện tập dựa trên đúng vốn từ hiện có trong bộ thẻ Anki của người dùng.
- Cần **phản hồi tức thì**, chi tiết (giải thích ngữ pháp, từ vựng, gợi ý cải thiện).

### Phạm vi ứng dụng
| Thành phần | Mô tả |
|:--|:--|
| **8 Game Mode** | Fill-in-blank, Cloze Paragraph, Translation, Word Unscramble, Word Matching, Story Generator, Sentence Transformation, Taboo |
| **2 ngôn ngữ học** | English (EN), Chinese (ZH) — dễ mở rộng |
| **Giao diện** | Tiếng Việt hoặc Tiếng Anh (i18n) |
| **Nguồn từ vựng** | Đọc trực tiếp từ bộ thẻ (deck) Anki đang có |
| **AI Backend** | Google Gemini API (structured JSON output) |
| **Anki versions** | 24.0 – 24.10 (Anki 25+ tương thích qua `task_results.py`) |

---

## 2. 🏗️ Kiến trúc & Cách thức Hoạt động (Architecture & Mechanism)

### Luồng xử lý tổng thể (System Pipeline)

```
┌─────────────────────────────────────────────────────────────┐
│                    SPA Frontend (WebView)                    │
│  web/js/app.js — 8 game renderers + router                 │
│  web/js/bridge.js — Promise-based pycmd client              │
└──────────────────┬──────────────────────────────────────────┘
                   │ JSON message (action + data)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  Bridge Layer (Qt → Python)                  │
│  ui/main_window.py — AIHubView: QTabWidget + AnkiWebView   │
│    → _on_bridge_cmd() → phân loại action                   │
│    → BACKGROUND_ACTIONS: taskman.run_in_background()        │
│    → SYNC actions: engine.handle_js_message() trực tiếp    │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Engine Layer (core/engine.py)                   │
│  AIEngine.handle_js_message() — router 20+ actions          │
│  → dispatch đến handler: _handle_generate, _handle_ai_grade │
│    _handle_save_settings, _handle_save_to_anki, ...         │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Core Services Layer                             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ PromptManager │  │GeminiClient  │  │ SchemaRegistry   │   │
│  │ - templates   │→ │ - key rotate │  │ - 8 JSON schemas │   │
│  │ - level_inst  │  │ - throttling │  │ - validation     │   │
│  │ - vocab inject│  │ - retry × 3  │  └──────────────────┘   │
│  └──────────────┘  │ - fallback   │                          │
│                    └──────────────┘                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ContentValid.  │  │ AI Grader    │  │ DeckSource       │   │
│  │ - 4-options   │  │ - 6 prompts  │  │ - Anki col I/O   │   │
│  │ - dedup check │  │ - temp 0.3   │  │ - sampling      │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ContextManager │  │ i18n         │  │ Logger           │   │
│  │ - JSON file   │  │ - vi/en      │  │ - file auto-     │   │
│  │ - TTL 60min   │  │ - fallback   │  │   rotate 1MB     │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Đầu vào (Input) → Xử lý (Processing) → Đầu ra (Output)

| Giai đoạn | Mô tả |
|:--|:--|
| **Input** | User chọn game mode, level, topic, language, count; hệ thống tự động lấy vocab pairs từ Anki deck qua `sample_vocab_pairs()` |
| **Processing** | ① PromptManager: template + level instruction + vocab injection | ② GeminiClient: key rotation, throttling (1.5s), retry (×3), schema validation | ③ ContentValidation: 4 options, dedup, correct_index range |
| **Output** | JSON response → GameModeBase.render_ui_data() → UI render; user answers → check_answer() / ai_grade() |

### Sơ đồ Plugin (Game Mode Architecture)

```
GameModeBase (ABC)
├── FillBlankMode
├── ClozeMode
├── TranslationMode
├── WordUnscrambleMode
├── WordMatchingMode        ← is_offline = True (không gọi API)
├── StoryGeneratorMode
├── SentenceTransformMode
└── TabooMode
    └── generate_ai_guess()  ← extension method riêng
```

Mỗi game mode kế thừa `GameModeBase` và implement 3 phương thức trừu tượng:
- `render_ui_data()` — transform raw API result → UI data
- `check_answer()` — local answer checking (không cần AI)
- `_format_anki_note()` — định dạng card để lưu vào Anki

---

## 3. ⚙️ Chi tiết Chức năng & Hàm Cốt lõi (Functions & Core Logic)

### 3.1 AIEngine — Bộ điều phối trung tâm (`core/engine.py`)

| Hàm | Vai trò | Input | Output |
|:--|:--|:--|:--|
| `handle_js_message(message)` | Router request từ JS bridge | JSON string `{action, data}` | Dict `{success, data, error_code, message}` |
| `_handle_generate(data)` | Sinh nội dung học tập | gamemode, language, level, topic, count, vocab_pairs | Dict (AI response hoặc error envelope) |
| `_handle_save_settings(data)` | Lưu settings → JSON file | API keys, model, temperature, lang | `{saved: [keys]}` |
| `_handle_ai_grade(data)` | Chấm điểm câu trả lời bằng AI | gamemode, user_answer, expected, source_text | `{correct, score, explanation, suggestion}` |
| `_handle_save_to_anki(data)` | Lưu kết quả game vào Anki deck | gamemode, content, deck_name | `{success, count}` |
| `_handle_check_answer(data)` | Kiểm tra đáp án local | user_input, correct | `{correct, points}` |
| `_handle_test_key(data)` | Test 1 API key | key string | `{ok, model, response}` |
| `_handle_test_all_keys(data)` | Test cả 3 keys | — | `{results: [{key, ok, model}]}` |
| `get_gamemode(name)` | Lazy-load + cache GameMode instance | tên game | GameModeBase instance |

**Logic `_handle_generate` (luồng chính):**
```
data → GAME_LIMITS clamp count → defaults injection
→ get_gamemode() → if offline → gm.generate() (không API)
→ get_schema(gamemode) → PromptManager.get_prompt()
→ GeminiClient.generate_structured() → AI call
→ ContentValidation.validate_game_result() → sanitize
→ GameModeBase.render_ui_data() → transform
→ ContextManager.save() → return result
```

### 3.2 GeminiClient — HTTP Transport Layer (`core/api_client.py`)

| Hàm | Vai trò | Input | Output |
|:--|:--|:--|:--|
| `generate_structured()` | Gọi API với schema | prompt, response_schema, temperature | Dict (parsed JSON) |
| `generate_text()` | Gọi API text thuần | prompt, temperature | Optional[str] (JSON string) |
| `test_key()` | Kiểm tra key hợp lệ | key string | `{ok, model, response}` |
| `_try_keys()` | Key rotation logic | payload, max_retries, base_delay | Dict (result từ key đầu tiên thành công) |
| `_call_api()` | HTTP POST thực tế | payload, key, model | Dict (raw response) |
| `_parse_response()` | Parse JSON từ response | raw dict | Dict |
| `_throttle()` | Rate limiting classmethod | — | Sleep nếu < 1.5s từ lần cuối |
| `resolve_model()` | Chọn model theo key prefix | preferred, api_key | model name string |
| `detect_key_type()` | Nhận dạng loại key | api_key | "new (AQ.)" / "old (AIzaSy)" / "unknown" |

**Retry & Key Rotation Strategy:**
```
Try keys theo thứ tự: active_index → others → cooldown queue
Mỗi key retry ×3 với exponential backoff (base=4s)
Error handlers:
  - 429 (RateLimit) → cooldown 60s
  - 404 (ModelNotFound) → cooldown 300s
  - SchemaNotSupported → text fallback (bỏ schema, gọi lại)
  - 403 / invalid → cooldown 3600s
  - Transport error → cooldown 20s
```

### 3.3 8 Game Mode Classes (`gamemodes/`)

| Mode | File | `render_ui_data()` transform | `check_answer()` logic | Ghi chú |
|:--|:--|:--|:--|:--|
| **fill_blank** | `fill_blank.py` | questions[].{sentence_with_blank, options, hint, ...} | `selected == correct_index` | — |
| **cloze** | `cloze.py` | paragraph_with_blanks + blanks[].{options, explanation} | `user_idx == correct_idx` | — |
| **translation** | `translation.py` | sentences[0].{source_text, target_text, grammar_notes, detailed_feedback} | Gọi AI grader | 1 câu/lần |
| **unscramble** | `word_unscramble.py` | questions[].{correct_sentence, shuffled_words, hint, translation} | `join(" ") == correct_sentence` | — |
| **matching** | `word_matching.py` | pairs[] + left_column[] + right_column[] | Ghép cặp term ↔ definition | **is_offline = True** |
| **story** | `story_generator.py` | story + comprehension_questions[].{question, options, correct_index} | So sánh index | — |
| **sentence_transform** | `sentence_transform.py` | questions[0].{original_sentence, instruction, hint_word, expected_answer, detailed_explanation} | Gọi AI grader | 1 câu/lần |
| **taboo** | `taboo.py` | rounds[0].{secret_word, forbidden_words, ai_description, category, difficulty} | `guess.lower() == word.lower()` | + `generate_ai_guess()` riêng |

### 3.4 Schema Registry (`core/schema_registry.py`)

7 JSON Schemas cho `response_mime_type=application/json`:
- **fill_blank** / **cloze** / **translation** / **unscramble** / **story** / **sentence_transform** / **taboo**
- Mỗi schema định nghĩa `type: object` với `properties` và `required` fields
- Schema được Gemini dùng để ép kiểu output trực tiếp

### 3.5 AI Grader (`core/ai_grader.py`)

6 grader prompt templates (format string):
- **Generic** (fallback): question + expected + user_answer → `{correct, score, explanation, suggestion}`
- **fill_blank**: question_sentence + blank_word + user_choice → `{correct, score, semantic, grammar, vocabulary_relation}`
- **translation**: source_text + expected_target + user_target → `{correct, score, errors[], explanation, suggestion}`
- **unscramble**: correct_sentence + user_sentence → `{correct, score, wrong_words[], grammar_rule, explanation}`
- **sentence_transform**: instruction + original + expected + user_answer → `{correct, score, grammar_rule, explanation, suggestion}`
- **taboo**: secret_word + user_guess → `{correct, score, explanation, suggested_words[]}`

**Temperature:** 0.3 (low creativity, grading accuracy)

### 3.6 Content Validation (`core/content_validation.py`)

Kiểm tra AI output trước khi gửi lên UI:
- Mỗi question trong choice games (fill_blank, cloze, story) phải có **exactly 4 options**
- Options không được trùng lặp hoặc empty
- `correct_index` phải ∈ [0, 3]
- Nếu AI trả về nhiều hơn `requested_count`, cắt bỏ phần thừa

### 3.7 SettingsManager (`core/engine.py:SettingsManager`)

- Lưu tại `user_files/settings.json`
- 3 API key slots (primary + 2 fallback)
- Settings: `api_key`, `model` (auto | gemini-1.5-flash | ...), `temperature`, `ui_lang`, `learn_lang`, `window_width/height`
- `get_active_keys()` → lọc key rỗng
- `get_api_keys()` → cả 3 key (kể cả rỗng)

### 3.8 DeckSource (`core/deck_source.py`)

Đọc Anki collection trên main thread:
- `list_decks()` → decks sorted by name, có `level` (subdeck depth)
- `_note_ids()` → query notes bằng `did:` + `mid:`, hỗ trợ descendant decks
- `list_source_models()` → note types trong deck đã chọn
- `list_source_fields()` → field names của model
- `sample_vocab_pairs()` → random sample N pairs, de-duplicated, exclude seen pair keys


### 3.10 i18n (`core/i18n.py`)

- File JSON: `lang/vi.json`, `lang/en.json`
- `load_strings(lang)` → cache trong `_cache` dict
- `t(key, lang)` → format string với **kwargs
- Mặc định: `vi` (Tiếng Việt)

### 3.11 Logger (`core/logger.py`)

- File log: `user_files/ai_hub.log`
- Auto-rotate khi > 1MB (rename → `.1`, `.2`, ...)
- Async append file + print to stdout/stderr
- 4 levels: DEBUG, INFO, WARN, ERROR
- Exception logging kèm 5 dòng traceback cuối

### 3.12 Bridge Layer & Background Tasks

**JS Bridge** (`web/js/bridge.js`):
```javascript
Bridge.sendAsync(action, data, timeout=90s)
  → Promise-based
  → pending Map with timeout
  → pycmd() callback → _settle()
Bridge.complete(id, result)  // background task callback
```

**MainWindow** (`ui/main_window.py`):
- `BACKGROUND_ACTIONS = {"generate", "test_key", "test_all_keys", "ai_grade"}`
- Sync actions: `pycmd()` → thread-safe `_on_bridge_cmd()` → `engine.handle_js_message()`
- Background actions: `taskman.run_in_background()` → `_background_complete()` → `hub_web.eval("Bridge.complete(...)")`
- `embed()`: replace main Anki WebView with QTabWidget (Anki tab + AI Hub tab)
- `close()`: restore original WebView

### 3.13 Entry Point (`__init__.py`)

```python
gui_hooks.main_window_did_init.append(init_addon)
# → menuTools.addAction("AI Learning Hub...") → open_hub()
# → menuTools.addAction("AI Learning Hub Settings...") → open_settings()
# QDialog: 3 keys, model selector, temperature, UI lang, learn lang
# Retranslation on language switch (ui_lang_cb → _retranslate)
```

---

## 4. 🔄 Tương tác Hệ thống & Trạng thái (System Integration & States)

### 4.1 Giao tiếp giữa các thành phần

```
SPA (app.js) ──JSON──▶ Bridge (bridge.js) ──pycmd()──▶ AIHubView._on_bridge_cmd()
  │                                                         │
  │ Sync (settings, list_decks, ...):                       │
  │ ◄── engine.handle_js_message() trực tiếp ──────────────┘
  │
  │ Async (generate, ai_grade, test_keys):
  │   ──▶ taskman.run_in_background() ──▶ engine.handle_js_message()
  │        ──▶ thread pool ──▶ Gemini API call (I/O bound)
  │   ◄── taskman callback ──▶ _background_complete() ──▶ hub_web.eval("Bridge.complete()")
```

### 4.2 Trạng thái & Edge Cases

| Kịch bản | Xử lý | File:Line |
|:--|:--|:--|
| **Không có API key** | `_handle_generate` → `E_NO_KEYS` | `engine.py:341-347` |
| **Key bị rate limit** | Cooldown 60s, retry ×3 → next key | `api_client.py:207-214` |
| **Key không hỗ trợ schema** | Schema fallback → text mode | `api_client.py:220-238` |
| **Model không tồn tại** | Cooldown 300s → next key | `api_client.py:215-219` |
| **Key invalid** | Cooldown 3600s (1 hour) | `api_client.py:243-244` |
| **AI response thiếu candidates** | `_parse_response` → `ApiError("No candidates")` | `api_client.py:140-143` |
| **Content bị Safety block** | Return `E_SAFETY` | `api_client.py:148-149` |
| **Content bị Recitation** | Return `E_RECITATION` | `api_client.py:150-151` |
| **JSON parse fail** | Codeblock stripping → retry → `ApiError` | `api_client.py:158-175` |
| **Options < 4 hoặc duplicate** | `validate_game_result` → `E_AI_CONTENT` | `content_validation.py:22-29` |
| **Anki collection chưa mở** | `E_COLLECTION_CLOSED` | `deck_source.py:41-42` |
| **Deck/Model không tồn tại** | `E_DECK_NOT_FOUND` / `E_MODEL_NOT_FOUND` | `deck_source.py:85-86,102-103` |
| **2 fields giống nhau** | `E_FIELDS_IDENTICAL` | `deck_source.py:124-125` |
| **Bridge action không hợp lệ** | `E_UNKNOWN` | `engine.py:258-262` |
| **Background task crash** | `_background_complete` → `E_BACKGROUND` | `main_window.py:88-92` |
| **Tất cả keys đều fail** | `_try_keys` → `E_API_ERROR` với last_error message | `api_client.py:258` |
| **Vocab pairs exhausted** | SPA throw error "Đã dùng hết mẫu" → user click "Làm mới vòng" | `app.js:29` |
| **User đóng Hub khi background task chạy** | `_bg_lock` + `if self._closed: return` | `main_window.py:82-83` |

### 4.3 API Integration

- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- **Header:** `x-goog-api-key: {key}`
- **Method:** POST
- **Timeout:** 60 giây (HTTP), 90 giây (bridge timeout)
- **Structured output:** `generationConfig.response_mime_type: "application/json"` + `response_schema`
- **Model resolution:** `auto` → detect từ key prefix: `AQ.` → `gemini-flash-latest`, `AIzaSy` → `gemini-1.5-flash`

---

## 5. 💡 Đánh giá Ưu / Nhược điểm & Rủi ro (Evaluation & Risks)

### Điểm mạnh

| Khía cạnh | Mô tả |
|:--|:--|
| **Plugin Architecture** | `GameModeBase` (ABC) cho phép thêm game mode mới mà không sửa core engine — chỉ cần thêm file + khai báo schema + prompt |
| **Key Rotation & Fallback** | 3 API key slots, tự động phát hiện key unhealthy, cooldown theo loại lỗi, retry exponential backoff |
| **Structured Output** | Dùng Gemini `response_schema` thay vì parse text → giảm hallucination, không cần regex |
| **Offline Mode** | `WordMatchingMode` không gọi API — hoạt động hoàn toàn local |
| **Content Validation** | Validate AI output trước khi render — bắt lỗi duplicate/empty options |
| **Async Bridge** | Promise-based JS ↔ Python, background I/O không block UI |
| **i18n Complete** | Toàn bộ UI strings qua `lang/*.json`, bao gồm settings dialog |
| **Comprehensive Logging** | File log auto-rotate, level-based, kèm extra data dict |
| **CEFR Level Instruction** | 5 cấp độ từ A1 đến C2, mỗi cấp có instruction riêng cho prompt |

### Điểm yếu & Rủi ro

| Vấn đề | Mức độ | Mô tả | Ảnh hưởng |
|:--|:--|:--|:--|
| **Single Point of Failure: Gemini API** | 🔴 **Critical** | Toàn bộ content generation phụ thuộc Gemini API. Nếu API down, 7/8 game modes không hoạt động | UX degradation |
| **GIL-bound (single-threaded)** | 🟡 **Medium** | `deck_source.py` chạy trên main thread (do Anki API restriction) — blocking I/O khi sync | UI lag (Anki restrict) |
| **Throttling global** | 🟡 **Medium** | `_last_request_time` là class variable — 1.5s interval áp dụng cho mọi instance | Slowdown khi concurrent |
| **Không có timeout configurable** | 🟢 **Low** | Timeout cứng 60s HTTP + 90s bridge — không configurable | Không linh hoạt cho network chậm |
| **Không cache prompt template** | 🟢 **Low** | Mỗi lần gọi `get_prompt()` → disk I/O nếu không trong cache | Performance (negligible) |
| **Security: API key in plaintext** | 🟠 **High** | Key lưu trong `settings.json` plaintext. Chỉ che bằng `EchoMode.Password` trên UI | Cần encryption |
| **Error envelope chưa đồng bộ** | 🟢 **Low** | `_handle_generate` return dict trực tiếp (không wrapper), trong khi các handler khác dùng `{success, data, error_code, message}` | Inconsistency |
| **No middleware pipeline** | 🟢 **Low** | Tất cả validation diễn ra trong từng handler, không có pre/post processing chain | Khó mở rộng logging/metrics |
| **Testing coverage** | 🔴 **Critical** | Không tìm thấy test files | Regression risk |
| **Anki API coupling** | 🟡 **Medium** | `aqt.mw`, `gui_hooks`, `AnkiWebView` — phụ thuộc chặt vào Anki API không public | Version compatibility |
| **JS SPA bundle** | 🟡 **Medium** | `app.js` là 1 file 78 dòng (minified-like) — khó maintain, không type checking | Developer experience |

### Độ phức tạp thuật toán

| Component | Complexity | Ghi chú |
|:--|:--|:--|
| `_note_ids()` | O(D + N) — D = number of decks, N = notes matched | Duyệt toàn bộ decks để tìm descendant |
| `sample_vocab_pairs()` | O(N log N) — shuffle + scan + dedup | Giới hạn 50 samples |
| `_try_keys()` | O(K × R) — K = keys (max 3), R = retries (max 3) | Luôn hằng số nhỏ |
| `ContentValidation` | O(I × O) — I = items, O = options (luôn 4) | Hằng số |
| `validate_game_result` | O(I) | Linear scan |

### Gợi ý tối ưu

| Hạng mục | Gợi ý |
|:--|:--|
| **Security** | Mã hóa API key bằng keyring OS hoặc Anki's built-in encryption |
| **Resilience** | Thêm circuit breaker pattern cho GeminiClient, fallback cache khi API offline, queue retry với backoff configurable |
| **Performance** | Cache prompt templates trong memory (Python dict), reduce disk I/O |
| **Architecture** | Thêm middleware pipeline: `[ValidationMiddleware, LoggingMiddleware, MetricsMiddleware]` chạy trước/sau mỗi handler |
| **Testing** | Unit test cho: GeminiClient._try_keys() (mock HTTP), ContentValidation, DeckSource, mỗi GameMode.check_answer() |
| **Maintainability** | Refactor `app.js` → component-based (React/Vue optional), add TypeScript |
| **Scale** | Configurable timeout và parallelism cho GeminiClient |
| **Error handling** | Đồng bộ error envelope format cho tất cả handlers (kể cả `_handle_generate`) |

---

## 6. 📌 Tóm tắt Cô đọng (Executive Summary)

**AI Learning Hub** là add-on Anki với kiến trúc 3 lớp (SPA WebView ↔ Bridge ↔ Python Engine) cho phép người dùng học ngoại ngữ qua 8 game mode tương tác sử dụng Gemini API. Hệ thống có thiết kế **Plugin Architecture** tốt (dễ thêm game mode mới), **Key Rotation & Fallback** thông minh với cooldown theo từng loại lỗi, và **Structured Output Validation** giúp đảm bảo chất lượng nội dung AI. Điểm yếu chính là phụ thuộc hoàn toàn vào Gemini API (single point of failure), thiếu test coverage, và security hạn chế (API key plaintext). Ưu tiên tối ưu gồm: thêm circuit breaker, encryption API keys, refactor frontend SPA, và xây dựng test suite để đảm bảo regression-free khi mở rộng.
