#!/usr/bin/env python3

from __future__ import annotations

import logging
import threading
import time
import warnings
from typing import Any

from onrobot.device import Device
from onrobot.dimensions import get_static_dimensions
from onrobot.errors import (
    OnRobotConnectionError,
    OnRobotError,
    OnRobotTimeoutError,
    OnRobotValidationError,
)
from onrobot.policies import OperationPolicy

LOGGER = logging.getLogger(__name__)

# Device ID
SG_ID = 0x50

# Legacy return codes
CONN_ERR = -2
RET_OK = 0
RET_FAIL = -1

DEFAULT_TOOL_TYPE = "SG-a-S"
SG_TOOL_TYPES = {
    "SG-a-H": 2,
    "SG-a-S": 3,
    "SG-b-H": 4,
}
_NORMALIZED_TOOL_TYPES = {
    name.lower(): tool_id for name, tool_id in SG_TOOL_TYPES.items()
}


class SG:
    """Soft Gripper client with typed API and compatibility wrappers."""

    cb = None

    def __init__(
        self,
        dev: Device,
        tool_type: str | int = DEFAULT_TOOL_TYPE,
        policy: OperationPolicy | None = None,
    ):
        get_cb = getattr(dev, "get_compute_box", None) or getattr(dev, "getCB")
        self.cb = get_cb()
        self._lock = threading.Lock()
        self._cb_ip = getattr(dev, "Global_cbip", None)
        self._status_client = None
        self._tool_type = self._resolve_tool_type(tool_type)
        self._policy = policy or OperationPolicy()

    @property
    def tool_type(self) -> str:
        return self._tool_type[0]

    @property
    def tool_id(self) -> int:
        return self._tool_type[1]

    def _call_xmlrpc(self, method_name: str, *args: Any):
        with self._lock:
            method = getattr(self.cb, method_name)
            return method(*args)

    def _safe_dimension_value(self, method_name: str, t_index: int = 0):
        try:
            return self._call_xmlrpc(method_name, t_index)
        except Exception:  # noqa: BLE001
            return None

    def _resolve_tool_type(self, tool_type: str | int | None) -> tuple[str, int]:
        if tool_type is None:
            return DEFAULT_TOOL_TYPE, SG_TOOL_TYPES[DEFAULT_TOOL_TYPE]
        if isinstance(tool_type, str):
            tool_id = _NORMALIZED_TOOL_TYPES.get(tool_type.strip().lower())
            if tool_id is None:
                raise OnRobotValidationError(f"Unsupported Soft Gripper tool type: {tool_type}")
            for name, candidate_id in SG_TOOL_TYPES.items():
                if candidate_id == tool_id:
                    return name, tool_id
        if isinstance(tool_type, int):
            for name, candidate_id in SG_TOOL_TYPES.items():
                if candidate_id == tool_type:
                    return name, candidate_id
        raise OnRobotValidationError(f"Unsupported Soft Gripper tool type: {tool_type}")

    def _require_connected(self, t_index: int = 0) -> None:
        try:
            connected = bool(self._call_xmlrpc("cb_is_device_connected", t_index, SG_ID))
        except Exception as exc:  # noqa: BLE001
            raise OnRobotConnectionError("Failed to query Soft Gripper connection") from exc
        if not connected:
            raise OnRobotConnectionError("No Soft Gripper connected on the given index")

    def _require_initialized(self, t_index: int = 0) -> None:
        if not self.is_initialized(t_index):
            raise OnRobotError("Soft Gripper is not initialized")

    def _wait_until_not_busy(self, t_index: int, timeout_s: float, reason: str) -> None:
        start = time.monotonic()
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if (
                not bool(self.is_busy(t_index))
                and time.monotonic() - start >= self._policy.poll_interval_s
            ):
                return
            time.sleep(self._policy.poll_interval_s)
        raise OnRobotTimeoutError(reason)

    def _validate_width(self, t_index: int, width: float) -> None:
        limits = self.get_min_max(t_index)
        min_open = limits["min_open"]
        max_open = limits["max_open"]
        if width < min_open or width > max_open:
            raise OnRobotValidationError(
                f"Invalid width {width}; valid range is {min_open}-{max_open}"
            )

    def is_connected(self, t_index: int = 0) -> bool:
        self._require_connected(t_index)
        return True

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
            LOGGER.exception("Unable to start Soft Gripper status stream")
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
        return client.get_device_variable(device_id=t_index, product_code=SG_ID)

    def isConnected(self, t_index=0):  # noqa: N802
        warnings.warn(
            "isConnected() is deprecated; use is_connected().",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            return self.is_connected(t_index=t_index)
        except OnRobotConnectionError:
            LOGGER.warning("No Soft Gripper connected on index %s", t_index)
            return False

    def is_initialized(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_initialized", t_index)

    def isInit(self, t_index=0):  # noqa: N802
        warnings.warn(
            "isInit() is deprecated; use is_initialized().",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            return self.is_initialized(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def is_busy(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_busy", t_index)

    def isBusy(self, t_index=0):  # noqa: N802
        warnings.warn("isBusy() is deprecated; use is_busy().", DeprecationWarning, stacklevel=2)
        try:
            return self.is_busy(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def is_gripped(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_grip_detected", t_index)

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

    def get_all_variables(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_all_variables", t_index)

    def get_all_double_variables(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_all_double_variables", t_index)

    def get_all_integer_variables(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_all_integer_variables", t_index)

    def get_all_boolean_variables(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_all_boolean_variables", t_index)

    def get_tool_id(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_sg_tool_id", t_index)

    def get_status(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_status", t_index)

    def get_error(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_error", t_index)

    def get_operation_counter(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_operation_counter", t_index)

    def get_width(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_width", t_index)

    def get_depth(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_depth", t_index)

    def get_depth_relative(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_depth_relative", t_index)

    def get_max_depth(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_depth_static_silicone", t_index)

    def get_min_max(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_min_max", t_index)

    def get_min_open(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_min_open", t_index)

    def get_max_open(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_max_open", t_index)

    def get_dimensions(self, t_index: int = 0):
        self._require_connected(t_index)
        tool_id = self._safe_dimension_value("sg_get_sg_tool_id", t_index)
        tool_type = None
        if tool_id is not None:
            for name, candidate_id in SG_TOOL_TYPES.items():
                if candidate_id == tool_id:
                    tool_type = name
                    break
        min_max = self._safe_dimension_value("sg_get_min_max", t_index)
        min_open = None
        max_open = None
        if isinstance(min_max, dict):
            min_open = min_max.get("min_open")
            max_open = min_max.get("max_open")
        return get_static_dimensions("sg").with_live_values(
            current_width_mm=self._safe_dimension_value("sg_get_width", t_index),
            current_depth_mm=self._safe_dimension_value("sg_get_depth", t_index),
            relative_depth_mm=self._safe_dimension_value(
                "sg_get_depth_relative",
                t_index,
            ),
            max_depth_mm=self._safe_dimension_value(
                "sg_get_depth_static_silicone",
                t_index,
            ),
            min_open_mm=min_open,
            max_open_mm=max_open,
            tool_id=tool_id,
            tool_type=tool_type,
            live_source="Compute Box XML-RPC",
        )

    def is_calibrated(self, t_index: int = 0):
        self._require_connected(t_index)
        return self._call_xmlrpc("sg_get_calibrated", t_index)

    def initialize(
        self,
        t_index: int = 0,
        tool_type: str | int | None = None,
        wait: bool = True,
    ) -> None:
        self._require_connected(t_index)
        selected_tool_type = self.tool_type if tool_type is None else tool_type
        _, tool_id = self._resolve_tool_type(selected_tool_type)
        result = self._call_xmlrpc("sg_initialize", t_index, int(tool_id))
        if wait:
            self._wait_until_not_busy(
                t_index,
                self._policy.busy_timeout_s,
                "Soft Gripper init command timeout",
            )
        if result != RET_OK:
            raise OnRobotError("Failed to initialize Soft Gripper")

    def init(self, t_index=0, tool_id=None):  # noqa: A002
        try:
            self.initialize(t_index=t_index, tool_type=tool_id, wait=True)
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Soft Gripper init failed: %s", exc)
            return RET_FAIL

    def calibrate(self, t_index: int = 0, wait: bool = True) -> None:
        self._require_connected(t_index)
        result = self._call_xmlrpc("sg_calibrate", t_index)
        if wait:
            self._wait_until_not_busy(
                t_index,
                self._policy.busy_timeout_s,
                "Soft Gripper calibrate command timeout",
            )
        if result != RET_OK:
            raise OnRobotError("Failed to calibrate Soft Gripper")

    def calibrate_legacy(self, t_index=0, f_wait=True):
        try:
            self.calibrate(t_index=t_index, wait=f_wait)
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Soft Gripper calibrate failed: %s", exc)
            return RET_FAIL

    def stop(self, t_index: int = 0) -> None:
        self._require_connected(t_index)
        self._call_xmlrpc("sg_stop", t_index)

    def halt(self, t_index=0):
        warnings.warn("halt() is deprecated; use stop().", DeprecationWarning, stacklevel=2)
        try:
            self.stop(t_index=t_index)
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Soft Gripper halt failed: %s", exc)
            return RET_FAIL

    def home(self, t_index: int = 0, wait: bool = True) -> None:
        self._require_connected(t_index)
        self._require_initialized(t_index)
        self._call_xmlrpc("sg_home", t_index)
        if wait:
            self._wait_until_not_busy(
                t_index,
                self._policy.busy_timeout_s,
                "Soft Gripper home command timeout",
            )

    def home_legacy(self, t_index=0, f_wait=True):
        try:
            self.home(t_index=t_index, wait=f_wait)
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Soft Gripper home failed: %s", exc)
            return RET_FAIL

    def move_to_width(
        self,
        t_index: int = 0,
        width: float = 0,
        gentle: bool = True,
        wait: bool = True,
    ) -> None:
        self._require_connected(t_index)
        self._require_initialized(t_index)
        self._validate_width(t_index, width)
        self._call_xmlrpc("sg_grip", t_index, int(width), bool(gentle), False)
        if wait:
            self._wait_until_not_busy(
                t_index,
                self._policy.busy_timeout_s,
                "Soft Gripper move command timeout",
            )

    def move(self, t_index=0, t_width=0, f_wait=True):
        try:
            self.move_to_width(t_index=t_index, width=t_width, gentle=True, wait=f_wait)
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Soft Gripper move failed: %s", exc)
            return RET_FAIL

    def grip(
        self,
        t_index: int = 0,
        width: float = 0,
        gentle: bool = False,
        wait: bool = True,
    ) -> None:
        self._require_connected(t_index)
        self._require_initialized(t_index)
        self._validate_width(t_index, width)
        self._call_xmlrpc("sg_grip", t_index, int(width), bool(gentle), True)
        if wait:
            self._wait_until_not_busy(
                t_index,
                self._policy.busy_timeout_s,
                "Soft Gripper grip command timeout",
            )

    def grip_legacy(self, t_index=0, t_width=0, f_wait=True):
        try:
            self.grip(t_index=t_index, width=t_width, gentle=False, wait=f_wait)
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Soft Gripper grip failed: %s", exc)
            return RET_FAIL

    def gentle_grip(self, t_index: int = 0, width: float = 0, wait: bool = True) -> None:
        self.grip(t_index=t_index, width=width, gentle=True, wait=wait)

    def gentle_grip_legacy(self, t_index=0, t_width=0, f_wait=True):
        try:
            self.gentle_grip(t_index=t_index, width=t_width, wait=f_wait)
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Soft Gripper gentle grip failed: %s", exc)
            return RET_FAIL


if __name__ == "__main__":
    device = Device()
    gripper_sg = SG(device)
    print("Connection check:", gripper_sg.is_connected())
