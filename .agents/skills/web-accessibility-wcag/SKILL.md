---
name: web-accessibility-wcag
description: "Quy chuẩn thiết kế và phát triển web dễ tiếp cận theo tiêu chuẩn quốc tế WCAG 2.2 (Level AA/AAA), độ tương phản màu sắc, điều hướng bàn phím và hỗ trợ trình đọc màn hình."
license: MIT
---

# Web Accessibility & WCAG 2.2 Standards (Khả Năng Tiếp Cận Toàn Diện)

Hướng dẫn áp dụng các tiêu chuẩn quốc tế **WCAG 2.2 (Web Content Accessibility Guidelines)** nhằm đảm bảo mọi người dùng, bao gồm cả những người có khiếm khuyết về thị giác, thính giác, vận động hoặc nhận thức, đều có thể tiếp cận và sử dụng trang web một cách thuận tiện nhất.

---

## 1. TỶ LỆ TƯƠNG PHẢN MÀU SẮC (Color Contrast - WCAG AA)

Màu chữ và màu nền phải có độ tương phản đủ lớn để mắt người dễ dàng nhận diện:

*   **Văn bản thông thường (< 18pt hoặc < 14pt bold):** Tỷ lệ tương phản tối thiểu là **`4.5:1`**.
*   **Văn bản lớn (≥ 18pt hoặc ≥ 14pt bold):** Tỷ lệ tương phản tối thiểu là **`3:1`**.
*   **Thành phần giao diện (Borders, Icons, Form Controls):** Tỷ lệ tương phản tối thiểu là **`3:1`** so với nền xung quanh.
*   *Nguyên tắc không chỉ dựa vào màu sắc:* Không bao giờ dùng màu sắc làm dấu hiệu duy nhất để biểu thị trạng thái (ví dụ: lỗi form bắt buộc phải có cả biểu tượng cảnh báo và dòng chữ giải thích bên cạnh việc đổi viền đỏ).

---

## 2. ĐIỀU HƯỚNG BẰNG BÀN PHÍM (Keyboard Navigation)

Trang web phải có thể được điều hướng hoàn toàn chỉ bằng phím `Tab`, `Shift + Tab`, `Enter`, `Space` và các phím mũi tên:

### A. Hiển Thị Con Trỏ Tiêu Điểm Rõ Ràng (`:focus-visible`)
Tuyệt đối **KHÔNG** viết `outline: none` mà không cung cấp phương án thay thế. Hãy dùng `:focus-visible` để chỉ hiện viền khi dùng bàn phím:
```css
/* Tốt: Hiện viền nổi bật khi người dùng duyệt bằng phím Tab */
button:focus-visible,
a:focus-visible,
input:focus-visible {
  outline: 2px solid var(--color-focus-ring, #00f0ff);
  outline-offset: 3px;
}
```

### B. Liên Kết Nhảy Qua Nội Dung (Skip to Content Link)
Giúp người khiếm thị không phải nhấn Tab qua hàng chục liên kết trên thanh Menu mỗi lần tải trang:
```html
<a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-white focus:text-black">
  Nhảy đến nội dung chính
</a>
```

### C. Bẫy Tiêu Điểm Hộp Thoại (Modal Focus Trap)
Khi một cửa sổ Modal hoặc Dialog mở ra:
1.  Khóa tiêu điểm (focus) bên trong Modal, không cho phép phím Tab nhảy ra các phần tử nền bên ngoài.
2.  Nhấn phím `Escape` (`Esc`) phải đóng Modal ngay lập tức.
3.  Khi đóng Modal, tiêu điểm phải tự động quay trở lại nút bấm đã mở Modal đó.

---

## 3. CÂY PHÂN CẤP TIÊU ĐỀ & NGỮ NGHĨA (Heading Hierarchy)

*   **Mỗi trang chỉ có duy nhất một thẻ `<h1>`:** Đại diện cho chủ đề chính của trang.
*   **Không bao giờ nhảy cóc cấp bậc tiêu đề:**
    *   *Sai:* `<h1>` nhảy sang `<h3>` rồi đến `<h5>`.
    *   *Đúng:* `<h1>` -> `<h2>` -> `<h3>` -> `<h4>` theo thứ tự tuần tự logic.
*   **Thuộc tính ẩn hỗ trợ Screen Reader:**
    *   `aria-hidden="true"`: Ẩn các biểu tượng icon trang trí khỏi trình đọc màn hình.
    *   Lớp CSS `.sr-only`: Ẩn phần tử khỏi mắt nhìn nhưng vẫn đọc to cho người khiếm thị:
        ```css
        .sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border-width: 0;
        }
        ```

---

## 4. FORM & CÁC TRƯỜNG NHẬP LIỆU (Accessible Forms)

*   Mọi thẻ `<input>`, `<select>`, `<textarea>` đều phải gắn kết với một thẻ `<label>` bằng thuộc tính `for` khớp với `id` của input.
*   Thông báo lỗi phải liên kết với input qua `aria-describedby="error-message-id"` và input lỗi phải có `aria-invalid="true"`.
