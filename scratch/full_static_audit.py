import ast
import json
import os
import re

REPO = r"D:\GithubDesktopClone\Anki_AI_Learning_Hub"

issues = []


def report(file_path, line_no, issue_type, desc, old_code, fixed_code):
    rel_path = os.path.relpath(file_path, REPO)
    issues.append({
        "file": rel_path.replace("\\", "/"),
        "line": line_no,
        "type": issue_type,
        "description": desc,
        "old_code": old_code,
        "fixed_code": fixed_code
    })


print("=== COMPREHENSIVE STATIC AUDIT STARTED ===")

# --- 1. AUDIT JS FILES ---
js_app_path = os.path.join(REPO, "web", "js", "app.js")
js_bridge_path = os.path.join(REPO, "web", "js", "bridge.js")
js_utils_path = os.path.join(REPO, "web", "js", "utils.js")
js_hint_path = os.path.join(REPO, "web", "js", "hint_system.js")
index_html_path = os.path.join(REPO, "web", "index.html")

with open(index_html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Collect static IDs in HTML
html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html_content))

with open(js_app_path, "r", encoding="utf-8") as f:
    app_lines = f.readlines()
app_content = "".join(app_lines)

# Scan app.js for document.querySelector('#id') where id is NOT in HTML and NOT in shell template
shell_match = re.search(r"root\.innerHTML\s*=\s*`([^`]+)`", app_content)
shell_template = shell_match.group(1) if shell_match else ""

dynamic_ids = set(re.findall(r'id=["\']([^"\']+)["\']', shell_template))
all_known_ids = html_ids.union(dynamic_ids)

# Check document.querySelector calls in app.js
qs_matches = re.finditer(r"document\.querySelector(?:All)?\(['\"]#([a-zA-Z0-9_-]+)['\"]\)", app_content)
for m in qs_matches:
    target_id = m.group(1)
    # Find line number
    pos = m.start()
    line_no = app_content[:pos].count("\n") + 1
    # If ID is not in static HTML or shell template, check if dynamic in game templates
    if target_id not in all_known_ids and not re.search(rf'id=["\']{target_id}["\']', app_content):
        line_text = app_lines[line_no - 1].strip()
        report(
            js_app_path,
            line_no,
            "Kiểu dữ liệu / Phụ thuộc DOM",
            f"Thao tác DOM chọn `#${target_id}` nhưng ID này không xuất hiện trong HTML tĩnh hoặc template động.",
            line_text,
            f"// Thêm null guard `if (document.querySelector('#{target_id}')) ...`"
        )

# --- 2. AUDIT PYTHON ENGINE HANDLERS & TYPE ANNOTATIONS ---
engine_path = os.path.join(REPO, "core", "engine.py")
with open(engine_path, "r", encoding="utf-8") as f:
    engine_lines = f.readlines()
engine_content = "".join(engine_lines)

# Check for unhandled exceptions or missing type annotations in Engine handlers
for idx, line in enumerate(engine_lines):
    line_no = idx + 1
    if line.strip().startswith("def _handle_") and "->" not in line:
        report(
            engine_path,
            line_no,
            "Kiểu dữ liệu",
            f"Thiếu khai báo type annotation cho return value của handler {line.strip().split('(')[0]}",
            line.strip(),
            line.strip().replace("):", ") -> dict:")
        )

# --- 3. AUDIT MAIN_WINDOW.PY ---
mw_path = os.path.join(REPO, "ui", "main_window.py")
with open(mw_path, "r", encoding="utf-8") as f:
    mw_lines = f.readlines()
mw_content = "".join(mw_lines)

for idx, line in enumerate(mw_lines):
    line_no = idx + 1
    if "mw.taskman.run_in_background" in line and "on_done" not in mw_lines[idx+1]:
        # check type handling
        pass

# Output summary
print(f"Total audit issues identified: {len(issues)}")
report_out_path = os.path.join(REPO, "scratch", "static_audit_final.json")
with open(report_out_path, "w", encoding="utf-8") as f:
    json.dump(issues, f, ensure_ascii=False, indent=2)
