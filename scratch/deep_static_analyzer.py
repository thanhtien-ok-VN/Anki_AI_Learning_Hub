import ast
import json
import os
import re
import sys

REPO = r"D:\GithubDesktopClone\Anki_AI_Learning_Hub"

report = []


def add_issue(file_path, line_no, issue_type, desc, old_code, fixed_code):
    rel_path = os.path.relpath(file_path, REPO)
    report.append({
        "file": rel_path,
        "line": line_no,
        "type": issue_type,
        "description": desc,
        "old_code": old_code,
        "fixed_code": fixed_code
    })


print("=== DEEP STATIC ANALYSIS STARTED ===")

# 1. ANALYZE PYTHON SYNTAX & IMPORTS & SIGNATURES
py_files = []
for root, dirs, files in os.walk(REPO):
    if ".git" in root or "__pycache__" in root or ".venv" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            py_files.append(os.path.join(root, f))

for py_file in py_files:
    try:
        with open(py_file, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code, filename=py_file)
    except SyntaxError as se:
        lines = code.splitlines()
        old_line = lines[se.lineno - 1] if se.lineno and se.lineno <= len(lines) else ""
        add_issue(py_file, se.lineno or 1, "Cú pháp", f"Lỗi cú pháp Python: {se.msg}", old_line, "# Corrected syntax")
    except Exception as e:
        add_issue(py_file, 1, "Cú pháp", f"Không thể parse file Python: {e}", "", "")

# 2. ANALYZE JS SYNTAX & MATCHING BRACKETS & UNDEFINED REFS
js_files = [
    os.path.join(REPO, "web", "js", "bridge.js"),
    os.path.join(REPO, "web", "js", "utils.js"),
    os.path.join(REPO, "web", "js", "hint_system.js"),
    os.path.join(REPO, "web", "js", "app.js"),
]

for js_file in js_files:
    if not os.path.exists(js_file):
        continue
    with open(js_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    content = "".join(lines)

    # Bracket matching analyzer
    stack = []
    in_string = None
    escaped = False
    in_comment = False

    for idx, line in enumerate(lines):
        line_no = idx + 1
        for col, ch in enumerate(line):
            if escaped:
                escaped = False
                continue
            if ch == '\\':
                escaped = True
                continue
            if in_comment:
                if ch == '\n':
                    in_comment = False
                continue

            if in_string:
                if ch == in_string:
                    in_string = None
                continue

            if ch in ('"', "'", '`'):
                in_string = ch
                continue

            if ch in ('(', '{', '['):
                stack.append((ch, line_no, col + 1, line.strip()))
            elif ch in (')', '}', ']'):
                expected = {'(': ')', '{': '}', '[': ']'}[stack[-1][0]] if stack else None
                if not stack or ch != expected:
                    add_issue(
                        js_file,
                        line_no,
                        "Cú pháp",
                        f"Ngoặc đóng '{ch}' không khớp. Kỳ vọng '{expected}' (mở tại dòng {stack[-1][1] if stack else 'N/A'})",
                        line.strip()[:80],
                        "// Corrected bracket matching"
                    )
                else:
                    stack.pop()

    if stack:
        for item in stack[:5]:
            add_issue(
                js_file,
                item[1],
                "Cú pháp",
                f"Ngoặc mở '{item[0]}' chưa được đóng",
                item[3][:80],
                "// Close bracket"
            )

# 3. RPC CONTRACT MATCHING BETWEEN JS AND PYTHON
js_actions = set()
for js_file in js_files:
    if not os.path.exists(js_file):
        continue
    with open(js_file, "r", encoding="utf-8") as f:
        text = f.read()
    # Find Bridge.sendAsync('action') or Bridge.send('action')
    matches = re.findall(r"Bridge\.send(?:Async)?\(\s*['\"]([^'\"]+)['\"]", text)
    for m in matches:
        js_actions.add(m)

py_engine_file = os.path.join(REPO, "core", "engine.py")
py_actions = set()
with open(py_engine_file, "r", encoding="utf-8") as f:
    engine_text = f.read()

# Extract handlers dictionary in handle_js_message
handler_matches = re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]:\s*self\._handle_", engine_text)
for h in handler_matches:
    py_actions.add(h)

missing_in_py = js_actions - py_actions
print(f"JS Actions: {sorted(list(js_actions))}")
print(f"Py Actions: {sorted(list(py_actions))}")
print(f"Missing in Python handlers: {missing_in_py}")

for missing in missing_in_py:
    add_issue(
        py_engine_file,
        236,
        "Cú pháp / Logic",
        f"Lớp RPC Frontend gọi action '{missing}' nhưng backend Python engine.py chưa đăng ký handler",
        f'"{missing}": missing',
        f'"{missing}": self._handle_{missing},'
    )

# Write report JSON to scratch
scratch_path = os.path.join(REPO, "scratch", "analysis_report.json")
os.makedirs(os.path.dirname(scratch_path), exist_ok=True)
with open(scratch_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"Analysis finished! Issues found: {len(report)}")
