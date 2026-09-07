"""
Script dong bo truc tiep ma nguon sach vao thu muc Add-on cua Anki Desktop phuc vu kiem thu.
Khong dong goi, khong tao file zip/ankiaddon, giup kiem thu nhanh chong.
"""
import os
import shutil
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPDATA = os.environ.get("APPDATA")

if not APPDATA:
    print("❌ ERROR: Khong tim thay bien moi truong APPDATA!")
    sys.exit(1)

ANKI_ADDON_DIR = os.path.join(APPDATA, "Anki2", "addons21", "AI_Learning_Hub")

PRODUCT_FILES = ["__init__.py", "manifest.json", "config.json", "config.md"]
PRODUCT_DIRS = ["core", "gamemodes", "llm", "lang", "prompts", "ui", "web"]

def sync():
    print(f"🔄 Dang dong bo ma nguon vao Anki Add-on:")
    print(f"   -> {ANKI_ADDON_DIR}")
    os.makedirs(ANKI_ADDON_DIR, exist_ok=True)

    # 1. Copy files
    for f in PRODUCT_FILES:
        src = os.path.join(REPO_ROOT, f)
        dst = os.path.join(ANKI_ADDON_DIR, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)

    # 2. Copy directories
    for d in PRODUCT_DIRS:
        src_dir = os.path.join(REPO_ROOT, d)
        dst_dir = os.path.join(ANKI_ADDON_DIR, d)
        if os.path.exists(src_dir):
            if os.path.exists(dst_dir):
                shutil.rmtree(dst_dir)
            shutil.copytree(
                src_dir,
                dst_dir,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "*.tmp")
            )

    print("✅ Dong bo thanh cong vao Anki! Hay khoi dong lai Anki Desktop de kiem thu.")

if __name__ == "__main__":
    sync()
