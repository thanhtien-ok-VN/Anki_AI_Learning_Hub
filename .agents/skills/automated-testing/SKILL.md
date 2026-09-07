---
name: automated-testing
description: "Quy chuẩn viết và thực thi kiểm thử tự động, đảm bảo chất lượng và độ bao phủ của mã nguồn."
---

# Kiểm Thử Tự Động (Automated Testing)

Bộ hướng dẫn viết test case, mock dữ liệu và chạy thử nghiệm để phát hiện lỗi sớm và ngăn ngừa lỗi cũ quay trở lại (regression).

## 1. Unit Testing (Kiểm thử Đơn vị)
- **Tập trung:** Mỗi test case chỉ nên kiểm tra một hàm hoặc một logic nghiệp vụ cụ thể.
- **Mocking:** Sử dụng mock để cô lập mã nguồn cần test, tránh kết nối thực tế đến cơ sở dữ liệu hoặc gọi API qua mạng.
- **Độ bao phủ (Coverage):** Đảm bảo test được cả các trường hợp chạy bình thường (happy path) và các trường hợp lỗi/ngoại lệ (edge cases/error paths).

## 2. Integration & E2E Testing (Kiểm thử Tích hợp & Hệ thống)
- **Luồng nghiệp vụ:** Kiểm tra sự tương tác giữa các module hoặc luồng đi hoàn chỉnh của người dùng trên giao diện.
- **Tải và Hiệu năng:** Đảm bảo hệ thống phản hồi đúng và ổn định dưới các điều kiện biên của dữ liệu đầu vào.

## 3. Quy Trình Chạy Test
- Luôn chạy lệnh kiểm thử trước khi commit code hoặc đề xuất hoàn thành tác vụ.
- Nếu kiểm thử thất bại, bắt buộc phải sửa code hoặc cập nhật lại test case cho đúng với thiết kế mới trước khi tiếp tục.
