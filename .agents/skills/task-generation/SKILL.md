---
name: task-generation
description: >-
  Phân tích yêu cầu, phân rã công việc thành các tasks độc lập, thiết lập độ ưu tiên và tiêu chí nghiệm thu rõ ràng theo mô hình Agile/SDD.
---
# Task Generation & Requirement Decomposition

## Triggers
- Kích hoạt khi tiếp nhận dự án mới, tính năng mới hoặc yêu cầu phân rã công việc trước khi triển khai.

## Guidelines
1. Phân tích tài liệu thiết kế (PRD) hoặc yêu cầu thô của người dùng.
2. Chia nhỏ thành các Tasks độc lập có phạm vi cụ thể (không vượt quá 100 dòng code mỗi task nếu có thể).
3. Mỗi Task cần định rõ:
   - **Mục tiêu:** Đầu ra mong muốn là gì.
   - **Độ ưu tiên:** High (bắt buộc), Medium (cải tiến), Low (thêm sau).
   - **Tiêu chí nghiệm thu (Acceptance Criteria):** Cách kiểm tra task đã hoàn thành.
4. Sắp xếp các task theo thứ tự phụ thuộc (dependency tree) - cái nào làm trước, cái nào làm sau.

