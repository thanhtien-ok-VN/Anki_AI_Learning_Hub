import sys
import threading
import traceback
import aqt.utils
from core.logger import log

def is_aihub_exception(exception, traceback_obj=None) -> bool:
    """Kiểm tra chính xác xem ngoại lệ có thuộc về AI_Learning_Hub hay không."""
    if not exception:
        return False
    
    # 1. Kiểm tra thông điệp lỗi
    exc_str = str(exception).lower()
    if "ai_learning_hub" in exc_str or "aihub" in exc_str:
        return True
    
    # 2. Kiểm tra traceback truyền vào
    tb = traceback_obj or (exception.__traceback__ if hasattr(exception, "__traceback__") else None)
    if tb:
        for frame in traceback.extract_tb(tb):
            filename = frame.filename.lower()
            if "ai_learning_hub" in filename or "ai_hub" in filename:
                return True
                
    # 3. Kiểm tra traceback hiện tại trong sys.exc_info()
    exc_type, exc_val, sys_tb = sys.exc_info()
    if sys_tb:
        for frame in traceback.extract_tb(sys_tb):
            filename = frame.filename.lower()
            if "ai_learning_hub" in filename or "ai_hub" in filename:
                return True
                
    return False

# ==========================================
# 1. Patch aqt.taskman.TaskManager.raise_exception
# ==========================================
try:
    from aqt.taskman import TaskManager
    original_raise_exception = TaskManager.raise_exception
    
    def custom_raise_exception(self, exception: Exception, *args, **kwargs):
        try:
            if is_aihub_exception(exception):
                tb_text = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
                log.error(f"[SHIELD] Suppressed TaskManager.raise_exception:\n{exception}\n{tb_text}")
                return  # Nuốt lỗi, ngăn chặn hiển thị popup
        except Exception as inner_err:
            log.error(f"Error in custom_raise_exception hook: {inner_err}")
            
        return original_raise_exception(self, exception, *args, **kwargs)
        
    TaskManager.raise_exception = custom_raise_exception
    log.info("TaskManager.raise_exception patched successfully.")
except Exception as e:
    log.error(f"Failed to patch TaskManager.raise_exception: {e}")

# ==========================================
# 2. Patch aqt.errors.show_exception
# ==========================================
try:
    import aqt.errors
    original_show_exception = getattr(aqt.errors, "show_exception", None)
    if not original_show_exception:
        original_show_exception = getattr(aqt.errors, "showException", None)
        
    if original_show_exception:
        def custom_show_exception(*args, **kwargs):
            try:
                # args thường là (parent, exception, traceback_str) hoặc (exception, traceback_str)
                tb_str = ""
                exc_obj = None
                for arg in args:
                    if isinstance(arg, str):
                        tb_str = arg
                    elif isinstance(arg, Exception):
                        exc_obj = arg
                
                if "ai_learning_hub" in tb_str.lower() or is_aihub_exception(exc_obj):
                    log.error(f"[SHIELD] Suppressed aqt.errors.show_exception:\nTraceback: {tb_str}")
                    return  # Nuốt lỗi
            except Exception as inner_err:
                log.error(f"Error in custom_show_exception hook: {inner_err}")
                
            return original_show_exception(*args, **kwargs)
            
        if hasattr(aqt.errors, "show_exception"):
            aqt.errors.show_exception = custom_show_exception
        if hasattr(aqt.errors, "showException"):
            aqt.errors.showException = custom_show_exception
        log.info("aqt.errors.show_exception patched successfully.")
    else:
        log.warn("aqt.errors.show_exception not found to patch.")
except Exception as e:
    log.error(f"Failed to patch aqt.errors.show_exception: {e}")

# ==========================================
# 3. Patch threading.excepthook
# ==========================================
try:
    original_thread_excepthook = threading.excepthook
    
    def custom_thread_excepthook(args):
        try:
            if is_aihub_exception(args.exc_value, args.exc_traceback):
                tb_text = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
                log.error(f"[SHIELD] Suppressed threading.excepthook:\n{args.exc_value}\n{tb_text}")
                return
        except Exception as inner_err:
            log.error(f"Error in custom_thread_excepthook: {inner_err}")
            
        return original_thread_excepthook(args)
        
    threading.excepthook = custom_thread_excepthook
    log.info("threading.excepthook patched successfully.")
except Exception as e:
    log.error(f"Failed to patch threading.excepthook: {e}")

# ==========================================
# 4. Patch sys.excepthook toàn cục
# ==========================================
_original_excepthook = sys.excepthook

def custom_sys_excepthook(exc_type, exc_value, exc_tb):
    try:
        if is_aihub_exception(exc_value, exc_tb):
            tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            log.error(f"[SHIELD] Suppressed sys.excepthook:\n{exc_value}\n{tb_text}")
            return  # Nuốt lỗi
    except Exception as e:
        log.error(f"Error in custom_sys_excepthook: {e}")
        
    if _original_excepthook:
        _original_excepthook(exc_type, exc_value, exc_tb)

sys.excepthook = custom_sys_excepthook
log.info("sys.excepthook patched successfully.")
