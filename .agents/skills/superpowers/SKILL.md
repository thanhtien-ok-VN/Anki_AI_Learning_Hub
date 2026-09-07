---
name: superpowers-methodology
description: "Quy trình phát triển phần mềm chuẩn kỹ nghệ sử dụng Superpowers, bao gồm Planning, TDD, Git Worktrees và Code Review."
---

# Quy Trình Phát Triển Phần Mềm Kỹ Nghệ (Superpowers Methodology)

Tài liệu này tích hợp phương pháp luận phát triển phần mềm có kỷ luật của Superpowers vào quy trình làm việc của AI Agent trong dự án này.

## 1. Nguyên Tắc Cốt Lõi (Core Directives)
- **Kiểm tra Kỹ năng trước:** Trước khi bắt đầu bất kỳ nhiệm vụ nào, AI Agent phải kiểm tra xem có Kỹ năng (Skill) nào phù hợp trong thư mục `AI_Skills/` hay không.
- **Tuân thủ Chu trình:** Không được bỏ qua các bước Thiết kế -> Lập kế hoạch -> Viết kiểm thử (TDD) -> Viết code -> Đánh giá mã nguồn (Review).

## 2. Các Bước Thực Hiện Chi Tiết

### Bước 1: Brainstorming, Định Hướng & Chốt Thiết Kế (Design & Direction Alignment)
- Thảo luận với người dùng về yêu cầu bài toán, đặc biệt là hướng đi và kiến trúc của giải pháp.
- Đưa ra ít nhất 2 phương án giải quyết (nếu có) kèm phân tích ưu/nhược điểm của từng hướng để người dùng chọn lựa hướng đi cụ thể.
- **Không tự ý giả định hoặc quyết định hướng đi:** Bắt buộc hỏi ý kiến người dùng về hướng đi trước khi quyết định chọn giải pháp cụ thể.
- Ghi nhận tài liệu thiết kế sơ bộ và thảo luận thống nhất hướng đi với người dùng.

### Bước 2: Lập Kế Hoạch & Xác Nhận Triển Khai (Planning & Confirmation)
- Tạo hoặc cập nhật tệp kế hoạch triển khai `implementation_plan.md` và danh sách việc cần làm `task.md`.
- Chia nhỏ công việc thành các tác vụ độc lập, dễ kiểm soát (bite-sized tasks).
- **Yêu cầu xác nhận từ người dùng:** Bắt buộc trình bày kế hoạch và nhận được sự phê duyệt hoặc xác nhận đồng ý triển khai từ người dùng trước khi thực hiện bất kỳ chỉnh sửa nào lên mã nguồn.

### Bước 3: Tạo Nhánh Cách Ly (Git Worktrees)
- Sử dụng Git branch hoặc Git worktree để thực hiện thay đổi trên nhánh độc lập, tránh sửa trực tiếp trên nhánh chính (`main`/`master`) khi chưa kiểm thử.

### Bước 4: Lập Trình Hướng Kiểm Thử (Test-Driven Development - TDD)
- Áp dụng chu trình **Red-Green-Refactor**:
  1. **Red:** Viết unit test cho tính năng mới và chạy thử để xác nhận test lỗi (failing test).
  2. **Green:** Viết lượng code tối thiểu cần thiết để bài test vượt qua (passing test).
  3. **Refactor:** Tối ưu hóa code, cấu trúc lại sạch sẽ mà không làm hỏng bài test.

### Bước 5: Đánh Giá Mã Nguồn (Code Review & Verification)
- Chạy toàn bộ các bài kiểm thử tự động của dự án.
- Tự rà soát lại mã nguồn dựa trên các tiêu chuẩn trong `CLAUDE.md`.
- Tạo tài liệu bàn giao `walkthrough.md` liệt kê các thay đổi và kết quả kiểm thử.

## 3. Cách Tùy Biến Cho Dự Án Phi Lập Trình (Non-Coding)
- Nếu dự án chỉ liên quan đến viết tài liệu, thiết kế UI/UX hoặc cấu hình:
  - Bỏ qua các bước liên quan đến TDD và kiểm thử tự động.
  - Áp dụng nghiêm ngặt bước **Brainstorming & Chốt Thiết Kế** và **Lập Kế Hoạch Triển Khai** để đảm bảo cấu trúc nội dung và phong cách trình bày đồng nhất.
- Khai báo các ngoại lệ này rõ ràng trong file `CLAUDE.md` của dự án.
