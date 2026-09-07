# Front-End Checklist: Critical & High Priority Pre-Flight Rules

Danh sách các quy tắc bắt buộc thuộc mức độ **🚨 CRITICAL** và **⚠️ HIGH** phải được kiểm tra và vượt qua trước khi bàn giao hoặc đưa website lên môi trường Production.

---

## 1. 🚨 CÁC QUY TẮC CRITICAL (Phải xử lý 100%)

### 1.1. Doctype HTML5 Chuẩn
* **Quy tắc:** Dòng đầu tiên của tệp HTML phải là `<!DOCTYPE html>`.
* **Lý do:** Kích hoạt chế độ Standards Mode trong trình duyệt, tránh chế độ Quirks Mode làm vỡ CSS layout.
```html
<!DOCTYPE html>
<html lang="vi">
```

### 1.2. Khai báo Bảng mã UTF-8 Đầu Tiên Trong `<head>`
* **Quy tắc:** `<meta charset="utf-8">` phải là thẻ con đầu tiên bên trong `<head>`.
* **Lý do:** Ngăn chặn lỗi hiển thị sai font chữ tiếng Việt, ký tự đặc biệt và tấn công mã hóa (UTF-7 XSS exploit).
```html
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tiêu đề trang</title>
</head>
```

### 1.3. Thẻ Viewport Responsive Hợp Lệ
* **Quy tắc:** Khai báo `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.
* **Nghiêm cấm:** Không được cấu hình `user-scalable=no` hoặc `maximum-scale=1.0` vì vi phạm nghiêm trọng tiêu chuẩn tiếp cận WCAG 2.1 SC 1.4.4 (ngăn người khiếm thị phóng to chữ).

---

## 2. ⚠️ CÁC QUY TẮC HIGH (Bắt buộc trong bản phát hành chính thức)

### 2.1. Ngữ Nghĩa & Khả Năng Tiếp Cận Cơ Bản
- [ ] **HTML `lang` Attribute:** Thẻ `<html>` phải có thuộc tính `lang="vi"` (hoặc mã ngôn ngữ BCP 47 tương ứng) để Screen Reader đọc đúng ngữ điệu và Google SEO phân vùng đúng.
- [ ] **Thẻ `alt` cho mọi hình ảnh:** Tất cả thẻ `<img>` phải có thuộc tính `alt`. Ảnh mang thông tin phải có text mô tả; ảnh trang trí phải để `alt=""` kèm `aria-hidden="true"`.
- [ ] **Unique IDs:** Tuyệt đối không được trùng lặp thuộc tính `id=""` trên cùng một trang DOM. Trùng ID gây hỏng form validation, ARIA linking và JavaScript query.
- [ ] **Visible Focus Indicators:** Không bao giờ viết CSS `outline: none` hoặc `outline: 0` mà không cung cấp viền focus thay thế (`:focus-visible`). Người dùng bàn phím cần thấy rõ vị trí con trỏ.
- [ ] **Semantic HTML5:** Sử dụng đúng thẻ ngữ nghĩa (`<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`, `<footer>`, `<button>`, `<a>`) thay vì lạm dụng toàn bộ thẻ `<div>`.

### 2.2. Hiệu Năng & Tối Ưu Tải Trang
- [ ] **Non-blocking Scripts:** Mọi thẻ `<script>` ở `<head>` phải sử dụng `defer`, `async`, hoặc `type="module"` để không chặn luồng dựng DOM (DOM Parsing).
- [ ] **Image Dimensions (Tránh Layout Shift - CLS):** Luôn khai báo rõ `width` và `height` (hoặc CSS `aspect-ratio`) trên thẻ `<img>` và `<video>` để trình duyệt dành sẵn không gian dựng trước khi ảnh tải xong.
- [ ] **Critical CSS inlined / CSS Minified:** Nén toàn bộ CSS và nhúng CSS trên màn hình đầu tiên (Above the fold) để tăng tốc First Contentful Paint (FCP).
- [ ] **Unused CSS / JS Removal:** Loại bỏ CSS và JS thừa (Tree-shaking) để giảm thiểu kích thước bundle.

### 2.3. Bảo Mật & SEO Thiết Yếu
- [ ] **HTTPS Bắt Buộc:** Toàn bộ liên kết, tài nguyên và API phải chạy trên giao thức `https://`.
- [ ] **Subresource Integrity (SRI):** Tất cả script/CSS tải từ CDN bên thứ 3 phải có mã băm toàn vẹn `integrity="sha384-..."` và `crossorigin="anonymous"`.
- [ ] **Canonical URL:** Khai báo `<link rel="canonical" href="...">` trên mọi trang để chống lỗi trùng lặp nội dung trong SEO.
- [ ] **External Links Security:** Tất cả liên kết mở tab mới `target="_blank"` phải có thuộc tính `rel="noopener noreferrer"` để ngăn chặn tấn công `window.opener` và rò rỉ referrer.
