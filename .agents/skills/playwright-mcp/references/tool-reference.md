# Playwright MCP: Detailed Tool Reference

Bảng tra cứu chi tiết danh mục công cụ, chức năng và cú pháp gọi lệnh của Playwright MCP server.

---

## 1. Điều Hướng & Trạng Thái Trang (Navigation & Snapshot)

### `browser_navigate`
* **Mô tả:** Mở trình duyệt và điều hướng tới địa chỉ URL mong muốn.
* **Tham số:**
  * `url` *(string, required)*: Địa chỉ web cần mở (ví dụ: `http://localhost:3000/login` hoặc `https://example.com`).
* **Kết quả trả về:** Accessibility snapshot của trang sau khi hoàn tất tải.

---

## 2. Thao Tác Tương Tác DOM (Element Interaction)

### `browser_click`
* **Mô tả:** Nhấp chuột (Click) vào một nút, liên kết hoặc phần tử giao diện.
* **Tham số:**
  * `element_id` *(number/string)*: ID tham chiếu của phần tử từ Accessibility Snapshot.

### `browser_fill`
* **Mô tả:** Điền dữ liệu một lần vào ô nhập liệu (`<input>`, `<textarea>`).
* **Tham số:**
  * `element_id` *(number/string)*: ID tham chiếu của ô nhập liệu.
  * `value` *(string)*: Giá trị chuỗi cần điền.

### `browser_type`
* **Mô tả:** Giả lập gõ từng phím tuần tự (hữu ích cho các ô autocomplete/search).
* **Tham số:**
  * `element_id` *(number/string)*: ID tham chiếu.
  * `text` *(string)*: Chuỗi cần gõ.

### `browser_hover`
* **Mô tả:** Di chuyển con trỏ chuột lên phần tử (để kích hoạt menu dropdown, tooltip, hoặc hover state).
* **Tham số:**
  * `element_id` *(number/string)*: ID tham chiếu.

### `browser_press_key`
* **Mô tả:** Nhấn các phím chức năng bàn phím.
* **Tham số:**
  * `key` *(string)*: Tên phím (ví dụ: `Enter`, `Escape`, `Tab`, `ArrowDown`, `Backspace`).

---

## 3. Chụp Ảnh Màn Hình & Debug (Inspection)

### `browser_screenshot`
* **Mô tả:** Chụp ảnh màn hình giao diện hiện tại để đối chiếu trực quan hoặc đính kèm báo cáo bug.
* **Tham số:**
  * `name` *(string, optional)*: Tên file ảnh lưu trữ.
  * `full_page` *(boolean, optional)*: Chụp toàn bộ trang cuộn (`true`) hay chỉ khung nhìn hiện tại (`false`).

### `browser_evaluate`
* **Mô tả:** Thực thi một đoạn JavaScript tùy ý trên trang và lấy kết quả trả về.
* **Tham số:**
  * `script` *(string)*: Đoạn mã JS (ví dụ: `() => window.localStorage.getItem('token')`).
