import unittest

from core.sanitizer import (
    clean_json_response,
    normalize_answer,
    sanitize_html,
    sanitize_dict,
)


class TestSanitizer(unittest.TestCase):
    def test_clean_json_response_markdown(self):
        raw = "```json\n{\"foo\": \"bar\"}\n```"
        self.assertEqual(clean_json_response(raw), '{"foo": "bar"}')

    def test_clean_json_response_with_surrounding_text(self):
        raw = "Here is your JSON output:\n```\n{\"key\": 123}\n```\nHope it helps!"
        self.assertEqual(clean_json_response(raw), '{"key": 123}')

    def test_clean_json_response_empty_and_invalid(self):
        self.assertEqual(clean_json_response(""), "")
        self.assertEqual(clean_json_response(None), "")
        self.assertEqual(clean_json_response("just some text with no braces"), "just some text with no braces")

    def test_normalize_answer(self):
        self.assertEqual(normalize_answer("  Hello World!  "), "hello world")
        self.assertEqual(normalize_answer("She   is  dancing..."), "she is dancing")
        self.assertEqual(normalize_answer(""), "")
        self.assertEqual(normalize_answer(None), "")
        self.assertEqual(normalize_answer("Wait?!"), "wait")

    def test_sanitize_html_safe_tags(self):
        raw = "<b>Bold</b> <i>Italic</i> <u>Underline</u> <code>x = 1</code> <p>Paragraph</p> <br> <hr>"
        self.assertEqual(sanitize_html(raw), raw)

    def test_sanitize_html_dangerous_tags(self):
        raw = "Hello <script>alert('XSS')</script> <iframe src='http://evil.com'></iframe> World"
        cleaned = sanitize_html(raw)
        self.assertNotIn("script", cleaned.lower())
        self.assertNotIn("iframe", cleaned.lower())
        self.assertIn("Hello", cleaned)
        self.assertIn("World", cleaned)

    def test_sanitize_html_inline_handlers(self):
        raw = '<span onclick="alert(1)" onmouseover="evil()">Click me</span>'
        cleaned = sanitize_html(raw)
        self.assertNotIn("onclick", cleaned)
        self.assertNotIn("onmouseover", cleaned)
        self.assertIn("Click me", cleaned)

    def test_sanitize_dict_recursive(self):
        payload = {
            ' "key_with_quotes" ': "<script>bad()</script><b>Safe</b>",
            "nested": [
                {"text": "Normal text", "xss": "<iframe src='bad'></iframe>ok"},
                123,
                True,
            ],
        }
        sanitized = sanitize_dict(payload)
        self.assertIn("key_with_quotes", sanitized)
        self.assertNotIn(' "key_with_quotes" ', sanitized)
        self.assertEqual(sanitized["key_with_quotes"], "<b>Safe</b>")
        self.assertEqual(sanitized["nested"][0]["xss"], "ok")
        self.assertEqual(sanitized["nested"][1], 123)


if __name__ == "__main__":
    unittest.main()
