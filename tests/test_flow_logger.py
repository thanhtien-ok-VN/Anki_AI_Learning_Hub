import os
import sys
import threading
import unittest

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ADDON_PATH not in sys.path:
    sys.path.insert(0, ADDON_PATH)

from core.logger import flow, FlowTimer, read_flow_logs, clear_all_logs, FLOW_LOG_PATH
from core.settings import SettingsManager


class FlowLoggerTests(unittest.TestCase):
    def setUp(self):
        clear_all_logs()

    def test_flow_logging_and_read(self):
        flow(phase="CONNECT", gamemode="fill_blank", message="Test connect message", duration_ms=50, extra={"test_key": "val1"})
        flow(phase="AI", gamemode="cloze", message="Test AI message", duration_ms=120, extra={"test_key": "val2"})

        entries = read_flow_logs(limit=10)
        self.assertGreaterEqual(len(entries), 2)
        self.assertEqual(entries[0]["phase"], "CONNECT")
        self.assertEqual(entries[0]["gamemode"], "fill_blank")
        self.assertEqual(entries[0]["duration_ms"], 50)
        self.assertEqual(entries[1]["phase"], "AI")

    def test_flow_timer(self):
        with FlowTimer("SYSTEM", gamemode="taboo", message="Timer test") as timer:
            timer.extra["custom_param"] = 123

        entries = read_flow_logs(phase="SYSTEM")
        self.assertGreaterEqual(len(entries), 1)
        latest = entries[-1]
        self.assertEqual(latest["phase"], "SYSTEM")
        self.assertEqual(latest["gamemode"], "taboo")
        self.assertEqual(latest["extra"].get("custom_param"), 123)
        self.assertIsNotNone(latest["duration_ms"])

    def test_multithread_safety(self):
        threads = []
        def worker(idx):
            for i in range(20):
                flow(phase="AI", gamemode="fill_blank", message=f"Thread {idx} step {i}")

        for t_idx in range(5):
            t = threading.Thread(target=worker, args=(t_idx,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        logs = read_flow_logs(limit=200)
        self.assertEqual(len(logs), 100)

    def test_key_masking_security(self):
        sm = SettingsManager()
        sm._settings.clear()
        sm._settings.update({
            "api_key1": "AQ.Ab8",          # 6 chars: <= 12 -> AQ****b8
            "api_key2": "AQ.Ab8123456789",  # 16 chars: > 12 -> AQ.A...6789
            "api_key3": "   ",             # whitespace -> ignored
            "api_key4": "",                # empty -> ignored
        })
        active = sm.get_active_keys()
        self.assertEqual(len(active), 2)
        self.assertEqual(active[0], "AQ.Ab8")
        self.assertEqual(active[1], "AQ.Ab8123456789")

        masked = [m for m in sm.get_masked_api_keys() if m]
        self.assertEqual(len(masked), 2)
        self.assertEqual(masked[0], "AQ****b8")
        self.assertEqual(masked[1], "AQ.A...6789")


if __name__ == "__main__":
    unittest.main()
