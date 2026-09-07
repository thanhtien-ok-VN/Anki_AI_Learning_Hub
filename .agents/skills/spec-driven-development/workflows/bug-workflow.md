# Quy trình Sửa Lỗi Có Bằng Chứng (Evidence-Based Bug Fix Workflow)

Quy trình 3 bước chuẩn mực từ **GitHub Spec Kit** giúp tránh lỗi "chữa ngọn bỏ gốc" và ngăn ngừa tái phát lỗi.

---

## 1. Pha 1: Đánh Giá Lỗi (Assess)
* **Thu thập dữ liệu thực tế:** Log lỗi, stack trace, môi trường xảy ra lỗi, payload yêu cầu.
* **Tái hiện lỗi (Reproduction):** Viết một kịch bản hoặc unit test nhỏ có thể tái hiện chính xác lỗi (Fail test).
* **Truy tìm nguyên nhân gốc rễ (Root Cause Analysis):**
  * Grep tìm tất cả các hàm gọi (callers) của hàm bị lỗi.
  * Phân tích xem lỗi nằm ở logic chung (shared guard/validation) hay ở dữ liệu đầu vào.
* **Tạo tài liệu chẩn đoán:** Ghi lại kết quả phân tích vào `specs/bugs/<bug-slug>/assess.md`.

---

## 2. Pha 2: Sửa Lỗi Tận Gốc (Fix)
* **Nguyên tắc "Fix Once, Protect All":** Sửa lỗi ngay tại hàm dùng chung hoặc lớp dữ liệu gốc để bảo vệ mọi luồng liên quan, không vá thủ công rải rác ở từng caller.
* **Tối thiểu hóa diff:** Giữ thay đổi gọn gàng, súc tích, không refactor lan man sang các module không liên quan.
* **Bảo toàn tính tương thích ngược (Backward Compatibility):** Đảm bảo không làm hỏng các trường hợp sử dụng bình thường khác.

---

## 3. Pha 3: Kiểm Thử & Nghiệm Thu (Test)
* **Chạy test tái hiện:** Test tái hiện ở Pha 1 phải chuyển từ Đỏ (Fail) sang Xanh (Pass).
* **Kiểm thử hồi quy (Regression Test):** Chạy toàn bộ test suite hiện có để đảm bảo không phát sinh lỗi phụ.
* **Xác nhận nghiệm thu:** Ghi nhận bằng chứng test thành công trước khi đóng ticket bug.
