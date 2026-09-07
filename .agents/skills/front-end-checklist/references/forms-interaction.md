# Front-End Checklist: Forms & Interactive Components Audit

Cẩm nang kiểm định biểu mẫu nhập liệu, xác thực người dùng và các linh kiện giao diện tương tác (Tooltips, Accordions, Notifications, Modals).

---

## 1. BIỂU MẪU & XÁC THỰC (Forms & Authentication)

### 1.1. Autocomplete & Password Fields
* **Đăng nhập (Sign In):** Ô mật khẩu đăng nhập phải có `autocomplete="current-password"`.
* **Đăng ký / Đổi mật khẩu (Sign Up / Reset):** Ô mật khẩu mới phải có `autocomplete="new-password"` để trình quản lý mật khẩu (1Password, Bitwarden, Chrome/Apple Keychain) tự động gợi ý mật khẩu mạnh.
* **Thông tin cá nhân:** Sử dụng đúng chuẩn:
  * `autocomplete="email"` cho email.
  * `autocomplete="name"` hoặc `autocomplete="given-name"` / `autocomplete="family-name"`.
  * `autocomplete="tel"`, `autocomplete="address-line1"`, `autocomplete="postal-code"`.

### 1.2. Nút Bấm Trong Form (Explicit Button Types)
* Mọi thẻ `<button>` trong form phải khai báo rõ ràng thuộc tính `type`:
  * `type="submit"` cho nút gửi form.
  * `type="button"` cho các nút phụ (hủy bỏ, toggle password, xóa nội dung) để tránh việc vô tình submit form khi người dùng nhấn Enter.

### 1.3. Thông Báo Lỗi Động & Live Regions
* Khi form xảy ra lỗi validation từ client hoặc server:
  * Đặt `aria-invalid="true"` trên ô nhập liệu có lỗi.
  * Thông báo lỗi phải được liên kết bằng `aria-describedby="field-error-id"`.
  * Khối thông báo lỗi tổng thể phải có `aria-live="polite"` hoặc `role="alert"` để Screen Reader đọc ngay lập tức mà không cần người dùng di chuyển focus.

---

## 2. LINH KIỆN TƯƠNG TÁC (Interactive Widgets)

### 2.1. Accordion / Collapse
* Nút bấm mở accordion phải có `aria-expanded="true|false"` và `aria-controls="accordion-content-id"`.
* Khối nội dung accordion phải có `id="accordion-content-id"` và ẩn đúng cách bằng `hidden` hoặc `display: none` khi đóng.

### 2.2. Modal Dialog
* Thẻ chứa modal phải có `role="dialog"` hoặc sử dụng thẻ HTML5 `<dialog>`, kèm `aria-modal="true"`.
* Modal phải có tiêu đề được gán nhãn qua `aria-labelledby="modal-title-id"`.
* **Focus Trap:** Khi modal mở, phím `Tab` phải được giữ kín bên trong modal. Nhấn phím `Escape` phải đóng modal và trả focus về phần tử đã kích hoạt mở modal trước đó.

### 2.3. Tooltips
* Tooltip mở khi hover chuột **BẮT BUỘC** cũng phải mở được khi focus bằng bàn phím (`onFocus`).
* Nội dung tooltip được liên kết với phần tử kích hoạt qua `aria-describedby="tooltip-id"`.
* Nhấn `Escape` phải đóng được tooltip mà không làm mất focus của phần tử.

### 2.4. Toast Notifications
* Toast thông báo thành công / trạng thái thông thường: dùng `role="status"` hoặc `aria-live="polite"`.
* Toast thông báo lỗi khẩn cấp: dùng `role="alert"` hoặc `aria-live="assertive"`.
* Toast không được tự động biến mất quá nhanh (< 5 giây) nếu chứa thông tin quan trọng mà người dùng cần đọc.
