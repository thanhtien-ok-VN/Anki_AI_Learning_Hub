# Git Conventions & Workflow Management

## Triggers
- Kích hoạt khi có các hành động liên quan đến git: commit, tạo nhánh (branch), đẩy code (push), tạo Pull Request (PR), hoặc viết Release Notes.

## Guidelines
1. **Đặt tên nhánh (Branch naming):**
   - `feature/ten-tinh-nang` cho tính năng mới.
   - `bugfix/ten-loi` cho sửa lỗi.
   - `docs/ten-tai-lieu` cho cập nhật tài liệu.
2. **Chuẩn commit (Conventional Commits):**
   - Định dạng: `<type>(<scope>): <description>`
   - Các type hợp lệ: `feat` (tính năng mới), `fix` (sửa lỗi), `docs` (tài liệu), `style` (định dạng, không ảnh hưởng code), `refactor` (tái cấu trúc), `perf` (hiệu năng), `test` (thêm kiểm thử), `chore` (cập nhật build/dependencies).
3. **Quản lý qua CLI:**
   - Ptruy cập và sử dụng GitHub CLI (`gh`) để quản lý issues, checkout PR, và merge nhánh để giữ tính nhất quán.
