---
name: system-programming
description: "Quy chuẩn lập trình hệ thống, thiết kế API, cấu trúc cơ sở dữ liệu và bảo mật backend."
---

# Lập Trình Hệ Thống & Backend (System Programming)

Bộ hướng dẫn thiết kế và xây dựng các dịch vụ backend hiệu năng cao, bảo mật và dễ mở rộng.

## 1. Thiết Kế API & Dịch Vụ
- **Chuẩn RESTful:** Thiết kế endpoint rõ ràng, sử dụng đúng HTTP Methods (`GET`, `POST`, `PUT`, `DELETE`) và mã trạng thái (HTTP Status Codes).
- **Kiểm soát dữ liệu đầu vào (Input Validation):** Luôn lọc và xác thực dữ liệu gửi lên từ client để tránh các lỗi bảo mật nguy hiểm (như SQL Injection, XSS).

## 2. Quản Lý Cơ Sở Dữ Liệu
- **Tối ưu hóa câu truy vấn:** Sử dụng index đúng cách, tránh truy vấn thừa hoặc truy vấn lặp trong vòng lặp (lỗi N+1 query).
- **Migration:** Mọi thay đổi cấu trúc database phải được thực hiện thông qua các tệp migration rõ ràng, không được sửa trực tiếp trên DB.

## 3. Quản Lý Lỗi & Ghi Log (Error Handling & Logging)
- Không bao giờ nuốt lỗi (empty catch blocks).
- Ghi log (logs) đầy đủ thông tin ngữ cảnh để dễ dàng debug khi hệ thống gặp lỗi trong môi trường Production.
