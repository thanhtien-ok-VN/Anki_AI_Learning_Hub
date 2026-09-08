"""Gemini LLM Provider Facade.

Coordinates API key rotation, waterfall model fallback, progress reporting,
and structured generation using modular transport, response, and model components.
"""
import json
import time
from typing import Any, Callable, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from core.constants import DEFAULT_CHAIN, MODEL_CHAINS, KEY_CHAIN_MAP, RETRY_CONFIG
from core.i18n import t
from core.logger import log, flow
from llm.base import BaseLLMProvider
from llm.gemini_models import (
    API_BASE,
    EC,
    ApiError,
    RateLimitError,
    ModelNotFoundError,
    SchemaNotSupportedError,
    detect_key_type,
    resolve_model_chain,
)
from llm.gemini_transport import GeminiTransport
from llm.gemini_response import clean_dict, parse_gemini_raw_response


class GeminiProvider(BaseLLMProvider):
    """Facade for Google Gemini API with multi-key rotation and multi-tier model fallback."""

    def __init__(
        self,
        api_keys: List[str],
        model_name: str = "auto",
        ui_lang: str = "en",
        cancel_event: Optional[Any] = None,
    ):
        self.keys = [k.strip() for k in api_keys if k.strip()]
        self.model_name = model_name
        self.ui_lang = ui_lang
        self.cancel_event = cancel_event
        self.last_response = None
        self._active_key_index = 0
        self._unhealthy_until: Dict[int, float] = {}

        log.info(
            "GeminiProvider init",
            {
                "key_count": len(self.keys),
                "key_types": [detect_key_type(k) for k in self.keys],
                "model": model_name,
                "ui_lang": ui_lang,
            },
        )

    @classmethod
    def from_settings(
        cls,
        settings: Optional[Dict[str, Any]] = None,
        cancel_event: Optional[Any] = None,
        **kwargs,
    ) -> "GeminiProvider":
        """Factory constructor instantiating GeminiProvider from standard settings dict."""
        settings = settings or {}
        keys = kwargs.get("api_keys") or settings.get("keys") or []
        model = kwargs.get("model_name") or settings.get("model", "auto")
        ui_lang = kwargs.get("ui_lang") or settings.get("ui_lang", "en")
        return cls(
            api_keys=keys,
            model_name=model,
            ui_lang=ui_lang,
            cancel_event=cancel_event,
        )

    @staticmethod
    def detect_key_type(api_key: str) -> str:
        return detect_key_type(api_key)

    @staticmethod
    def resolve_model_chain(api_key: str) -> list:
        return resolve_model_chain(api_key)

    def _models_for_call(self, api_key: str) -> list:
        preferred = self.model_name
        if preferred and preferred != "auto":
            return [preferred]
        return resolve_model_chain(api_key)

    def _err(self, code: str, msg: str, detail: str = "") -> dict:
        result = {"error": True, "error_code": code, "message": msg}
        log.warn(f"API error [{code}]: {detail or msg}")
        return result

    def _ok(self, data: dict, key_label: str, model: str) -> dict:
        data["_key_used"] = key_label
        data["_model_used"] = model
        data["error_code"] = EC["SUCCESS"]
        return data

    def _call_api(self, payload: dict, key: str, model: str) -> dict:
        raw = GeminiTransport.execute_http(
            payload=payload,
            key=key,
            model=model,
            cancel_event=self.cancel_event,
        )
        return parse_gemini_raw_response(raw)

    def _try_keys(
        self,
        payload: dict,
        max_retries: int,
        base_delay: float,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> dict:
        if not self.keys:
            return self._err(EC["NO_KEYS"], t("app.ai_no_keys", lang=self.ui_lang))

        has_schema = "response_schema" in payload.get("generationConfig", {})
        last_error = ""
        final_code = EC["API_ERROR"]
        now = time.monotonic()
        order = [self._active_key_index] + [
            i for i in range(len(self.keys)) if i != self._active_key_index
        ]
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
                key_label = f"key{idx+1} ({detect_key_type(key)})"

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
                        log.debug(
                            f"Trying {key_label} step {step} model {model} attempt {attempt+1}/{max_retries}"
                        )
                        notify(t("api.calling", lang=self.ui_lang, idx=idx + 1, model=model))

                        data = self._call_api(payload, key, model)

                        # If safety/recitation error returned as dict
                        if data.get("error"):
                            return data

                        self._active_key_index = idx
                        self._unhealthy_until.pop(idx, None)
                        log.info(
                            f"Success: {key_label} step {step} ({model}) attempt {attempt+1}"
                        )
                        notify(t("api.success", lang=self.ui_lang, model=model))
                        return self._ok(data, key_label, model)

                    except RateLimitError as e:
                        last_error = str(e)
                        final_code = EC["RATE_LIMIT"]
                        log.warn(f"Rate limited on {key_label} model {model} attempt {attempt+1}")
                        if attempt < max_retries - 1:
                            delay = GeminiTransport.retry_delay(attempt, base_delay)
                            notify(
                                t(
                                    "api.rate_limited_retry",
                                    lang=self.ui_lang,
                                    idx=idx + 1,
                                    seconds=f"{delay:.1f}",
                                )
                            )
                            time.sleep(delay)
                        else:
                            cooldown = RETRY_CONFIG.get("cooldown_seconds", 30.0)
                            self._unhealthy_until[idx] = time.monotonic() + cooldown
                            notify(
                                t(
                                    "api.rate_limited_next",
                                    lang=self.ui_lang,
                                    idx=idx + 1,
                                )
                            )
                            break

                    except SchemaNotSupportedError as e:
                        last_error = str(e)
                        final_code = EC["SCHEMA_NOT_SUPPORTED"]
                        log.warn(f"Schema unsupported: {key_label} model {model}")
                        notify(t("api.schema_fallback", lang=self.ui_lang, model=model))
                        break

                    except ModelNotFoundError as e:
                        last_error = str(e)
                        final_code = EC["MODEL_NOT_FOUND"]
                        log.warn(f"Model not found: {key_label} model {model}")
                        notify(t("api.model_not_found", lang=self.ui_lang, model=model))
                        break

                    except ApiError as e:
                        last_error = str(e)
                        final_code = EC["API_ERROR"]
                        log.error(f"ApiError: {key_label} model {model}: {e}")
                        if "API key invalid" in str(e):
                            final_code = EC["KEY_INVALID"]
                            self._unhealthy_until[idx] = time.monotonic() + 86400
                            break
                        if attempt < max_retries - 1:
                            delay = GeminiTransport.retry_delay(attempt, base_delay)
                            notify(
                                t(
                                    "api.error_retry",
                                    lang=self.ui_lang,
                                    error=str(e)[:60],
                                    seconds=f"{delay:.1f}",
                                )
                            )
                            time.sleep(delay)
                        else:
                            break

        if final_code == EC["RATE_LIMIT"]:
            cooldown_s = int(RETRY_CONFIG.get("cooldown_seconds", 30))
            msg = t("app.ai_rate_limit", lang=self.ui_lang, seconds=cooldown_s)
        elif final_code == EC["KEY_INVALID"]:
            msg = t("app.ai_key_invalid", lang=self.ui_lang)
        elif final_code == EC["SCHEMA_NOT_SUPPORTED"]:
            msg = t("app.ai_schema_unsupported", lang=self.ui_lang)
        elif final_code == EC["MODEL_NOT_FOUND"]:
            msg = t("app.ai_model_not_found", lang=self.ui_lang)
        else:
            msg = t("app.ai_all_failed", lang=self.ui_lang)

        return self._err(final_code, msg, detail=last_error)

    def generate_structured(
        self,
        prompt: str,
        response_schema: Optional[dict] = None,
        temperature: float = 0.7,
        max_retries: int = 2,
        base_delay: Optional[float] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> dict:
        try:
            payload = GeminiTransport.build_payload(
                prompt, schema=response_schema, temperature=temperature
            )
            return self._try_keys(
                payload,
                max_retries=max_retries,
                base_delay=base_delay or RETRY_CONFIG["rate_limit_base"],
                progress_callback=progress_callback,
            )
        except Exception as e:
            log.exception(f"Unexpected error in generate_structured: {e}")
            return self._err(EC["INTERNAL_ERROR"], t("app.ai_all_failed", lang=self.ui_lang), detail=str(e))

    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_retries: int = 2,
        base_delay: Optional[float] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        try:
            payload = GeminiTransport.build_payload(prompt, temperature=temperature)
            result = self._try_keys(
                payload,
                max_retries=max_retries,
                base_delay=base_delay or RETRY_CONFIG["rate_limit_base"],
                progress_callback=progress_callback,
            )
            if result.get("error"):
                return ""
            if isinstance(result, dict):
                for k in ["text", "content", "response", "result"]:
                    if k in result:
                        return str(result[k])
                return json.dumps(result)
            return str(result)
        except Exception as e:
            log.exception(f"Unexpected error in generate_text: {e}")
            return ""

    def generate_text_result(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_retries: int = 2,
        base_delay: Optional[float] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> dict:
        try:
            payload = GeminiTransport.build_payload(prompt, temperature=temperature)
            return self._try_keys(
                payload,
                max_retries=max_retries,
                base_delay=base_delay or RETRY_CONFIG["rate_limit_base"],
                progress_callback=progress_callback,
            )
        except Exception as e:
            log.exception(f"Unexpected error in generate_text_result: {e}")
            return self._err(EC["INTERNAL_ERROR"], t("app.ai_all_failed", lang=self.ui_lang), detail=str(e))

    @classmethod
    def test_key_with_waterfall(
        cls,
        api_key: str,
        cancel_event: Optional[Any] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        max_retries: int = 1,
    ) -> dict:
        client = cls(api_keys=[api_key], cancel_event=cancel_event)
        result = client.generate_structured(
            prompt='Respond with JSON: {"ok": true}',
            response_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
            max_retries=max_retries,
            progress_callback=progress_callback,
        )
        if result.get("error"):
            return {
                "ok": False,
                "error": result.get("message", "Test failed"),
                "error_code": result.get("error_code"),
            }
        return {
            "ok": True,
            "model": result.get("_model_used", "unknown"),
            "key_type": detect_key_type(api_key),
        }
