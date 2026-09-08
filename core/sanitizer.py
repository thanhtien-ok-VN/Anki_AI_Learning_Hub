"""Text sanitization and normalization utilities.

Decoupled from core.engine to eliminate circular dependencies across
LLM client and gamemodes. Pre-compiles all regular expressions at module
import time for optimal runtime performance.
"""
from __future__ import annotations

import re
from typing import Any

# Pre-compiled regular expressions for performance
_MD_CODE_BLOCK_RE = re.compile(r"```(?:json)?")
_NORMALIZE_WS_RE = re.compile(r"\s+")
_DANGEROUS_TAGS_BLOCK_RE = re.compile(
    r"<(script|iframe|style|link|embed|object|form|input|button)\b[^<]*(?:(?!</\1>)<[^<]*)*</\1>",
    flags=re.IGNORECASE | re.DOTALL,
)
_DANGEROUS_TAGS_SELF_RE = re.compile(
    r"<(script|iframe|style|link|embed|object|form|input|button)\b[^>]*/>?",
    flags=re.IGNORECASE,
)
_INLINE_EVENT_RE = re.compile(
    r"\s*on\w+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
    flags=re.IGNORECASE,
)
_JS_URI_RE = re.compile(
    r"(href|src|action)\s*=\s*[\"']?\s*javascript:[^\"'>]*[\"']?",
    flags=re.IGNORECASE,
)
_TAG_WHITELIST_RE = re.compile(r"<(/?[a-zA-Z0-9]+)(?:\s+[^>]*)?>")
_ALLOWED_HTML_TAGS = frozenset({"b", "i", "u", "br", "p", "span", "code", "hr"})


def clean_json_response(raw_text: str) -> str:
    """Strip markdown code blocks and extra text, returning pure JSON string."""
    if not raw_text or not isinstance(raw_text, str):
        return raw_text or ""
    cleaned = _MD_CODE_BLOCK_RE.sub("", raw_text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start : end + 1]
    return cleaned.strip()


def normalize_answer(text: str) -> str:
    """Normalize answer for comparison (lowercase, trimmed whitespace, stripped punctuation)."""
    if not text:
        return ""
    return _NORMALIZE_WS_RE.sub(" ", str(text).lower().strip()).rstrip(".,!?;:")


def sanitize_html(text: str) -> str:
    """Strip all HTML tags except safe formatting ones: b, i, u, br, p, span, code, hr."""
    if not text or not isinstance(text, str):
        return text or ""
    # 1. Strip dangerous tags completely along with their contents
    text = _DANGEROUS_TAGS_BLOCK_RE.sub("", text)
    text = _DANGEROUS_TAGS_SELF_RE.sub("", text)
    # 2. Strip inline event attributes like onclick=...
    text = _INLINE_EVENT_RE.sub("", text)
    # 3. Strip javascript: URIs
    text = _JS_URI_RE.sub("", text)
    # 4. Strip any tag NOT in the whitelist
    def tag_repl(match: re.Match) -> str:
        tag_name = match.group(1).lstrip("/").lower()
        if tag_name in _ALLOWED_HTML_TAGS:
            return match.group(0)
        return ""

    return _TAG_WHITELIST_RE.sub(tag_repl, text)


def sanitize_dict(val: Any) -> Any:
    """Recursively sanitize strings within a dictionary or list, stripping bad quotes from keys."""
    if isinstance(val, dict):
        cleaned_dict = {}
        for k, v in val.items():
            clean_key = k.strip().strip('"').strip("'").strip() if isinstance(k, str) else k
            cleaned_dict[clean_key] = sanitize_dict(v)
        return cleaned_dict
    elif isinstance(val, list):
        return [sanitize_dict(item) for item in val]
    elif isinstance(val, str):
        return sanitize_html(val)
    return val


__all__ = [
    "clean_json_response",
    "normalize_answer",
    "sanitize_html",
    "sanitize_dict",
]
