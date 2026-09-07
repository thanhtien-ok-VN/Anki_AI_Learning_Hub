---
name: svg-icon-engineering
description: "Quy chuẩn kỹ nghệ đồ họa vector SVG, tối ưu hóa kích thước (SVGO), hiệu ứng vẽ nét (line drawing animation) và tích hợp Icon hệ thống hiện đại."
license: MIT
---

# SVG & Icon Engineering (Kỹ Nghệ Đồ Họa Vector)

Hướng dẫn chuyên sâu về việc thiết kế, làm sạch, tối ưu hóa và lập trình tương tác hoạt ảnh cho đồ họa vector SVG và hệ thống biểu tượng (Icon Systems) trên nền tảng web.

---

## 1. QUY CHUẨN TỐI ƯU HÓA SVG (SVGO & Clean Architecture)

### A. Cấu trúc SVG Tiêu chuẩn
Một tệp SVG chất lượng cao phục vụ web **BẮT BUỘC** phải đáp ứng các tiêu chí:
1.  **Luôn có `viewBox` chuẩn:** Ví dụ `viewBox="0 0 24 24"` đối với Icon, hoặc `viewBox="0 0 800 600"` đối với hình minh họa minh họa.
2.  **Không cố định `width`/`height` cứng khi nhúng Responsive:** Để phần tử cha (CSS Flexbox/Grid) quản lý kích thước hoặc đặt `width="100%"` và `height="auto"`.
3.  **Lược bỏ rác phần mềm đồ họa:** Xóa bỏ toàn bộ các thẻ rác do Illustrator, Figma hay Inkscape sinh ra:
    *   Thẻ `<?xml ... ?>`, `<!DOCTYPE svg ...>`, `<!-- Generator: ... -->`.
    *   Các thuộc tính `xmlns:sketch`, `xmlns:xlink` không cần thiết.
    *   Các thẻ `<metadata>`, `<defs>` rỗng hoặc id không sử dụng.

### B. Sử dụng `currentColor` Cho Biểu Tượng
Để biểu tượng tự động kế thừa màu chữ của phần tử cha (dễ dàng đổi màu khi hover chuột hoặc đổi theme Dark/Light mode):
```html
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10" />
  <path d="m10 15 5-3-5-3v6Z" />
</svg>
```

---

## 2. HOẠT ẢNH VẼ NÉT SVG (Line Drawing Animations)

Sử dụng CSS thuần để tạo hiệu ứng đường viền tự vẽ cực kỳ nghệ thuật mà không cần thư viện bên thứ ba:

```css
.animated-draw-path {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: drawLine 2.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

@keyframes drawLine {
  to {
    stroke-dashoffset: 0;
  }
}
```

*Mẹo tính toán độ dài nét vẽ chính xác bằng JavaScript:*
```javascript
const path = document.querySelector(".my-path");
const pathLength = path.getTotalLength();
path.style.strokeDasharray = pathLength;
path.style.strokeDashoffset = pathLength;
```

---

## 3. DẢI MÀU PHÁT QUANG TRONG SVG (`<defs> & <linearGradient>`)

Tạo các điểm nhấn phát sáng công nghệ (Cyberpunk / Neon Tech) bên trong vector:

```html
<svg viewBox="0 0 100 100" class="w-16 h-16">
  <defs>
    <linearGradient id="neonGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f0ff" />
      <stop offset="100%" stop-color="#7000ff" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>
  <polygon points="50,5 90,90 10,90" stroke="url(#neonGradient)" stroke-width="4" fill="none" filter="url(#glow)" />
</svg>
```

---

## 4. BỘ ICON KHUYÊN DÙNG & AN TOÀN BẢO MẬT

*   **Bộ icon vector chất lượng cao nhất hiện nay:**
    *   **Lucide Icons (`lucide-react`):** Đơn giản, hiện đại, hỗ trợ tree-shaking tuyệt đối.
    *   **Phosphor Icons (`@phosphor-icons/react`):** Cực kỳ đa dạng biến thể (Regular, Bold, Duotone, Thin, Fill).
    *   **Hugeicons (`hugeicons-react`):** Phong cách cao cấp cho SaaS hiện đại.
*   **Bảo mật XSS (SVG Security):**
    *   Không bao giờ render chuỗi SVG do người dùng tải lên bằng `dangerouslySetInnerHTML` mà chưa qua thư viện làm sạch như `DOMPurify`. Các tệp SVG độc hại có thể chứa thẻ `<script>` hoặc thuộc tính `onload="alert(1)"`.
