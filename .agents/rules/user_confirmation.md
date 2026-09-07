# Rule: User Confirmation & Direction Alignment

## Metadata
- **name**: user-confirmation-alignment
- **description**: Enforces mandatory user confirmation before implementing any code/config changes and consultation on direction during planning.
- **glob**: "**/*"

## Rule Description
This rule ensures that the AI Agent does not make any unauthorized modifications to the codebase or configuration, and always aligns with the user on design directions and implementation plans before executing them.

### Guidelines
1. **Mandatory Plan & Confirmation**:
   - Trước khi triển khai bất kỳ tác vụ nào (kể cả viết code, sửa cấu hình hoặc tạo file), agent BẮT BUỘC phải tạo/cập nhật `implementation_plan.md` và `task.md`.
   - Agent BẮT BUỘC phải dừng lại và chờ sự xác nhận rõ ràng của người dùng (nút "Proceed" hoặc tin nhắn đồng ý) trước khi tiến hành chỉnh sửa mã nguồn.
2. **Tham vấn hướng đi (Direction Consultation)**:
   - Trong giai đoạn lập kế hoạch, agent phải kết hợp phân tích các hướng giải quyết/kiến trúc khả thi và hỏi ý kiến người dùng để cùng thống nhất hướng đi trước khi quyết định phương án cuối cùng.
3. **Không tự quyết định trong vùng không rõ ràng (No Assumptions)**:
   - Tuyệt đối không tự ý giả định yêu cầu hoặc triển khai ngầm mà không có sự thông qua của người dùng.
