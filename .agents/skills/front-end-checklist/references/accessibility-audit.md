# Front-End Checklist: Accessibility (a11y) Audit Guide

Hướng dẫn kiểm định chuyên sâu chuẩn tiếp cận theo **WCAG 2.1 Level AA & AAA** từ 95 quy tắc trong Front-End Checklist.

---

## 1. Tương Phản Màu Sắc (Color Contrast)
* **Quy chuẩn WCAG AA:**
  * Văn bản thông thường (< 18pt hoặc < 14pt bold): Tỷ lệ tương phản tối thiểu **4.5:1** so với nền.
  * Văn bản lớn (>= 18pt hoặc >= 14pt bold): Tỷ lệ tương phản tối thiểu **3.0:1**.
  * Các thành phần giao diện & Icon tương tác: Tối thiểu **3.0:1**.
* **Nguyên tắc không phụ thuộc vào màu sắc:** Không được truyền tải thông tin quan trọng (lỗi, thành công, trạng thái) chỉ bằng mỗi màu sắc. Luôn kết hợp kèm icon hoặc văn bản giải thích.

---

## 2. Điều Hướng Bàn Phím (Keyboard Navigation)
* **Tab Order logic:** Thứ tự nhảy phím `Tab` phải đi tuần tự theo luồng đọc nội dung tự nhiên từ trái sang phải, từ trên xuống dưới.
* **Không bị bẫy bàn phím (No Keyboard Trap):** Người dùng bấm `Tab` hoặc `Shift+Tab` phải có thể vào và thoát ra khỏi bất kỳ Modal/Dialog, Menu dropdown hay Widget nào.
* **Skip Link (Nhảy tới nội dung chính):** Cung cấp liên kết ẩn "Nhảy tới nội dung chính" (`Skip to main content`) ở đầu trang để người dùng bàn phím bỏ qua thanh điều hướng lặp lại:
```html
<a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:p-4 focus:bg-white focus:text-black">
  Nhảy tới nội dung chính
</a>
```

---

## 3. Biểu Mẫu & Tương Tác (Forms & Controls)
* **Liên kết nhãn rõ ràng:** Mỗi `<input>`, `<textarea>`, `<select>` phải có `<label>` tương ứng thông qua `for="input-id"` hoặc bao bọc trực tiếp.
```html
<!-- Đúng -->
<label for="user-email">Địa chỉ Email</label>
<input id="user-email" type="email" name="email" required />

<!-- Sai: Chỉ dùng placeholder làm nhãn -->
<input type="email" placeholder="Địa chỉ Email" />
```
* **Báo lỗi dễ tiếp cận:**
  * Khai báo `aria-invalid="true"` khi ô nhập có lỗi.
  * Liên kết thông báo lỗi qua `aria-describedby="error-id"`.

---

## 4. Cấu Trúc Ngữ Nghĩa & ARIA (Semantic & ARIA Rules)
* **Thứ bậc tiêu đề (Heading Hierarchy):** Mỗi trang duy nhất 1 thẻ `<h1>`. Thứ bậc `<h2>`, `<h3>`, `<h4>` phải liền mạch, không được nhảy cóc (ví dụ từ `<h2>` nhảy thẳng xuống `<h4>`).
* **Nút bấm vs Liên kết:**
  * Dùng `<a>` khi hành động là **chuyển hướng URL / sang trang mới**.
  * Dùng `<button>` khi hành động là **thực hiện logic, mở modal, submit form, toggle UI**.
  * Nghiêm cấm viết `<div onClick={...}>` mà không có `role="button"`, `tabIndex={0}`, và sự kiện `onKeyDown`.
* **Thuộc tính ARIA:** Chỉ dùng ARIA khi HTML5 ngữ nghĩa không đáp ứng được. ("No ARIA is better than bad ARIA").
