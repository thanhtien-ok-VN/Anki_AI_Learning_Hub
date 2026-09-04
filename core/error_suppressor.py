import sys
import traceback
import aqt.errors
from core.logger import log

def is_aihub_exception_str(error_str: str) -> bool:
    """Kiểm tra xem chuỗi traceback lỗi có chứa dấu vết của AI_Learning_Hub hay không."""
    err_lower = error_str.lower()
    return "ai_learning_hub" in err_lower or "aihub" in err_lower

# ==========================================================
# 1. Patch aqt.errors.ErrorHandler.onTimeout (Chìa Khóa Vàng)
# ==========================================================
try:
    original_onTimeout = aqt.errors.ErrorHandler.onTimeout

    def custom_onTimeout(self):
        try:
            error_content = self.pool
            if is_aihub_exception_str(error_content):
                log.error(f"[SHIELD] Suppressed Anki ErrorHandler error:\n{error_content}")
                self.pool = ""  # Xóa sạch bộ đệm lỗi
                return  # Thoát sớm để nuốt lỗi, ngăn chặn popup xuất hiện
        except Exception as inner_err:
            log.error(f"Error in custom_onTimeout hook: {inner_err}")
            
        return original_onTimeout(self)

    aqt.errors.ErrorHandler.onTimeout = custom_onTimeout
    log.info("aqt.errors.ErrorHandler.onTimeout patched successfully.")
except Exception as e:
    log.error(f"Failed to patch ErrorHandler.onTimeout: {e}")

# ==========================================
# 2. Patch sys.excepthook (Lưới bảo vệ phụ)
# ==========================================
_original_excepthook = sys.excepthook

def custom_sys_excepthook(exc_type, exc_value, exc_tb):
    try:
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        if is_aihub_exception_str(tb_text):
            log.error(f"[SHIELD] Suppressed sys.excepthook:\n{exc_value}\n{tb_text}")
            return  # Nuốt lỗi
    except Exception as e:
        log.error(f"Error in custom_sys_excepthook: {e}")
        
    if _original_excepthook:
        _original_excepthook(exc_type, exc_value, exc_tb)

sys.excepthook = custom_sys_excepthook
log.info("sys.excepthook patched successfully.")
