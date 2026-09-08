# Release Notes - l(3)

- **Ngày phát hành:** 2026-09-08
- **Tập tin đóng gói:** `AI_Learning_Hub.ankiaddon` và `AI_Learning_Hub.zip`
- **Bộ kiểm thử:** 90/90 Unit & E2E tests PASS 100%.

### Điểm mới và cải tiến vượt bậc trong bản phát hành l(3):
1. **Khắc phục triệt để phụ thuộc Pydantic (Zero-Dependency Architecture)**:
   - Hệ thống chuyển đổi toàn bộ 7 game modes AI sang cấu trúc `CANONICAL_SCHEMAS` OpenAPI thuần túy.
   - Hoạt động 100% độc lập, không còn gặp lỗi `Unknown gamemode` trên môi trường Python nhúng của Anki Desktop.
2. **Tối ưu hóa Lấy mẫu từ vựng (Vocabulary Sampling)**:
   - Áp dụng truy vấn SQLite Fast-path, nạp schema và field chỉ trong vài mili-giây thay vì nạp toàn bộ deck.
   - Thuật toán chống lặp thông minh và dành 30% quota ưu tiên từ vựng có SRS yếu.
3. **Đồng bộ hóa 100% Đa ngôn ngữ (Language Parity & UI Switcher)**:
   - Bổ sung nút chuyển đổi nhanh **🌐 VI / EN** ngay trên thanh Header.
   - Bản địa hóa toàn diện: nhãn nút Tạo bài, các cấp độ CEFR A1-C2, placeholder ngữ cảnh và bảng thống kê game Nối từ.
4. **Gia cố Cầu nối IPC & Ghi dữ liệu An toàn (Atomic Write)**:
   - Cơ chế phòng thủ 3 tầng bóc tách payload an toàn, loại bỏ lỗi `unhashable type: dict`.
   - Cơ chế ghi file nguyên tử chống hỏng hóc tệp cấu hình khi tắt đột ngột.
5. **Kiến trúc mô-đun hóa Clean Architecture**:
   - Tách tầng Services (`anki_service`, `generation_service`, `prefs_service`, `keys_service`), Router chuyên biệt, LLM Factory và cấu trúc thư mục Frontend SPA độc lập.
