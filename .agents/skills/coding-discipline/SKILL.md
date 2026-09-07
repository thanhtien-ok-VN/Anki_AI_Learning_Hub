---
name: coding-discipline
description: "Bộ quy tắc hướng dẫn lập trình có kỷ luật, tối giản hóa cấu trúc code và đảm bảo chất lượng kiểm thử."
---

# Lập Trình Kỷ Luật & Tối Giản (Coding Discipline)

Tập hợp các hướng dẫn hành vi để tránh các lỗi logic, giả định sai và code quá phức tạp.

## 1. Nguyên Tắc Lập Trình Sạch
- **Nghĩ trước khi viết:** Luôn đặt câu hỏi: "Có cách nào giải quyết bài toán này đơn giản hơn không?".
- **Tránh tối ưu hóa sớm (Premature Optimization):** Không cấu trúc code cho các kịch bản chưa xảy ra.
- **Độc lập và cô lập:** Mỗi hàm chỉ nên làm một nhiệm vụ duy nhất (Single Responsibility Principle).

## 2. Kiểm Soát Phản Hồi Từ Người Dùng
- Nếu yêu cầu của người dùng có thể hiểu theo nhiều nghĩa khác nhau hoặc cần lựa chọn giải pháp, **bắt buộc** phải dừng lại để thảo luận hướng đi.
- **Bắt buộc** có sự đồng ý hoặc xác nhận của người dùng sau khi đã lập kế hoạch rõ ràng trước khi thực hiện bất kỳ chỉnh sửa nào lên mã nguồn.
- Luôn báo cáo, giải trình và liệt kê các file sẽ thay đổi trước khi thực hiện viết code thực tế.

## 3. Cách Viết Code
- Ưu tiên viết code dễ đọc hơn code ngắn gọn nhưng khó hiểu.
- Loại bỏ code dư thừa hoặc các thư viện không cần thiết.
