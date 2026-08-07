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


if __name__ == '__main__':
    unittest.main()
