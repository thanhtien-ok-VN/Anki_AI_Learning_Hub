"""Gemini response parsing, cleaning, and content safety verification."""
import json
from typing import Any, Dict

from core.logger import log
from core.sanitizer import clean_json_response
from llm.gemini_models import ApiError, EC


def clean_dict(val: Any) -> Any:
    """Recursively strip surrounding whitespace and quotes from dictionary keys and string values."""
    if isinstance(val, dict):
        return {
            k.strip().strip('"').strip("'").strip(): clean_dict(v)
            for k, v in val.items()
            if isinstance(k, str)
        }
    elif isinstance(val, list):
        return [clean_dict(item) for item in val]
    return val


def parse_gemini_raw_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and validate text and structured JSON from Gemini raw API response dict."""
    candidates = raw.get("candidates", [])
    if not candidates:
        log.warn("No candidates in response", {"raw": str(raw)[:200]})
        raise ApiError("No candidates in response")

    candidate = candidates[0]
    reason = candidate.get("finishReason", "")

    if reason == "SAFETY":
        return {"error": True, "error_code": EC["SAFETY"], "message": "Content blocked by safety settings. Try rephrasing."}
    if reason == "RECITATION":
        return {"error": True, "error_code": EC["RECITATION"], "message": "Content blocked due to recitation. Try a different topic."}

    text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
    if not text:
        log.warn("Empty response text")
        raise ApiError("Empty response text")

    cleaned = clean_json_response(text)
    if not cleaned:
        raise ApiError(f"Empty response after cleaning: {text[:120]}")
    try:
        parsed = json.loads(cleaned)
        return clean_dict(parsed)
    except json.JSONDecodeError as e:
        raise ApiError(f"JSON parse failed after clean_json_response: {e}")
