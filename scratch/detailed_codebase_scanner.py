import ast
import json
import os
import re

REPO = r"D:\GithubDesktopClone\Anki_AI_Learning_Hub"

findings = []


def add_finding(file_path, line_no, err_type, desc, old_code, fixed_code):
    rel = os.path.relpath(file_path, REPO).replace("\\", "/")
    findings.append({
        "location": f"[{rel} - Dòng {line_no}]",
        "type": f"Loại lỗi: {err_type}",
        "desc": f"Mô tả: {desc}",
        "old_code": old_code,
        "fixed_code": fixed_code
    })


# 1. Inspect app.js lines 3415-3425 for duplicate IIFE closing syntax
app_path = os.path.join(REPO, "web", "js", "app.js")
with open(app_path, "r", encoding="utf-8") as f:
    app_lines = f.readlines()

for idx, line in enumerate(app_lines):
    if line.strip() == "};" and idx + 1 < len(app_lines) and app_lines[idx + 1].strip() == "})();":
        add_finding(
            app_path,
            idx + 1,
            "Cú pháp",
            "Dấu `};` thừa kết thúc khối lệnh trước `})();` gây lỗi cú pháp (SyntaxError) trong trình duyệt Strict Mode của QtWebEngine, làm ngắt quãng toàn bộ quá trình nạp `app.js` làm treo màn hình Boot Overlay vĩnh viễn.",
            "  return appObj;\n};\n})();",
            "  return appObj;\n})();"
        )

# 2. Inspect app.js line 924 cancelGen ID mismatch
for idx, line in enumerate(app_lines):
    if "document.querySelector('#cancel-gen')" in line:
        add_finding(
            app_path,
            idx + 1,
            "Kiểu dữ liệu / Phụ thuộc DOM",
            "Thao tác DOM truy vấn `#cancel-gen` không có trong HTML/template làm trả về null. Cần bọc null guard an toàn.",
            "const cancelGen = document.querySelector('#cancel-gen');\nif (cancelGen) { cancelGen.onclick = ... }",
            "const cancelGen = document.querySelector('#loading-cancel-btn');\nif (cancelGen) { cancelGen.onclick = ... }"
        )

# 3. Inspect ui/main_window.py for background task return typing
mw_path = os.path.join(REPO, "ui", "main_window.py")
with open(mw_path, "r", encoding="utf-8") as f:
    mw_lines = f.readlines()

for idx, line in enumerate(mw_lines):
    if "def _on_bridge_cmd(self, cmd: str)" in line:
        if "-> str:" not in line:
            add_finding(
                mw_path,
                idx + 1,
                "Kiểu dữ liệu",
                "Thiếu return type annotation `-> str` cho phương thức `_on_bridge_cmd`.",
                line.strip(),
                "def _on_bridge_cmd(self, cmd: str) -> str:"
            )

# 4. Inspect core/engine.py handlers type hints
engine_path = os.path.join(REPO, "core", "engine.py")
with open(engine_path, "r", encoding="utf-8") as f:
    engine_lines = f.readlines()

for idx, line in enumerate(engine_lines):
    if line.strip().startswith("def _handle_") and "->" not in line:
        add_finding(
            engine_path,
            idx + 1,
            "Kiểu dữ liệu",
            f"Thiếu type annotation `-> dict` cho handler `{line.strip().split('(')[0]}`.",
            line.strip(),
            line.strip().replace("):", ") -> dict:")
        )

# Save scanner output
scratch_report = os.path.join(REPO, "scratch", "findings_report.json")
with open(scratch_report, "w", encoding="utf-8") as f:
    json.dump(findings, f, ensure_ascii=False, indent=2)

print(f"Detailed scanner completed. Total findings: {len(findings)}")
