# Kế hoạch Kỹ thuật: Tích hợp Bộ AI Skills Thiết yếu vào Anki AI Learning Hub

- **Tên nhiệm vụ:** `integrate-essential-skills`
- **Mã nhánh Git:** `feat/integrate-essential-skills`
- **Ngày khởi tạo:** 2026-09-07
- **Trạng thái:** COMPLETE

---

## 1. ĐỐI CHUẨN KIẾN TRÚC & THAM KHẢO DỰ ÁN LỚN (BENCHMARKING)

- **Pattern áp dụng:**
  - **Context Engineering & Skill-Driven Agent Architecture:** Học hỏi mô hình Agent Context Protocol từ Anthropic Model Context Protocol (MCP) và Microsoft Playwright MCP architecture.
  - **Separation of Concerns (SoC):** Tách bạch rõ ràng giữa Core Logic (Python domain), Presentation (HTML5/CSS3 Glassmorphism SPA), Testing & E2E Validation (Playwright MCP, Unittest) và Version Control Governance (Conventional Commits, Branching Strategy).
- **Dự án tham chiếu:**
  - **Microsoft Playwright (`@playwright/mcp`):** Tận dụng Accessibility Tree Snapshots thay vì xử lý raw image từ Vision models, giúp kiểm thử tự động UI trong Anki WebView với độ chính xác cao và chi phí token thấp.
  - **Frontend Checklist (frontendchecklist.io):** Quy chuẩn 385 điểm kiểm tra pre-launch đảm bảo khả năng tiếp cận WCAG 2.2, zero memory leak và UTF-8/i18n integrity.
  - **Conventional Commits 1.0.0 & Angular Git Guidelines:** Tiêu chuẩn hóa commit log phục vụ tự động hóa changelog và truy vết phiên bản.
- **Đánh giá Trade-off:**
  - *Lý do chọn tích hợp cục bộ trong `.agents/skills/`:* Mỗi dự án Anki addon có môi trường độc lập, không phụ thuộc vào global machine config, dễ dàng đóng gói và di chuyển giữa các máy của lập trình viên.
  - *Lý do loại bỏ các skills React/Tailwind/GSAP:* Tránh bloated context, gây hallucination cho AI Agent khi sinh code (dự án dùng thuần Vanilla JS và CSS3 Glassmorphism).

---

## 2. MA TRẬN KỸ NĂNG & CÔNG CỤ (SKILLS & TOOLCHAIN MATRIX)

| Kỹ năng / Công cụ | Danh mục | Mục đích kỹ thuật trong Anki Hub |
| :--- | :--- | :--- |
| **`playwright-mcp`** | `testing` | Kiểm thử E2E tương tác DOM, mô phỏng người dùng chơi 8 game modes và kiểm tra IPC bridge. |
| **`git-conventions`** | `code` | Kiểm soát quy ước phân nhánh, atomic commits chuẩn Conventional Commits kèm rationale *Why*. |
| **`ui-ux-pro-max`** | `design` | Cung cấp design tokens, chuẩn tương phản Glassmorphism, micro-interactions và responsive UI. |
| **`front-end-checklist`**| `testing` | Kiểm định pre-launch 385 tiêu chí: a11y, performance, memory leaks, i18n encoding. |
| **`web-accessibility-wcag`** | `code` | Tối ưu hóa phím tắt bàn phím (Tab, Enter, Space, Escape modal trap) theo chuẩn WCAG 2.2 AA. |
| **`svg-icon-engineering`** | `design` | Chuẩn hóa hệ thống biểu tượng SVG cho game modes, dùng `currentColor` tương thích Dark/Light mode. |
| **`ponytail`** | `rule` | Bổ trợ `karpathy.md`, tư duy kỹ sư senior tinh gọn: YAGNI, ưu tiên standard library, minimal diff. |

---

## 3. DANH SÁCH FILE THAY ĐỔI & TẠO MỚI

### Đã tạo mới (Skills & Rules):
- `[NEW]` `.agents/skills/playwright-mcp/` (toàn bộ cấu trúc từ ThietLapAntigravity)
- `[NEW]` `.agents/skills/git-conventions/` (toàn bộ cấu trúc)
- `[NEW]` `.agents/skills/ui-ux-pro-max/` (toàn bộ cấu trúc)
- `[NEW]` `.agents/skills/front-end-checklist/` (toàn bộ cấu trúc)
- `[NEW]` `.agents/skills/web-accessibility-wcag/` (toàn bộ cấu trúc)
- `[NEW]` `.agents/skills/svg-icon-engineering/` (toàn bộ cấu trúc)
- `[NEW]` `.agents/rules/ponytail.md`

### Đã cập nhật (Documentation & Registry):
- `[MODIFY]` `.agents/AGENTS.md`: Mở rộng bảng tra cứu Skills Index (từ 11 lên 17 skills) và cập nhật rules.
- `[MODIFY]` `.gitignore`: Cho phép theo dõi `.agents/`, `plans/`, `logActivities/` trong git.

---

## 4. MA TRẬN KIỂM THỬ & NGHIỆM THU (TEST MATRIX)

1. **Kiểm tra tính toàn vẹn tập tin (File Integrity):**
   - 17/17 skills có đầy đủ `SKILL.md`.
   - Rule `ponytail.md` tồn tại trong `.agents/rules/`.
2. **Kiểm thử hồi quy Backend Python (Regression Suite):**
   - `python -B -m unittest discover -s tests -p "test_*.py" -v` -> **65/65 tests PASS (100%)**.
3. **Kiểm thử đóng gói Release Addon:**
   - `python scripts/build_addon.py` -> **PASS (100%)**, tạo `dist/AI_Learning_Hub.ankiaddon` và `dist/AI_Learning_Hub.zip`.
