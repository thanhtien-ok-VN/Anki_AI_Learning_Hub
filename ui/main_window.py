"""The Hub tab controller.

Anki does not expose a public main-window tab API, so this controller owns the
small QTabWidget wrapper and restores the original web view exactly once.
"""

from __future__ import annotations

import json
import os
import threading
from functools import partial

from aqt import mw
from aqt.qt import QTabWidget, QUrl
from aqt.webview import AnkiWebView

ADDON_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKGROUND_ACTIONS = {"generate", "test_key", "test_all_keys", "ai_grade"}


class AIHubView:
    def __init__(self, engine):
        self.engine = engine
        self.engine.main_window = self
        self._tabs: QTabWidget | None = None
        self._hub_web: AnkiWebView | None = None
        self._main_web = None
        self._closed = True
        self._bg_lock = threading.Lock()

    def _hub_url(self) -> QUrl:
        package = mw.addonManager.addonFromModule("AI_Learning_Hub")
        port = mw.mediaServer.getPort()
        return QUrl(f"http://127.0.0.1:{port}/_addons/{package}/web/index.html")

    @staticmethod
    def _result(
        success: bool, data: dict | None = None, code: str = "", message: str = ""
    ) -> dict:
        return {
            "success": success,
            "data": data or {},
            "error_code": code,
            "message": message,
        }

    def _on_bridge_cmd(self, cmd: str) -> str:
        from core.logger import log

        try:
            msg = json.loads(cmd)
            action = msg.get("action", "")
            request_id = msg.get("request_id", "")
            if action == "close_hub":
                self.close()
                return json.dumps(self._result(True))
            if action in BACKGROUND_ACTIONS:
                if not request_id:
                    return json.dumps(
                        self._result(
                            False, code="E_REQUEST_ID", message="Missing request id."
                        )
                    )
                payload = json.dumps({"action": action, "data": msg.get("data", {})})
                mw.taskman.run_in_background(
                    lambda: self.engine.handle_js_message(payload),
                    partial(self._background_complete, request_id),
                )
                return json.dumps(
                    self._result(True, {"pending": True, "request_id": request_id})
                )
            return json.dumps(
                self.engine.handle_js_message(
                    json.dumps({"action": action, "data": msg.get("data", {})})
                )
            )
        except Exception as exc:
            log.error(f"Bridge error: {exc}")
            return json.dumps(self._result(False, code="E_BRIDGE", message=str(exc)))

    def _background_complete(self, request_id: str, result) -> None:
        with self._bg_lock:
            if self._closed or not self._hub_web:
                return
            # Anki 2025's taskman passes a concurrent.futures.Future to on_done.
            # Older Anki variants may pass the task result directly, so support both.
            try:
                from core.task_results import resolve_background_result

                response = resolve_background_result(result)
            except Exception as exc:
                response = self._result(False, code="E_BACKGROUND", message=str(exc))
            try:
                js = "window.Bridge && window.Bridge.complete(%s, %s);" % (
                    json.dumps(request_id),
                    json.dumps(response, ensure_ascii=False),
                )
                self._hub_web.eval(js)
            except Exception as e:
                log.error(f"background_complete eval failed: {e}")

    def _on_load_finished(self, ok: bool) -> None:
        try:
            if ok and self._hub_web:
                self._hub_web.eval("window.Bridge && window.Bridge.hostReady();")
        except Exception as e:
            from core.logger import log
            log.error(f"loadFinished eval failed: {e}")

    def embed(self):
        if not self._closed:
            self.focus()
            return
        self._main_web = mw.web
        mw.mainLayout.removeWidget(self._main_web)
        self._main_web.hide()
        self._tabs = QTabWidget(mw)
        self._tabs.addTab(self._main_web, "Anki")
        self._hub_web = AnkiWebView(title="AI Learning Hub")
        self._hub_web.set_open_links_externally(False)
        self._hub_web.set_bridge_command(self._on_bridge_cmd, self)
        self._hub_web.loadFinished.connect(self._on_load_finished)
        self._tabs.addTab(self._hub_web, "AI Hub")
        self._tabs.setCurrentWidget(self._hub_web)
        self._tabs.setStyleSheet(
            "QTabBar::tab { min-width: 100px; padding: 6px 16px; }"
        )
        mw.mainLayout.insertWidget(1, self._tabs)
        self._closed = False
        self._hub_web.load_url(self._hub_url())

    def close(self):
        if self._closed:
            return
        tabs, main_web = self._tabs, self._main_web
        self._closed = True
        self._hub_web = None
        self._tabs = None
        self._main_web = None
        if tabs:
            mw.mainLayout.removeWidget(tabs)
            tabs.removeTab(0)
            tabs.deleteLater()
        if main_web:
            mw.mainLayout.insertWidget(1, main_web)
            main_web.show()

    def is_closed(self):
        return self._closed

    def focus(self):
        if self._tabs and self._hub_web:
            self._tabs.setCurrentWidget(self._hub_web)
