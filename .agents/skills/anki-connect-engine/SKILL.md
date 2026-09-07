---
name: anki-connect-engine
description: >-
  Kỹ năng quản trị, kết nối và thực thi các thao tác an toàn với cơ sở dữ liệu Anki thông qua AnkiConnect API. Bao gồm quy trình sao lưu dự phòng (backup), chia lô xử lý (batching 250-500 thẻ), lưu vết điểm kiểm tra (checkpoint), bảo toàn 100% tiến độ ôn tập SRS và đóng gói .apkg từng phần.
---

# AnkiConnect Engine (Quy Chuẩn Tương Tác & Tái Cấu Trúc An Toàn Anki)

Tài liệu này hướng dẫn chi tiết cách thức AI Agent kết nối, trích xuất, tái cấu trúc và gán nhãn hàng chục nghìn thẻ ghi nhớ trong Anki thông qua **AnkiConnect** mà không làm mất dữ liệu hay tiến độ học tập.

---

## 1. Nguyên Tắc An Toàn Bất Biến (Golden Directives)

1. **Bảo toàn 100% Tiến độ SRS (Spaced Repetition System):**
   - **TUYỆT ĐỐI KHÔNG** xuất file văn bản thô rồi xóa thẻ cũ và tạo lại thẻ mới. Điều này sẽ xóa sạch toàn bộ lịch sử học tập (`review history`), số lần lặp lại (`reps`), số lần quên (`lapses`), khoảng cách ôn tập (`interval`), hệ số dễ (`factor`) và ngày đến hạn (`due`).
   - **LUÔN DÙNG LỆNH `changeDeck`:** Khi chuyển thẻ vào Deck mới, Anki chỉ thay đổi trường con trỏ `did` (deck ID) của bảng `cards` trong cơ sở dữ liệu. Mọi thông số SRS được giữ nguyên vẹn 100%.

2. **Bảo vệ File Đa phương tiện (Media Files):**
   - Không di chuyển, sao chép hoặc đổi tên các tệp trong thư mục `collection.media`.
   - Các trường thẻ chứa `[sound:...]` hoặc `<img src="...">` chỉ tham chiếu theo tên file, việc đổi deck không ảnh hưởng tới đường dẫn media.

3. **Sao lưu Dự phòng (Safety Backup First):**
   - Trước khi thực hiện bất kỳ thao tác ghi (`changeDeck`, `addTags`, `deleteNotes`), bắt buộc phải kiểm tra hoặc thực hiện một bản sao lưu tệp `collection.anki21` hoặc xuất backup dự phòng toàn bộ collection.

4. **Xử lý theo Lô (Batching & Rate Limiting):**
   - Đối với bộ thẻ quy mô lớn (> 10,000 thẻ), không gửi mảng ID khổng lồ trong một yêu cầu duy nhất gây treo giao diện (GUI Freeze) của Anki.
   - Chia thành từng lô **250 – 500 thẻ/lần**, nghỉ ngắn 0.1s – 0.2s giữa các đợt gọi API.
   - Luôn cập nhật tiến trình vào file `checkpoint.json` sau mỗi lô thành công.

---

## 2. Giao Thức Kết Nối AnkiConnect

- **Địa chỉ mặc định:** `http://127.0.0.1:8765`
- **Phiên bản API khuyến nghị:** `version: 6`
- **Cấu trúc Payload chuẩn:**
  ```json
  {
    "action": "<action_name>",
    "version": 6,
    "params": { ... }
  }
  ```

### Kiểm Tra Kết Nối (Health Check)
```python
import requests

def check_anki_connection(url="http://127.0.0.1:8765"):
    try:
        res = requests.post(url, json={"action": "version", "version": 6}, timeout=5)
        res.raise_for_status()
        return res.json().get("result") == 6
    except Exception as e:
        print(f"Không thể kết nối tới AnkiConnect: {e}")
        return False
```

---

## 3. Các Lệnh AnkiConnect Cốt Lõi Được Sử Dụng

### A. Đọc & Trích xuất (Read-only)
1. **`deckNames`**: Lấy danh sách toàn bộ deck và subdeck hiện có.
2. **`findNotes`**: Tìm danh sách Note IDs theo câu truy vấn (ví dụ: `query: "deck:TongHopCopNhat"`).
3. **`notesInfo`**: Đọc chi tiết từng note (Model, Fields, Tags, Card IDs).
4. **`cardsInfo`**: Đọc thông tin chi tiết của Card (Deck Name, Due, Interval, Factor, Reps, Lapses).

### B. Can thiệp & Tái Cấu Trúc (Execution)
1. **`createDeck`**: Tự động tạo cấu trúc Deck phân cấp (ví dụ: `English::01_Topics::Environment`).
2. **`changeDeck`**: Di chuyển danh sách Card IDs sang Deck mới.
   ```python
   # Di chuyển các card sang deck đích mà không mất tiến độ
   payload = {
       "action": "changeDeck",
       "version": 6,
       "params": {
           "cards": [card_id_1, card_id_2],
           "deck": "English::01_Topics::Environment"
       }
   }
   ```
3. **`addTags`**: Gán nhãn hàng loạt cho các Note IDs.
   ```python
   # Gán nhãn cho note
   payload = {
       "action": "addTags",
       "version": 6,
       "params": {
           "notes": [note_id_1, note_id_2],
           "tags": "level::B2 topic::Environment"
       }
   }
   ```
4. **`exportPackage`**: Đóng gói deck con thành file `.apkg` (kèm cờ `includeMedia: true`).
   ```python
   payload = {
       "action": "exportPackage",
       "version": 6,
       "params": {
           "deck": "English::01_Topics::Environment",
           "path": "D:/AntigravityProject/Anki/exports/Environment.apkg",
           "includeSched": true
       }
   }
   ```

---

## 4. Cơ Chế Checkpoint & Khôi Phục Sự Cố

Tệp trạng thái lưu tại: `data/checkpoints/migration_checkpoint.json`
```json
{
  "total_notes": 22898,
  "processed_note_ids": [1712345678, 1712345679],
  "last_processed_index": 500,
  "last_updated": "2026-09-03T10:30:00",
  "status": "in_progress",
  "errors": []
}
```
- Khi bắt đầu mỗi batch mới: Đọc file checkpoint, bỏ qua các note IDs đã có trong `processed_note_ids`.
- Khi hoàn tất batch: Ghi nối tiếp vào file checkpoint.
- Nếu gặp lỗi mạng hoặc Anki tắt: Ghi nhận lỗi vào danh sách `errors`, cho phép người dùng mở lại Anki và chạy tiếp tục mà không bị lặp lại thao tác.
