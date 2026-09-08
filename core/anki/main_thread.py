"""Anki collection access and main thread execution primitives."""
from __future__ import annotations

from concurrent.futures import Future
import html
import re
import threading
from typing import Any, Callable, Dict, Optional

try:
    from aqt import mw
except ImportError:
    mw = None

_TAG_RE = re.compile(r"<[^>]*>")
_MEDIA_RE = re.compile(r"\[sound:[^\]]+\]", re.IGNORECASE)


def get_collection() -> Any:
    """Return the active Anki collection, or None if closed."""
    import sys
    deck_source = sys.modules.get("core.deck_source")
    if deck_source and hasattr(deck_source, "mw") and deck_source.mw is not None:
        return getattr(deck_source.mw, "col", None)
    return getattr(mw, "col", None)


def ok_response(data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format a successful operation envelope."""
    return {"success": True, "data": data or {}}


def error_response(code: str, message: str) -> Dict[str, Any]:
    """Format an error operation envelope."""
    return {"success": False, "error": True, "data": {}, "error_code": code, "message": message}


def plain_text(value: str) -> str:
    """Extract clean readable text from an Anki field without HTML or media markup."""
    value = _MEDIA_RE.sub("", value or "")
    value = _TAG_RE.sub(" ", value)
    return " ".join(html.unescape(value).split())


def run_on_main(fn: Callable[[], Any], timeout: float = 10.0) -> Any:
    """Safely execute a function on Anki's Qt main thread from any thread."""
    if threading.current_thread() is threading.main_thread():
        return fn()

    import sys
    deck_source = sys.modules.get("core.deck_source")
    target_mw = (getattr(deck_source, "mw", None) if deck_source else None) or mw

    if target_mw and hasattr(target_mw, "taskman") and hasattr(target_mw.taskman, "run_on_main"):
        fut = Future()

        def wrapper():
            try:
                fut.set_result(fn())
            except BaseException as e:
                fut.set_exception(e)

        target_mw.taskman.run_on_main(wrapper)
        return fut.result(timeout=timeout)

    return fn()
