import json
import time
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .logger import log

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Error codes
EC = {
    "SUCCESS": 0,
    "NO_KEYS": "E_NO_KEYS",
    "RATE_LIMIT": "E_RATE_LIMIT",
    "MODEL_NOT_FOUND": "E_MODEL_NOT_FOUND",
    "SCHEMA_NOT_SUPPORTED": "E_SCHEMA_UNSUPPORTED",
    "API_ERROR": "E_API_ERROR",
    "PARSE_FAILED": "E_PARSE_FAILED",
    "SAFETY": "E_SAFETY",
    "RECITATION": "E_RECITATION",
    "EMPTY_RESPONSE": "E_EMPTY_RESPONSE",
    "KEY_INVALID": "E_KEY_INVALID",
}


class GeminiClient:
    
    _last_request_time = 0.0
    _min_interval = 1.5

    MODEL_MAP = {
        "AQ.": "gemini-flash-latest",
        "AIzaSy": "gemini-1.5-flash",
    }

    def __init__(self, api_keys: list[str], model_name: str = "auto"):
        self.keys = [k.strip() for k in api_keys if k.strip()]
        self.model_name = model_name
        self.last_response = None
        self._active_key_index = 0
        self._unhealthy_until: dict[int, float] = {}
        log.info("GeminiClient init", {
            "key_count": len(self.keys),
            "key_types": [self.detect_key_type(k) for k in self.keys],
            "model": model_name,
        })

    @staticmethod
    def detect_key_type(api_key: str) -> str:
        k = api_key.strip()
        if k.startswith("AQ."):
            return "new (AQ.)"
        if k.startswith("AIzaSy"):
            return "old (AIzaSy)"
        return "unknown"

    @staticmethod
    def resolve_model(preferred: str, api_key: str) -> str:
        if preferred and preferred != "auto":
            return preferred
        for prefix, model in GeminiClient.MODEL_MAP.items():
            if api_key.startswith(prefix):
                return model
        return "gemini-1.5-flash"

    def _err(self, code: str, msg: str, extra: dict = None) -> dict:
        result = {"error": True, "error_code": code, "message": msg}
        if extra:
            result.update(extra)
        log.warn(f"API error [{code}]: {msg}", extra)
        return result

    def _ok(self, data: dict, key_label: str, model: str) -> dict:
        data["_key_used"] = key_label
        data["_model_used"] = model
        data["error_code"] = EC["SUCCESS"]
        return data

    def _build_url(self, model: str) -> str:
        return f"{API_BASE}/{model}:generateContent"

    def _build_payload(self, prompt: str, schema: Optional[dict] = None, temperature: float = 0.7) -> dict:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if schema:
            payload["generationConfig"]["response_mime_type"] = "application/json"
            payload["generationConfig"]["response_schema"] = schema
        return payload

    @classmethod
    def _throttle(cls):
        now = time.time()
        since = now - cls._last_request_time
        if since < cls._min_interval:
            delay = cls._min_interval - since
            log.debug(f"Throttle: sleep {delay:.2f}s")
            time.sleep(delay)
        cls._last_request_time = time.time()

    def _call_api(self, payload: dict, key: str, model: str) -> dict:
        self._throttle()
        url = self._build_url(model)
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "x-goog-api-key": key}
        req = Request(url, data=data, headers=headers)

        log.debug(f"API call: model={model} url_len={len(data)}")

        try:
            resp = urlopen(req, timeout=60)
            self.last_response = resp
            raw = json.loads(resp.read().decode("utf-8"))
            log.debug("API response OK", {"model": model})
        except HTTPError as e:
            code = e.code
            body = e.read().decode("utf-8", errors="replace")[:500]
            log.warn(f"HTTP {code}", {"model": model, "body": body[:200]})
            if code == 429:
                raise RateLimitError("Rate limited (quota exceeded)")
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

        return self._parse_response(raw)

    def _parse_response(self, raw: dict) -> dict:
        candidates = raw.get("candidates", [])
        if not candidates:
            log.warn("No candidates in response", {"raw": str(raw)[:200]})
            raise ApiError("No candidates in response")

        candidate = candidates[0]
        reason = candidate.get("finishReason", "")

        if reason == "SAFETY":
            return self._err(EC["SAFETY"], "Content blocked by safety settings. Try rephrasing.")
        if reason == "RECITATION":
            return self._err(EC["RECITATION"], "Content blocked due to recitation. Try a different topic.")

        text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
        if not text:
            log.warn("Empty response text")
            raise ApiError("Empty response text")

        def _clean_dict(val):
            if isinstance(val, dict):
                return {k.strip().strip('"').strip("'").strip(): _clean_dict(v) for k, v in val.items() if isinstance(k, str)}
            elif isinstance(val, list):
                return [_clean_dict(item) for item in val]
            return val

        stripped = text.strip()
        if stripped.startswith("{"):
            try:
                parsed = json.loads(stripped)
                return _clean_dict(parsed)
            except json.JSONDecodeError as e:
                raise ApiError(f"JSON parse failed: {e}")
        if stripped.startswith("```"):
            for marker in ["```json\n", "```\n", "```"]:
                if marker in stripped:
                    stripped = stripped.split(marker, 1)[1]
                    if stripped.endswith("```"):
                        stripped = stripped[:-3]
                    break
            try:
                parsed = json.loads(stripped.strip())
                return _clean_dict(parsed)
            except json.JSONDecodeError as e:
                raise ApiError(f"JSON parse (codeblock) failed: {e}")
        raise ApiError(f"Response is not JSON: {text[:120]}")

    def _try_keys(self, payload: dict, max_retries: int, base_delay: float) -> dict:
        if not self.keys:
            return self._err(EC["NO_KEYS"], "No API keys configured. Set at least one in Settings.")

        has_schema = "response_schema" in payload.get("generationConfig", {})
        last_error = ""
        now = time.monotonic()
        order = [self._active_key_index] + [i for i in range(len(self.keys)) if i != self._active_key_index]
        eligible = [i for i in order if self._unhealthy_until.get(i, 0) <= now]
        # When all keys are cooling down, make one attempt with the soonest key.
        if not eligible:
            eligible = [min(range(len(self.keys)), key=lambda i: self._unhealthy_until.get(i, 0))]

        for position, idx in enumerate(eligible):
            key = self.keys[idx]
            model = self.resolve_model(self.model_name, key)
            key_label = f"key{idx+1} ({self.detect_key_type(key)})"

            if position > 0:
                time.sleep(0.25)

            for attempt in range(max_retries):
                try:
                    log.debug(f"Trying {key_label} attempt {attempt+1}/{max_retries}", {"model": model})
                    result = self._call_api(payload, key, model)
                    if isinstance(result, dict) and not result.get("error"):
                        self._active_key_index = idx
                        self._unhealthy_until.pop(idx, None)
                        return self._ok(result, key_label, model)
                    return result
                except RateLimitError:
                    self._unhealthy_until[idx] = time.monotonic() + 60
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        log.warn(f"{key_label} rate limited, retry in {delay}s")
                        time.sleep(delay)
                        continue
                    last_error = f"{key_label}: rate limited after {max_retries} retries"
                except ModelNotFoundError as e:
                    self._unhealthy_until[idx] = time.monotonic() + 300
                    last_error = f"{key_label}: {e}"
                    log.warn(last_error)
                    break
                except SchemaNotSupportedError as e:
                    if has_schema:
                        log.info(f"{key_label} schema unsupported, retry as text")
                        new_payload = dict(payload)
                        new_payload["generationConfig"] = dict(payload.get("generationConfig", {}))
                        new_payload["generationConfig"].pop("response_schema", None)
                        new_payload["generationConfig"]["response_mime_type"] = "text/plain"
                        try:
                            result = self._call_api(new_payload, key, model)
                            if isinstance(result, dict) and not result.get("error"):
                                self._active_key_index = idx
                                self._unhealthy_until.pop(idx, None)
                                return self._ok(result, f"{key_label} (text fallback)", model)
                            return result
                        except Exception as e2:
                            last_error = f"{key_label}: schema+text both failed: {e2}"
                            log.error(last_error)
                            break
                    last_error = f"{key_label}: {e}"
                    break
                except ApiError as e:
                    last_error = f"{key_label}: {e}"
                    # Invalid/unauthorised keys should not be retried on every
                    # request; transient transport failures get a shorter rest.
                    delay = 3600 if "invalid" in str(e).lower() or "authoriz" in str(e).lower() else 20
                    self._unhealthy_until[idx] = time.monotonic() + delay
                    if attempt < max_retries - 1:
                        log.warn(f"{last_error}, retry in {base_delay}s")
                        time.sleep(base_delay)
                        continue
                    break
                except Exception as e:
                    last_error = f"{key_label}: {e}"
                    if attempt < max_retries - 1:
                        time.sleep(base_delay)
                        continue
                    break

        return self._err(EC["API_ERROR"], f"All keys failed. Last: {last_error}")

    def generate_structured(
        self,
        prompt: str,
        response_schema: Optional[dict] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
        base_delay: float = 4.0,
    ) -> dict:
        payload = self._build_payload(prompt, response_schema, temperature)
        log.info("generate_structured", {
            "prompt_len": len(prompt),
            "has_schema": response_schema is not None,
            "temperature": temperature,
        })
        return self._try_keys(payload, max_retries, base_delay)

    def generate_text(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        payload = self._build_payload(prompt, schema=None, temperature=temperature)
        log.info("generate_text", {"prompt_len": len(prompt)})
        result = self._try_keys(payload, max_retries=2, base_delay=1.0)
        if result.get("error"):
            return None
        return json.dumps(result, ensure_ascii=False)

    def test_key(self, key: str) -> dict:
        self._throttle()
        model = self.resolve_model("auto", key)
        key_type = self.detect_key_type(key)
        log.info(f"test_key: type={key_type} model={model}")
        payload = {
            "contents": [{"parts": [{"text": "Say OK and nothing else."}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 10},
        }
        try:
            url = self._build_url(model)
            data = json.dumps(payload).encode("utf-8")
            req = Request(url, data=data, headers={
                "Content-Type": "application/json",
                "x-goog-api-key": key,
            })
            resp = urlopen(req, timeout=30)
            raw = json.loads(resp.read().decode("utf-8"))
            text = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            log.info(f"test_key OK: {model} -> {text}")
            return {"ok": True, "model": model, "response": text}
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:300]
            code = e.code
            log.warn(f"test_key FAIL: HTTP {code}", {"model": model, "body": body[:150]})
            if code == 429:
                return {"ok": False, "model": model, "error": "Rate limited (quota exceeded). Add a fallback key in Settings."}
            if code == 404:
                return {"ok": False, "model": model, "error": f"Model '{model}' not found for this key type."}
            if code == 403:
                return {"ok": False, "model": model, "error": "API key invalid or not authorized."}
            return {"ok": False, "model": model, "error": f"HTTP {code}"}
        except Exception as e:
            log.error(f"test_key exception: {e}")
            return {"ok": False, "model": model, "error": str(e)}


class RateLimitError(Exception):
    pass


class ModelNotFoundError(Exception):
    pass


class SchemaNotSupportedError(Exception):
    pass


class ApiError(Exception):
    pass
