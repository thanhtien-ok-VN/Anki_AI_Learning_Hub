import random
from typing import Any
from .base import GameModeBase

class WordUnscrambleMode(GameModeBase):
    name = "unscramble"
    display_name = "Word Unscramble"
    icon = "🧩"
    is_offline = True

    # Pool câu mẫu đa dạng phân chia theo level và topic để sinh offline
    SENTENCE_POOL = [
        # Beginner - Daily Life
        {
            "correct_sentence": "She enjoys reading books in the park.",
            "meaning_vi": "Cô ấy thích đọc sách trong công viên.",
            "hint": "Một sở thích lành mạnh ngoài trời",
            "key_vocabulary": [
                {"word": "enjoys", "meaning_vi": "thích thú, tận hưởng"},
                {"word": "park", "meaning_vi": "công viên"}
            ],
            "difficulty_reason": "Sử dụng động từ thêm -ing sau 'enjoy' và cụm giới từ chỉ nơi chốn.",
            "grammar_note": "Cấu trúc: enjoy + V-ing (thích làm việc gì).",
            "level": "beginner",
            "topic": "daily_life"
        },
        {
            "correct_sentence": "They have been friends since childhood.",
            "meaning_vi": "Họ đã là bạn bè từ thời thơ ấu.",
            "hint": "Một tình bạn bền chặt lâu năm",
            "key_vocabulary": [
                {"word": "friends", "meaning_vi": "bạn bè"},
                {"word": "childhood", "meaning_vi": "thời thơ ấu"}
            ],
            "difficulty_reason": "Sử dụng thì hiện tại hoàn thành với 'since' chỉ mốc thời gian.",
            "grammar_note": "Thì hiện tại hoàn thành: S + have/has + V3/ed + since + mốc thời gian.",
            "level": "beginner",
            "topic": "daily_life"
        },
        # Elementary - Travel
        {
            "correct_sentence": "We booked a comfortable hotel near the beach.",
            "meaning_vi": "Chúng tôi đã đặt một khách sạn thoải mái gần bãi biển.",
            "hint": "Chuẩn bị chỗ ở cho chuyến đi nghỉ",
            "key_vocabulary": [
                {"word": "booked", "meaning_vi": "đặt trước (chỗ, phòng)"},
                {"word": "comfortable", "meaning_vi": "thoải mái, dễ chịu"}
            ],
            "difficulty_reason": "Sử dụng tính từ đứng trước danh từ và cụm giới từ chỉ vị trí.",
            "grammar_note": "Trật tự từ: Adjective + Noun (comfortable hotel). Near là giới từ chỉ vị trí gần.",
            "level": "elementary",
            "topic": "travel"
        },
        {
            "correct_sentence": "Please check the flight schedule before leaving.",
            "meaning_vi": "Vui lòng kiểm tra lịch trình chuyến bay trước khi đi.",
            "hint": "Lời nhắc nhở quan trọng tại sân bay",
            "key_vocabulary": [
                {"word": "flight", "meaning_vi": "chuyến bay"},
                {"word": "schedule", "meaning_vi": "lịch trình, thời gian biểu"}
            ],
            "difficulty_reason": "Sử dụng câu mệnh lệnh lịch sự với 'Please' và mệnh đề rút gọn với 'before + V-ing'.",
            "grammar_note": "Rút gọn mệnh đề trạng ngữ: before/after + V-ing (khi cùng chủ ngữ).",
            "level": "elementary",
            "topic": "travel"
        },
        # Intermediate - Work
        {
            "correct_sentence": "The manager advocates using technology to improve work efficiency.",
            "meaning_vi": "Người quản lý ủng hộ việc sử dụng công nghệ để nâng cao hiệu suất công việc.",
            "hint": "Cách cải tiến quy trình làm việc",
            "key_vocabulary": [
                {"word": "advocates", "meaning_vi": "ủng hộ, tán thành"},
                {"word": "efficiency", "meaning_vi": "hiệu suất, hiệu quả"}
            ],
            "difficulty_reason": "Sử dụng động từ đi kèm danh động từ và cụm giới từ chỉ mục đích.",
            "grammar_note": "Cấu trúc: advocate + V-ing (ủng hộ làm việc gì). To + Verb chỉ mục đích.",
            "level": "intermediate",
            "topic": "work"
        },
        {
            "correct_sentence": "We need to mitigate risks before launching the new project.",
            "meaning_vi": "Chúng ta cần giảm thiểu rủi ro trước khi ra mắt dự án mới.",
            "hint": "Quản trị rủi ro trong doanh nghiệp",
            "key_vocabulary": [
                {"word": "mitigate", "meaning_vi": "giảm nhẹ, giảm thiểu"},
                {"word": "launching", "meaning_vi": "ra mắt, khởi chạy"}
            ],
            "difficulty_reason": "Sử dụng động từ khuyết thiếu nhẹ 'need to' và mệnh đề phân từ.",
            "grammar_note": "Cấu trúc: need + to-inf (cần làm gì). 'Before + V-ing' thay cho 'before we launch'.",
            "level": "intermediate",
            "topic": "work"
        },
        # Upper-Intermediate - Culture
        {
            "correct_sentence": "Traditional customs are passing down through generations.",
            "meaning_vi": "Các phong tục truyền thống đang được truyền lại qua các thế hệ.",
            "hint": "Sự kế thừa văn hóa gia đình và xã hội",
            "key_vocabulary": [
                {"word": "traditional", "meaning_vi": "truyền thống"},
                {"word": "generations", "meaning_vi": "các thế hệ"}
            ],
            "difficulty_reason": "Sử dụng phrasal verb ở thì tiếp diễn và từ vựng trừu tượng.",
            "grammar_note": "Cụm động từ: pass down (truyền lại). Thì hiện tại tiếp diễn chỉ xu hướng đang diễn ra.",
            "level": "upper_intermediate",
            "topic": "culture"
        },
        {
            "correct_sentence": "Language plays an essential role in preserving cultural identity.",
            "meaning_vi": "Ngôn ngữ đóng vai trò cốt lõi trong việc gìn giữ bản sắc văn hóa.",
            "hint": "Mối quan hệ giữa ngôn ngữ và văn hóa dân tộc",
            "key_vocabulary": [
                {"word": "essential", "meaning_vi": "thiết yếu, cốt lõi"},
                {"word": "preserving", "meaning_vi": "gìn giữ, bảo tồn"}
            ],
            "difficulty_reason": "Sử dụng cụm từ cố định 'play a role in' đi kèm danh động từ.",
            "grammar_note": "Collocation: play a/an + Adj + role + in + V-ing (đóng vai trò như thế nào trong việc gì).",
            "level": "upper_intermediate",
            "topic": "culture"
        },
        # Advanced - Science & Technology
        {
            "correct_sentence": "Artificial intelligence is shifting the paradigm of modern education.",
            "meaning_vi": "Trí tuệ nhân tạo đang thay đổi mô hình của giáo dục hiện đại.",
            "hint": "Tác động của AI đối với trường học",
            "key_vocabulary": [
                {"word": "paradigm", "meaning_vi": "mô hình, khuôn mẫu"},
                {"word": "shifting", "meaning_vi": "dịch chuyển, thay đổi"}
            ],
            "difficulty_reason": "Sử dụng từ vựng nâng cao và danh từ ghép phức tạp.",
            "grammar_note": "Cụm từ: shift the paradigm (thay đổi hoàn toàn tư duy/mô hình).",
            "level": "advanced",
            "topic": "science"
        },
        {
            "correct_sentence": "We conducted a comprehensive study to scrutinize the hypothesis.",
            "meaning_vi": "Chúng tôi đã tiến hành một nghiên cứu toàn diện để xem xét kỹ lưỡng giả thuyết.",
            "hint": "Các bước trong nghiên cứu khoa học",
            "key_vocabulary": [
                {"word": "comprehensive", "meaning_vi": "toàn diện"},
                {"word": "scrutinize", "meaning_vi": "xem xét kỹ lưỡng"}
            ],
            "difficulty_reason": "Sử dụng cấu trúc câu phức với động từ chỉ mục đích và từ vựng học thuật C1-C2.",
            "grammar_note": "Cấu trúc: conduct a study (tiến hành nghiên cứu). Scrutinize là động từ học thuật chỉ sự xem xét tỉ mỉ.",
            "level": "advanced",
            "topic": "science"
        }
    ]

    def generate(self, **kwargs) -> dict:
        level = kwargs.get("level", "intermediate")
        topic = kwargs.get("topic", "daily_life")
        count = kwargs.get("count", 5)
        vocab_pairs = kwargs.get("vocab_pairs") or []
        
        # 1. Tìm các câu mẫu chứa các từ trong vocab_pairs của người dùng
        matched_sentences = []
        if vocab_pairs:
            terms = [p.get("term", "").strip().lower() for p in vocab_pairs if p.get("term")]
            # Xáo trộn các từ vựng để chọn ngẫu nhiên
            random.shuffle(terms)
            for term in terms:
                if len(matched_sentences) >= count:
                    break
                # Tìm xem có câu mẫu nào chứa từ khóa này không
                for s in self.SENTENCE_POOL:
                    sentence_text = s["correct_sentence"].lower()
                    # So khớp từ đơn lập để tránh khớp một phần từ (ví dụ 'eat' khớp với 'creative')
                    if f" {term} " in f" {sentence_text} " or sentence_text.startswith(term + " ") or sentence_text.endswith(" " + term) or sentence_text.endswith(" " + term + "."):
                        if s not in matched_sentences:
                            matched_sentences.append(s)
                            break

        # 2. Nếu chưa đủ số lượng, bổ sung câu từ Pool theo level và topic của giao diện
        fallback_sentences = [
            s for s in self.SENTENCE_POOL
            if s.get("level") == level and s.get("topic") == topic
        ]
        # Nếu không có câu nào đúng level/topic trong pool, lấy toàn bộ pool làm fallback
        if not fallback_sentences:
            fallback_sentences = self.SENTENCE_POOL[:]
            
        random.shuffle(fallback_sentences)
        
        for s in fallback_sentences:
            if len(matched_sentences) >= count:
                break
            if s not in matched_sentences:
                matched_sentences.append(s)
                
        # 3. Đảm bảo có ít nhất 1 câu hỏi nếu pool trống (tránh lỗi chia cho 0)
        if not matched_sentences:
            matched_sentences = [self.SENTENCE_POOL[0]]
            
        # 4. Trả về đúng schema
        return {
            "sentences": matched_sentences[:count]
        }

    def fisher_yates_shuffle(self, words: list[str]) -> list[str]:
        arr = list(words)
        for i in range(len(arr) - 1, 0, -1):
            j = random.randint(0, i)
            arr[i], arr[j] = arr[j], arr[i]
        return arr

    def render_ui_data(self, raw_result: dict) -> dict:
        sentences = raw_result.get("sentences", [])
        return {
            "questions": [
                {
                    "correct_sentence": s.get("correct_sentence", ""),
                    "shuffled_words": self.fisher_yates_shuffle(
                        s.get("correct_sentence", "").split()
                    ),
                    "hint": s.get("hint", ""),
                    "meaning_vi": s.get("meaning_vi", ""),
                    "key_vocabulary": s.get("key_vocabulary", []),
                    "difficulty_reason": s.get("difficulty_reason", ""),
                    "grammar_note": s.get("grammar_note", ""),
                    "word_count": len(s.get("correct_sentence", "").split()),
                }
                for s in sentences
            ]
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        user_str = (
            " ".join(user_input) if isinstance(user_input, list) else str(user_input)
        )
        correct_str = str(correct) if correct else ""
        norm_user = " ".join(user_str.strip().split()).lower()
        norm_correct = " ".join(correct_str.strip().split()).lower()
        is_correct = norm_user == norm_correct

        user_words = norm_user.split()
        correct_words = norm_correct.split()
        correct_positions = sum(
            1
            for i, w in enumerate(user_words)
            if i < len(correct_words) and w == correct_words[i]
        )

        return {
            "correct": is_correct,
            "user_sentence": user_str,
            "expected": correct_str,
            "correct_positions": correct_positions,
            "total_positions": len(correct_words),
            "points": 1 if is_correct else 0,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        shuffled = data.get("shuffled_words")
        if isinstance(shuffled, list):
            shuffled = " ".join(shuffled)
        else:
            shuffled = " ".join(
                self.fisher_yates_shuffle(data.get("correct_sentence", "").split())
            )
        return (f"Unscramble: {shuffled}", data.get("correct_sentence", ""))
