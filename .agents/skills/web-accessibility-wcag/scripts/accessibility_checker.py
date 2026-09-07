#!/usr/bin/env python3
import sys
import os
import re

# Cấu hình ép kiểu mã hóa UTF-8 cho Windows terminal tránh lỗi encoding ký tự tiếng Việt
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Lỗi: Thư viện 'beautifulsoup4' chưa được cài đặt.")
    print("Vui lòng cài đặt bằng lệnh: pip install beautifulsoup4")
    sys.exit(1)

class WCAGAccessibilityChecker:
    def __init__(self, file_path):
        self.file_path = file_path
        self.findings = []
        self.score = 100
        self.total_checks = 0
        self.failed_checks = 0

    def add_finding(self, severity, criterion, message, element_snippet=""):
        # severity: CRITICAL (-15), WARNING (-5), INFO (0)
        self.findings.append({
            "severity": severity,
            "criterion": criterion,
            "message": message,
            "element": element_snippet
        })
        if severity == "CRITICAL":
            self.score = max(0, self.score - 15)
            self.failed_checks += 1
        elif severity == "WARNING":
            self.score = max(0, self.score - 5)
            self.failed_checks += 1
        self.total_checks += 1

    def run_audit(self):
        if not os.path.exists(self.file_path):
            print(f"Lỗi: Không tìm thấy tệp {self.file_path}")
            sys.exit(1)

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        soup = BeautifulSoup(content, "html.parser")

        # 1. Kiểm tra thuộc tính lang trong thẻ <html> (WCAG 3.1.1 - Cấp A)
        html_tag = soup.find("html")
        if not html_tag or not html_tag.has_attr("lang") or not html_tag.get("lang", "").strip():
            self.add_finding("CRITICAL", "WCAG 3.1.1 (Language of Page)", 
                "Thẻ <html> thiếu thuộc tính 'lang' hợp lệ (ví dụ: lang=\"vi\" hoặc lang=\"en\"). Trình đọc màn hình không thể phát âm chính xác ngôn ngữ.")
        else:
            self.total_checks += 1

        # 2. Kiểm tra thẻ <title> trang (WCAG 2.4.2 - Cấp A)
        title_tag = soup.find("title")
        if not title_tag or not title_tag.get_text(strip=True):
            self.add_finding("CRITICAL", "WCAG 2.4.2 (Page Titled)", 
                "Trang web thiếu thẻ <title> hoặc nội dung tiêu đề rỗng. Tiêu đề giúp người dùng định vị ngữ cảnh trang.")
        else:
            self.total_checks += 1

        # 3. Phân cấp thẻ tiêu đề (Headings Hierarchy - WCAG 1.3.1 - Cấp A)
        headings = soup.find_all(re.compile(r"^h[1-6]$"))
        h1_tags = [h for h in headings if h.name == "h1"]
        if len(h1_tags) == 0:
            self.add_finding("WARNING", "WCAG 1.3.1 (Info and Relationships)", 
                "Trang không có thẻ <h1> nào. Nên có đúng 1 thẻ <h1> mô tả nội dung chính.")
        elif len(h1_tags) > 1:
            self.add_finding("WARNING", "WCAG 1.3.1 (Info and Relationships)", 
                f"Trang phát hiện {len(h1_tags)} thẻ <h1>. Tiêu chuẩn khuyên dùng mỗi trang chỉ nên có duy nhất 1 thẻ <h1>.")
        else:
            self.total_checks += 1

        prev_level = 0
        for h in headings:
            curr_level = int(h.name[1])
            if prev_level > 0 and curr_level > prev_level + 1:
                self.add_finding("WARNING", "WCAG 1.3.1 (Heading Order)", 
                    f"Cây tiêu đề bị nhảy bậc: từ <h{prev_level}> nhảy thẳng sang <h{curr_level}> bỏ qua mức giữa.", str(h)[:100])
            prev_level = curr_level

        # 4. Kiểm tra văn bản thay thế hình ảnh (WCAG 1.1.1 - Cấp A)
        images = soup.find_all("img")
        for img in images:
            alt = img.get("alt")
            src = img.get("src", "unknown")
            if alt is None:
                self.add_finding("CRITICAL", "WCAG 1.1.1 (Non-text Content)", 
                    f"Ảnh thiếu thuộc tính 'alt': {src}", str(img)[:100])
            elif alt.strip().lower() in ["image", "photo", "picture", "icon", "hinh anh", "anh"]:
                self.add_finding("WARNING", "WCAG 1.1.1 (Non-text Content)", 
                    f"Thuộc tính 'alt' chứa từ ngữ chung chung vô nghĩa ('{alt}'): {src}", str(img)[:100])
            else:
                self.total_checks += 1

        # 5. Kiểm tra liên kết trống (Empty Links - WCAG 2.4.4 - Cấp A)
        links = soup.find_all("a")
        for a in links:
            text = a.get_text(strip=True)
            has_aria = a.has_attr("aria-label") or a.has_attr("title")
            img_with_alt = any(img.has_attr("alt") and img["alt"].strip() for img in a.find_all("img"))
            if not text and not has_aria and not img_with_alt:
                self.add_finding("CRITICAL", "WCAG 2.4.4 (Link Purpose)", 
                    "Thẻ liên kết <a> rỗng: không có chữ hiển thị, không có 'aria-label', và không có ảnh chứa 'alt'. Trình đọc màn hình không thể biết link dẫn tới đâu.", str(a)[:100])
            else:
                self.total_checks += 1

        # 6. Kiểm tra nút bấm trống (Empty Buttons - WCAG 4.1.2 - Cấp A)
        buttons = soup.find_all("button")
        for btn in buttons:
            text = btn.get_text(strip=True)
            has_aria = btn.has_attr("aria-label") or btn.has_attr("title")
            if not text and not has_aria:
                self.add_finding("CRITICAL", "WCAG 4.1.2 (Name, Role, Value)", 
                    "Nút bấm <button> không có chữ và thiếu 'aria-label' hoặc 'title'.", str(btn)[:100])
            else:
                self.total_checks += 1

        # 7. Nhãn các trường nhập liệu (Form Labels - WCAG 1.3.1 / 3.3.2)
        inputs = soup.find_all("input", type=lambda t: t not in ["hidden", "submit", "button", "image", "reset"])
        for inp in inputs:
            inp_id = inp.get("id")
            has_label = False
            if inp_id:
                has_label = soup.find("label", attrs={"for": inp_id}) is not None
            if not has_label and not inp.has_attr("aria-label") and not inp.has_attr("aria-labelledby"):
                self.add_finding("CRITICAL", "WCAG 3.3.2 (Labels or Instructions)", 
                    f"Trường nhập liệu (input id='{inp_id or 'none'}') không được gắn kết với thẻ <label> hoặc 'aria-label'.", str(inp)[:100])
            else:
                self.total_checks += 1

    def print_report(self):
        print("=" * 72)
        print(f" BÁO CÁO KIỂM TRA KHẢ NĂNG TIẾP CẬN WCAG 2.2: {os.path.basename(self.file_path)}")
        print("=" * 72)
        print(f"Điểm số Tiếp Cận (Accessibility Score): {self.score}/100")
        
        rating = "Chuẩn Quốc Tế (Pass)" if self.score >= 90 else "Khá (Cần khắc phục)" if self.score >= 70 else "Chưa Đạt Chuẩn"
        print(f"Đánh giá xếp hạng: {rating}")
        print(f"Tổng kiểm tra: {self.total_checks} | Lỗi phát hiện: {self.failed_checks}")
        print("-" * 72)

        criticals = [f for f in self.findings if f["severity"] == "CRITICAL"]
        warnings = [f for f in self.findings if f["severity"] == "WARNING"]

        if criticals:
            print("\n🔴 LỖI VI PHẠM NGHIÊM TRỌNG (WCAG CẤP A):")
            for f in criticals:
                print(f"  • [{f['criterion']}] {f['message']}")
                if f['element']:
                    print(f"    Mã HTML: {f['element']}...")

        if warnings:
            print("\n⚠️ CẢNH BÁO CẦN CẢI THIỆN (WCAG CẤP AA/AAA):")
            for f in warnings:
                print(f"  • [{f['criterion']}] {f['message']}")
                if f['element']:
                    print(f"    Mã HTML: {f['element']}...")

        if not self.findings:
            print("\n✅ Tuyệt vời! Tệp HTML tuân thủ xuất sắc các tiêu chuẩn tiếp cận WCAG 2.2.")
        print("=" * 72)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Sử dụng: python accessibility_checker.py <duong_dan_file_html>")
        sys.exit(1)

    checker = WCAGAccessibilityChecker(sys.argv[1])
    checker.run_audit()
    checker.print_report()
