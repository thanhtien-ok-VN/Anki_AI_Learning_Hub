# Quy trình Đánh Giá Ý Tưởng (Idea Assessment Workflow)

Quy trình 5 bước độc lập từ **GitHub Spec Kit** giúp biến ý tưởng sơ khai thành quyết định triển khai chính xác có căn cứ dữ liệu.

---

## 1. Bước 1: Tiếp Nhận (Intake)
* Tiếp nhận mô tả ý tưởng thô từ người dùng hoặc stakeholder.
* Ghi lại bối cảnh, đối tượng hưởng lợi và mục tiêu mong đợi ban đầu vào `specs/ideas/<slug>/intake.md`.

---

## 2. Bước 2: Nghiên Cứu (Research)
* **Thu thập bằng chứng hỗ trợ & phản biện:**
  * Có giải pháp mã nguồn mở hoặc thư viện có sẵn nào giải quyết bài toán này không?
  * Đánh giá rủi ro kỹ thuật, tính tương thích với tech stack hiện có và chi phí bảo trì dài hạn.
  * Phân tích các sản phẩm/đối thủ tương tự trên thị trường.

---

## 3. Bước 3: Định Nghĩa (Define)
* Xác định rõ bài toán cốt lõi cần giải quyết (Problem Statement).
* Đặt ra các mục tiêu rõ ràng (Goals) và những điều không thuộc phạm vi giải quyết (Non-Goals).
* Thiết lập các chỉ số đo lường thành công (Success Metrics / KPIs).

---

## 4. Bước 4: Định Hình Giải Pháp (Shape)
* Phác thảo 2-3 phương án kiến trúc/giải pháp khả thi.
* Phân tích điểm mạnh, điểm yếu, chi phí và sự đánh đổi (Trade-offs) của từng phương án.

---

## 5. Bước 5: Quyết Định (Decide)
Đưa ra kết luận minh bạch kèm tài liệu giải trình:
* **🟢 GO:** Ý tưởng khả thi và có giá trị cao → Chuyển sang chu trình **Spec-Driven Development (Pha 1: Specify)** để tạo PRD và bắt đầu lập trình.
* **🟡 NEEDS CLARIFICATION:** Cần bổ sung thêm dữ liệu nghiên cứu hoặc làm rõ các ràng buộc kỹ thuật/nghiệp vụ.
* **🔴 KILL:** Không khả thi về mặt kỹ thuật, chi phí vượt quá lợi ích hoặc vi phạm Hiến pháp dự án → Dừng lại để tiết kiệm nguồn lực.
