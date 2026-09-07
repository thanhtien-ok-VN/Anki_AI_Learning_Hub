---
name: front-end-checklist
description: Comprehensive Front-End Quality and Pre-launch Audit System containing 385 rules across 11 categories (HTML, CSS, JavaScript, Performance, Accessibility/a11y, SEO, Security, Images, Testing, Privacy, i18n). Use whenever conducting frontend code reviews, pre-deployment audits, accessibility checks (WCAG 2.1), performance optimization (Core Web Vitals), SEO validation, or frontend security hardening.
argument-hint: "[category | rule | audit]"
license: MIT
---

# Front-End Checklist: Quality & Pre-Launch Audit System

Hệ thống tiêu chuẩn và kiểm định chất lượng Front-End toàn diện với **385 quy tắc kỹ thuật** trên **11 danh mục** chuẩn hóa từ [frontendchecklist.io](https://frontendchecklist.io) (tác giả David Dias).

---

## 1. NGUYÊN TẮC BẮT LỖI CHUẨN XÁC (Audit Stance & Anti-False Positives)

Để tránh bắt bẻ thừa thãi hoặc sinh lỗi giả (False Positives), AI Agent **BẮT BUỘC** tuân thủ các nguyên tắc sau:

1. **Thận trọng & Thực tế (Be Conservative):** Chỉ báo cáo vấn đề khi mã nguồn hoặc giao diện thực tế thể hiện rõ ràng vi phạm. Ưu tiên 1-2 phát hiện quan trọng nhất có bằng chứng xác thực thay vì liệt kê hàng loạt phỏng đoán.
2. **Phân biệt ngữ cảnh Component vs Toàn trang:** Không coi đoạn mã React/JSX/Vue nhỏ lẻ là một tài liệu HTML hoàn chỉnh. Không bắt bẻ thiếu thẻ `<html>`, `<head>`, hay `<!DOCTYPE>` trên các component con.
3. **Nhận diện Next.js App Router & React 19:** Khi audit các tệp `page.tsx` / `layout.tsx`, luôn kiểm tra `export const metadata`, `export const viewport`, hoặc hàm `generateMetadata()` trước khi kết luận thiếu thẻ meta.
4. **Không bắt lỗi ảnh trang trí (Decorative Images):** Thẻ `<img ... alt="" aria-hidden="true">` là chuẩn mực tiếp cận cho hình ảnh trang trí thuần túy. Không bắt đặt text mô tả và không bắt lazy-load cho các icon SVG nhỏ.
5. **Tôn trọng `autocomplete="off"`:** Không tự động coi `autocomplete="off"` là lỗi trừ khi có rủi ro bảo mật hoặc cản trở rõ ràng trải nghiệm điền form của người dùng.

---

## 2. MA TRẬN PHÂN CẤP ƯU TIÊN (Priority Legend)

| Mức Độ Ưu Tiên | Ý Nghĩa Kỹ Thuật | Hành Động Yêu Cầu |
| :--- | :--- | :--- |
| 🚨 **CRITICAL** | Lỗi làm sập giao diện, xung đột mã hóa UTF-8, vi phạm bảo mật nghiêm trọng hoặc sập SEO. | **Bắt buộc khắc phục 100% trước khi deploy.** |
| ⚠️ **HIGH** | Ảnh hưởng lớn đến trải nghiệm người dùng, khả năng tiếp cận (WCAG 2.1), tốc độ Core Web Vitals. | **Bắt buộc xử lý** trong bản phát hành chính thức. |
| 🔵 **MEDIUM** | Các thực hành chuẩn mực tốt nhất (Best Practices) về kiến trúc, form validation, SEO meta. | Nên xử lý trong các đợt Code Review định kỳ. |
| ⚪ **LOW** | Tối ưu hóa nâng cao, cải tiến theo từng ngữ cảnh. | Cải tiến khi có thời gian tối ưu hóa sâu. |

---

## 3. DANH MỤC CẨM NANG CHUYÊN ĐỀ (Reference Guides)

Tra cứu hướng dẫn chi tiết theo từng chuyên đề tại thư mục [references/](file:///d:/AntigravityProject/ThietLapAntigravity/AI_Skills/testing/front-end-checklist/references/):

* 🚨 **[references/critical-preflight.md](file:///d:/AntigravityProject/ThietLapAntigravity/AI_Skills/testing/front-end-checklist/references/critical-preflight.md)**: Danh sách kiểm tra 100% các quy tắc Critical & High bắt buộc phải vượt qua trước khi bàn giao.
* ♿ **[references/accessibility-audit.md](file:///d:/AntigravityProject/ThietLapAntigravity/AI_Skills/testing/front-end-checklist/references/accessibility-audit.md)**: Cẩm nang kiểm tra chuẩn tiếp cận WCAG 2.1 AA/AAA (ARIA, tương phản màu, điều hướng bàn phím).
* 📝 **[references/forms-interaction.md](file:///d:/AntigravityProject/ThietLapAntigravity/AI_Skills/testing/front-end-checklist/references/forms-interaction.md)**: Cẩm nang kiểm định biểu mẫu, autocomplete mật khẩu, aria-live regions, Modal Dialog, Accordion, Tooltip.
* 🎬 **[references/media-motion.md](file:///d:/AntigravityProject/ThietLapAntigravity/AI_Skills/testing/front-end-checklist/references/media-motion.md)**: Cẩm nang tối ưu ảnh AVIF/WebP, responsive srcset, và kiểm soát `prefers-reduced-motion`.
* ⚡ **[references/performance-seo.md](file:///d:/AntigravityProject/ThietLapAntigravity/AI_Skills/testing/front-end-checklist/references/performance-seo.md)**: Cẩm nang tối ưu Core Web Vitals (LCP, CLS, INP), Open Graph, Twitter Cards, Schema.org JSON-LD.
* 🔒 **[references/security-privacy.md](file:///d:/AntigravityProject/ThietLapAntigravity/AI_Skills/testing/front-end-checklist/references/security-privacy.md)**: Cẩm nang bảo mật frontend (Subresource Integrity - SRI, CSP headers, X-Frame-Options, GDPR).

---

## 4. TÍCH HỢP MCP SERVER (Automated Agent Tooling)

Dự án cung cấp endpoint MCP server công khai để tự động tra cứu quy tắc hoặc audit URL:
* **Public MCP Endpoint:** `https://mcp.frontendchecklist.io`
* **Công cụ hữu ích:**
  * `review_code`: Rà soát đoạn code HTML/CSS/JS/React/Next.js dán vào.
  * `audit_url`: Kiểm tra toàn diện một website công khai `https://`.
  * `search_rules`: Tìm kiếm quy tắc theo từ khóa hoặc danh mục.
  * `get_workflow`: Lấy checklist chuyên đề cho ngày release/launch.
