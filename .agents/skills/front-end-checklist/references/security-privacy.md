# Front-End Checklist: Security & Privacy Guide

Cẩm nang rà soát bảo mật Front-End và bảo vệ quyền riêng tư người dùng.

---

## 1. BẢO MẬT FRONT-END (Security Hardening)

### 1.1. Subresource Integrity (SRI)
* Khi nạp thư viện hoặc CSS/JS từ bên ngoài (CDN như cdnjs, unpkg, jsdelivr), bắt buộc phải có `integrity` và `crossorigin="anonymous"` để ngăn chặn mã độc khi CDN bị tấn công:
```html
<script
  src="https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.21/lodash.min.js"
  integrity="sha512-WFN04846sdKMGo5...=="
  crossorigin="anonymous"
></script>
```

### 1.2. Content Security Policy (CSP Headers)
* Ngăn chặn tấn công XSS (Cross-Site Scripting) và chèn mã độc vào trang:
```http
Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted-cdn.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; object-src 'none';
```

### 1.3. Chống Tấn Công Clickjacking (X-Frame-Options)
* Ngăn chặn website bị nhúng vào `<iframe>` độc hại trên trang web khác:
```http
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
```

### 1.4. An Toàn Khi Sử Dụng Liên Kết Ngoài
* Thẻ `<a>` mở tab mới `target="_blank"` bắt buộc phải đi kèm:
```html
<a href="https://external-site.com" target="_blank" rel="noopener noreferrer">
  Liên kết ngoài an toàn
</a>
```

---

## 2. QUYỀN RIÊNG TƯ & DỮ LIỆU CÁ NHÂN (Privacy & GDPR/CCPA)

### 2.1. Quản lý Cookie & Tracking Consent
* **Banner chấp thuận Cookie:** Phải có thông báo rõ ràng cho phép người dùng đồng ý hoặc từ chối các loại cookie phân tích (Analytics) / quảng cáo trước khi script theo dõi chạy.
* **Không tải tracker trước:** Không được kích hoạt Google Analytics, Facebook Pixel, TikTok Pixel trước khi người dùng nhấn "Chấp nhận".

### 2.2. Không Rò Rỉ Thông Tin Định Danh (No PII Leakage)
* Không truyền email, số điện thoại, mật khẩu hoặc thông tin cá nhân (PII) trên URL Parameters (`GET` query string) vì sẽ bị lưu vào server log và Google Analytics.
* Dùng phương thức `POST` và mã hóa dữ liệu nhạy cảm qua HTTPS.
