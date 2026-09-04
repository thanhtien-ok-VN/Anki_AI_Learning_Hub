import os
import tempfile
import unittest
from unittest.mock import patch

from core.logger import Logger


class LoggerTests(unittest.TestCase):
    def test_warn_and_error_write_to_file_without_printing(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = os.path.join(directory, "ai_hub.log")
            with patch("core.logger.LOG_PATH", log_path), patch("builtins.print") as output:
                logger = Logger("Test")
                logger.warn("rate limited")
                logger.error("network failed")

                self.assertFalse(output.called)
                self.assertTrue(os.path.exists(log_path))
                with open(log_path, encoding="utf-8") as log_file:
                    content = log_file.read()
                self.assertIn("[WARN] [Test] rate limited", content)
                self.assertIn("[ERROR] [Test] network failed", content)


if __name__ == "__main__":
    unittest.main()
