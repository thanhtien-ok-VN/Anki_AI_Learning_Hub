import json
import os
import sys
import time
import traceback
from datetime import datetime

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(ADDON_PATH, "user_files", "ai_hub.log")
MAX_LOG_BYTES = 1 * 1024 * 1024


class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class Logger:
    def __init__(self, name: str = "AIHub"):
        self.name = name
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    def _rotate_if_needed(self):
        if not os.path.isfile(LOG_PATH):
            return
        try:
            size = os.path.getsize(LOG_PATH)
            if size > MAX_LOG_BYTES:
                base = LOG_PATH
                idx = 1
                while os.path.isfile(f"{base}.{idx}"):
                    idx += 1
                os.rename(base, f"{base}.{idx}")
        except Exception:
            pass

    def _write(self, level: str, message: str, extra: dict = None):
        self._rotate_if_needed()
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
        if level in (LogLevel.ERROR, LogLevel.WARN):
            print(line, file=sys.stderr)
        else:
            print(line)

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
