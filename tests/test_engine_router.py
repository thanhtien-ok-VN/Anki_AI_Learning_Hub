import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock aqt and GUI dependencies so tests run completely standalone without Anki UI
sys.modules['aqt'] = MagicMock()
sys.modules['aqt.qt'] = MagicMock()
sys.modules['aqt.gui_hooks'] = MagicMock()
sys.modules['aqt.utils'] = MagicMock()

from core.engine import AIEngine


class TestEngineRouter(unittest.TestCase):
    @patch('core.engine.SessionTimer')
    def setUp(self, mock_timer):
        self.engine = AIEngine()

    def test_handle_js_message_generate_success(self):
        mock_result = {
            "questions": [
                {
                    "sentence": "I ___ a book.",
                    "target_word": "read",
                    "options": [
                        {"word": "read", "is_correct": True, "type": "correct"},
                        {"word": "red", "is_correct": False, "type": "synonym"}
                    ],
                    "explanation": "Test explanation"
                }
            ]
        }

        with patch.object(self.engine, '_handle_generate', return_value=mock_result):
            res = self.engine.handle_js_message('{"action": "generate", "data": {"gamemode": "fill_blank"}}')
            self.assertTrue(res.get("success"))
            self.assertEqual(res.get("data"), mock_result)

    def test_handle_js_message_invalid_action(self):
        res = self.engine.handle_js_message('{"action": "non_existent_action", "data": {}}')
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error_code"), "E_UNKNOWN")

    def test_handle_js_message_invalid_json(self):
        res = self.engine.handle_js_message('{invalid json')
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error_code"), "E_INTERNAL")

    def test_test_all_keys_cancellation(self):
        def mock_test(key, progress_callback=None):
            self.engine.cancel_event.set()
            return {"ok": True, "model": "test"}

        with patch.object(self.engine.settings, 'get_api_keys', return_value=['key1', 'key2']), \
             patch('core.api_client.GeminiClient.test_key_with_waterfall', side_effect=mock_test):
            res = self.engine._handle_test_all_keys()
            self.assertTrue(res.get("cancelled"))


    def test_aiengine_result_staticmethod(self):
        res = AIEngine._result(True, {"key": "val"}, "E_CODE", "msg")
        self.assertEqual(res, {"success": True, "data": {"key": "val"}, "error_code": "E_CODE", "message": "msg"})

    def test_handle_generate_offline_matching(self):
        mock_gm = MagicMock()
        mock_gm.is_offline = True
        mock_gm.generate.return_value = {"game_id": "123", "pairs": [1, 2, 3, 4, 5]}
        with patch.object(self.engine, 'get_gamemode', return_value=mock_gm):
            res = self.engine._handle_generate({"gamemode": "matching"})
            self.assertTrue(res.get("success"))
            self.assertEqual(res.get("data", {}).get("game_id"), "123")

    def test_handle_generate_offline_not_enough_vocab(self):
        mock_gm = MagicMock()
        mock_gm.is_offline = True
        mock_gm.generate.return_value = {"error": True, "error_code": "E_NOT_ENOUGH_VOCAB", "message": "Not enough vocab"}
        with patch.object(self.engine, 'get_gamemode', return_value=mock_gm):
            res = self.engine._handle_generate({"gamemode": "matching"})
            self.assertFalse(res.get("success"))
            self.assertEqual(res.get("error_code"), "E_NOT_ENOUGH_VOCAB")

    def test_handle_generate_ai_fill_blank_language_names(self):
        mock_client = MagicMock()
        mock_payload = {
            "questions": [
                {
                    "sentence": "She ______ a book.",
                    "target_word": "read",
                    "meaning": "đọc",
                    "full_translation": "Cô ấy đọc một cuốn sách.",
                    "options": [
                        {"word": "read", "is_correct": True, "type": "correct", "reason": "phù hợp"},
                        {"word": "red", "is_correct": False, "type": "wrong_context", "reason": "sai nghĩa"},
                        {"word": "write", "is_correct": False, "type": "wrong_context", "reason": "sai nghĩa"},
                        {"word": "sing", "is_correct": False, "type": "wrong_context", "reason": "sai nghĩa"}
                    ],
                    "explanation": "Từ read là chính xác."
                }
            ]
        }
        mock_client.generate_structured.return_value = mock_payload

        with patch.object(self.engine.settings, 'get_api_keys', return_value=['dummy_key']), \
             patch.object(self.engine, '_get_api_client', return_value=mock_client), \
             patch('core.prompt_manager.PromptManager.get_prompt', wraps=self.engine.get_prompt_manager().get_prompt) as mock_get_prompt:
            res = self.engine._handle_generate({
                "gamemode": "fill_blank",
                "language": "en",
                "level": "intermediate",
                "count": 1,
                "topic": "reading"
            })
            self.assertIn("questions", res)
            mock_get_prompt.assert_called()
            call_kwargs = mock_get_prompt.call_args.kwargs
            self.assertEqual(call_kwargs.get("source_lang"), "English")
            self.assertEqual(call_kwargs.get("target_lang"), "English")


if __name__ == '__main__':
    unittest.main()
