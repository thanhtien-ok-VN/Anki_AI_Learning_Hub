import json

from aqt import gui_hooks
from aqt.utils import tooltip


def setup_bridge(webview, engine, dialog):
    def on_js_message(handled, message, context):
        if not message.startswith("aihub:"):
            return handled

        try:
            payload = json.loads(message[6:])
            action = payload.get("action", "")
            data = payload.get("data", {})
            msg_id = payload.get("id", 0)

            response = engine.handle_js_message(json.dumps({"action": action, "data": data}))

            if response is not None:
                js = json.dumps({
                    "id": msg_id,
                    "action": action,
                    "data": response,
                })
                webview.eval(f"window.Bridge.receive('{_escape(js)}')")
                return (True, None)

        except Exception as e:
            from core.logger import log
            import traceback
            tb = traceback.format_exc()
            log.error(f"Error in on_js_message: {e}\n{tb}")

        return handled

    gui_hooks.webview_did_receive_js_message.append(on_js_message)
    return on_js_message


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
