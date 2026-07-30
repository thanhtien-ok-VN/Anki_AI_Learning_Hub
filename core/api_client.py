import json
import random
import time
from typing import Optional, Callable
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .constants import KEY_CHAIN_MAP, MODEL_CHAINS, DEFAULT_CHAIN, RETRY_CONFIG
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
    "INTERNAL_ERROR": "E_INTERNAL",
}


class GeminiClient:
    
    _last_request_time = 0.0
    _min_interval = 1.5

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
    def resolve_model_chain(api_key: str) -> list:
        for prefix, chain_name in KEY_CHAIN_MAP.items():
            if api_key.startswith(prefix):
                return MODEL_CHAINS[chain_name]
        return MODEL_CHAINS[DEFAULT_CHAIN]

    def _models_for_call(self, api_key: str) -> list:
        preferred = self.model_name
        if preferred and preferred != "auto":
            return [preferred]
        return self.resolve_model_chain(api_key)

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

    @staticmethod
    def _retry_delay(attempt: int, base: float = None) -> float:
        b = base if base is not None else RETRY_CONFIG["rate_limit_base"]
        return b * (2 ** attempt) + random.uniform(0, RETRY_CONFIG["jitter_max"])

    @staticmethod
    def _should_retry(code: int) -> bool:
        return code in RETRY_CONFIG["retry_codes"]

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
            if self._should_retry(code):
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

        return self._parse_response(raw)

    def _parse_response(self, raw: dict) -> dict:
        from core.engine import clean_json_response
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

        cleaned = clean_json_response(text)
        if not cleaned:
            raise ApiError(f"Empty response after cleaning: {text[:120]}")
        try:
            parsed = json.loads(cleaned)
            return _clean_dict(parsed)
        except json.JSONDecodeError as e:
            raise ApiError(f"JSON parse failed after clean_json_response: {e}")

    def _try_keys(self, payload: dict, max_retries: int, base_delay: float, progress_callback: Optional[Callable[[str], None]] = None) -> dict:
        if not self.keys:
            return self._err(EC["NO_KEYS"], "No API keys configured. Set at least one in Settings.")

        has_schema = "response_schema" in payload.get("generationConfig", {})
        last_error = ""
        now = time.monotonic()
        order = [self._active_key_index] + [i for i in range(len(self.keys)) if i != self._active_key_index]
        eligible = [i for i in order if self._unhealthy_until.get(i, 0) <= now]
        if not eligible:
            eligible = [min(range(len(self.keys)), key=lambda i: self._unhealthy_until.get(i, 0))]

        def notify(text: str):
            if progress_callback:
                try:
                    progress_callback(text)
                except Exception as ex:
                    log.error(f"progress_callback error: {ex}")

        # Vòng lặp ngoài: duyệt qua từng mức ưu tiên của model (step 0, step 1, step 2...)
        # Xác định số lượng model tối đa của các key
        max_model_steps = 0
        for idx in eligible:
            key = self.keys[idx]
            max_model_steps = max(max_model_steps, len(self._models_for_call(key)))

        for step in range(max_model_steps):
            # Với mỗi model step, duyệt qua các key hợp lệ
            for position, idx in list(enumerate(eligible)):
                # Nếu idx đã bị loại bỏ khỏi eligible do lỗi xác thực trước đó, ta bỏ qua
                if idx not in eligible:
                    continue

                key = self.keys[idx]
                key_label = f"key{idx+1} ({self.detect_key_type(key)})"

                models_for_key = self._models_for_call(key)
                if step >= len(models_for_key):
                    continue
                model = models_for_key[step]

                if position > 0:
                    time.sleep(0.25)

                for attempt in range(max_retries):
                    try:
                        log.debug(f"Trying {key_label} step {step} model {model} attempt {attempt+1}/{max_retries}")
                        notify(f"Đang gọi: key{idx+1} ({model})...")
                        result = self._call_api(payload, key, model)
                        if isinstance(result, dict) and not result.get("error"):
                            self._active_key_index = idx
                            self._unhealthy_until.pop(idx, None)
                            return self._ok(result, key_label, model)
                        return result
                    except RateLimitError:
                        if attempt < max_retries - 1:
                            delay = self._retry_delay(attempt)
                            log.warn(f"{key_label} {model} rate limited, retry in {delay:.1f}s")
                            notify(f"Key{idx+1} ({model}) bận. Đang thử lại sau {delay:.1f}s...")
                            time.sleep(delay)
                            continue
                        self._unhealthy_until[idx] = time.monotonic() + 60
                        last_error = f"{key_label} {model}: rate limited after {max_retries} retries"
                        notify(f"Key{idx+1} ({model}) hết lượt gọi. Đang chuyển key...")
                    except ModelNotFoundError as e:
                        self._unhealthy_until[idx] = time.monotonic() + 300
                        last_error = f"{key_label}: {e}"
                        log.warn(last_error)
                        notify(f"Key{idx+1} không hỗ trợ model {model}. Đang chuyển key...")
                        break
                    except SchemaNotSupportedError as e:
                        if has_schema:
                            log.info(f"{key_label} schema unsupported, retry as text")
                            notify(f"Key{idx+1} ({model}) không hỗ trợ schema. Đang chuyển cấu trúc...")
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
                                notify(f"Key{idx+1} ({model}) gọi dự phòng thất bại. Đang chuyển key...")
                                break
                        last_error = f"{key_label}: {e}"
                        break
                    except ApiError as e:
                        last_error = f"{key_label}: {e}"
                        is_auth_error = "invalid" in str(e).lower() or "authoriz" in str(e).lower()
                        delay = 3600 if is_auth_error else 20
                        self._unhealthy_until[idx] = time.monotonic() + delay
                        if is_auth_error:
                            log.warn(f"Auth error on {key_label}. Skipping this key entirely.")
                            notify(f"Key{idx+1} lỗi xác thực. Bỏ qua key này...")
                            if idx in eligible:
                                eligible.remove(idx)
                            break
                        notify(f"Key{idx+1} gặp lỗi API. Đang chuyển key...")
                        if attempt < max_retries - 1:
                            log.warn(f"{last_error}, retry in {base_delay}s")
                            time.sleep(base_delay)
                            continue
                        break
                    except Exception as e:
                        last_error = f"{key_label}: {e}"
                        notify(f"Key{idx+1} lỗi không xác định. Đang chuyển key...")
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
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> dict:
        try:
            payload = self._build_payload(prompt, response_schema, temperature)
            log.info("generate_structured", {
                "prompt_len": len(prompt),
                "has_schema": response_schema is not None,
                "temperature": temperature,
            })
            return self._try_keys(payload, max_retries, base_delay, progress_callback)
        except Exception as e:
            log.error(f"Uncaught exception in generate_structured: {e}")
            return self._err(EC["INTERNAL_ERROR"], f"Internal client error: {e}")

    def generate_text(self, prompt: str, temperature: float = 0.7, progress_callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        try:
            payload = self._build_payload(prompt, schema=None, temperature=temperature)
            log.info("generate_text", {"prompt_len": len(prompt)})
            result = self._try_keys(payload, max_retries=2, base_delay=1.0, progress_callback=progress_callback)
            if result.get("error"):
                return None
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            log.error(f"Uncaught exception in generate_text: {e}")
            return None

    def test_key(self, key: str) -> dict:
        self._throttle()
        models = self._models_for_call(key)
        model = models[0] if models else "gemini-1.5-flash"
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
