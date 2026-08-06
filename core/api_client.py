from llm.gemini import (
    GeminiProvider,
    RateLimitError,
    ModelNotFoundError,
    SchemaNotSupportedError,
    ApiError,
    EC,
)

# Backward-compatibility alias
GeminiClient = GeminiProvider

__all__ = [
    "GeminiClient",
    "GeminiProvider",
    "RateLimitError",
    "ModelNotFoundError",
    "SchemaNotSupportedError",
    "ApiError",
    "EC",
]
