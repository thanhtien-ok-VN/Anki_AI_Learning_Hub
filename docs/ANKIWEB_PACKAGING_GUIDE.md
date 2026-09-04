# Hướng Dẫn Đóng Gói, Tương Thích Đa Nền Tảng & Đẩy Add-on Lên AnkiWeb

> **Dự án**: AI Learning Hub (Anki Add-on)  
> **Tài liệu**: Quy trình chuẩn hóa đóng gói `.ankiaddon`, `.zip` và đăng tải công khai lên AnkiWeb (Anki Shared Add-ons).

---

## 📖 MỤC LỤC
1. [Cấu Trúc Thư Mục Add-on Chuẩn Anki](#1-cấu-trúc-thư-mục-add-on-chuẩn-anki)
2. [Đảm Bảo Tương Thích Tất Cả Thiết Bị (Windows, macOS, Linux, Qt5 & Qt6)](#2-đảm-bảo-tương-thích-tất-cả-thiết-bị)
3. [Script Đóng Gói Tự Động (`scripts/build_addon.py`)](#3-script-đóng-gói-tự-động)
4. [Hướng Dẫn Chi Tiết Đẩy Lên AnkiWeb](#4-hướng-dẫn-chi-tiết-đẩy-lên-ankiweb)
5. [Kiểm Thử & Xác Minh Khi Cài Đặt Sạch](#5-kiểm-thử--xác-minh-khi-cài-đặt-sạch)

---

## 1. Cấu Trúc Thư Mục Add-on Chuẩn Anki

Một Anki Add-on hợp lệ khi nén zip đẩy lên AnkiWeb phải chứa các file gốc ngay tại root của file zip (không lồng trong một thư mục cha):

```plaintext
AI_Learning_Hub/
├── __init__.py          # (Bắt buộc) File khởi tạo chính của Add-on trong Anki
├── manifest.json        # (Khuyên dùng) Metadata định danh gói & phiên bản tương thích
├── config.json          # (Tuỳ chọn) Thiết lập mặc định hiển thị trong Anki Add-on Config
├── config.md            # (Tuỳ chọn) Hướng dẫn người dùng cấu hình add-on
├── core/                # Bộ xử lý trung tâm (Engine, Settings, Logger, i18n, Prompt Manager)
├── gamemodes/           # Logic 8 chế độ chơi AI (Fill Blank, Cloze, Translation, v.v.)
├── llm/                 # Client giao tiếp với Gemini API & Waterfalls
├── lang/                # Catalog đa ngôn ngữ (en.json, vi.json)
├── prompts/             # System prompts cho các game (en/, zh/, common/)
├── ui/                  # Giao diện Qt Native (MainWindow, Dialogs)
└── web/                 # Giao diện HTML5/JS/CSS cho Hub
```

---

## 2. Đảm Bảo Tương Thích Tất Cả Thiết Bị

Để add-on chạy mượt mà trên mọi máy người dùng (Windows, macOS Intel/Apple Silicon, Linux):

### A. Tương thích Qt5 và Qt6
- **Quy tắc**: Tuyệt đối không import trực tiếp `PyQt5` hay `PyQt6`.
- **Cách dùng đúng**:
  ```python
  from aqt.qt import *
  # Hoặc import cụ thể từ wrapper do Anki cung cấp:
  from aqt.qt import QAction, QDialog, QVBoxLayout, QWidget
  ```

### B. An toàn Đường dẫn Hệ điều hành (Cross-Platform Pathing)
- **Quy tắc**: Không sử dụng dấu gạch ngược Windows `\`.
- **Cách dùng đúng**: Dùng `os.path.join()` hoặc dấu gạch chéo `/`:
  ```python
  import os
  addon_dir = os.path.dirname(os.path.abspath(__file__))
  prompt_path = os.path.join(addon_dir, "prompts", "common", "fill_blank.txt")
  ```

### C. Đa luồng Xử lý Giao diện (Background Threads)
- **Quy tắc**: Không chạy tác vụ mạng (API LLM) hoặc tính toán nặng trên Main Thread làm treo UI Anki.
- **Cách dùng đúng**: Dùng `mw.taskman.run_in_background()` hoặc `QueryOp`.

### D. Khai báo Web Exports trong `manifest.json`
- Để Anki WebEngine phục vụ tài nguyên HTML/JS/CSS từ `localhost` trên mọi OS, khai báo trong `manifest.json`:
  ```json
  {
      "name": "AI Learning Hub - 8 Gamified AI Language Games",
      "package": "AI_Learning_Hub",
      "author": "Your Name",
      "version": "2.0.0",
      "min_point_version": 45,
      "description": "8 AI-powered language learning games using Gemini API.",
      "web_exports": ["web/*"]
  }
  ```

---

## 3. Script Đóng Gói Tự Động (`scripts/build_addon.py`)

Kịch bản Python dưới đây sẽ tự động chạy unit test, lọc sạch file rác phát triển, và nén thành 2 file `.zip` (cho AnkiWeb) và `.ankiaddon` (cho cài đặt thử nghiệm):

```python
"""
Script đóng gói Anki Add-on tự động.
Tạo ra file dist/AI_Learning_Hub.zip và dist/AI_Learning_Hub.ankiaddon.
"""
import os
import shutil
import stat
import subprocess
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(REPO_ROOT, "dist")
BUILD_DIR = os.path.join(DIST_DIR, "build_temp")

# Các file và thư mục sản phẩm cần nén
PRODUCT_FILES = ["__init__.py", "manifest.json", "config.json", "config.md"]
PRODUCT_DIRS = ["core", "gamemodes", "llm", "lang", "prompts", "ui", "web"]

# Danh sách loại trừ rác phát triển
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".git*",
    ".codegraph",
    ".agents",
    "node_modules",
    "tests",
    "user_files",  # Không đóng gói file log/cài đặt cá nhân
    ".env",
    "server.ts",
]


def run_tests():
    print("🧪 [1/4] Đang chạy bộ Unit Test Suite (43/43 tests)...")
    res = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
    if res.returncode != 0:
        print("❌ ERROR: Unit tests thất bại! Hủy đóng gói.")
        sys.exit(1)
    print("✅ Unit tests PASS 100%!")


def prepare_build_directory():
    print("📁 [2/4] Chuẩn bị thư mục build sạch...")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, onerror=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))
    os.makedirs(BUILD_DIR, exist_ok=True)

    # Coppy files
    for f in PRODUCT_FILES:
        src = os.path.join(REPO_ROOT, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(BUILD_DIR, f))

    # Copy directories
    for d in PRODUCT_DIRS:
        src_dir = os.path.join(REPO_ROOT, d)
        dst_dir = os.path.join(BUILD_DIR, d)
        if os.path.exists(src_dir):
            shutil.copytree(
                src_dir,
                dst_dir,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
            )
    print("✅ Đã sao chép các thành phần sản phẩm sạch.")


def create_zip_packages():
    print("📦 [3/4] Đang nén gói Add-on chuẩn zip root...")
    zip_path = os.path.join(DIST_DIR, "AI_Learning_Hub.zip")
    ankiaddon_path = os.path.join(DIST_DIR, "AI_Learning_Hub.ankiaddon")

    for p in [zip_path, ankiaddon_path]:
        if os.path.exists(p):
            os.remove(p)

    # Nén nội dung bên trong BUILD_DIR (không nén nguyên thư mục cha)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(BUILD_DIR):
            for file in files:
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, BUILD_DIR)
                zf.write(full_p, rel_p)

    shutil.copy2(zip_path, ankiaddon_path)
    print(f"🎉 [4/4] Hoàn tất đóng gói!")
    print(f"   - File AnkiWeb Upload: {zip_path}")
    print(f"   - File Cài đặt 1-Click: {ankiaddon_path}")


if __name__ == "__main__":
    run_tests()
    prepare_build_directory()
    create_zip_packages()
```

---

## 4. Hướng Dẫn Chi Tiết Đẩy Lên AnkiWeb

Sau khi chạy script đóng gói thu được file `dist/AI_Learning_Hub.zip`, tiến hành đăng tải lên AnkiWeb theo các bước:

### Bước 1: Đăng nhập AnkiWeb
- Truy cập địa chỉ chính thức: [https://ankiweb.net/shared/addons21](https://ankiweb.net/shared/addons21)
- Đăng nhập bằng tài khoản AnkiWeb của bạn.

### Bước 2: Tạo bài đăng Add-on Mới
- Ở góc trên màn hình, chọn **Share Item** ➔ Chọn **Add-on**.

### Bước 3: Điền Thông Tin Bài Đăng
1. **Title**: `AI Learning Hub - 8 Gamified AI Language Games (Gemini Powered)`
2. **Support URL**: dán link GitHub Repository của bạn (VD: `https://github.com/yourusername/Anki_AI_Learning_Hub`)
3. **Description**: Nhập bài viết giới thiệu chi tiết (hỗ trợ Markdown/HTML).
   - Mô tả 8 chế độ chơi (Fill Blank, Cloze, Translation, Taboo, Story, Unscramble, Matching, Sentence Transform).
   - Hướng dẫn nhập API Key miễn phí từ Google AI Studio.
   - Đèn hiệu tính năng (Hỗ trợ Tiếng Việt & Tiếng Anh, Chế độ Offline từ thẻ Anki).
4. **Upload File**: Chọn file `dist/AI_Learning_Hub.zip`.
5. **Supported Versions**: Đánh dấu tích chọn các bản Anki tương thích:
   - `2.1.45+`
   - `2.1.50+ (Qt5 & Qt6)`
   - `23.10+`
   - `24.x+`

### Bước 4: Nhận Mã Add-on Code
- Sau khi nhấn **Share**, AnkiWeb sẽ cấp cho bạn một **Mã Code 9 chữ số** (Ví dụ: `182736450`).
- Người dùng chỉ cần mở Anki ➔ **Tools** ➔ **Add-ons** ➔ **Get Add-ons...** ➔ Nhập mã `182736450` là cài đặt thành công 1-click!

---

## 5. Kiểm Thử & Xác Minh Khi Cài Đặt Sạch

Trước khi publish chính thức, hãy tự cài đặt thử nghiệm trên máy sạch:

1. Mở Anki trên máy của bạn ➔ **Tools** ➔ **Add-ons**.
2. Nhấn nút **Install from file...** (Cài đặt từ file).
3. Trỏ tới file `dist/AI_Learning_Hub.ankiaddon`.
4. Khởi động lại Anki.
5. Mở **Tools ➔ AI Learning Hub...** và trải nghiệm đảm bảo các tính năng hoạt động trơn tru.
