# PLAN-004: Tái Cấu Trúc Kiến Trúc Chuyên Sâu Theo Chuẩn SOLID & Module Hóa Toàn Diện

> **Trạng thái**: HOÀN THÀNH 100% (Đã triển khai, 85/85 tests PASS, xác minh thị giác Playwright đầy đủ)

Bản kế hoạch kỹ thuật toàn diện nhằm giải quyết các điểm nghẽn kiến trúc (architectural bottlenecks), đảm bảo tuân thủ nghiêm ngặt các nguyên lý SOLID (Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion), phân rã các module nguyên khối thành các thành phần chuyên biệt, dễ bảo trì, mở rộng và kiểm thử độc lập.

## User Review Required

> [!IMPORTANT]
> **ĐIỂM DỪNG BẮT BUỘC (HARD STOP - Phase 1 Approval Gate)**:  
> Hiện tại hệ thống **CHƯA THAY ĐỔI BẤT KỲ DÒNG MÃ NGUỒN SẢN PHẨM NÀO**.  
> Bản kế hoạch này được đệ trình để Quý Kỹ sư Trưởng / Người dùng xem xét, phê duyệt trước khi bắt đầu Phase 2 (Implementation).
> 
> **Quy tắc đóng gói**: Tuyệt đối **KHÔNG** đóng gói add-on (`scripts/build_addon.py`). Chỉ đồng bộ file sạch sang `%APPDATA%\Anki2\addons21\AI_Learning_Hub\` phục vụ kiểm thử sau khi hoàn thành.

---

## I. Đánh Giá Hiện Trạng & Phân Tích Điểm Nghẽn

### 1. Hiện trạng kiểm thử cơ sở (Baseline Verification)
- **Python Unit Tests**: **83/83 PASS** trong ~14.9s (`python -B -m unittest discover -s tests -p "test_*.py" -v`).
- **Frontend Bootstrap (Node VM)**: **PASS** (`node tests/test_web_bootstrap.js`).
- **Playwright E2E**: **PASS** (`test_frontend_full_game_lifecycle`).

### 2. Các điểm nghẽn kiến trúc & Vi phạm SOLID

1. **Frontend Monolith (`web/js/app.js` ~3,600 dòng)**:
   - Vi phạm **SRP** & **OCP**: Tập trung State, LocalStorage persistence, Router/Shell, Note Type picker, và toàn bộ 8 Game Renderers vào 1 file duy nhất. Thêm mới hoặc chỉnh sửa 1 game mode bắt buộc phải can thiệp file 3,600 dòng.
2. **Dynamic Game Registration chưa khép kín (End-to-end)**:
   - Frontend vẫn phụ thuộc danh sách fallback tĩnh. Renderers chưa tự đăng ký động dựa trên `manifest` trả về từ Backend.
3. **Grading Strategy vi phạm OCP**:
   - `GradingService.ai_grade()` chứa chuỗi `if/elif/else` rẽ nhánh thủ công cho từng game mode. Thêm game mới buộc phải can thiệp vào service cốt lõi.
4. **LLM Provider Monolith (`llm/gemini.py` ~480 dòng)**:
   - Vi phạm **Separation of Concerns**: Trộn lẫn logic mạng `urllib`, throttle, exponential backoff với jitter, mapping model chain theo tiền tố API key, xử lý finishReason (`SAFETY`, `RECITATION`), và parse JSON.
   - `LLMProviderFactory` chưa có cơ chế provider tự đăng ký (self-registration).
5. **Tầng truy cập Anki Collection chưa phân tách (`core/deck_source.py` ~370 dòng)**:
   - Gắn chặt truy xuất DB SQLite, luồng chính Anki Qt, giải mã cây phân cấp deck và thuật toán lấy mẫu từ vựng ưu tiên từ yếu.
6. **Siêu dữ liệu IPC phân tán & Duplicate**:
   - `ui/main_window.py` duy trì một tập hợp hardcoded `BACKGROUND_ACTIONS` tách rời khỏi `core/router.py`.
7. **Đảo ngược phụ thuộc cấu hình (Dependency Inversion)**:
   - `PrefsService` import ngược `core.engine.ADDON_PATH` để lấy đường dẫn file lưu trữ.

---

## II. Phân Bổ Vai Trò Tự Trị (`/teamwork-preview` & `/boost`) & Ma Trận Kỹ Năng

### 1. Đội ngũ tự trị (`/teamwork-preview` & `/boost`)
- **Vai trò 1: Principal Architect & Spec Custodian (`spec-driven-development`, `boost`)**:
  - Bảo vệ hợp đồng kiến trúc (API contracts), kiểm soát ranh giới module, phê duyệt các interface mới, ngăn ngừa architectural drift.
- **Vai trò 2: Senior System & Backend Engineer (`system-programming`, `coding-discipline`)**:
  - Trích xuất `core/paths.py`, module hóa `core/anki/`, triển khai `IPCActionSpec` trên router, loại bỏ reverse dependencies.
- **Vai trò 3: LLM & AI Engine Specialist (`system-programming`, `coding-discipline`)**:
  - Phân rã `llm/gemini_*` (models, transport, response), hiện thực hóa provider self-registration trong `LLMProviderFactory`.
- **Vai trò 4: Frontend Architect & UI/UX Specialist (`ui-ux-pro-max`, `front-end-checklist`)**:
  - Phân rã `web/js/app.js` thành Pages, Core State/Persistence và 8 Game Renderers độc lập, bảo toàn 100% giao diện Glassmorphism.
- **Vai trò 5: QA Automation & Visual Verification Specialist (`playwright-mcp`, `automated-testing`)**:
  - Đảm bảo 83/83 unit tests luôn pass, kiểm thử Node bootstrap, thực thi E2E browser tests và chụp ảnh bằng chứng thị giác.

---

## III. Chi Tiết Các Thay Đổi Đề Xuất (Proposed Changes)

### Component 1: Cấu hình đường dẫn & Tầng IPC Router

#### [NEW] [core/paths.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/paths.py)
- Khai báo các đường dẫn hằng số: `ADDON_PATH`, `USER_FILES_DIR`, `PREFS_PATH`, `PROMPTS_DIR`, `WEB_DIR`.
- Cung cấp lớp `PathConfig` hỗ trợ Dependency Injection.

#### [MODIFY] [core/services/prefs_service.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/services/prefs_service.py)
- Nhận `PathConfig` qua constructor, loại bỏ hoàn toàn `import core.engine`.

#### [MODIFY] [core/router.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/router.py)
- Bổ sung dataclass `IPCActionSpec(name, handler, execution_mode, timeout_sec, description)`.
- Cung cấp phương thức `is_background_action(action: str) -> bool` và `get_specs()`.

#### [MODIFY] [ui/main_window.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/ui/main_window.py)
- Thay thế biến hardcoded `BACKGROUND_ACTIONS` bằng việc gọi `self.engine.router.is_background_action(action)`.

---

### Component 2: Tầng Anki Engine & Truy Xuất Bộ Sưu Tập

#### [NEW] [core/anki/main_thread.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/anki/main_thread.py)
- Đảm bảo thực thi an toàn trên main thread của Anki Qt (`run_on_main`), `get_collection()`, response formatters (`_ok`, `_error`).

#### [NEW] [core/anki/decks.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/anki/decks.py)
- Duyệt cấu trúc cây Deck, tính toán cấp bậc thụt lề (`level`), lấy danh sách con (`list_decks`).

#### [NEW] [core/anki/queries.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/anki/queries.py)
- Truy vấn SQLite fast-path trên `cards` và `notes`, lấy danh sách Note IDs theo Deck và Model.

#### [NEW] [core/anki/vocabulary_source.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/anki/vocabulary_source.py)
- Thuật toán lấy mẫu từ vựng `sample_vocab_pairs`: tự động nhận diện trường term/definition, làm sạch HTML/media markup, ưu tiên từ yếu (weak words).

#### [NEW] [core/anki/service.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/anki/service.py)
- `AnkiService` facade kết hợp toàn bộ thao tác collection.

#### [MODIFY] [core/deck_source.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/deck_source.py)
- Chuyển thành proxy mỏng ủy quyền (delegate) trực tiếp sang `core/anki/service.py` để giữ trọn vẹn tương thích ngược.

---

### Component 3: Domain Grading & LLM Provider Layer

#### [MODIFY] [gamemodes/base.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/gamemodes/base.py)
- Khai báo hook đa hình `build_grading_prompt_data(data: Dict[str, Any], common_context: Dict[str, Any]) -> Dict[str, Any]`.

#### [MODIFY] [gamemodes/](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/gamemodes/) (`fill_blank.py`, `translation.py`, `unscramble.py`, `sentence_transform.py`, `taboo.py`)
- Triển khai `build_grading_prompt_data` riêng cho từng mode.

#### [MODIFY] [core/services/grading_service.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/services/grading_service.py)
- Xóa bỏ hoàn toàn cây `if/elif/else` rẽ nhánh game mode, ủy nhiệm đa hình cho đối tượng gamemode.

#### [NEW] [llm/gemini_models.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/llm/gemini_models.py)
- Bảng mã lỗi `EC`, `detect_key_type`, `resolve_model_chain`, exceptions (`ApiError`, `RateLimitError`...).

#### [NEW] [llm/gemini_transport.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/llm/gemini_transport.py)
- `GeminiTransport`: Throttle, HTTP request dispatch, retry backoff với jitter, xử lý mã HTTP status.

#### [NEW] [llm/gemini_response.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/llm/gemini_response.py)
- `GeminiResponseParser`: Kiểm tra `finishReason`, lọc nội dung an toàn, parse JSON làm sạch.

#### [MODIFY] [llm/gemini.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/llm/gemini.py)
- Facade `GeminiProvider` kế thừa `BaseLLMProvider`, tinh gọn điều phối xoay vòng key và waterfall.

#### [MODIFY] [llm/factory.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/llm/factory.py)
- Bổ sung `register_provider(name, provider_cls)` hỗ trợ OCP.

---

### Component 4: Tái cấu trúc Frontend SPA (`web/js/`)

#### [NEW] [web/js/core/state.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/core/state.js)
- Khởi tạo đối tượng `state` toàn cục, quản lý session và danh mục models mặc định.

#### [NEW] [web/js/core/persistence.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/core/persistence.js)
- Các hàm quản lý LocalStorage: `loadPrefs`, `savePrefs`, `loadMatchingStats`, `saveMatchingStats`, `loadHistory`, `saveHistory`.

#### [NEW] [web/js/pages/source.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/pages/source.js)
- Giao diện và logic panel chọn nguồn từ vựng (Deck, Note type, Term, Definition, Samples).

#### [NEW] [web/js/pages/home.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/pages/home.js)
- Giao diện Dashboard trang chủ, hiển thị danh mục chế độ chơi từ registry và lịch sử học tập.

#### [NEW] [web/js/renderers/registry.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/renderers/registry.js)
- `GameRendererRegistry`: Quản lý các renderer của game, tự động render theo mode ID.

#### [NEW] [web/js/renderers/](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/renderers/)
- `fill_blank.js`, `cloze.js`, `matching.js`, `unscramble.js`, `story.js`, `translation.js`, `sentence_transform.js`, `taboo.js`.

#### [MODIFY] [web/js/app.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/app.js)
- Rút gọn từ ~3,600 dòng xuống dưới 600 dòng, đóng vai trò Orchestrator kết nối các trang, lắng nghe sự kiện bridge và điều phối vòng đời ứng dụng.

#### [MODIFY] [web/index.html](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/index.html) & [tests/test_web_bootstrap.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/tests/test_web_bootstrap.js)
- Cập nhật thứ tự nạp các script modularized, đảm bảo tương thích tuyệt đối trong môi trường QWebEngine và Node VM.

---

## IV. Kế Hoạch Xác Minh (Verification Plan)

### 1. Automated Tests
- **Unit Testing Toàn Diện**:
  ```powershell
  python -B -m unittest discover -s tests -p "test_*.py" -v
  ```
  *Mục tiêu: Đạt tối thiểu 83/83 PASS (kèm các test case mới cho `core/paths.py`, `core/anki/`, `llm/gemini_*`).*
- **Smoke Test Khởi Động Frontend**:
  ```powershell
  node tests/test_web_bootstrap.js
  ```
  *Mục tiêu: Bootstrap thành công, `window.App` và `App.start` hiển thị trang chủ không lỗi.*
- **Playwright E2E Browser Testing**:
  ```powershell
  python -B -m unittest tests/test_playwright_e2e.py -v
  ```
  *Mục tiêu: Chạy trọn vẹn luồng sinh đề, kiểm tra trả lời và chấm điểm AI.*

### 2. Manual Verification & Visual Proofing
- Sử dụng Playwright chụp ảnh màn hình các trang: Dashboard, Config panel, và các màn chơi chính (FillBlank, Matching, Story, SentenceTransform).
- Lưu bằng chứng thị giác vào thư mục brain và đối soát trực quan để đảm bảo không bị suy thoái giao diện (Zero Visual Regression).
- Đồng bộ file sạch sang thư mục Anki `%APPDATA%\Anki2\addons21\AI_Learning_Hub\`.
