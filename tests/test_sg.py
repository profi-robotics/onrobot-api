from __future__ import annotations

import pytest

from onrobot.errors import OnRobotConnectionError, OnRobotValidationError
from onrobot.policies import OperationPolicy
from onrobot.sg import CONN_ERR, RET_FAIL, RET_OK, SG


class _FakeCB:
    def __init__(self) -> None:
        self.connected = True
        self.initialized = True
        self.calibrated = False
        self.busy_values = [False]
        self.calls = []
        self.initialize_result = 0
        self.calibrate_result = 0

    def cb_is_device_connected(self, t_index, device_id):  # noqa: ANN001, ANN201
        self.calls.append(("cb_is_device_connected", t_index, device_id))
        return self.connected

    def sg_initialize(self, t_index, tool_id):  # noqa: ANN001, ANN201
        self.calls.append(("sg_initialize", t_index, tool_id))
        if self.initialize_result == 0:
            self.initialized = True
        return self.initialize_result

    def sg_calibrate(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_calibrate", t_index))
        if self.calibrate_result == 0:
            self.calibrated = True
        return self.calibrate_result

    def sg_get_initialized(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_initialized", t_index))
        return self.initialized

    def sg_get_busy(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_busy", t_index))
        if len(self.busy_values) > 1:
            return self.busy_values.pop(0)
        return self.busy_values[0]

    def sg_get_grip_detected(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_grip_detected", t_index))
        return False

    def sg_get_calibrated(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_calibrated", t_index))
        return self.calibrated

    def sg_get_status(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_status", t_index))
        return 2

    def sg_get_error(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_error", t_index))
        return 0

    def sg_get_operation_counter(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_operation_counter", t_index))
        return 11

    def sg_get_sg_tool_id(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_sg_tool_id", t_index))
        return 3

    def sg_get_width(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_width", t_index))
        return 49

    def sg_get_depth(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_depth", t_index))
        return 5.7

    def sg_get_depth_relative(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_depth_relative", t_index))
        return 4.7

    def sg_get_depth_static_silicone(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_depth_static_silicone", t_index))
        return 70.5

    def sg_get_min_max(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_min_max", t_index))
        return {"min_open": 11, "max_open": 75}

    def sg_get_min_open(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_min_open", t_index))
        return 11

    def sg_get_max_open(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_max_open", t_index))
        return 75

    def sg_get_all_variables(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_all_variables", t_index))
        return {
            "sg_tool_id": 3,
            "width": 49,
            "depth": 5.7,
            "depth_relative": 4.7,
            "depth_static_silicone": 70.5,
            "max_open": 75,
            "min_open": 11,
            "status": 2,
            "busy": False,
            "initialized": self.initialized,
            "grip_detected": False,
            "calibrated": self.calibrated,
            "error": 0,
            "operation_counter": 11,
        }

    def sg_get_all_double_variables(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_all_double_variables", t_index))
        return [5.7, 4.7, 70.5]

    def sg_get_all_integer_variables(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_all_integer_variables", t_index))
        return [3, 49, 75, 11, 2, 0, 11]

    def sg_get_all_boolean_variables(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_get_all_boolean_variables", t_index))
        return [False, True, False, self.calibrated]

    def sg_grip(self, t_index, width, gentle, is_grip):  # noqa: ANN001, ANN201
        self.calls.append(("sg_grip", t_index, width, gentle, is_grip))
        return 0

    def sg_home(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_home", t_index))
        return 0

    def sg_stop(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("sg_stop", t_index))
        return 0


class _FakeDevice:
    Global_cbip = "192.168.1.5"

    def __init__(self) -> None:
        self.cb = _FakeCB()

    def get_compute_box(self):
        return self.cb


class _FakeStatusClient:
    def __init__(self) -> None:
        self.disconnected = False

    def get_device_variable(self, *, device_id, product_code):  # noqa: ANN001, ANN201
        if device_id == 0 and product_code == 0x50:
            return {"width": 49}
        return None

    def disconnect(self):  # noqa: ANN201
        self.disconnected = True


@pytest.mark.unit
def test_sg_connection_failure_raises_and_legacy_returns_code() -> None:
    device = _FakeDevice()
    device.cb.connected = False
    gripper = SG(device)

    with pytest.raises(OnRobotConnectionError):
        gripper.is_connected()

    assert gripper.isConnected() is False
    assert gripper.init() == CONN_ERR


@pytest.mark.unit
def test_sg_default_tool_type_is_sg_a_s() -> None:
    gripper = SG(_FakeDevice())

    assert gripper.tool_type == "SG-a-S"
    assert gripper.tool_id == 3


@pytest.mark.unit
def test_sg_rejects_invalid_tool_type() -> None:
    with pytest.raises(OnRobotValidationError):
        SG(_FakeDevice(), tool_type="SG-x")

    gripper = SG(_FakeDevice())
    with pytest.raises(OnRobotValidationError):
        gripper.initialize(tool_type=99, wait=False)


@pytest.mark.unit
def test_sg_initialize_uses_default_tool_id() -> None:
    device = _FakeDevice()
    gripper = SG(device, policy=OperationPolicy(poll_interval_s=0))

    gripper.initialize()

    assert ("sg_initialize", 0, 3) in device.cb.calls


@pytest.mark.unit
def test_sg_calibrate_calls_xmlrpc_and_waits() -> None:
    device = _FakeDevice()
    device.cb.busy_values = [True, False]
    gripper = SG(device, policy=OperationPolicy(poll_interval_s=0))

    gripper.calibrate()

    assert ("sg_calibrate", 0) in device.cb.calls
    assert len([call for call in device.cb.calls if call[0] == "sg_get_busy"]) >= 2
    assert gripper.is_calibrated()


@pytest.mark.unit
def test_sg_scalar_getters_map_to_xmlrpc_methods() -> None:
    device = _FakeDevice()
    gripper = SG(device)

    assert gripper.get_tool_id() == 3
    assert gripper.get_width() == 49
    assert gripper.get_depth() == 5.7
    assert gripper.get_depth_relative() == 4.7
    assert gripper.get_max_depth() == 70.5
    assert gripper.get_min_max() == {"min_open": 11, "max_open": 75}
    assert gripper.get_min_open() == 11
    assert gripper.get_max_open() == 75
    assert gripper.get_status() == 2
    assert gripper.is_busy() is False
    assert gripper.is_initialized() is True
    assert gripper.is_gripped() is False
    assert gripper.is_calibrated() is False
    assert gripper.get_error() == 0
    assert gripper.get_operation_counter() == 11

    method_names = {call[0] for call in device.cb.calls}
    assert {
        "sg_get_sg_tool_id",
        "sg_get_width",
        "sg_get_depth",
        "sg_get_depth_relative",
        "sg_get_depth_static_silicone",
        "sg_get_min_max",
        "sg_get_min_open",
        "sg_get_max_open",
        "sg_get_status",
        "sg_get_busy",
        "sg_get_initialized",
        "sg_get_grip_detected",
        "sg_get_calibrated",
        "sg_get_error",
        "sg_get_operation_counter",
    }.issubset(method_names)


@pytest.mark.unit
def test_sg_raw_getters_return_passthrough_values() -> None:
    gripper = SG(_FakeDevice())

    assert gripper.get_all_variables()["sg_tool_id"] == 3
    assert gripper.get_all_double_variables() == [5.7, 4.7, 70.5]
    assert gripper.get_all_integer_variables() == [3, 49, 75, 11, 2, 0, 11]
    assert gripper.get_all_boolean_variables() == [False, True, False, False]


@pytest.mark.unit
def test_sg_status_snapshot_filters_by_product_code() -> None:
    gripper = SG(_FakeDevice())
    client = _FakeStatusClient()
    gripper._status_client = client  # noqa: SLF001

    assert gripper.get_status_snapshot() == {"width": 49}
    assert gripper.get_status_snapshot(t_index=1) is None
    gripper.stop_status_stream()
    assert client.disconnected is True


@pytest.mark.unit
def test_sg_width_validation_uses_live_min_max() -> None:
    gripper = SG(_FakeDevice())

    with pytest.raises(OnRobotValidationError):
        gripper.move_to_width(width=10, wait=False)

    assert gripper.move(t_width=10, f_wait=False) == RET_FAIL


@pytest.mark.unit
def test_sg_move_to_width_sends_non_grip_flag() -> None:
    device = _FakeDevice()
    gripper = SG(device)

    gripper.move_to_width(width=56, gentle=True, wait=False)

    assert ("sg_grip", 0, 56, True, False) in device.cb.calls


@pytest.mark.unit
def test_sg_grip_and_gentle_grip_send_grip_flag() -> None:
    device = _FakeDevice()
    gripper = SG(device)

    gripper.grip(width=74, wait=False)
    gripper.gentle_grip(width=75, wait=False)

    assert ("sg_grip", 0, 74, False, True) in device.cb.calls
    assert ("sg_grip", 0, 75, True, True) in device.cb.calls


@pytest.mark.unit
def test_sg_wait_behavior_polls_busy() -> None:
    device = _FakeDevice()
    device.cb.busy_values = [True, False]
    gripper = SG(device, policy=OperationPolicy(poll_interval_s=0))

    assert gripper.grip_legacy(t_width=56, f_wait=True) == RET_OK

    busy_calls = [call for call in device.cb.calls if call[0] == "sg_get_busy"]
    assert len(busy_calls) >= 2


@pytest.mark.unit
def test_sg_legacy_wrappers_return_failure_codes() -> None:
    device = _FakeDevice()
    gripper = SG(device)
    device.cb.calibrate_result = -1

    assert gripper.calibrate_legacy() == RET_FAIL

    device.cb.connected = False
    assert gripper.home_legacy() == CONN_ERR
    assert gripper.halt() == CONN_ERR
