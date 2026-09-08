# PLAN-006: Khắc Phục Triệt Để Phụ Thuộc Pydantic Trong Môi Trường Anki Desktop & Gia Cố Độ Bền IPC Bridge

Dựa trên phân tích 2 ảnh chụp màn hình do người dùng cung cấp (`media_1788838816268.png`, `media_1788838862468.png`) và kiểm tra chi tiết tệp nhật ký thực tế của Anki Desktop tại `%APPDATA%\Anki2\addons21\AI_Learning_Hub\user_files\ai_hub.log` và `ai_hub_flow.jsonl`:

## 1. Bối cảnh & Hiện trạng Sự cố

1. **Lỗi `Unknown gamemode: fill_blank` và `Unknown gamemode: cloze` khi bấm "Tạo bài"**:
   - Khi người dùng đã lấy mẫu từ vựng thành công và nhấn **"Tạo bài"**, Toast thông báo màu đỏ/vàng lập tức xuất hiện: `⚠️ Unknown gamemode: fill_blank ✕` (hoặc `⚠️ Unknown gamemode: cloze ✕`, `⚠️ Unknown gamemode: translation ✕`).
   - Quá trình sinh bài hoàn toàn bị chặn lại trước khi gọi tới Gemini API.
2. **Lỗi `IPCRouter dispatch error: 'SettingsManager' object has no attribute 'get_all'`**:
   - Xuất hiện trong log thực tế lúc `10:39:01` (dòng 1930, 1946, 1974) khi frontend tải thiết lập ban đầu.
3. **Lỗi `Bridge error: unhashable type: 'dict'`**:
   - Xuất hiện trong log thực tế lúc `10:39:01` (dòng 1925, 1927) khi WebView gọi lấy danh sách game mode.

---

## 2. Phân Tích Nguyên Nhân Gốc Rễ (Root Cause Analysis - RCA)

### RCA 1: Thiếu thư viện Pydantic trong môi trường nhúng của Anki Desktop (Gây lỗi `Unknown gamemode`)
- **Cơ chế lỗi**:
  - Python nhúng đi kèm Anki Desktop trên máy người dùng là Python tiêu chuẩn độc lập, **không cài đặt thư viện ngoài `pydantic`**.
  - Tại [core/schema_registry.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/schema_registry.py), khi `import pydantic` thất bại:
    ```python
    try:
        from pydantic import BaseModel
        HAS_PYDANTIC = True
    except ImportError:
        HAS_PYDANTIC = False
        BaseModel = object
    ...
    if HAS_PYDANTIC:
        REGISTRY = { ... }
    else:
        REGISTRY = {}
    ```
  - Khi `HAS_PYDANTIC = False`, biến `REGISTRY` bị gán rỗng `{}`.
  - Hàm `get_schema(gamemode)` gọi `model = REGISTRY.get(gamemode)`. Khi `model` là `None`, hàm trả về dictionary rỗng `{}`.
  - Tại [core/services/generation_service.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/services/generation_service.py) dòng 127–130:
    ```python
    schema = get_schema(gamemode)
    if not schema:
        log.warn(f"No schema for gamemode: {gamemode}")
        return {"error": True, "error_code": "E_NO_SCHEMA", "message": f"Unknown gamemode: {gamemode}"}
    ```
  - Hệ quả là tệp log ghi nhận liên tiếp:
    `[WARN] [AIHub] No schema for gamemode: fill_blank`
    `[WARN] [AIHub] No schema for gamemode: cloze`
    `[WARN] [AIHub] No schema for gamemode: translation`
    và trả thông báo `Unknown gamemode: ...` hiển thị lên giao diện.

### RCA 2: Lệch Interface giữa `PrefsService` và `SettingsManager`
- Tại [core/services/prefs_service.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/services/prefs_service.py) dòng 32:
  `for key, value in self.settings.get_all().items()`
- Tuy nhiên, trong [core/settings.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/settings.py), lớp `SettingsManager` chỉ có thuộc tính `.data`, `.get(key)`, `.set(key, value)`, `set_many(items)`, hoàn toàn thiếu hàm `get_all()`, `set_api_keys()` và `save()`.
- Dẫn đến ngoại lệ `AttributeError: 'SettingsManager' object has no attribute 'get_all'`.

### RCA 3: Chữ ký gọi `Bridge.sendAsync` truyền object thay vì action string
- Tại [web/js/core/manifest_client.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/core/manifest_client.js) dòng 29:
  `const res = await window.Bridge.sendAsync({ action: 'get_gamemodes' });`
- Chữ ký chuẩn của `Bridge.sendAsync` là `(action: string, data: object, opts: object)`. Việc truyền một object `{ action: 'get_gamemodes' }` làm tham số thứ nhất khiến payload gửi sang backend có `action = {"action": "get_gamemodes"}`.
- Tại [core/router.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/router.py) dòng 55: `self._specs.get(action)` ném lỗi `TypeError: unhashable type: 'dict'` vì dictionary không thể dùng làm hash key trong Python dict.

---

## 3. Kế Hoạch Nhiệm Vụ Kỹ Thuật Chi Tiết (Tích Hợp Kỹ Năng)

### Nhiệm vụ 1: Khôi phục Canonical Schemas thuần túy 0-Dependency (Skills: `system-programming`, `coding-discipline`)
- **Mục tiêu**: Đảm bảo `core/schema_registry.py` hoạt động hoàn hảo 100% trong Anki Desktop mà không cần bất kỳ gói thư viện ngoài nào (kể cả khi không có `pydantic`).
- **Thực hiện**:
  1. Đưa toàn bộ 7 Schema JSON chuẩn OpenAPI của Gemini (`fill_blank`, `cloze`, `translation`, `unscramble`, `story`, `sentence_transform`, `taboo`) thành `CANONICAL_SCHEMAS` dạng dictionary Python thuần túy.
  2. Hàm `get_schema(gamemode)` ưu tiên lấy trực tiếp từ `CANONICAL_SCHEMAS.get(gamemode, {})`.
  3. Giữ `REGISTRY` và các class `BaseModel` như một lớp bổ trợ kiểm tra dữ liệu nếu môi trường máy chủ/nhà phát triển có cài sẵn `pydantic`, nhưng **tuyệt đối không để thiếu pydantic làm hỏng chức năng chính**.

### Nhiệm vụ 2: Bổ sung đầy đủ Interface cho `SettingsManager` (Skills: `system-programming`, `coding-discipline`)
- **Mục tiêu**: Khắc phục dứt điểm `AttributeError: 'SettingsManager' object has no attribute 'get_all'`.
- **Thực hiện**:
  1. Trong [core/settings.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/settings.py):
     - Bổ sung phương thức `get_all(self) -> dict`: trả về `dict(self._settings)`.
     - Bổ sung phương thức `set_api_keys(self, keys: list[str]) -> dict`: nhận mảng key và ánh xạ an toàn vào `api_key1` đến `api_key10`.
     - Bổ sung phương thức `save(self) -> bool`: gọi `self._save()`.

### Nhiệm vụ 3: Chuẩn hóa Bridge Action & Phòng thủ lỗi IPC đa tầng (Skills: `system-programming`, `web-accessibility-wcag`)
- **Mục tiêu**: Xóa bỏ lỗi `unhashable type: 'dict'` và ngăn ngừa triệt để việc truyền sai tham số từ Frontend.
- **Thực hiện**:
  1. Trong [web/js/core/manifest_client.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/core/manifest_client.js):
     - Sửa lệnh gọi: `await window.Bridge.sendAsync('get_gamemodes', {});`.
  2. Trong [web/js/bridge.js](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/web/js/bridge.js):
     - Tại `sendAsync(action, data, opts)`: bổ sung kiểm tra phòng thủ: nếu `typeof action === 'object' && action !== null && action.action`, tự động chuẩn hóa lại `data = action.data || data; action = action.action;`.
  3. Trong [core/router.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/core/router.py) & [ui/main_window.py](file:///d:/AntigravityProject/Anki_AI_Learning_Hub/ui/main_window.py):
     - Bổ sung phòng thủ: nếu `isinstance(action, dict)`, tự động lấy `action = action.get("action", "")`. Kiểm tra `isinstance(action, str)` trước khi tra cứu `_specs.get(action)`.

### Nhiệm vụ 4: Kiểm thử tự động môi trường No-Pydantic & Regression Tests (Skills: `automated-testing`)
- **Mục tiêu**: Xác minh toàn bộ hệ sinh thái chạy độc lập với thư viện bên ngoài.
- **Thực hiện**:
  1. Thêm Unit test trong `tests/test_schema_registry.py` kiểm tra: khi giả lập `HAS_PYDANTIC = False`, hàm `get_schema(gm)` vẫn trả về đầy đủ 7/7 schema hợp lệ với các trường bắt buộc (`properties`, `required`, `type`).
  2. Thêm test kiểm tra `SettingsManager.get_all()`, `set_api_keys()`, `save()`.
  3. Thêm test kiểm tra `IPCRouter` xử lý an toàn khi client gửi payload `action` dạng dict.
  4. Đảm bảo toàn bộ test suite (>= 86 tests) đạt **100% PASS**.

### Nhiệm vụ 5: Kiểm định E2E Trình duyệt & Xác minh Thị giác (Skills: `playwright-mcp`, `front-end-checklist`)
- **Mục tiêu**: Xác minh trải nghiệm người dùng không còn gặp lỗi `Unknown gamemode`.
- **Thực hiện**:
  1. Chạy kịch bản Playwright E2E mô phỏng thao tác lấy mẫu và bấm **"Tạo bài"** cho cả `fill_blank`, `cloze` và `translation`.
  2. Chụp ảnh màn hình kiểm chứng kết quả render thành công của các game mode.

### Nhiệm vụ 6: Đồng bộ Add-on sang Anki Desktop (Skills: `coding-discipline`)
- **Mục tiêu**: Cập nhật file sạch vào môi trường Anki Desktop thực tế.
- **Thực hiện**:
  1. Sao chép các tệp mã nguồn sạch sang `%APPDATA%\Anki2\addons21\AI_Learning_Hub\`.
  2. Tuân thủ tuyệt đối quy tắc: **Không đóng gói `.ankiaddon`**.

---

## 4. Kế Hoạch Xác Minh (Verification Plan)

### Kiểm thử tự động (Automated Tests)
```bash
python -B -m unittest discover -s tests -p "test_*.py" -v
```
- Yêu cầu: Tất cả các bài kiểm thử đều PASS (0 failures, 0 errors).

### Kiểm định log Anki thực tế
- Sau khi khởi động lại Anki hoặc mở Hub, kiểm tra `user_files/ai_hub.log`:
  - Không còn dòng `[WARN] [AIHub] No schema for gamemode: ...`.
  - Không còn dòng `[ERROR] [AIHub] Bridge error: unhashable type: 'dict'`.
  - Không còn dòng `[ERROR] [AIHub] IPCRouter dispatch error: 'SettingsManager' object has no attribute 'get_all'`.
- Giao diện Anki hiển thị bài tập hoàn chỉnh khi bấm "Tạo bài".
