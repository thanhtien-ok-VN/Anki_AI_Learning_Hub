"""
Script đóng gói Anki Add-on tự động cho AI Learning Hub.
Tạo ra file dist/AI_Learning_Hub.zip và dist/AI_Learning_Hub.ankiaddon.
"""
import os
import shutil
import stat
import subprocess
import sys
import zipfile

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(REPO_ROOT, "dist")
BUILD_DIR = os.path.join(DIST_DIR, "build_temp")

# Các file và thư mục sản phẩm cần nén
PRODUCT_FILES = ["__init__.py", "manifest.json", "config.json", "config.md"]
PRODUCT_DIRS = ["core", "gamemodes", "llm", "lang", "prompts", "ui", "web"]


def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def run_tests():
    print("🧪 [1/4] Đang chạy bộ Unit Test Suite (64/64 tests)...")
    res = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        cwd=REPO_ROOT,
    )
    if res.returncode != 0:
        print("❌ ERROR: Unit tests thất bại! Hủy đóng gói.")
        sys.exit(1)
    print("✅ Unit tests PASS 100%!")


def prepare_build_directory():
    print("📁 [2/4] Chuẩn bị thư mục build sạch...")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, onerror=remove_readonly)
    os.makedirs(BUILD_DIR, exist_ok=True)

    # Copy root product files if they exist
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
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "*.log"),
            )
    print("✅ Đã sao chép các thành phần sản phẩm sạch.")


def create_zip_packages():
    print("📦 [3/4] Đang nén gói Add-on chuẩn zip root...")
    zip_path = os.path.join(DIST_DIR, "AI_Learning_Hub.zip")
    ankiaddon_path = os.path.join(DIST_DIR, "AI_Learning_Hub.ankiaddon")

    os.makedirs(DIST_DIR, exist_ok=True)
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

    # Clean up build temp
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, onerror=remove_readonly)

    print("🎉 [4/4] Hoàn tất đóng gói!")
    print(f"   - File AnkiWeb / Zip: {zip_path}")
    print(f"   - File Cài đặt 1-Click Anki: {ankiaddon_path}")


if __name__ == "__main__":
    run_tests()
    prepare_build_directory()
    create_zip_packages()
