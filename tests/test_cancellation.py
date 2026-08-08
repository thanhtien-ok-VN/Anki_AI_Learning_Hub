import sys
import unittest
import threading
from unittest.mock import MagicMock, patch

# Mock aqt and GUI dependencies for standalone test execution
sys.modules['aqt'] = MagicMock()
sys.modules['aqt.qt'] = MagicMock()
sys.modules['aqt.gui_hooks'] = MagicMock()
sys.modules['aqt.utils'] = MagicMock()

from core.engine import AIEngine


class CancellationIsolationTests(unittest.TestCase):
    """Unit tests for task cancellation event isolation and unpoisoning."""

    @patch('core.engine.SessionTimer')
    def setUp(self, mock_timer):
        self.engine = AIEngine()

    def test_cancelled_run_does_not_poison_next_run(self):
        """Test that calling cancel_current_task() on run 1 does not poison run 2."""
        # 1. Start task 1 and cancel it
        evt1 = self.engine._new_cancel_event()
        self.engine.cancel_current_task()
        self.assertTrue(evt1.is_set())

        # 2. Start task 2
        evt2 = self.engine._new_cancel_event()
        self.assertFalse(evt2.is_set())
        # Evt1 remains set, while Evt2 is fresh and active
        self.assertTrue(evt1.is_set())
        self.assertFalse(evt2.is_set())

    def test_overlapping_test_all_keys_event_isolation(self):
        """Test that two overlapping _handle_test_all_keys calls run with isolated events."""
        with patch("core.settings.SettingsManager.get_api_keys", return_value=["KEY1"]):
            with patch("core.api_client.GeminiClient") as mock_client_cls:
                mock_client = MagicMock()
                mock_client_cls.return_value = mock_client
                mock_client.test_key_with_waterfall.return_value = {"ok": True, "model": "gemini-1.5-flash"}

                # Run 1 creates event 1
                evt1 = self.engine._new_cancel_event()
                self.engine.cancel_current_task()  # Cancel run 1

                # Run 2 starts immediately and creates event 2
                res2 = self.engine._handle_test_all_keys()

                # Verify run 2 succeeded because it was isolated from event 1
                self.assertNotIn("cancelled", res2)
                self.assertEqual(len(res2.get("results", [])), 1)
                self.assertTrue(res2["results"][0]["ok"])


if __name__ == "__main__":
    unittest.main()
