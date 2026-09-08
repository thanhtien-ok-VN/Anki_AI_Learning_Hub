"""HTTP network transport and rate limiting for Gemini API."""
import json
import random
import time
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from core.constants import RETRY_CONFIG
from core.logger import log, flow
from llm.gemini_models import (
    API_BASE,
    ApiError,
    RateLimitError,
    ModelNotFoundError,
    SchemaNotSupportedError,
)


class GeminiTransport:
    """Handles network dispatch, rate-limiting, and error mapping for Gemini."""

    _last_request_time = 0.0
    _min_interval = 1.5

    @classmethod
    def throttle(cls, cancel_event=None) -> None:
        """Enforce inter-request spacing to avoid bursts."""
        if cancel_event and cancel_event.is_set():
            raise ApiError("API request cancelled by user")
        now = time.time()
        since = now - cls._last_request_time
        if since < cls._min_interval:
            delay = cls._min_interval - since
            log.debug(f"Throttle: sleep {delay:.2f}s")
            time.sleep(delay)
        cls._last_request_time = time.time()

    @staticmethod
    def retry_delay(attempt: int, base: Optional[float] = None) -> float:
        """Calculate exponential backoff delay with random jitter."""
        b = base if base is not None else RETRY_CONFIG["rate_limit_base"]
        return b * (2 ** attempt) + random.uniform(0, RETRY_CONFIG["jitter_max"])

    @staticmethod
    def should_retry(code: int) -> bool:
        """Check whether HTTP status code qualifies for retry."""
        return code in RETRY_CONFIG["retry_codes"]

    @staticmethod
    def build_url(model: str) -> str:
        """Construct endpoint URL for generateContent."""
        return f"{API_BASE}/{model}:generateContent"

    @staticmethod
    def build_payload(
        prompt: str,
        schema: Optional[dict] = None,
        temperature: float = 0.7,
    ) -> dict:
        """Construct JSON payload for generateContent request."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if schema:
            payload["generationConfig"]["response_mime_type"] = "application/json"
            payload["generationConfig"]["response_schema"] = schema
        return payload

    @classmethod
    def execute_http(
        cls,
        payload: dict,
        key: str,
        model: str,
        cancel_event=None,
        timeout: float = 60.0,
    ) -> dict:
        """Send HTTP request to Gemini API and return decoded JSON response body."""
        if cancel_event and cancel_event.is_set():
            raise ApiError("API request cancelled by user")
        cls.throttle(cancel_event)

        url = cls.build_url(model)
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "x-goog-api-key": key}
        req = Request(url, data=data, headers=headers)

        log.debug(f"API call: model={model} url_len={len(data)}")
        start_t = time.time()

        import sys
        gemini_mod = sys.modules.get("llm.gemini")
        target_urlopen = (getattr(gemini_mod, "urlopen", None) if gemini_mod else None) or urlopen

        try:
            resp = target_urlopen(req, timeout=timeout)
            raw = json.loads(resp.read().decode("utf-8"))
            latency_ms = int((time.time() - start_t) * 1000)
            flow(phase="API", message=f"API call succeeded: model={model}, latency={latency_ms}ms")
            log.debug("API response OK", {"model": model, "latency_ms": latency_ms})
            return raw
        except HTTPError as e:
            code = e.code
            body = e.read().decode("utf-8", errors="replace")[:500]
            log.warn(f"HTTP {code}", {"model": model, "body": body[:200]})
            if cls.should_retry(code):
                raise RateLimitError(f"HTTP {code}: {body[:120]}")
            if code == 404:
                raise ModelNotFoundError(f"Model '{model}' not found for this key type")
            if "response_schema" in body.lower() or "response_mime_type" in body.lower():
                raise SchemaNotSupportedError(body)
            if code == 403:
                raise ApiError("API key invalid or not authorized")
            raise ApiError(f"HTTP {code}: {body}")
        except URLError as e:
            log.error("URLError", {"model": model, "reason": str(e.reason)})
            raise ApiError(f"Connection error: {e.reason}")
        except Exception as e:
            log.error("Unexpected HTTP error", {"error": str(e)})
            raise ApiError(str(e))
