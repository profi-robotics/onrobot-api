#!/usr/bin/env python3

from __future__ import annotations

import logging
import time
import warnings

from onrobot.device import Device
from onrobot.dimensions import get_static_dimensions
from onrobot.errors import (
    OnRobotConnectionError,
    OnRobotValidationError,
    OnRobotTimeoutError,
)
from onrobot.policies import OperationPolicy

LOGGER = logging.getLogger(__name__)

# Device IDs
VG10_ID = 0x10
VGC10_ID = 0x11

# Legacy return codes
CONN_ERR = -2
RET_OK = 0
RET_FAIL = -1


class VG:
    """VG10/VGC10 vacuum gripper API with snake_case methods and legacy wrappers."""

    cb = None

    def __init__(self, dev: Device, policy: OperationPolicy | None = None):
        get_cb = getattr(dev, "get_compute_box", None) or getattr(dev, "getCB")
        self.cb = get_cb()
        self._cb_ip = getattr(dev, "Global_cbip", None)
        self._status_client = None
        self._policy = policy or OperationPolicy()

    def _require_connected(self, t_index: int = 0) -> None:
        try:
            connected = bool(
                self.cb.cb_is_device_connected(t_index, VG10_ID)
                or self.cb.cb_is_device_connected(t_index, VGC10_ID)
            )
        except Exception as exc:  # noqa: BLE001
            raise OnRobotConnectionError("Failed to query VG connection") from exc
        if not connected:
            raise OnRobotConnectionError("No VG10/VGC10 device connected")

    def _validate_vacuum(self, vacuum: int | float, name: str) -> None:
        if vacuum < 1 or vacuum > 80:
            raise OnRobotValidationError(f"Invalid {name} {vacuum}; valid range is 1-80")

    def is_connected(self, t_index: int = 0) -> bool:
        self._require_connected(t_index)
        return True

    def is_vg10(self, t_index: int = 0) -> bool:
        self._require_connected(t_index)
        return bool(self.cb.cb_is_device_connected(t_index, VG10_ID))

    def is_vgc10(self, t_index: int = 0) -> bool:
        self._require_connected(t_index)
        return bool(self.cb.cb_is_device_connected(t_index, VGC10_ID))

    def get_dimensions(self, t_index: int = 0):
        self._require_connected(t_index)
        try:
            if bool(self.cb.cb_is_device_connected(t_index, VGC10_ID)):
                return get_static_dimensions("vgc10")
            if bool(self.cb.cb_is_device_connected(t_index, VG10_ID)):
                return get_static_dimensions("vg10")
        except Exception as exc:  # noqa: BLE001
            raise OnRobotConnectionError("Failed to query VG model dimensions") from exc
        raise OnRobotConnectionError("No VG10/VGC10 device connected")

    def isVG10(self, t_index=0):  # noqa: N802
        warnings.warn("isVG10() is deprecated; use is_vg10().", DeprecationWarning, stacklevel=2)
        try:
            return self.is_vg10(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def isVGC10(self, t_index=0):  # noqa: N802
        warnings.warn("isVGC10() is deprecated; use is_vgc10().", DeprecationWarning, stacklevel=2)
        try:
            return self.is_vgc10(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

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
            LOGGER.exception("Unable to start VG status stream")
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
        snapshot = client.get_device_variable(device_id=t_index, product_code=VGC10_ID)
        if snapshot is not None:
            return snapshot
        return client.get_device_variable(device_id=t_index, product_code=VG10_ID)

    def isConnected(self, t_index=0):  # noqa: N802
        warnings.warn("isConnected() is deprecated; use is_connected().", DeprecationWarning, stacklevel=2)
        try:
            return self.is_connected(t_index=t_index)
        except OnRobotConnectionError:
            LOGGER.warning("No VGC10 connected on index %s", t_index)
            return False

    def grip_vacuum(self, t_index: int = 0, vacuum_a: int = 1, vacuum_b: int = 1, wait: bool = False) -> None:
        self._require_connected(t_index)
        self._validate_vacuum(vacuum_a, "vacuum_a")
        self._validate_vacuum(vacuum_b, "vacuum_b")
        self.cb.vg10_grip(t_index, 0, float(vacuum_a))
        self.cb.vg10_grip(t_index, 1, float(vacuum_b))
        if not wait:
            return
        deadline = time.monotonic() + self._policy.vacuum_timeout_s
        while time.monotonic() < deadline:
            vac_a = self.get_vacuum_a(t_index)
            vac_b = self.get_vacuum_b(t_index)
            if vacuum_a <= vac_a and vacuum_b <= vac_b:
                return
            time.sleep(self._policy.poll_interval_s)
        self.release_vacuum(
            t_index=t_index,
            channel_a=vacuum_a > self.get_vacuum_a(t_index),
            channel_b=vacuum_b > self.get_vacuum_b(t_index),
            wait=False,
        )
        raise OnRobotTimeoutError("Timeout during VG grip command")

    def grip(self, t_index=0, vacuumA=1, vacuumB=1, waiting=False):  # noqa: N803
        try:
            self.grip_vacuum(
                t_index=t_index,
                vacuum_a=vacuumA,
                vacuum_b=vacuumB,
                wait=waiting,
            )
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("VG grip failed: %s", exc)
            return RET_FAIL

    def release_vacuum(
        self,
        t_index: int = 0,
        channel_a: bool = True,
        channel_b: bool = True,
        wait: bool = False,
    ) -> None:
        self._require_connected(t_index)
        self.cb.vg10_release(t_index, channel_a, channel_b)
        if not wait:
            return
        deadline = time.monotonic() + self._policy.vacuum_timeout_s
        while time.monotonic() < deadline:
            vac_a = self.get_vacuum_a(t_index)
            vac_b = self.get_vacuum_b(t_index)
            ok_a = (not channel_a) or vac_a <= 0.1
            ok_b = (not channel_b) or vac_b <= 0.1
            if ok_a and ok_b:
                return
            time.sleep(self._policy.poll_interval_s)
        raise OnRobotTimeoutError("Timeout during VG release command")

    def release(self, t_index=0, channelA=True, channelB=True, waiting=False):  # noqa: N803
        try:
            self.release_vacuum(
                t_index=t_index,
                channel_a=channelA,
                channel_b=channelB,
                wait=waiting,
            )
            return RET_OK
        except OnRobotConnectionError:
            return CONN_ERR
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("VG release failed: %s", exc)
            return RET_FAIL

    def get_vacuum_a(self, t_index: int = 0):
        return self.get_vacuum(t_index).get("a_vacuum", 0.0)

    def getvacA(self, t_index=0):  # noqa: N802
        warnings.warn("getvacA() is deprecated; use get_vacuum_a().", DeprecationWarning, stacklevel=2)
        try:
            return self.get_vacuum_a(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def get_vacuum_b(self, t_index: int = 0):
        return self.get_vacuum(t_index).get("b_vacuum", 0.0)

    def getvacB(self, t_index=0):  # noqa: N802
        warnings.warn("getvacB() is deprecated; use get_vacuum_b().", DeprecationWarning, stacklevel=2)
        try:
            return self.get_vacuum_b(t_index=t_index)
        except OnRobotConnectionError:
            return CONN_ERR

    def idle(self, t_index=0, channelA=True, channelB=True):  # noqa: N803
        try:
            self._require_connected(t_index)
        except OnRobotConnectionError:
            return CONN_ERR
        self.cb.vg10_idle(t_index, channelA, channelB)
        return RET_OK

    def idle_vacuum(
        self,
        t_index: int = 0,
        channel_a: bool = True,
        channel_b: bool = True,
    ) -> None:
        self._require_connected(t_index)
        self.cb.vg10_idle(t_index, channel_a, channel_b)

    def get_vacuum(self, t_index: int = 0):
        self._require_connected(t_index)
        return self.cb.vg10_get_vacuum(t_index)

    def get_all_double_variables(self, t_index: int = 0):
        self._require_connected(t_index)
        return self.cb.vg10_get_all_double_variables(t_index)

    def get_operation_counter(self, t_index: int = 0):
        self._require_connected(t_index)
        return self.cb.vg10_get_operation_counter(t_index)


if __name__ == "__main__":
    device = Device()
    gripper_vgc10 = VG(device)
    if gripper_vgc10.is_connected():
        print("Connected!")
