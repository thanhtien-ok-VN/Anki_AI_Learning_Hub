"""IPC Router for Anki AI Learning Hub.

Dispatches incoming JSON messages from QWebEngineView PyCmd bridge to registered
service handlers and enforces standardized response envelopes and execution metadata.
"""
from dataclasses import dataclass
import json
import traceback
from typing import Any, Callable, Dict, List, Optional
from core.logger import log, flow


@dataclass(frozen=True)
class IPCActionSpec:
    """Metadata specification for an IPC action."""
    name: str
    handler: Callable[[Dict[str, Any]], Any]
    execution_mode: str = "main"  # "main" | "background"
    timeout_sec: float = 30.0
    description: str = ""


class IPCRouter:
    def __init__(self):
        self._specs: Dict[str, IPCActionSpec] = {}

    def register_spec(self, spec: IPCActionSpec) -> None:
        """Register an IPCActionSpec defining handler and execution mode."""
        self._specs[spec.name] = spec

    def register_handler(
        self,
        action: str,
        handler: Callable[[Dict[str, Any]], Any],
        execution_mode: str = "main",
        timeout_sec: float = 30.0,
        description: str = "",
    ) -> None:
        """Register a handler function for an IPC action."""
        spec = IPCActionSpec(
            name=action,
            handler=handler,
            execution_mode=execution_mode,
            timeout_sec=timeout_sec,
            description=description,
        )
        self.register_spec(spec)

    def get_spec(self, action: str) -> Optional[IPCActionSpec]:
        """Retrieve action specification if registered."""
        return self._specs.get(action)

    def is_background_action(self, action: Any) -> bool:
        """Check if action is configured to run asynchronously in the background."""
        if isinstance(action, dict):
            action = action.get("action", "")
        if not isinstance(action, str):
            return False
        spec = self._specs.get(action)
        return bool(spec and spec.execution_mode == "background")

    def get_action_names(self) -> List[str]:
        """Return list of all registered action names."""
        return list(self._specs.keys())

    def dispatch(self, raw_message: Any) -> Dict[str, Any]:
        """Dispatch a raw JSON string or dict message to its handler."""
        if not raw_message:
            return {
                "success": False,
                "data": {},
                "error_code": "E_EMPTY_MSG",
                "message": "Empty message received",
            }

        try:
            if isinstance(raw_message, dict):
                msg = raw_message
            else:
                msg = json.loads(raw_message)

            action = msg.get("action")
            data = msg.get("data", {})
            if isinstance(action, dict):
                data = action.get("data", data)
                action = action.get("action")

            if not action or not isinstance(action, str):
                log.warn("Missing or invalid 'action' in IPC message")
                return {
                    "success": False,
                    "data": {},
                    "error_code": "E_NO_ACTION",
                    "message": "Missing 'action' in request",
                }

            flow(
                phase="EVENT",
                message=f"IPC received action: {action}",
                extra={"has_data": bool(data)}
            )

            spec = self._specs.get(action)
            if not spec or not spec.handler:
                log.warn(f"Unknown IPC action: {action}")
                return {
                    "success": False,
                    "data": {},
                    "error_code": "E_UNKNOWN",
                    "message": f"Unknown action: {action}",
                }

            result = spec.handler(data)

            # Response normalization
            if isinstance(result, dict) and "success" in result:
                if not result.get("success"):
                    err_msg = result.get("message") or "The operation failed."
                    err_code = result.get("error_code") or "E_OPERATION"
                    log.warn(f"Bridge operation failed [{err_code}]: {err_msg}")
                    return {
                        "success": False,
                        "data": result.get("data", {}),
                        "error_code": err_code,
                        "message": err_msg,
                    }
                return result

            if isinstance(result, dict) and result.get("error"):
                err_msg = result.get("message") or "The operation failed."
                err_code = result.get("error_code") or "E_OPERATION"
                return {
                    "success": False,
                    "data": {},
                    "error_code": err_code,
                    "message": err_msg,
                }

            return {"success": True, "data": result or {}}

        except json.JSONDecodeError as e:
            log.warn(f"Invalid JSON in IPC message: {e}")
            return {
                "success": False,
                "data": {},
                "error_code": "E_INTERNAL",
                "message": "Malformed JSON request",
            }
        except Exception as e:
            tb = traceback.format_exc()
            log.error(f"IPCRouter dispatch error: {e}\n{tb}")
            return {
                "success": False,
                "data": {},
                "error_code": "E_INTERNAL",
                "message": "The AI Hub could not complete this request.",
            }
