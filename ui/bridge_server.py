import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from core.logger import log


class _BridgeHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress standard HTTP access log noise
        pass

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Bridge-Token, Authorization")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != "/bridge":
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()
            return

        # Secret Token Authentication check
        req_token = self.headers.get("X-Bridge-Token") or self.headers.get("Authorization", "").replace("Bearer ", "")
        expected_token = getattr(self.server, "expected_token", "")
        if expected_token and req_token != expected_token:
            self.send_response(403)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            err_bytes = json.dumps({"success": False, "error_code": "E_FORBIDDEN", "message": "Invalid bridge token"}).encode("utf-8")
            self.wfile.write(err_bytes)
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            payload_str = body_bytes.decode("utf-8")

            # Call the Python bridge handler passed from main_window
            handler = getattr(self.server, "bridge_handler", None)
            if handler:
                response_str = handler(payload_str)
            else:
                response_str = json.dumps({"success": False, "error_code": "E_NO_HANDLER", "message": "No handler attached"})

            response_bytes = response_str.encode("utf-8")

            self.send_response(200)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)

        except Exception as e:
            log.exception(f"Error handling HTTP bridge request: {e}")
            self.send_response(500)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            err_bytes = json.dumps({"success": False, "error_code": "E_HTTP_SERVER", "message": str(e)}).encode("utf-8")
            self.wfile.write(err_bytes)


class BridgeServer:
    def __init__(self, bridge_handler, token: str = ""):
        self.bridge_handler = bridge_handler
        self.token = token
        self.httpd: HTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.port: int = 0

    def start(self) -> int:
        if self.httpd:
            return self.port

        self.httpd = HTTPServer(("127.0.0.1", 0), _BridgeHTTPHandler)
        self.httpd.bridge_handler = self.bridge_handler
        self.httpd.expected_token = self.token
        self.port = self.httpd.server_address[1]

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

        log.info(f"Local HTTP Bridge Server started on http://127.0.0.1:{self.port}/bridge")
        return self.port

    def stop(self):
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception as e:
                log.error(f"Error shutting down BridgeServer: {e}")
            self.httpd = None
            self.thread = None
            log.info("Local HTTP Bridge Server stopped.")
