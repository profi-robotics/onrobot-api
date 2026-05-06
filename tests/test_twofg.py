from __future__ import annotations

import pytest

from onrobot.errors import OnRobotConnectionError, OnRobotValidationError
from onrobot.twofg import CONN_ERR, RET_OK, TWOFG


class _FakeCB:
    def __init__(self) -> None:
        self.connected = True
        self.busy = False
        self.gripped = True

    def cb_is_device_connected(self, t_index, device_id):  # noqa: ANN001, ANN201
        return self.connected

    def twofg_get_max_external_width(self, t_index):  # noqa: ANN001, ANN201
        return 80.0

    def twofg_get_min_external_width(self, t_index):  # noqa: ANN001, ANN201
        return 0.0

    def twofg_get_busy(self, t_index):  # noqa: ANN001, ANN201
        return self.busy

    def twofg_get_grip_detected(self, t_index):  # noqa: ANN001, ANN201
        return self.gripped

    def twofg_grip_external(self, t_index, width, force, speed):  # noqa: ANN001, ANN201
        return None

    def twofg_get_external_width(self, t_index):  # noqa: ANN001, ANN201
        return 30.0

    def twofg_get_force(self, t_index):  # noqa: ANN001, ANN201
        return 20.0

    def twofg_get_status(self, t_index):  # noqa: ANN001, ANN201
        return 0

    def twofg_stop(self, t_index):  # noqa: ANN001, ANN201
        return None

    def twofg_finger_orientation_outward(self, t_index):  # noqa: ANN001, ANN201
        return 1


class _FakeDevice:
    Global_cbip = "192.168.1.5"

    def __init__(self) -> None:
        self.cb = _FakeCB()

    def get_compute_box(self):
        return self.cb


@pytest.mark.unit
def test_twofg_snake_case_connection_error() -> None:
    device = _FakeDevice()
    device.cb.connected = False
    gripper = TWOFG(device)
    with pytest.raises(OnRobotConnectionError):
        gripper.is_connected()
    assert gripper.isConnected() is False


@pytest.mark.unit
def test_twofg_validation_error_for_width() -> None:
    gripper = TWOFG(_FakeDevice())
    with pytest.raises(OnRobotValidationError):
        gripper.grip_external(t_width=200.0)
    assert gripper.grip(t_width=200.0) != RET_OK


@pytest.mark.unit
def test_twofg_legacy_connection_code() -> None:
    device = _FakeDevice()
    device.cb.connected = False
    gripper = TWOFG(device)
    assert gripper.grip() == CONN_ERR
