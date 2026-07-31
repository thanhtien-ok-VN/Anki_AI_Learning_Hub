import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from core.api_client import ApiError, GeminiClient, RateLimitError


class GeminiClientErrorTests(unittest.TestCase):
    def setUp(self):
        self.log_patch = patch("core.api_client.log")
        self.log_patch.start()
        self.addCleanup(self.log_patch.stop)
        GeminiClient._last_request_time = 0

    def test_returns_no_keys_without_raising(self):
        result = GeminiClient([]).generate_structured("prompt", max_retries=1)

        self.assertTrue(result["error"])
        self.assertEqual(result["error_code"], "E_NO_KEYS")

    def test_returns_rate_limit_when_all_attempts_are_limited(self):
        client = GeminiClient(["AIzaSy-test"], model_name="test-model")
        with patch.object(client, "_call_api", side_effect=RateLimitError("HTTP 429")):
            result = client.generate_structured("prompt", max_retries=1)

        self.assertTrue(result["error"])
        self.assertEqual(result["error_code"], "E_RATE_LIMIT")
        self.assertNotIn("HTTP 429", result["message"])

    def test_returns_generic_api_message_without_transport_details(self):
        client = GeminiClient(["AIzaSy-test"], model_name="test-model")
        transport_detail = "Connection error: api.example.test refused request"
        with patch.object(client, "_call_api", side_effect=ApiError(transport_detail)):
            result = client.generate_structured("prompt", max_retries=1)

        self.assertTrue(result["error"])
        self.assertEqual(result["error_code"], "E_API_ERROR")
        self.assertNotIn("api.example.test", result["message"])

    def test_http_429_becomes_rate_limit_result(self):
        client = GeminiClient(["AIzaSy-test"], model_name="test-model")
        http_error = HTTPError(
            "https://example.test", 429, "Too many requests", None,
            io.BytesIO(b'{"error": "too many requests"}'),
        )
        with patch("core.api_client.urlopen", side_effect=http_error):
            result = client.generate_structured("prompt", max_retries=1)

        self.assertEqual(result["error_code"], "E_RATE_LIMIT")
        self.assertNotIn("429", result["message"])

    def test_network_failure_becomes_safe_api_result(self):
        client = GeminiClient(["AIzaSy-test"], model_name="test-model")
        with patch("core.api_client.urlopen", side_effect=URLError("offline host")):
            result = client.generate_structured("prompt", max_retries=1)

        self.assertEqual(result["error_code"], "E_API_ERROR")
        self.assertNotIn("offline host", result["message"])

    def test_key_test_hides_http_response_body(self):
        client = GeminiClient(["AIzaSy-test"], model_name="test-model")
        http_error = HTTPError(
            "https://example.test", 500, "Server error", None,
            io.BytesIO(b'{"private": "response body"}'),
        )
        with patch("core.api_client.urlopen", side_effect=http_error):
            result = client.test_key_with_waterfall("AIzaSy-test", max_retries=1)

        self.assertEqual(result["error_code"], "E_RATE_LIMIT")
        self.assertNotIn("response body", result["error"])

    def test_public_generate_converts_unexpected_errors_to_internal_result(self):
        client = GeminiClient(["AIzaSy-test"], model_name="test-model")
        with patch.object(client, "_try_keys", side_effect=RuntimeError("unexpected detail")):
            result = client.generate_structured("prompt")

        self.assertTrue(result["error"])
        self.assertEqual(result["error_code"], "E_INTERNAL")
        self.assertNotIn("unexpected detail", result["message"])

    def test_text_result_preserves_error_for_bridge_callers(self):
        client = GeminiClient(["AIzaSy-test"], model_name="test-model")
        expected = {
            "error": True,
            "error_code": "E_RATE_LIMIT",
            "message": "AI is temporarily busy. Please try again later.",
        }
        with patch.object(client, "_try_keys", return_value=expected):
            result = client.generate_text_result("prompt")

        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
