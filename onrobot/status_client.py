import threading
import time
from typing import Any, Callable, Dict, Optional

import socketio


class OnRobotStatusClient:
    """Listen for Compute Box status updates over Socket.IO."""

    def __init__(
        self,
        cb_ip: str,
        *,
        on_update: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self._cb_ip = cb_ip
        self._on_update = on_update
        self._lock = threading.Lock()
        self._latest: Dict[str, Any] = {}
        self._latest_timestamp: Optional[float] = None
        self._sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=1.0,
            reconnection_delay_max=5.0,
        )
        self._sio.on("message", self._handle_message)

    def connect(self, timeout_s: float = 2.0) -> None:
        if self._sio.connected:
            return
        self._sio.connect(
            f"http://{self._cb_ip}",
            transports=["websocket", "polling"],
            wait_timeout=timeout_s,
        )

    def disconnect(self) -> None:
        if self._sio.connected:
            self._sio.disconnect()

    def is_connected(self) -> bool:
        return self._sio.connected

    def latest_timestamp(self) -> Optional[float]:
        with self._lock:
            return self._latest_timestamp

    def latest_payload(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._latest)

    def get_device_variable(
        self,
        *,
        device_id: int = 0,
        product_code: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        payload = self.latest_payload()
        devices = payload.get("devices", [])
        for device in devices:
            if device.get("deviceId") != device_id:
                continue
            if product_code is not None and device.get("productCode") != product_code:
                continue
            variable = device.get("variable")
            if isinstance(variable, dict):
                return dict(variable)
        return None

    def _handle_message(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        if "devices" not in payload:
            return
        with self._lock:
            self._latest = payload
            self._latest_timestamp = time.time()
        if self._on_update is not None:
            try:
                self._on_update(payload)
            except Exception:
                # Avoid crashing the socket thread due to user callbacks.
                pass
