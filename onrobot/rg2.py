#!/usr/bin/env python3

from __future__ import annotations

import logging
import time
import warnings

from onrobot.device import Device
from onrobot.dimensions import get_static_dimensions
from onrobot.errors import OnRobotConnectionError, OnRobotTimeoutError
from onrobot.policies import OperationPolicy

LOGGER = logging.getLogger(__name__)

# Device IDs
RG2_ID = 0x20

# Legacy return codes
CONN_ERR = -2
RET_OK = 0
RET_FAIL = -1


class RG:
    """RG2 gripper API with snake_case methods and legacy wrappers."""

    cb = None

    def __init__(self, dev: Device, policy: OperationPolicy | None = None):
        super().__init__()
        get_cb = getattr(dev, "get_compute_box", None) or getattr(dev, "getCB")
        self.cb = get_cb()
        self._policy = policy or OperationPolicy()

    def _require_connected(self, t_index: int) -> None:
        try:
            connected = bool(self.cb.cb_is_device_connected(t_index, RG2_ID))
        except Exception as exc:  # noqa: BLE001
            raise OnRobotConnectionError("Failed to query RG2 connection") from exc
        if not connected:
            raise OnRobotConnectionError("No RG2 device connected")

    def _wait_until_not_busy(self, t_index: int, timeout_s: float, reason: str) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if not bool(self.cb.rg_get_busy(t_index)):
                return
            time.sleep(self._policy.poll_interval_s)
        raise OnRobotTimeoutError(reason)

    def _safe_dimension_value(self, method_name: str, t_index: int = 0):
        try:
            method = getattr(self.cb, method_name)
            return method(t_index)
        except Exception:  # noqa: BLE001
            return None

    def is_connected(self, t_index: int) -> bool:
        self._require_connected(t_index)
        return True

    def isConnected(self, t_index):  # noqa: N802
        warnings.warn("isConnected() is deprecated; use is_connected().", DeprecationWarning, stacklevel=2)
        try:
            return self.is_connected(t_index=t_index)
        except OnRobotConnectionError:
            LOGGER.warning("No RG2 device connected on index %s", t_index)
            return False

    def move_grip(self, t_index: int, twidth: float, tforce: float, wait: bool) -> None:
        self._require_connected(t_index)
        self.cb.rg_grip(t_index, float(twidth), float(tforce))
        if wait:
            self._wait_until_not_busy(t_index, self._policy.busy_timeout_s, "RG move timeout")

    def move(self, t_index, twidth, tforce, fwait):
        try:
            self.move_grip(t_index=t_index, twidth=twidth, tforce=tforce, wait=fwait)
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("RG move failed: %s", exc)
            return RET_FAIL

    def grip_with_detection(self, t_index: int, twidth: float, tforce: float, wait: bool) -> None:
        self._require_connected(t_index)
        self.cb.rg_grip(t_index, float(twidth), float(tforce))
        if not wait:
            return
        self._wait_until_not_busy(t_index, self._policy.busy_timeout_s, "RG grip timeout")
        deadline = time.monotonic() + self._policy.detect_timeout_s
        while time.monotonic() < deadline:
            if bool(self.cb.rg_get_grip_detected(t_index)):
                return
            time.sleep(self._policy.poll_interval_s)
        raise OnRobotTimeoutError("RG grip detection timeout")

    def grip(self, t_index, twidth, tforce, fwait):
        try:
            self.grip_with_detection(
                t_index=t_index,
                twidth=twidth,
                tforce=tforce,
                wait=fwait,
            )
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("RG grip failed: %s", exc)
            return RET_FAIL

    def stop(self, t_index):
        try:
            self._require_connected(t_index)
        except OnRobotConnectionError:
            return CONN_ERR
        return self.cb.rg_stop(t_index)

    def get_speed(self, t_index):
        try:
            self._require_connected(t_index)
        except OnRobotConnectionError:
            return CONN_ERR
        return self.cb.rg_get_speed(t_index)

    def get_depth(self, t_index):
        try:
            self._require_connected(t_index)
        except OnRobotConnectionError:
            return CONN_ERR
        return self.cb.rg_get_depth(t_index)

    def get_rel_depth(self, t_index):
        try:
            self._require_connected(t_index)
        except OnRobotConnectionError:
            return CONN_ERR
        return self.cb.rg_get_relative_depth(t_index)

    def get_width(self, t_index):
        try:
            self._require_connected(t_index)
        except OnRobotConnectionError:
            return CONN_ERR
        return self.cb.rg_get_width(t_index)

    def get_ft_offset(self, t_index):
        try:
            self._require_connected(t_index)
        except OnRobotConnectionError:
            return CONN_ERR
        return self.cb.rg_get_fingertip_offset(t_index)

    def get_dimensions(self, t_index: int = 0):
        self._require_connected(t_index)
        return get_static_dimensions("rg2").with_live_values(
            current_width_mm=self._safe_dimension_value("rg_get_width", t_index),
            current_depth_mm=self._safe_dimension_value("rg_get_depth", t_index),
            relative_depth_mm=self._safe_dimension_value(
                "rg_get_relative_depth",
                t_index,
            ),
            fingertip_offset_mm=self._safe_dimension_value(
                "rg_get_fingertip_offset",
                t_index,
            ),
            live_source="Compute Box XML-RPC",
        )

    def is_busy(self, t_index):
        self._require_connected(t_index)
        return self.cb.rg_get_busy(t_index)

    def isBusy(self, t_index):  # noqa: N802
        warnings.warn("isBusy() is deprecated; use is_busy().", DeprecationWarning, stacklevel=2)
        try:
            return self.is_busy(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def is_gripped(self, t_index):
        self._require_connected(t_index)
        return self.cb.rg_get_grip_detected(t_index)

    def isGripped(self, t_index):  # noqa: N802
        warnings.warn("isGripped() is deprecated; use is_gripped().", DeprecationWarning, stacklevel=2)
        try:
            return self.is_gripped(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def is_safety_on(self, t_index):
        self._require_connected(t_index)
        s1 = self.cb.rg_get_s1_triggered(t_index)
        s2 = self.cb.rg_get_s2_triggered(t_index)
        return bool(s1 or s2)

    def isSafetyON(self, t_index):  # noqa: N802
        warnings.warn(
            "isSafetyON() is deprecated; use is_safety_on().",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            return self.is_safety_on(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def set_ft_offset(self, t_index, ft_offset):
        try:
            self._require_connected(t_index)
        except OnRobotConnectionError:
            return CONN_ERR
        return self.cb.rg_set_fingertip_offset(t_index, float(ft_offset))

    def reset_power(self, t_index):
        self._require_connected(t_index)
        self.cb.cb_reset_tool_power()

    def resetpower(self, t_index):  # noqa: N802
        warnings.warn(
            "resetpower() is deprecated; use reset_power().",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            self.reset_power(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR


if __name__ == "__main__":
    device = Device()
    gripper_rg2 = RG(device)
    print("Connection check:", gripper_rg2.is_connected(0))
