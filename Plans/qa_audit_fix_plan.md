# 📋 Kế Hoạch Vá Lỗi QA Audit — AI Learning Hub

File này lưu trữ toàn bộ các lỗi đã được xác minh thực tế từ 3 subagent kiểm định (app.js, server.ts, Python backend) cùng phương án khắc phục chi tiết.

---

## Tóm Tắt Phát Hiện

| Mức độ | Số lượng | Mô tả |
|--------|----------|-------|
| 🔴 P0 Critical | 4 | Runtime crash, schema mismatch, type error |
| 🟠 P1 High | 7 | Missing empty states, unused code, i18n gaps |
| 🟡 P2 Medium | 5 | Dead code cleanup, consolidation, CSS |

---

## 🔴 Phase 1: P0 — Critical Fixes (Runtime Crashes & Data Corruption)

### 1.1 `finishGame()` duplicate const → Runtime SyntaxError (ĐÃ KHẮC PHỤC KHẨN CẤP)
- **Tệp**: `web/js/app.js` (dòng 1713-1778)
- **Mô tả**: `finishGame()` chứa block code duplicate bị lồng trong string literal dẫn tới `SyntaxError`.
- **Trạng thái**: ✅ Đã sửa & deploy.

### 1.2 Schema Mismatch — Post-processing bị skip
- **Tệp**: `server.ts`
- **Các lỗi**:
  - `translation` (dòng 979-984): Code check `if (gamemode === "translation" && parsed.sentences)` nhưng schema trả về `parsed.source_sentence` (top-level) → post-processing bị bỏ qua.
  - `unscramble` (dòng 985-1003): Code check `parsed.sentences` nhưng schema trả về `parsed.questions` → post-processing bị bỏ qua.
  - System instructions (dòng 868-904) dùng hậu tố `_vietnamese` trong khi schema enforce `_vi` (ví dụ `meaning_vi`, `explanation_vi`).
  - `sentence_transform` và `taboo` thiếu field normalization đầy đủ.

### 1.3 Translation Grader thiếu source language context
- **Tệp**: `server.ts` (dòng 1040-1135)
- **Mô tả**: Endpoint `ai_grade` không đọc `source_lang` từ request, grader prompt hardcode phản hồi bằng tiếng Việt.

### 1.4 `save_to_anki` type mismatch
- **Tệp**: `core/engine.py` & `gamemodes/base.py`
- **Mô tả**: `engine.py` truyền 1 `dict` đơn lẻ vào `gm.save_to_anki()` trong khi `base.py` mong chờ `List[dict]`, dẫn tới lỗi khi iterate. `base.py` hardcode `note["Front"]`/`note["Back"]` thay vì dùng field động.

---

## 🟠 Phase 2: P1 — High Priority (Missing States & Logic Gaps)

### 2.1 Missing Empty States trong UI
- **Tệp**: `web/js/app.js`
- **Mô tả**: 5 hàm render (`renderFillBlank`, `renderCloze`, `renderTranslation`, `renderSentenceTransform`, `renderTaboo`) chưa có guard check dữ liệu rỗng/undefined, gây `TypeError` nếu AI trả về dữ liệu rỗng.

### 2.2 `resetGameState()` thiếu reset `currentHistoryItem`
- **Tệp**: `web/js/app.js`
- **Mô tả**: Không reset `state.currentHistoryItem`, có thể gây rò rỉ dữ liệu giữa các lượt chơi.

### 2.3 Field Name Aliasing — Chuẩn hóa tên trường
- **Tệp**: `server.ts`
- **Chuẩn hóa**:
  - `target_word` (thay vì `secret_word`)
  - `taboo_words` (thay vì `forbidden_words`)
  - `meaning_vi` (thay vì `meaning_vietnamese`, `word_meaning_vietnamese`)
  - `explanation_vi` (thay vì `explanation_vietnamese`, `explanation_short`)
  - `clue` (thay vì `ai_description`)

### 2.4 Dọn dẹp `sanitizeHtml` dư thừa trong `app.js`
- **Tệp**: `web/js/app.js` (dòng 141-148)
- **Mô tả**: Định nghĩa nhưng không bao giờ gọi.

### 2.5 Xử lý `appContext` không được sử dụng
- **Tệp**: `server.ts` (dòng 21, 754-769)
- **Mô tả**: Endpoints `save_context`/`load_context`/`clear_context` hoạt động nhưng `appContext` không được đưa vào prompt Gemini.

### 2.6 Xóa `WordMatchingSchema` không dùng
- **Tệp**: `core/schema_registry.py` (dòng 77-96, 219)
- **Mô tả**: Mode Word Matching chạy hoàn toàn offline (`is_offline = True`), không sử dụng Pydantic Schema.

### 2.7 Ép i18n cho các chuỗi hardcode trong Matching UI
- **Tệp**: `web/js/app.js`

---

## 🟡 Phase 3: P2 — Medium (Cleanup & Optimization)

1. Dọn dẹp code thừa (comment trùng lặp, i18n keys không sử dụng).
2. Sửa tên field `UnscrambleSchema.sentences` → `questions` trong Pydantic.
3. Thêm dynamic field lookup cho `base.py` `save_to_anki()`.
