# Front-End Checklist: Media & Motion Optimization Guide

Cẩm nang tối ưu hóa tài nguyên đa phương tiện (Ảnh, Video, Audio) và kiểm soát hiệu ứng chuyển động (Motion & Animations).

---

## 1. TỐI ƯU HÓA HÌNH ẢNH (Image Optimization)

### 1.1. Thẻ `<picture>` & Định Dạng Thế Hệ Mới
* Ưu tiên phục vụ `AVIF` và `WebP` với fallback về `JPG/PNG`:
```html
<picture>
  <source srcset="/images/hero.avif" type="image/avif">
  <source srcset="/images/hero.webp" type="image/webp">
  <img
    src="/images/hero.jpg"
    alt="Mô tả nội dung hình ảnh"
    width="1200"
    height="675"
    loading="eager"
    fetchpriority="high"
    class="h-auto w-full"
  >
</picture>
```

### 1.2. Responsive Images (`srcset` & `sizes`)
* Cung cấp các độ phân giải khác nhau cho các kích thước màn hình:
```html
<img
  src="/images/card-800.webp"
  srcset="
    /images/card-400.webp 400w,
    /images/card-800.webp 800w,
    /images/card-1200.webp 1200w
  "
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
  alt="Sản phẩm nổi bật"
  width="800"
  height="600"
  loading="lazy"
>
```

### 1.3. Quy Tắc Tải Hình Ảnh (Loading Strategy)
* **Above-the-fold (Hình ảnh trên màn hình đầu tiên / Hero):** Sử dụng `loading="eager"` kèm `fetchpriority="high"`. Tuyệt đối không để `loading="lazy"` cho ảnh Hero vì sẽ làm chậm điểm LCP (Largest Contentful Paint).
* **Below-the-fold (Hình ảnh phía dưới trang):** Luôn để `loading="lazy"`.

---

## 2. KIỂM SOÁT HIỆU ỨNG CHUYỂN ĐỘNG (Motion & Animations)

### 2.1. Hỗ Trợ `prefers-reduced-motion` Bắt Buộc
* Những người dùng mắc hội chứng tiền đình hoặc nhạy cảm với chuyển động thường kích hoạt chế độ "Reduce Motion" trong cài đặt hệ điều hành. Website **BẮT BUỘC** phải tôn trọng tùy chọn này:

```css
/* CSS thuần */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

```tsx
// Trong Framer Motion / Motion
import { useReducedMotion } from "motion/react";

export const HeroAnimation = () => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: shouldReduceMotion ? 0 : 0.5 }}
    >
      Nội dung Hero
    </motion.div>
  );
};
```

### 2.2. Chỉ Chuyển Động Các Thuộc Tính Được GPU Tăng Tốc (Composite-Only Properties)
* **Được phép chuyển động:** `transform` (`translate`, `scale`, `rotate`) và `opacity`.
* **Nghiêm cấm chuyển động liên tục:** `width`, `height`, `top`, `left`, `margin`, `padding`, `box-shadow` vì chúng gây kích hoạt lại luồng tính toán bố cục (Layout/Reflow) và vẽ lại pixel (Repaint) trên Main Thread, làm tụt FPS và giật lag trên thiết bị di động.
