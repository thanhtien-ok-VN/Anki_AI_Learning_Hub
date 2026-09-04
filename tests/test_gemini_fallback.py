import unittest
from unittest.mock import MagicMock, patch
from llm.gemini import GeminiProvider, EC, RateLimitError


class TestGeminiFallback(unittest.TestCase):
    def test_no_keys_returns_error(self):
        provider = GeminiProvider([])
        res = provider.generate_structured("prompt", {})
        self.assertTrue(res.get("error"))
        self.assertEqual(res.get("error_code"), EC["NO_KEYS"])

    def test_key_detection(self):
        self.assertEqual(GeminiProvider.detect_key_type("AIzaSy12345"), "old (AIzaSy)")
        self.assertEqual(GeminiProvider.detect_key_type("AQ.67890"), "new (AQ.)")
        self.assertEqual(GeminiProvider.detect_key_type("other_key"), "unknown")

    def test_key_rotation_on_failure(self):
        keys = ["KEY_1_BAD", "KEY_2_GOOD"]
        provider = GeminiProvider(keys, model_name="auto")

        def mock_call_api(payload, key, model):
            if key == "KEY_1_BAD":
                raise RateLimitError("HTTP 429: Rate limit exceeded")
            return {"result": "success"}

        with patch.object(provider, '_call_api', side_effect=mock_call_api):
            res = provider.generate_structured("test prompt", {})
            self.assertFalse(res.get("error"))
            self.assertEqual(res.get("result"), "success")
            self.assertEqual(res.get("_key_used"), "key2 (unknown)")


if __name__ == '__main__':
    unittest.main()
