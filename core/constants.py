MODEL_CHAINS = {
    "stable": ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3-flash-preview"],
    "simple": ["gemini-3.5-flash-lite", "gemini-3.6-flash"],
}

KEY_CHAIN_MAP = {
    "AQ.": "stable",
    "AIzaSy": "simple",
}

DEFAULT_CHAIN = "simple"

RETRY_CONFIG = {
    "max_retries": 3,
    "rate_limit_base": 2.0,
    "jitter_max": 0.5,
    "retry_codes": {429, 500, 503},
}
