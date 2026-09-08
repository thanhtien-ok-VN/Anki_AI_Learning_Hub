# PLAN-005: Khắc Phục Lỗi Lấy Mẫu Anki Desktop & Chuẩn Hóa Toàn Diện Đa Ngôn Ngữ UI/UX

## 1. Bối cảnh & Hiện trạng Sự cố

Qua kiểm thử thực tế trên Anki Desktop (Anki 25+) và phân tích ảnh chụp màn hình do người dùng cung cấp (`media_1788836811524.png`), hệ thống gặp 2 lỗi nghiêm trọng ảnh hưởng trực tiếp đến trải nghiệm người dùng:

1. **Lỗi Lấy mẫu từ vựng ("AI Hub không thể hoàn tất yêu cầu này.")**:
   - Khi bấm **"Lấy mẫu"** trên giao diện Nguồn từ vựng Anki, Toast Banner màu vàng lập tức cảnh báo: `⚠️ AI Hub không thể hoàn tất yêu cầu này. ✕`.
   - Dữ liệu từ vựng không được nạp vào Hub; danh sách mẫu hiển thị rỗng.
2. **Không đồng bộ ngôn ngữ (Language Mismatch & Unlocalized Elements)**:
   - Giao diện người dùng đang ở tiếng Việt (Deck, Loại thẻ, Lấy mẫu, Đóng Hub...), nhưng nút bấm chính trong Config Panel lại hiển thị tiếng Anh: `Generate` (thay vì `Tạo bài`).
   - Các nhãn và tùy chọn trong Config Panel hiển thị tiếng Anh: `Level`, `Learning language`, `Topic`, `A1 Beginner`, `B1 Intermediate`, `C1–C2 Advanced`.
   - Ô nhập Topic mặc định giá trị slug tiếng Anh thô: `daily_life`.
   - Trong game Taboo, placeholder hiển thị mã ISO thô của ngôn ngữ: `Nhập từ bạn đoán bằng en...` thay vì `Nhập từ bạn đoán bằng Tiếng Anh...`.
   - Thiếu nút chuyển đổi ngôn ngữ giao diện (UI Language Switcher) ngay trên Hub để người dùng chủ động chọn Tiếng Việt hoặc English.

---

## 2. Phân tích Nguyên nhân Gốc rễ (Root Cause Analysis - RCA)

### RCA 1: Lỗi Lấy Mẫu Anki Desktop
- **Nguyên nhân chính (Mismatched Keyword Arguments in `AnkiService`)**:
  - Tại `core/services/anki_service.py` (dòng 33–41):
    ```python
    return sample_vocab_pairs(
        deck_id=data.get("deck_id"),
        model_id=data.get("model_id"),
        term_field=data.get("term_field"),
        def_field=data.get("def_field"),       # <-- LỖI: core.anki.vocabulary_source yêu cầu "definition_field"
        limit=data.get("limit", 20),
        strategy=data.get("strategy", "mixed"), # <-- LỖI: vocabulary_source không nhận tham số "strategy"
        cancel_event=cancel_event,              # <-- LỖI: vocabulary_source không nhận tham số "cancel_event"
    )
    ```
  - Trong khi đó, định nghĩa gốc tại `core/anki/vocabulary_source.py` (dòng 81):
    ```python
    def sample_vocab_pairs(
        *,
        deck_id: Optional[int],
        model_id: int,
        term_field: str,
        definition_field: str,
        limit: int = 50,
        excluded_pair_keys: Optional[List[str]] = None,
        weak_words: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
    ```
  - Do `core.anki.vocabulary_source.sample_vocab_pairs` dùng cú pháp keyword-only (`*`), việc truyền `def_field`, `strategy`, `cancel_event` khiến Python văng ngoại lệ `TypeError: sample_vocab_pairs() got an unexpected keyword argument 'def_field'`.
  - Tại `core/router.py` (dòng 142–150), khối `except Exception` bắt `TypeError` này và trả về envelope:
    `{"success": False, "data": {}, "error_code": "E_INTERNAL", "message": "The AI Hub could not complete this request."}`.
  - Tại `web/js/app.js` (dòng 231–252), hàm `bridgeMessage` kiểm tra `error.message.includes('The AI Hub could not')` và ánh xạ trực tiếp sang chuỗi: `t('app.ai_internal_error', 'AI Hub không thể hoàn tất yêu cầu này.')`.
  - Hơn nữa, `excluded_pair_keys` và `weak_words` không được chuyển từ frontend vào backend, làm mất tính năng ưu tiên 30% từ vựng yếu và chống lặp thẻ.
  - Ngoài ra, nếu `deck_id` hoặc `model_id` được gửi từ JS dưới dạng chuỗi ("123") hoặc chưa được chọn (None, NaN), hàm `int(model_id)` văng `ValueError`/`TypeError` nếu không có lớp tiền kiểm tra (guard clause).

### RCA 2: Không đồng bộ Đa ngôn ngữ (Language Parity)
- **Nguyên nhân 1 (Ghi đè `window.t` triệt tiêu từ điển `Utils.__`)**:
  - File `web/js/utils.js` (dòng 4–15) nạp toàn bộ chuỗi dịch từ `Bridge.sendAsync('get_ui_strings')` vào `Utils.__` và gán `window.t = Utils.t.bind(Utils)`.
  - Tuy nhiên, file `web/js/app.js` (được nạp sau trong `index.html`) tại dòng 108–118 đã **ghi đè** lại `window.t`:
    ```javascript
    const t = (key, fallback, ...args) => {
      if (typeof window.t === 'function' && window.t !== t) return window.t(key, fallback, ...args);
      let text = fallback || key; // <-- Luôn trả về fallback, hoàn toàn bỏ qua Utils.__!
      ...
      return text;
    };
    window.t = t;
    ```
    Vì `window.t === t` là true, điều kiện `window.t !== t` thành false. Do đó, hàm `t()` trong `app.js` **chỉ trả về chuỗi `fallback` mặc định**, không bao giờ tra cứu từ điển `vi.json` hay `en.json` đã nạp!
- **Nguyên nhân 2 (Fallback viết bằng tiếng Anh trong khi các component khác viết bằng tiếng Việt)**:
  - Nút bấm `generate` trong `manifest_client.js` và `app.js` được truyền fallback tiếng Anh: `t('controls.generate', 'Generate')`.
  - Nhãn `Level`, `Learning language`, `Topic` trong `manifest_client.js` và `app.js` dùng fallback tiếng Anh: `'Level'`, `'Learning language'`, `'Topic'`.
  - Các cấp độ CEFR dùng fallback tiếng Anh: `'A1 Beginner'`, `'B1 Intermediate'`, `'C1-C2 Advanced'`.
  - Trong khi đó, `home.js` và thanh header lại dùng fallback tiếng Việt: `'Lấy mẫu'`, `'Làm mới vòng'`, `'Nguồn từ vựng Anki'`. Kết quả tạo ra giao diện lai tạp (nửa Anh nửa Việt).
- **Nguyên nhân 3 (Nội suy mã ISO thay vì tên hiển thị trong Taboo)**:
  - Tại `web/js/renderers/taboo.js` (dòng 28): `const langLabel = (state.userPrefs && state.userPrefs.language) || 'en';`.
  - Khi truyền vào `t('placeholder.taboo', 'Nhập từ bạn đoán bằng {0}...', langLabel)`, nó trở thành `Nhập từ bạn đoán bằng en...`. Cần phải tra cứu qua từ điển tên ngôn ngữ (`state.supportedLanguages` hoặc `Utils.getLanguageName(code, uiLang)` -> `"Tiếng Anh"`).
- **Nguyên nhân 4 (Thiếu các khóa bản dịch trong `vi.json` & `en.json`)**:
  - Các khóa Hint (`hint.hint_btn`, `hint.level_1`, `hint.grammar_structure`, v.v.) và một số nhãn trường dữ liệu chưa có mặt trong `lang/vi.json` và `lang/en.json`.

---

## 3. Kiến trúc Đội ngũ & Phân vai Kỹ thuật (/teamwork-preview & /boost)

Nhằm đảm bảo giải quyết dứt điểm các lỗi với kỷ luật công nghệ cao, đội ngũ phân chia 4 vai trò chuyên trách:

| Vai trò | Chuyên môn chính | Trách nhiệm trong PLAN-005 |
| :--- | :--- | :--- |
| **System & Anki Specialist** | `system-programming`, `anki-connect-engine` | Sửa chữ ký hàm `AnkiService.sample_vocab_pairs`, bảo vệ guard clause kiểu dữ liệu (deck_id, model_id), truyền đầy đủ `excluded_pair_keys` và `weak_words`. |
| **Frontend & i18n Architect** | `ui-ux-pro-max`, `coding-discipline` | Chuẩn hóa `window.t` hợp nhất với `Utils.t`, sửa toàn bộ fallback về i18n keys chuẩn, khử mã ISO trong Taboo, bổ sung UI Language Switcher trên Hub. |
| **Data & Localization Engineer** | `coding-discipline` | Đồng bộ 100% key-value giữa `lang/vi.json` và `lang/en.json`, Việt hóa nhãn Level (`A1 Sơ cấp`, `B1 Trung cấp`, ...), bổ sung gợi ý Hint. |
| **QA & Verification Engineer** | `automated-testing`, `playwright-mcp` | Viết Python unit tests cho IPC router/AnkiService, chạy visual E2E verification qua Playwright, xác minh không hồi quy (65+ tests PASS). |

---

## 4. Chi tiết Nhiệm vụ Triển khai (Task Breakdown)

### Nhóm A: Sửa Lỗi Lấy Mẫu Anki & Bảo Toàn SRS Quota (Backend)
- **Task A.1 (Chuẩn hóa `AnkiService.sample_vocab_pairs`)**:
  - Sửa `core/services/anki_service.py` để forward chính xác các đối số keyword: `deck_id`, `model_id`, `term_field`, `definition_field` (fallback từ `def_field`), `limit`, `excluded_pair_keys`, `weak_words`.
  - Thêm tiền kiểm tra an toàn (safe integer parsing): xử lý ngoại lệ nếu `deck_id` hoặc `model_id` là null, string rỗng hoặc không phải số hợp lệ. Trả về `E_DECK_REQUIRED` hoặc `E_MODEL_REQUIRED` thay vì văng crash.
  - Cập nhật `core/anki/main_thread.py`: đảm bảo `error_response` trả về cả `"success": False` và `"error": True` để tương thích hoàn toàn với router.
  - *Skills*: `system-programming`, `coding-discipline`.

- **Task A.2 (Bổ sung Unit Tests cho IPC `sample_vocab_pairs`)**:
  - Bổ sung test case trong `tests/test_engine_router.py` và `tests/test_anki_service.py` giả lập dispatch action `sample_vocab_pairs` qua IPC router.
  - Xác nhận bắt lỗi chính xác khi thiếu tham số và trả về dữ liệu thành công khi đủ tham số.
  - *Skills*: `automated-testing`.

---

### Nhóm B: Hợp nhất Hệ Thống Bản Dịch i18n & Khắc Phục Lỗi Ghi Đè (Frontend Core)
- **Task B.1 (Sửa `window.t` trong `web/js/app.js` & kết nối chặt với `Utils.t`)**:
  - Bỏ cơ chế ghi đè biến `window.t` tại dòng 108–118 của `web/js/app.js`.
  - Thay thế bằng hàm ủy quyền trực tiếp tới `Utils.t(key, fallback, ...args)`.
  - Cải tiến `Utils.t` trong `web/js/utils.js`:
    - Tra cứu `this.__[key]`. Nếu tìm thấy, sử dụng chuỗi đã dịch.
    - Nếu không tìm thấy, fallback sang `defaultText` (hoặc `key`).
    - Hỗ trợ format biến cả dạng positional `{0}, {1}` và named `{key}`.
  - Thêm helper `Utils.getLanguageName(code, uiLang)` tra cứu tên hiển thị (VD: `en` -> `Tiếng Anh` khi `uiLang === 'vi'`, `English` khi `uiLang === 'en'`).
  - *Skills*: `ui-ux-pro-max`, `coding-discipline`.

- **Task B.2 (Bổ sung Bộ Chuyển Đổi Ngôn Ngữ Giao Diện - UI Language Switcher)**:
  - Thêm toggle nhỏ gọn `🌐 VI | EN` trên thanh timer/top-bar hoặc header của Hub (`web/js/app.js`, `web/js/pages/home.js`).
  - Khi người dùng click chọn:
    - Gọi `Bridge.sendAsync('set_ui_lang', { lang })`.
    - Gọi `Utils.initI18n()` nạp bộ từ điển mới.
    - Cập nhật `document.documentElement.lang`.
    - Re-render giao diện lập tức không cần reload trang.
  - *Skills*: `ui-ux-pro-max`, `web-accessibility-wcag`.

---

### Nhóm C: Chuẩn Hóa Nhãn UI, Placeholder & Khử Mã ISO (Frontend & Language Catalogs)
- **Task C.1 (Chuẩn hóa Config Panel & Game Renderers)**:
  - Trong `web/js/core/manifest_client.js` và `web/js/app.js`:
    - Thay thế `'Generate'` bằng `t('controls.generate', 'Tạo bài')`.
    - Thay thế `'Learning language'` bằng `t('app.language', 'Ngôn ngữ học')`.
    - Thay thế `'Level'` bằng `t('app.level', 'Trình độ')`.
    - Thay thế `'Topic'` bằng `t('app.topic', 'Chủ đề')`.
    - Đổi input `topic` sang placeholder `t('app.topic_placeholder', 'Nhập mô tả chủ đề...')` thay vì gán cứng giá trị `"daily_life"`.
  - Trong `web/js/renderers/taboo.js`:
    - Dùng `Utils.getLanguageName(langCode, uiLang)` để lấy `"Tiếng Anh"` (hoặc `"English"`).
    - Placeholder thành: `Nhập từ bạn đoán bằng Tiếng Anh...`.
  - Trong `web/js/pages/source.js`:
    - Tách biệt placeholder: `Chọn trường từ khóa` cho ô Term, `Chọn trường định nghĩa` cho ô Definition.
  - *Skills*: `ui-ux-pro-max`.

- **Task C.2 (Cập nhật và Đồng Bộ `lang/vi.json` & `lang/en.json`)**:
  - Bổ sung toàn bộ các khóa còn thiếu:
    - Nhóm `hint.*`: `hint.hint_btn`, `hint.level_1`, `hint.level_2`, `hint.level_3`, `hint.grammar_structure`, `hint.word_length`, `hint.structure_tip`, `hint.starts_with`, `hint.meaning_label`.
    - Nhóm `controls.level_*`: Việt hóa trong `vi.json` thành `A1 - Sơ cấp (Beginner)`, `A2 - Sơ trung cấp (Elementary)`, `B1 - Trung cấp (Intermediate)`, `B2 - Trung cấp nâng cao (Upper-intermediate)`, `C1–C2 - Nâng cao (Advanced)`.
    - Nhóm `source.*`: `source.select_deck_first`, `source.select_term_first`, `source.select_def_first`.
  - Đảm bảo parity 100% giữa `vi.json` và `en.json`.
  - *Skills*: `coding-discipline`.

---

## 5. Kiểm Thử Tự Động & Xác Minh Thị Giác (Verification)
- **Task D.1 (Hồi quy Python Tests)**:
  - Chạy `python -B -m unittest discover -s tests -p "test_*.py" -v`.
  - Yêu cầu: Tối thiểu 85/85 tests PASS, bao gồm test IPC mới cho `sample_vocab_pairs`.
  - *Skills*: `automated-testing`.

- **Task D.2 (Visual E2E Verification bằng Playwright)**:
  - Khởi động Playwright test suite (`tests/test_playwright_e2e.py`).
  - Kiểm tra DOM & Render:
    - Bấm lấy mẫu -> không xuất hiện lỗi banner "AI Hub không thể hoàn tất yêu cầu này".
    - Kiểm tra nút bấm hiển thị đúng `Tạo bài` khi ở tiếng Việt, `Generate` khi ở tiếng Anh.
    - Kiểm tra placeholder Taboo hiển thị tên ngôn ngữ tiếng Việt/tiếng Anh, không chứa `en`.
    - Bấm switch ngôn ngữ -> UI chuyển đổi mượt mà giữa VI và EN.
  - Chụp ảnh màn hình lưu vào artifact bằng chứng.
  - *Skills*: `playwright-mcp`.

- **Task D.3 (Đồng bộ file sạch sang Anki Desktop)**:
  - Đồng bộ file đã sửa sang `%APPDATA%\Anki2\addons21\AI_Learning_Hub\`.
  - TUYỆT ĐỐI KHÔNG đóng gói `.ankiaddon` trừ khi người dùng ra lệnh.

---

## 6. Tiêu Chí Nghiệm Thu (Acceptance Criteria)

1. **Lấy mẫu thành công 100%**:
   - Bấm `Lấy mẫu` trên bất kỳ Deck/Note Type hợp lệ nào đều trả về danh sách cặp từ vựng ngẫu nhiên kèm quota từ yếu (30%).
   - Hoàn toàn không còn xuất hiện thông báo: `"AI Hub không thể hoàn tất yêu cầu này."`.
   - Nếu người dùng chưa chọn deck/note type, hiển thị toast hướng dẫn rõ ràng (`"Hãy chọn deck, note type và hai trường."`).
2. **Ngôn ngữ chuẩn xác và đồng nhất**:
   - Khi chọn Tiếng Việt (`vi`):
     - Nút bấm hiển thị `Tạo bài`.
     - Nhãn hiển thị `Ngôn ngữ học`, `Trình độ`, `Chủ đề`.
     - Các mức độ hiển thị rõ tiếng Việt (`A1 - Sơ cấp`, `B1 - Trung cấp`, ...).
     - Game Taboo hiển thị placeholder `Nhập từ bạn đoán bằng Tiếng Anh...`.
   - Khi chuyển sang English (`en`):
     - Tất cả các nhãn và nút tự động chuyển sang tiếng Anh đồng bộ (`Generate`, `Learning language`, `Level`, `Topic`, `A1 Beginner`...).
3. **Chất lượng kiểm thử**:
   - 100% Python unit tests vượt qua (>= 86 tests).
   - E2E Playwright test xác minh trực quan thành công với ảnh chụp bằng chứng.
