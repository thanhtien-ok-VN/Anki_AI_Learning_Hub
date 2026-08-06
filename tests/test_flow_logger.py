import os
import sys
import pytest

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ADDON_PATH not in sys.path:
    sys.path.insert(0, ADDON_PATH)

from core.logger import flow, FlowTimer, read_flow_logs, clear_all_logs, FLOW_LOG_PATH


def test_flow_logging_and_read():
    clear_all_logs()
    
    flow(phase="CONNECT", gamemode="fill_blank", message="Test connect message", duration_ms=50, extra={"test_key": "val1"})
    flow(phase="AI", gamemode="cloze", message="Test AI message", duration_ms=120, extra={"test_key": "val2"})
    
    entries = read_flow_logs(limit=10)
    assert len(entries) >= 2
    assert entries[0]["phase"] == "CONNECT"
    assert entries[0]["gamemode"] == "fill_blank"
    assert entries[0]["duration_ms"] == 50
    assert entries[1]["phase"] == "AI"
    assert entries[1]["gamemode"] == "cloze"


def test_flow_timer():
    with FlowTimer("SYSTEM", gamemode="taboo", message="Timer test") as timer:
        timer.extra["custom_param"] = 123

    entries = read_flow_logs(phase="SYSTEM")
    assert len(entries) >= 1
    latest = entries[-1]
    assert latest["phase"] == "SYSTEM"
    assert latest["gamemode"] == "taboo"
    assert latest["extra"].get("custom_param") == 123
    assert latest["duration_ms"] is not None


def test_clear_all_logs():
    flow(phase="RENDER", gamemode="story", message="Clear test")
    assert os.path.isfile(FLOW_LOG_PATH)
    
    ok = clear_all_logs()
    assert ok is True
    logs = read_flow_logs()
    assert len(logs) == 0
