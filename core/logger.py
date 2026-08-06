import json
import os
import time
import uuid
import traceback
from datetime import datetime
from typing import Optional, Any, Dict, List

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(ADDON_PATH, "user_files", "ai_hub.log")
FLOW_LOG_PATH = os.path.join(ADDON_PATH, "user_files", "ai_hub_flow.jsonl")
MAX_LOG_BYTES = 1 * 1024 * 1024
SESSION_ID = uuid.uuid4().hex[:8]


class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Logger:
    def __init__(self, name: str = "AIHub"):
        self.name = name
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    def _rotate_if_needed(self, path: str):
        if not os.path.isfile(path):
            return
        try:
            if os.path.getsize(path) > MAX_LOG_BYTES:
                idx = 1
                while os.path.isfile(f"{path}.{idx}"):
                    idx += 1
                os.rename(path, f"{path}.{idx}")
        except Exception:
            pass

    def _write(self, level: str, message: str, extra: dict = None):
        self._rotate_if_needed(LOG_PATH)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
        parts = [f"[{ts}]", f"[{level}]", f"[{self.name}]", message]
        if extra:
            parts.append(json.dumps(extra, ensure_ascii=False, default=str))
        line = " ".join(parts)
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def debug(self, message: str, extra: dict = None):
        self._write(LogLevel.DEBUG, message, extra)

    def info(self, message: str, extra: dict = None):
        self._write(LogLevel.INFO, message, extra)

    def warn(self, message: str, extra: dict = None):
        self._write(LogLevel.WARN, message, extra)

    def error(self, message: str, extra: dict = None):
        self._write(LogLevel.ERROR, message, extra)

    def exception(self, message: str, extra: dict = None):
        tb = traceback.format_exc()
        ext = dict(extra or {})
        ext["traceback"] = tb.strip().split("\n")[-5:]
        self._write(LogLevel.ERROR, message, ext)


log = Logger("AIHub")


def flow(
    phase: str,
    gamemode: str = "",
    message: str = "",
    level: str = "INFO",
    duration_ms: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    """Write structured JSONL log entry for application observability."""
    os.makedirs(os.path.dirname(FLOW_LOG_PATH), exist_ok=True)
    log._rotate_if_needed(FLOW_LOG_PATH)
    entry = {
        "ts": datetime.now().isoformat(),
        "session_id": SESSION_ID,
        "level": level,
        "phase": phase.upper(),
        "gamemode": gamemode,
        "message": message,
        "duration_ms": duration_ms,
        "extra": extra or {},
    }
    try:
        with open(FLOW_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


class FlowTimer:
    """Context manager measuring execution time and logging as structured flow entry."""

    def __init__(
        self,
        phase: str,
        gamemode: str = "",
        message: str = "",
        level: str = "INFO",
    ):
        self.phase = phase
        self.gamemode = gamemode
        self.message = message
        self.level = level
        self.extra: Dict[str, Any] = {}
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.monotonic() - self.start_time) * 1000)
        lvl = LogLevel.ERROR if exc_type else self.level
        msg = f"{self.message} (Error: {exc_val})" if exc_type else self.message
        flow(
            phase=self.phase,
            gamemode=self.gamemode,
            message=msg,
            level=lvl,
            duration_ms=duration_ms,
            extra=self.extra,
        )


def read_flow_logs(
    limit: int = 200,
    level: Optional[str] = None,
    phase: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Read and filter structured JSONL flow log entries."""
    if not os.path.isfile(FLOW_LOG_PATH):
        return []
    entries = []
    try:
        with open(FLOW_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if level and level != "ALL" and data.get("level") != level:
                        continue
                    if phase and phase != "ALL" and data.get("phase") != phase:
                        continue
                    entries.append(data)
                except Exception:
                    continue
    except Exception:
        pass
    return entries[-limit:]


def clear_all_logs() -> bool:
    """Delete all main log and flow log files including rotated backups."""
    user_files = os.path.dirname(LOG_PATH)
    if not os.path.isdir(user_files):
        return False
    try:
        for fname in os.listdir(user_files):
            if fname.startswith("ai_hub.log") or fname.startswith("ai_hub_flow.jsonl"):
                full_path = os.path.join(user_files, fname)
                if os.path.isfile(full_path):
                    os.remove(full_path)
        return True
    except Exception:
        return False
