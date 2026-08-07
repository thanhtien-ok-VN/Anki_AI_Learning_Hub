import json
import random
import time
from typing import Optional, Callable, Dict, Any, List
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from core.constants import KEY_CHAIN_MAP, MODEL_CHAINS, DEFAULT_CHAIN, RETRY_CONFIG
from core.logger import log
from core.i18n import t
from llm.base import BaseLLMProvider

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

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


class GeminiProvider(BaseLLMProvider):
    _last_request_time = 0.0
    _min_interval = 1.5

    def __init__(self, api_keys: List[str], model_name: str = "auto", ui_lang: str = "en", cancel_event=None):
        self.keys = [k.strip() for k in api_keys if k.strip()]
        self.model_name = model_name
        self.ui_lang = ui_lang
        self.cancel_event = cancel_event
        self.last_response = None
        self._active_key_index = 0
        self._unhealthy_until: Dict[int, float] = {}
        log.info("GeminiProvider init", {
            "key_count": len(self.keys),
            "key_types": [self.detect_key_type(k) for k in self.keys],
            "model": model_name,
            "ui_lang": ui_lang,
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

    def _err(self, code: str, msg: str, detail: str = "") -> dict:
        result = {"error": True, "error_code": code, "message": msg}
        log.warn(f"API error [{code}]: {detail or msg}")
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

    def _throttle(self):
        if self.cancel_event and self.cancel_event.is_set():
            raise ApiError("API request cancelled by user")
        now = time.time()
        since = now - GeminiProvider._last_request_time
        if since < GeminiProvider._min_interval:
            delay = GeminiProvider._min_interval - since
            log.debug(f"Throttle: sleep {delay:.2f}s")
            time.sleep(delay)
        GeminiProvider._last_request_time = time.time()

    @staticmethod
    def _retry_delay(attempt: int, base: float = None) -> float:
        b = base if base is not None else RETRY_CONFIG["rate_limit_base"]
        return b * (2 ** attempt) + random.uniform(0, RETRY_CONFIG["jitter_max"])

    @staticmethod
    def _should_retry(code: int) -> bool:
        return code in RETRY_CONFIG["retry_codes"]

    def _call_api(self, payload: dict, key: str, model: str) -> dict:
        if self.cancel_event and self.cancel_event.is_set():
            raise ApiError("API request cancelled by user")
        self._throttle()
        url = self._build_url(model)
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "x-goog-api-key": key}
        req = Request(url, data=data, headers=headers)

        log.debug(f"API call: model={model} url_len={len(data)}")
        start_t = time.time()

        try:
            resp = urlopen(req, timeout=60)
            self.last_response = resp
            raw = json.loads(resp.read().decode("utf-8"))
            latency_ms = int((time.time() - start_t) * 1000)
            from core.logger import flow
            flow(phase="API", message=f"API call succeeded: model={model}, latency={latency_ms}ms")
            log.debug("API response OK", {"model": model, "latency_ms": latency_ms})
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
            return self._err(EC["NO_KEYS"], t("app.ai_no_keys", lang=self.ui_lang))

        has_schema = "response_schema" in payload.get("generationConfig", {})
        last_error = ""
        final_code = EC["API_ERROR"]
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

        max_model_steps = 0
        for idx in eligible:
            key = self.keys[idx]
            max_model_steps = max(max_model_steps, len(self._models_for_call(key)))

        for step in range(max_model_steps):
            if self.cancel_event and self.cancel_event.is_set():
                log.info("API call cancelled during step loop")
                return self._err("E_CANCELLED", t("app.cancelled_gen", lang=self.ui_lang))

            for position, idx in list(enumerate(eligible)):
                if self.cancel_event and self.cancel_event.is_set():
                    log.info("API call cancelled during key loop")
                    return self._err("E_CANCELLED", t("app.cancelled_gen", lang=self.ui_lang))

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
                    if self.cancel_event and self.cancel_event.is_set():
                        log.info("API call cancelled during attempt loop")
                        return self._err("E_CANCELLED", t("app.cancelled_gen", lang=self.ui_lang))

                    try:
                        log.debug(f"Trying {key_label} step {step} model {model} attempt {attempt+1}/{max_retries}")
                        notify(t("api.calling", lang=self.ui_lang, idx=idx+1, model=model))
                        result = self._call_api(payload, key, model)
                        if isinstance(result, dict) and not result.get("error"):
                            self._active_key_index = idx
                            self._unhealthy_until.pop(idx, None)
                            return self._ok(result, key_label, model)
                        return result
                    except RateLimitError:
                        final_code = EC["RATE_LIMIT"]
                        if attempt < max_retries - 1:
                            delay = self._retry_delay(attempt)
                            log.warn(f"{key_label} {model} rate limited, retry in {delay:.1f}s")
                            notify(t("api.busy", lang=self.ui_lang, idx=idx+1, model=model, delay=delay))
                            time.sleep(delay)
                            continue
                        self._unhealthy_until[idx] = time.monotonic() + 60
                        last_error = f"{key_label} {model}: rate limited after {max_retries} retries"
                        notify(t("api.exhausted", lang=self.ui_lang, idx=idx+1, model=model))
                    except ModelNotFoundError as e:
                        final_code = EC["API_ERROR"]
                        self._unhealthy_until[idx] = time.monotonic() + 300
                        last_error = f"{key_label}: {e}"
                        log.warn(last_error)
                        notify(t("api.no_model", lang=self.ui_lang, idx=idx+1, model=model))
                        break
                    except SchemaNotSupportedError as e:
                        if has_schema:
                            log.info(f"{key_label} schema unsupported, retry as text")
                            notify(t("api.no_schema", lang=self.ui_lang, idx=idx+1, model=model))
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
                                final_code = EC["API_ERROR"]
                                last_error = f"{key_label}: schema+text both failed: {e2}"
                                log.error(last_error)
                                notify(t("api.fallback_fail", lang=self.ui_lang, idx=idx+1, model=model))
                                break
                        last_error = f"{key_label}: {e}"
                        break
                    except ApiError as e:
                        final_code = EC["API_ERROR"]
                        last_error = f"{key_label}: {e}"
                        is_auth_error = "invalid" in str(e).lower() or "authoriz" in str(e).lower()
                        delay = 3600 if is_auth_error else 20
                        self._unhealthy_until[idx] = time.monotonic() + delay
                        if is_auth_error:
                            log.warn(f"Auth error on {key_label}. Skipping this key entirely.")
                            notify(t("api.auth_error", lang=self.ui_lang, idx=idx+1))
                            if idx in eligible:
                                eligible.remove(idx)
                            break
                        notify(t("api.api_error", lang=self.ui_lang, idx=idx+1))
                        if attempt < max_retries - 1:
                            log.warn(f"{last_error}, retry in {base_delay}s")
                            time.sleep(base_delay)
                            continue
                        break
                    except Exception as e:
                        final_code = EC["INTERNAL_ERROR"]
                        last_error = f"{key_label}: {e}"
                        notify(t("api.unknown_error", lang=self.ui_lang, idx=idx+1))
                        if attempt < max_retries - 1:
                            time.sleep(base_delay)
                            continue
                        break

        if not eligible and not last_error:
            last_error = "No active or valid API keys available."
            final_code = EC["NO_KEYS"]
            message = t("app.ai_no_keys", lang=self.ui_lang)
            return self._err(final_code, message, last_error)

        from core.logger import flow
        flow(phase="API", message=f"All API keys/models exhausted or timed out. Last error: {last_error}")

        if final_code == EC["RATE_LIMIT"]:
            message = t("app.ai_rate_limited", lang=self.ui_lang)
        elif final_code == EC["INTERNAL_ERROR"]:
            message = t("app.ai_overloaded", lang=self.ui_lang)
        elif final_code == EC["NO_KEYS"]:
            message = t("app.ai_no_keys", lang=self.ui_lang)
        else:
            message = t("app.ai_overloaded", lang=self.ui_lang)
        return self._err(final_code, message, last_error)

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
            return self._err(EC["INTERNAL_ERROR"], "The AI request could not be completed.", str(e))

    def generate_text_result(self, prompt: str, temperature: float = 0.7, progress_callback: Optional[Callable[[str], None]] = None) -> dict:
        try:
            payload = self._build_payload(prompt, schema=None, temperature=temperature)
            log.info("generate_text", {"prompt_len": len(prompt)})
            return self._try_keys(payload, max_retries=2, base_delay=1.0, progress_callback=progress_callback)
        except Exception as e:
            log.error(f"Uncaught exception in generate_text: {e}")
            return self._err(EC["INTERNAL_ERROR"], "The AI request could not be completed.", str(e))

    def generate_text(self, prompt: str, temperature: float = 0.7, progress_callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        result = self.generate_text_result(prompt, temperature, progress_callback)
        if result.get("error"):
            return None
        return json.dumps(result, ensure_ascii=False)

    def test_key_with_waterfall(self, key: str, max_retries: int = 2, progress_callback: Optional[Callable[[str], None]] = None) -> dict:
        models = self._models_for_call(key)
        last_error = ""
        error_code = EC["API_ERROR"]
        last_model = models[0] if models else "gemini-1.5-flash"

        def notify(text: str):
            if progress_callback:
                try:
                    progress_callback(text)
                except Exception as ex:
                    log.error(f"progress_callback error in test_key: {ex}")

        for step, model in enumerate(models):
            for attempt in range(max_retries):
                if self.cancel_event and self.cancel_event.is_set():
                    return {"ok": False, "error_code": "E_CANCELLED", "error": t("app.cancelled_gen", lang=self.ui_lang)}
                try:
                    self._throttle()
                    notify(t("api.calling", lang=self.ui_lang, idx=self.keys.index(key)+1 if key in self.keys else 1, model=model))
                    payload = {
                        "contents": [{"parts": [{"text": "Say OK and nothing else."}]}],
                        "generationConfig": {"temperature": 0, "maxOutputTokens": 10},
                    }
                    url = self._build_url(model)
                    data = json.dumps(payload).encode("utf-8")
                    headers = {"Content-Type": "application/json", "x-goog-api-key": key}
                    req = Request(url, data=data, headers=headers)
                    resp = urlopen(req, timeout=8)
                    if self.cancel_event and self.cancel_event.is_set():
                        return {"ok": False, "error_code": "E_CANCELLED", "error": t("app.cancelled_gen", lang=self.ui_lang)}
                    raw = json.loads(resp.read().decode("utf-8"))
                    text = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    log.info(f"test_key_with_waterfall OK: key={self.detect_key_type(key)} model={model} response={text}")
                    return {"ok": True, "model": model, "response": text}
                except HTTPError as e:
                    if self.cancel_event and self.cancel_event.is_set():
                        return {"ok": False, "error_code": "E_CANCELLED", "error": t("app.cancelled_gen", lang=self.ui_lang)}
                    body = e.read().decode("utf-8", errors="replace")[:300]
                    code = e.code
                    log.warn(f"test_key_with_waterfall FAIL: key={self.detect_key_type(key)} model={model} attempt={attempt+1} HTTP {code}")
                    if code in {429, 500, 503} and attempt < max_retries - 1:
                        delay = 2.0 * (2 ** attempt) + random.uniform(0, 0.5)
                        if self.cancel_event and self.cancel_event.is_set():
                            return {"ok": False, "error_code": "E_CANCELLED", "error": t("app.cancelled_gen", lang=self.ui_lang)}
                        time.sleep(delay)
                        continue
                    if code in {429, 500, 503}:
                        error_code = EC["RATE_LIMIT"]
                        last_error = "AI is temporarily busy. Please try again later."
                        break
                    if code == 404:
                        last_error = "The selected model is unavailable."
                        break
                    if code == 403:
                        return {
                            "ok": False,
                            "model": model,
                            "error_code": EC["KEY_INVALID"],
                            "error": "API key invalid or not authorized.",
                        }
                    last_error = "AI is temporarily unavailable. Please try again later."
                    if attempt >= max_retries - 1:
                        break
                    time.sleep(2.0)
                except Exception as e:
                    last_error = "AI is temporarily unavailable. Please try again later."
                    log.error(f"test_key_with_waterfall exception: key={self.detect_key_type(key)} model={model} error={e}")
                    break
            else:
                continue
            break

        return {
            "ok": False,
            "model": last_model,
            "error_code": error_code,
            "error": last_error or "AI is temporarily unavailable. Please try again later.",
        }

    def test_key(self, key: str, progress_callback: Optional[Callable[[str], None]] = None) -> dict:
        return self.test_key_with_waterfall(key, progress_callback=progress_callback)


class RateLimitError(Exception):
    pass


class ModelNotFoundError(Exception):
    pass


class SchemaNotSupportedError(Exception):
    pass


class ApiError(Exception):
    pass
