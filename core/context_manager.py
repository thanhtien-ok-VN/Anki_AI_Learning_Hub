import json
import os
import time
from typing import Any, Optional

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEXT_PATH = os.path.join(ADDON_PATH, "user_files", "context.json")


class ContextManager:
    def __init__(self, path: str = CONTEXT_PATH):
        self.path = path

    def save(self, gamemode: str, data: dict, ttl_minutes: int = 60) -> dict:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        ctx = {
            "gamemode": gamemode,
            "data": data,
            "saved_at": time.time(),
            "ttl": ttl_minutes * 60,
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(ctx, f, ensure_ascii=False, indent=2)
        return ctx

    def load(self) -> Optional[dict]:
        if not os.path.isfile(self.path):
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                ctx = json.load(f)
            elapsed = time.time() - ctx.get("saved_at", 0)
            ttl = ctx.get("ttl", 3600)
            if elapsed > ttl:
                self.clear()
                return None
            return ctx
        except Exception:
            self.clear()
            return None

    def get_expired_seconds(self) -> Optional[int]:
        ctx = self.load()
        if not ctx:
            return None
        elapsed = time.time() - ctx.get("saved_at", 0)
        return int(elapsed)

    def clear(self):
        try:
            if os.path.isfile(self.path):
                os.remove(self.path)
        except Exception:
            pass

    def has_valid(self) -> bool:
        return self.load() is not None
