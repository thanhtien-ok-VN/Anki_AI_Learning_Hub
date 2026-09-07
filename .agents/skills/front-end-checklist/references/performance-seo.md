# Front-End Checklist: Performance & SEO Optimization Guide

Cẩm nang tối ưu hóa hiệu năng tải trang, Core Web Vitals và cấu trúc SEO chuẩn mực.

---

## 1. TỐI ƯU HÓA HIỆU NĂNG & CORE WEB VITALS

### 1.1. Largest Contentful Paint (LCP < 2.5s)
* **Preload LCP Image:** Đối với ảnh Hero lớn trên màn hình đầu tiên, thêm thẻ `<link rel="preload" as="image" href="..." fetchpriority="high">`.
* **Sử dụng định dạng ảnh hiện đại:** Chuyển đổi toàn bộ JPG/PNG sang `WebP` hoặc `AVIF` để giảm 30-70% dung lượng.
* **Tối ưu Web Font:** Dùng font định dạng `WOFF2`, thêm `font-display: swap;` trong `@font-face` để tránh lỗi FOIT (Flash of Invisible Text).

### 1.2. Cumulative Layout Shift (CLS < 0.1)
* **Khai báo kích thước trước:** Mọi thẻ `<img>`, `<video>`, `<iframe>` phải có thuộc tính `width` và `height` hoặc style `aspect-ratio`.
* **Không chèn động quảng cáo/banner ở phía trên nội dung:** Dành sẵn khoảng trống cố định (min-height) cho các khối dữ liệu tải chậm.

### 1.3. Interaction to Next Paint (INP < 200ms)
* **Tránh Long Tasks (> 50ms):** Tách nhỏ các tác vụ JavaScript nặng bằng `requestIdleCallback()` hoặc `setTimeout(fn, 0)`.
* **Debounce / Throttle:** Áp dụng debounce cho các sự kiện tìm kiếm và throttle cho sự kiện cuộn/resize màn hình.

---

## 2. CHUẨN HÓA SEO & METADATA

### 2.1. Thẻ Meta Cốt Lõi (Core Meta Tags)
```html
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  
  <title>Tiêu Đề Trang Dưới 60 Ký Tự | Tên Thương Hiệu</title>
  <meta name="description" content="Mô tả nội dung trang súc tích, hấp dẫn trong khoảng 150-160 ký tự giúp tăng tỷ lệ nhấp chuột (CTR) trên Google.">
  <link rel="canonical" href="https://example.com/bai-viet-chuan">
  <meta name="robots" content="index, follow">
</head>
```

### 2.2. Mạng Xã Hội (Open Graph & Twitter Cards)
```html
<!-- Open Graph / Facebook / Zalo / LinkedIn -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://example.com/bai-viet-chuan">
<meta property="og:title" content="Tiêu Đề Bài Viết Chuẩn SEO">
<meta property="og:description" content="Mô tả ngắn gọn nội dung bài viết.">
<meta property="og:image" content="https://example.com/images/og-banner.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Tiêu Đề Bài Viết Chuẩn SEO">
<meta name="twitter:description" content="Mô tả ngắn gọn nội dung bài viết.">
<meta name="twitter:image" content="https://example.com/images/og-banner.jpg">
```

### 2.3. Dữ Liệu Có Cấu Trúc (JSON-LD Structured Data)
Nhúng Schema.org JSON-LD để giúp công cụ tìm kiếm hiểu rõ ngữ nghĩa sản phẩm, bài viết hoặc tổ chức:
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Tiêu Đề Bài Viết",
  "image": "https://example.com/images/og-banner.jpg",
  "author": {
    "@type": "Person",
    "name": "Tên Tác Giả"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Tên Công Ty",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  },
  "datePublished": "2026-08-24"
}
</script>
```
