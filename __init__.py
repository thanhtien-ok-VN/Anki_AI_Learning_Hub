import os
import sys

ADDON_NAME = "AI Learning Hub"
ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ADDON_PATH)

from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showInfo

from core.logger import log

mw.addonManager.setWebExports(__name__, r"web/.*")
log.info(f"Add-on loaded: {ADDON_NAME} v2.0")


def open_hub():
    try:
        if hasattr(mw, "ai_hub_view") and mw.ai_hub_view is not None and not mw.ai_hub_view.is_closed():
            mw.ai_hub_view.focus()
            return

        from ui.main_window import AIHubView
        if not hasattr(mw, "ai_engine") or mw.ai_engine is None:
            from core.engine import AIEngine
            mw.ai_engine = AIEngine()
            mw.ai_engine.start()

        mw.ai_hub_view = AIHubView(mw.ai_engine)
        mw.ai_hub_view.embed()
        log.info("Hub view embedded")
    except Exception as e:
        log.error(f"Error opening AI Hub: {e}")


def open_settings():
    if not hasattr(mw, "ai_engine") or mw.ai_engine is None:
        from core.engine import AIEngine
        mw.ai_engine = AIEngine()
        mw.ai_engine.start()

    from ui.settings_dialog import SettingsDialog
    dialog = SettingsDialog(mw)
    dialog.exec()


def init_addon():
    from core.engine import AIEngine

    try:
        mw.ai_engine = AIEngine()
        log.info("AIEngine created")
    except Exception as e:
        log.error(f"Error initializing AIEngine: {e}")

    def on_profile_open():
        try:
            mw.ai_engine.start()
        except Exception as e:
            log.error(f"Error starting AIEngine on profile open: {e}")

    gui_hooks.profile_did_open.append(on_profile_open)

    menu = mw.form.menuTools
    action = QAction(f"{ADDON_NAME}...", mw)
    action.triggered.connect(open_hub)
    menu.addAction(action)

    settings_action = QAction(f"{ADDON_NAME} Settings...", mw)
    settings_action.triggered.connect(open_settings)
    menu.addAction(settings_action)

    def on_browser_context_menu(browser, context_menu):
        ai_menu = QAction("✨ AI Learning Hub: Luyện tập thẻ đã chọn", browser)
        ai_menu.triggered.connect(lambda: _on_browser_practice(browser))
        context_menu.addAction(ai_menu)

    gui_hooks.browser_will_show_context_menu.append(on_browser_context_menu)
    log.info("Menu items and Anki Browser hooks registered")


def _on_browser_practice(browser):
    nids = browser.selectedNotes()
    if not nids:
        showInfo("Hãy chọn ít nhất một thẻ trong danh sách để luyện tập AI.")
        return
    open_hub()


gui_hooks.main_window_did_init.append(init_addon)
