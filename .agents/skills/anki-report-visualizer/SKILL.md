---
name: anki-report-visualizer
description: >-
  Kỹ năng tạo báo cáo Dashboard HTML tương tác, tự thân (self-contained) phục vụ việc kiểm toán dữ liệu Anki trước khi di chuyển. Tích hợp Chart.js hiển thị biểu đồ phân bổ Band CEFR, ma trận chủ đề, bảng lọc các từ trùng lặp và mô phỏng cây Deck phân cấp để người dùng xem trước và phê duyệt.
---

# Anki Report Visualizer (Báo Cáo Kiểm Toán Dữ Liệu & Dashboard Trực Quan)

Kỹ năng này chịu trách nhiệm chuyển hóa toàn bộ dữ liệu trích xuất và kết quả phân loại thô thành một Dashboard HTML hiện đại, trực quan, cho phép người dùng kiểm toán dữ liệu và phê duyệt phương án di chuyển trước khi hệ thống thực hiện bất kỳ lệnh ghi nào trên Anki.

---

## 1. Nguyên Tắc Thiết Kế Dashboard

1. **Độc lập và Tự thân (Self-contained):**
   - File HTML duy nhất (`reports/audit_dashboard.html`), có thể mở trực tiếp trên bất kỳ trình duyệt nào mà không cần cài đặt Node.js hay web server.
   - Nhúng trực tiếp thư viện CSS hiện đại (Inter font, Tailwind CDN hoặc Vanilla CSS kính mờ/glassmorphism) và thư viện biểu đồ nhẹ (Chart.js CDN).

2. **Minh bạch & Đầy đủ Dữ liệu (Transparency):**
   - Hiển thị đầy đủ con số tổng thể và chi tiết từng nhóm dữ liệu.
   - Cung cấp ô tìm kiếm nhanh (live search) để người dùng có thể gõ bất kỳ từ vựng nào kiểm tra xem từ đó đã được gán đúng Band và Topic hay chưa.

---

## 2. Cấu Trúc Thành Phần Giao Diện Dashboard

Dashboard bao gồm 4 khu vực chính:

```text
+-----------------------------------------------------------------------------------+
|  HEADER: TỔNG QUAN DỰ ÁN TÁI CẤU TRÚC DỮ LIỆU ANKI (Tổng Notes, Cards, Media)       |
+-----------------------------------------------------------------------------------+
|  METRIC CARDS: [22,898 Notes] | [19,250 Từ Độc Bản] | [3,648 Từ Trùng Lặp]        |
+-------------------------------------------------+---------------------------------+
|  BIỂU ĐỒ TRÒN: PHÂN BỔ CEFR BAND (A1 -> C2)    | BIỂU ĐỒ CỘT: 14 CHỦ ĐỀ ACADEMIC |
+-------------------------------------------------+---------------------------------+
|  MÔ PHỎNG CÂY THƯ MỤC DECK MỚI (Tree View: English::01_Topics::...)               |
+-----------------------------------------------------------------------------------+
|  BẢNG TRA CỨU TỪ TRÙNG LẶP & ĐỐI SOÁT LỊCH SỬ HỌC (Interactive Table)             |
+-----------------------------------------------------------------------------------+
```

### Thành phần 1: Thẻ Chỉ số Tổng quan (Metric Cards)
- Tổng số Note & Card quét được trong deck mục tiêu.
- Số lượng từ vựng độc bản (Unique Keywords).
- Số lượng từ vựng phát hiện bị trùng lặp nhiều lần (Duplicates).
- Dung lượng ước tính của tệp Media liên quan.

### Thành phần 2: Biểu Đồ Phân Bổ CEFR & Topic (Chart.js)
- **Doughnut Chart:** Tỷ lệ % và số lượng từ thuộc các cấp độ: A1, A2, B1, B2, C1, C2 và Nhóm đặc thù (Chưa phân nhóm).
- **Bar Chart:** Xếp hạng các chủ đề từ vựng từ nhiều nhất đến ít nhất trong 14 Topics lớn.

### Thành phần 3: Mô Phỏng Cây Thư Mục Deck Mới (Deck Tree Preview)
- Hiển thị danh sách các Deck con dự kiến sẽ được tạo tự động trên Anki.
- Cho phép người dùng click để mở rộng/thu gọn và xem số lượng thẻ dự kiến được chuyển vào từng deck.

### Thành phần 4: Bảng Kiểm Toán Từ Trùng Lặp (Duplicates Inspector)
- Hỗ trợ phân trang, lọc theo subdeck gốc hoặc tìm kiếm từ khóa.
- Hiển thị so sánh rõ ràng: Thẻ chính (có số lần học cao nhất) vs Thẻ phụ (các bản sao ở subdeck khác) kèm ngữ cảnh câu ví dụ.
