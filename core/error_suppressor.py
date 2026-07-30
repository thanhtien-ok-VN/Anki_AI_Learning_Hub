import sys
import aqt.utils
from core.logger import log

original_showException = aqt.utils.showException

API_KEYWORDS = [
    "API", "api", "GeminiClient", "test_key", "generate_structured",
    "_try_keys", "_call_api", "urllib", "HTTPError", "URLError",
    "ApiError", "RateLimitError", "ModelNotFoundError",
    "E_API_ERROR", "E_NO_KEYS", "E_RATE_LIMIT", "E_KEY_INVALID",
    "429", "403", "404", "503", "500", "Quota", "quota"
]

def custom_showException(fname, entity, parent=None):
    try:
        msg = str(fname) + " " + str(entity)
        if any(kw in msg for kw in API_KEYWORDS) or "AI_Learning_Hub" in msg or "ai_learning_hub" in msg.lower():
            log.warn(f"[Suppressed Anki Error] {fname}: {entity}")
            return
    except Exception as e:
        log.error(f"Error in custom_showException: {e}")
    
    if original_showException:
        original_showException(fname, entity, parent)

aqt.utils.showException = custom_showException

# Global excepthook shield
_original_excepthook = sys.excepthook

def aihub_suppressor_excepthook(exc_type, exc_value, exc_tb):
    try:
        import traceback as _tb_mod
        tb_text = "".join(_tb_mod.format_exception(exc_type, exc_value, exc_tb))
        if any(kw in tb_text for kw in API_KEYWORDS) or "AI_Learning_Hub" in tb_text or "ai_learning_hub" in tb_text.lower():
            log.error(f"[GLOBAL SUPPRESSOR] Suppressed unhandled exception:\n{tb_text}")
            return  # Prevent Anki's error popup dialog
    except Exception as e:
        log.error(f"[GLOBAL SUPPRESSOR] Error in global guard: {e}")
    
    if _original_excepthook:
        _original_excepthook(exc_type, exc_value, exc_tb)

sys.excepthook = aihub_suppressor_excepthook
log.info("Error suppressor initialized and showException patched.")
