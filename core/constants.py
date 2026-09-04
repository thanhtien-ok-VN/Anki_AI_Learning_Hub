# Model waterfall chains by key type / scenario
MODEL_CHAINS = {
    # Full multi-tier waterfall chain for high-performance AQ keys
    "stable": [
        "gemini-3.5-flash-lite",      # Tier 1: Fastest & most stable (0.93s, 100% - batch generation)
        "gemini-flash-lite-latest",   # Tier 2: Ultra-fast fallback (<1s, 100%)
        "gemini-3.5-flash",           # Tier 3: Academic / B2-C2 / Story reading
        "gemini-3.6-flash",           # Tier 4: Strong reasoning & pedagogical grading
        "gemini-3.1-flash-lite",      # Tier 5: Backup tier 2
        "gemini-3-flash-preview",     # Tier 6: Backup tier 3
    ],
    # Fast lightweight chain for standard/legacy keys
    "simple": [
        "gemini-3.5-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview",
    ],
}

KEY_CHAIN_MAP = {
    "AQ.": "stable",
    "AIzaSy": "simple",
}

DEFAULT_CHAIN = "stable"

RETRY_CONFIG = {
    "max_retries": 3,
    "rate_limit_base": 2.0,
    "jitter_max": 0.5,
    "retry_codes": {429, 500, 503},
}
