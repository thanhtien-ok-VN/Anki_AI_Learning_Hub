"""Gemini API model configurations, error codes, and exception classes."""
from core.constants import KEY_CHAIN_MAP, MODEL_CHAINS, DEFAULT_CHAIN

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


class ApiError(Exception):
    """General error communicating with Gemini API."""
    pass


class RateLimitError(ApiError):
    """429 Resource Exhausted error."""
    pass


class ModelNotFoundError(ApiError):
    """404 Model Not Found error."""
    pass


class SchemaNotSupportedError(ApiError):
    """Structured Outputs (responseSchema) unsupported error."""
    pass


def detect_key_type(api_key: str) -> str:
    """Detect whether API key is new format (AQ.) or old format (AIzaSy)."""
    k = api_key.strip()
    if k.startswith("AQ."):
        return "new (AQ.)"
    if k.startswith("AIzaSy"):
        return "old (AIzaSy)"
    return "unknown"


def resolve_model_chain(api_key: str) -> list:
    """Resolve the waterfall fallback chain of models for a given key prefix."""
    for prefix, chain_name in KEY_CHAIN_MAP.items():
        if api_key.startswith(prefix):
            return MODEL_CHAINS[chain_name]
    return MODEL_CHAINS[DEFAULT_CHAIN]
