#!/usr/bin/env python3

from __future__ import annotations

import logging
import threading
import time
import urllib.error
import urllib.request
import warnings
from typing import Any

from onrobot.device import Device
from onrobot.errors import (
    OnRobotConnectionError,
    OnRobotTimeoutError,
    OnRobotValidationError,
)
from onrobot.dimensions import get_static_dimensions
from onrobot.gripper_profiles import get_gripper_profile
from onrobot.policies import OperationPolicy

LOGGER = logging.getLogger(__name__)

# Device ID
TWOFG_ID = 0xC0

# Legacy return codes
CONN_ERR = -2
RET_OK = 0
RET_FAIL = -1

GRIPPER_PROFILE = get_gripper_profile("twofg7")


class TWOFG:
    """2FG gripper client with typed snake_case API + compatibility wrappers."""

    cb = None

    def __init__(self, dev: Device, policy: OperationPolicy | None = None):
        get_cb = getattr(dev, "get_compute_box", None) or getattr(dev, "getCB")
        self.cb = get_cb()
        self._lock = threading.Lock()
        self._cb_ip = getattr(dev, "Global_cbip", None)
        self._status_client = None
        self._profile = GRIPPER_PROFILE
        self._policy = policy or OperationPolicy()

    @property
    def profile(self):
        return self._profile

    def _call_xmlrpc(self, method_name: str, *args: Any):
        with self._lock:
            method = getattr(self.cb, method_name)
            return method(*args)

    def _call_rest(self, path: str, timeout_s: float = 2.0):
        if not self._cb_ip:
            raise OnRobotConnectionError("Compute Box IP is not configured")
        url = f"http://{self._cb_ip}/{path.lstrip('/')}"
        with self._lock:
            request = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                return response.read().decode("utf-8")

    def _require_connected(self, t_index: int = 0) -> None:
        try:
            connected = bool(
                self._call_xmlrpc("cb_is_device_connected", t_index, TWOFG_ID)
            )
        except Exception as exc:  # noqa: BLE001
            raise OnRobotConnectionError("Failed to query 2FG connection status") from exc
        if not connected:
            raise OnRobotConnectionError("No 2FG device connected on the given index")

    def _wait_until(self, predicate, timeout_s: float, timeout_message: str) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(self._policy.poll_interval_s)
        raise OnRobotTimeoutError(timeout_message)

    def start_status_stream(self, on_update=None, timeout_s: float = 2.0) -> bool:
        if not self._cb_ip:
            return False
        if self._status_client is None:
            from onrobot.status_client import OnRobotStatusClient

            self._status_client = OnRobotStatusClient(self._cb_ip, on_update=on_update)
        try:
            self._status_client.connect(timeout_s=timeout_s)
            return True
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unable to start 2FG status stream")
            return False

    def stop_status_stream(self):
        client = self._status_client
        if client is None:
            return
        client.disconnect()

    def get_status_snapshot(self, t_index: int = 0):
        client = self._status_client
        if client is None:
            return None
        return client.get_device_variable(device_id=t_index, product_code=TWOFG_ID)

    def _safe_dimension_value(self, method_name: str, t_index: int = 0):
        try:
            return self._call_xmlrpc(method_name, t_index)
        except Exception:  # noqa: BLE001
            return None

    def _normalize_finger_orientation(self, orientation):
        if isinstance(orientation, bool):
            return orientation
        if isinstance(orientation, str):
            cleaned = orientation.strip().lower()
            if cleaned in {"outward", "out", "outside"}:
                return True
            if cleaned in {"inward", "in", "inside"}:
                return False
            return None
        if isinstance(orientation, (int, float)):
            value = int(orientation)
            if value < 0:
                return None
            if value == 2:
                return True
            if value == 1:
                return False
            return bool(value)
        return None

    def get_finger_orientation(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("twofg_finger_orientation_outward", t_index)

    def get_finger_orientation_label(self, t_index: int = 0):
        raw = self.get_finger_orientation(t_index)
        orientation = self._normalize_finger_orientation(raw)
        if orientation is None:
            return None
        return "outward" if orientation else "inward"

    def set_finger_orientation_value(
        self,
        t_index: int = 0,
        orientation=None,
        outward=None,
    ) -> None:
        self._require_connected(t_index)
        if outward is not None:
            resolved = bool(outward)
        else:
            resolved = self._normalize_finger_orientation(orientation)
        if resolved is None:
            raise OnRobotValidationError("Invalid finger orientation argument")
        try:
            self._call_xmlrpc("twofg_set_finger_orientation", t_index, float(resolved))
            return
        except Exception:
            pass
        try:
            rest_value = "true" if resolved else "false"
            self._call_rest(f"api/dc/twofg/set_finger_orientation/{t_index}/{rest_value}")
            return
        except (urllib.error.URLError, OnRobotConnectionError) as exc:
            raise OnRobotConnectionError("Unable to set finger orientation") from exc

    def set_finger_orientation(self, t_index=0, orientation=None, outward=None):
        try:
            self.set_finger_orientation_value(
                t_index=t_index,
                orientation=orientation,
                outward=outward,
            )
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception:  # noqa: BLE001
            return RET_FAIL

    def is_connected(self, t_index: int = 0) -> bool:
        self._require_connected(t_index)
        return True

    def isConnected(self, t_index=0):  # noqa: N802
        warnings.warn(
            "isConnected() is deprecated; use is_connected().",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            return self.is_connected(t_index=t_index)
        except OnRobotConnectionError:
            LOGGER.warning("No 2FG device connected on index %s", t_index)
            return False

    def is_busy(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("twofg_get_busy", t_index)

    def isBusy(self, t_index=0):  # noqa: N802
        warnings.warn("isBusy() is deprecated; use is_busy().", DeprecationWarning, stacklevel=2)
        try:
            return self.is_busy(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def is_gripped(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("twofg_get_grip_detected", t_index)

    def isGripped(self, t_index=0):  # noqa: N802
        warnings.warn(
            "isGripped() is deprecated; use is_gripped().",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            return self.is_gripped(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def get_status(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("twofg_get_status", t_index)

    def getStatus(self, t_index=0):  # noqa: N802
        warnings.warn(
            "getStatus() is deprecated; use get_status().",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            return self.get_status(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def get_external_width(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("twofg_get_external_width", t_index)

    def get_ext_width(self, t_index=0):
        try:
            return self.get_external_width(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def get_min_external_width(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("twofg_get_min_external_width", t_index)

    def get_min_ext_width(self, t_index=0):
        try:
            return self.get_min_external_width(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def get_max_external_width(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("twofg_get_max_external_width", t_index)

    def get_max_ext_width(self, t_index=0):
        try:
            return self.get_max_external_width(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def get_dimensions(self, t_index: int = 0):
        self._require_connected(t_index)
        orientation = None
        try:
            orientation = self.get_finger_orientation_label(t_index)
        except Exception:  # noqa: BLE001
            orientation = None
        return get_static_dimensions("twofg7").with_live_values(
            current_width_mm=self._safe_dimension_value(
                "twofg_get_external_width",
                t_index,
            ),
            min_width_mm=self._safe_dimension_value(
                "twofg_get_min_external_width",
                t_index,
            ),
            max_width_mm=self._safe_dimension_value(
                "twofg_get_max_external_width",
                t_index,
            ),
            finger_length_mm=self._safe_dimension_value("twofg_finger_length", t_index),
            finger_height_mm=self._safe_dimension_value("twofg_finger_height", t_index),
            fingertip_offset_mm=self._safe_dimension_value(
                "twofg_fingertip_offset",
                t_index,
            ),
            finger_orientation=orientation,
            live_source="Compute Box XML-RPC",
        )

    def get_force_value(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("twofg_get_force", t_index)

    def get_force(self, t_index=0):
        try:
            return self.get_force_value(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def stop_operation(self, t_index: int = 0):
        self._require_connected(t_index)
        self._call_xmlrpc("twofg_stop", t_index)

    def stop(self, t_index=0):
        try:
            self.stop_operation(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def grip_external(
        self,
        t_index: int = 0,
        t_width: float = GRIPPER_PROFILE.open_width_default,
        n_force: float = GRIPPER_PROFILE.force_default,
        p_speed: int = GRIPPER_PROFILE.speed_default,
        wait: bool = True,
    ) -> None:
        self._require_connected(t_index)
        max_width = self.get_max_external_width(t_index)
        min_width = self.get_min_external_width(t_index)
        if t_width > max_width or t_width < min_width:
            raise OnRobotValidationError(
                f"Invalid width {t_width}; valid range is {min_width}-{max_width}"
            )
        profile = self._profile
        if n_force > profile.force_max or n_force < profile.force_min:
            raise OnRobotValidationError(
                f"Invalid force {n_force}; valid range is {profile.force_min}-{profile.force_max}"
            )
        if p_speed > profile.speed_max or p_speed < profile.speed_min:
            raise OnRobotValidationError(
                f"Invalid speed {p_speed}; valid range is {profile.speed_min}-{profile.speed_max}"
            )
        self._call_xmlrpc("twofg_grip_external", t_index, float(t_width), int(n_force), int(p_speed))
        if not wait:
            return
        self._wait_until(
            lambda: not bool(self.is_busy(t_index)),
            self._policy.busy_timeout_s,
            "2FG grip command timeout",
        )
        self._wait_until(
            lambda: bool(self.is_gripped(t_index)),
            self._policy.detect_timeout_s,
            "2FG grip detection timeout",
        )

    def grip(
        self,
        t_index=0,
        t_width=GRIPPER_PROFILE.open_width_default,
        n_force=GRIPPER_PROFILE.force_default,
        p_speed=GRIPPER_PROFILE.speed_default,
        f_wait=True,
    ):
        try:
            self.grip_external(
                t_index=t_index,
                t_width=t_width,
                n_force=n_force,
                p_speed=p_speed,
                wait=f_wait,
            )
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("2FG grip failed: %s", exc)
            return RET_FAIL

    def move_external(self, t_index: int, t_width: float = 20.0, wait: bool = True) -> None:
        self._require_connected(t_index)
        max_width = self.get_max_external_width(t_index)
        min_width = self.get_min_external_width(t_index)
        if t_width > max_width or t_width < min_width:
            raise OnRobotValidationError(
                f"Invalid width {t_width}; valid range is {min_width}-{max_width}"
            )
        self._call_xmlrpc("twofg_grip_external", t_index, float(t_width), 100, 80)
        if not wait:
            return
        self._wait_until(
            lambda: not bool(self.is_busy(t_index)),
            self._policy.busy_timeout_s,
            "2FG move timeout",
        )

    def move(self, t_index, t_width=20.0, f_wait=True):
        try:
            self.move_external(t_index=t_index, t_width=t_width, wait=f_wait)
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("2FG move failed: %s", exc)
            return RET_FAIL


if __name__ == "__main__":
    device = Device()
    gripper_2fg7 = TWOFG(device)
    print("Connection check:", gripper_2fg7.is_connected())
