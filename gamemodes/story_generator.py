from typing import Any
from .base import GameModeBase

class StoryGeneratorMode(GameModeBase):
    name = "story"
    display_name = "Story Generator"
    icon = "📚"

    def render_ui_data(self, raw_result: dict) -> dict:
        import random
        story_data = raw_result.get("story", {})
        if isinstance(story_data, str):
            story_data = {
                "title": "",
                "content": story_data,
                "word_count": 0,
                "highlighted_vocab": [],
                "full_translation": ""
            }
            
        rendered_questions = []
        for i, q in enumerate(raw_result.get("questions", [])):
            options = q.get("options", [])
            
            # Xáo trộn options và tính correct_index
            indices = list(range(len(options)))
            random.shuffle(indices)
            shuffled_options = [options[j] for j in indices]
            
            correct_index = -1
            for idx, opt in enumerate(shuffled_options):
                if isinstance(opt, dict) and opt.get("is_correct"):
                    correct_index = idx
                    break
            
            rendered_questions.append({
                "id": q.get("id", i + 1),
                "type": q.get("type", "detail"),
                "question": q.get("question", ""),
                "options": shuffled_options,
                "correct_index": correct_index,
                "explanation": q.get("explanation", ""),
                "evidence_quote": q.get("evidence_quote", ""),
                "target_word": q.get("target_word", ""),
            })

        return {
            "story": {
                "title": story_data.get("title", ""),
                "content": story_data.get("content", ""),
                "word_count": story_data.get("word_count", 0),
                "highlighted_vocab": story_data.get("highlighted_vocab", []),
                "full_translation": story_data.get("full_translation", ""),
            },
            "questions": rendered_questions,
            "discussion_prompt": raw_result.get("discussion_prompt", ""),
        }

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        selected = int(user_input) if user_input is not None else -1
        correct_idx = -1
        options = correct if isinstance(correct, list) else []
        for i, o in enumerate(options):
            if isinstance(o, dict) and o.get("is_correct"):
                correct_idx = i
                break
            elif isinstance(o, int):
                correct_idx = int(correct)
                break
        is_correct = selected == correct_idx
        return {
            "correct": is_correct,
            "selected": selected,
            "correct_index": correct_idx,
            "points": 1 if is_correct else 0,
        }

    def check_all_answers(self, answers: list[dict]) -> dict:
        total = len(answers)
        correct = 0
        details = []
        for ans in answers:
            result = self.check_answer(ans.get("selected"), ans.get("options", ans.get("correct_index")))
            if result["correct"]:
                correct += 1
            details.append(result)
        return {
            "correct": correct,
            "total": total,
            "percentage": round((correct / total) * 100) if total else 0,
            "details": details,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        story = data.get("story", {})
        content = story.get("content", "") if isinstance(story, dict) else str(story)
        front = (content or "Story")[:80] + "..."
        return (front, content)
