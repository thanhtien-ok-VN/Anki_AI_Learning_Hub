MODEL_CHAINS = {
    "stable": ["gemini-flash-latest", "gemini-3.6-flash", "gemma-4-31b-it"],
    "simple": ["gemini-3.1-flash-lite", "gemini-flash-latest"],
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
