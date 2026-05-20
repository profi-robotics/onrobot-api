from __future__ import annotations

import pytest

from onrobot import (
    DetectedGripper,
    GripperDimensions,
    detect_gripper,
    detect_gripper_type,
    get_static_dimensions,
)
from onrobot.errors import OnRobotConnectionError
from onrobot.rg2 import RG
from onrobot.sg import SG
from onrobot.twofg import TWOFG
from onrobot.vgc10 import VG


class _FakeCB:
    def __init__(self, connected_product_codes: set[int] | None = None) -> None:
        self.connected_product_codes = connected_product_codes or set()

    def cb_is_device_connected(self, t_index, device_id):  # noqa: ANN001, ANN201
        return device_id in self.connected_product_codes

    def twofg_get_external_width(self, t_index):  # noqa: ANN001, ANN201
        return 31.0

    def twofg_get_min_external_width(self, t_index):  # noqa: ANN001, ANN201
        return 1.0

    def twofg_get_max_external_width(self, t_index):  # noqa: ANN001, ANN201
        return 73.0

    def twofg_finger_length(self, t_index):  # noqa: ANN001, ANN201
        return 44.0

    def twofg_finger_height(self, t_index):  # noqa: ANN001, ANN201
        return 12.0

    def twofg_fingertip_offset(self, t_index):  # noqa: ANN001, ANN201
        return 3.5

    def twofg_get_finger_orientation_outward(self, t_index):  # noqa: ANN001, ANN201
        return 2

    def rg_get_width(self, t_index):  # noqa: ANN001, ANN201
        return 50.0

    def rg_get_depth(self, t_index):  # noqa: ANN001, ANN201
        return 9.0

    def rg_get_relative_depth(self, t_index):  # noqa: ANN001, ANN201
        return 4.0

    def rg_get_fingertip_offset(self, t_index):  # noqa: ANN001, ANN201
        return 6.0

    def sg_get_sg_tool_id(self, t_index):  # noqa: ANN001, ANN201
        return 3

    def sg_get_width(self, t_index):  # noqa: ANN001, ANN201
        return 49.0

    def sg_get_depth(self, t_index):  # noqa: ANN001, ANN201
        return 5.7

    def sg_get_depth_relative(self, t_index):  # noqa: ANN001, ANN201
        return 4.7

    def sg_get_depth_static_silicone(self, t_index):  # noqa: ANN001, ANN201
        return 70.5

    def sg_get_min_max(self, t_index):  # noqa: ANN001, ANN201
        return {"min_open": 11.0, "max_open": 75.0}


class _FakeDevice:
    Global_cbip = "192.168.1.5"

    def __init__(self, connected_product_codes: set[int] | None = None) -> None:
        self.cb = _FakeCB(connected_product_codes)

    def get_compute_box(self):
        return self.cb


@pytest.mark.unit
def test_detect_gripper_returns_client_and_live_dimensions() -> None:
    detected = detect_gripper(_FakeDevice({0xC0}))

    assert isinstance(detected, DetectedGripper)
    assert detected.key == "twofg7"
    assert detected.display_name == "OnRobot 2FG7"
    assert detected.product_code == 0xC0
    assert isinstance(detected.client, TWOFG)
    assert detected.dimensions.current_width_mm == 31.0
    assert detected.dimensions.finger_orientation == "outward"


@pytest.mark.unit
def test_detect_gripper_type_uses_registry_order_for_vg_models() -> None:
    assert detect_gripper_type(_FakeDevice({0x10, 0x11})) == "vgc10"


@pytest.mark.unit
def test_detect_gripper_create_client_false_returns_static_metadata() -> None:
    detected = detect_gripper(_FakeDevice({0x20}), create_client=False)

    assert detected.key == "rg2"
    assert detected.client is None
    assert detected.dimensions.body_length_mm == 213.0
    assert detected.dimensions.current_width_mm is None


@pytest.mark.unit
def test_detect_gripper_raises_when_no_supported_gripper_connected() -> None:
    with pytest.raises(OnRobotConnectionError):
        detect_gripper(_FakeDevice())


@pytest.mark.unit
def test_twofg_dimensions_include_static_and_live_values() -> None:
    dimensions = TWOFG(_FakeDevice({0xC0})).get_dimensions()

    assert dimensions.body_length_mm == 144.0
    assert dimensions.body_width_mm == 90.0
    assert dimensions.body_depth_mm == 71.0
    assert dimensions.current_width_mm == 31.0
    assert dimensions.min_width_mm == 1.0
    assert dimensions.max_width_mm == 73.0
    assert dimensions.finger_length_mm == 44.0
    assert dimensions.finger_height_mm == 12.0
    assert dimensions.fingertip_offset_mm == 3.5


@pytest.mark.unit
def test_rg_dimensions_include_static_and_live_values() -> None:
    dimensions = RG(_FakeDevice({0x20})).get_dimensions(0)

    assert dimensions.body_length_mm == 213.0
    assert dimensions.current_width_mm == 50.0
    assert dimensions.current_depth_mm == 9.0
    assert dimensions.relative_depth_mm == 4.0
    assert dimensions.fingertip_offset_mm == 6.0


@pytest.mark.unit
def test_vg_dimensions_select_connected_model() -> None:
    vgc10_dimensions = VG(_FakeDevice({0x11})).get_dimensions()
    vg10_dimensions = VG(_FakeDevice({0x10})).get_dimensions()

    assert vgc10_dimensions.key == "vgc10"
    assert vgc10_dimensions.body_length_mm == 101.0
    assert vg10_dimensions.key == "vg10"
    assert vg10_dimensions.folded_length_mm == 105.0
    assert vg10_dimensions.unfolded_width_mm == 390.0


@pytest.mark.unit
def test_sg_dimensions_include_static_and_live_values() -> None:
    dimensions = SG(_FakeDevice({0x50})).get_dimensions()

    assert dimensions.body_height_mm == 84.0
    assert dimensions.body_diameter_mm == 98.0
    assert dimensions.current_width_mm == 49.0
    assert dimensions.current_depth_mm == 5.7
    assert dimensions.relative_depth_mm == 4.7
    assert dimensions.max_depth_mm == 70.5
    assert dimensions.min_open_mm == 11.0
    assert dimensions.max_open_mm == 75.0
    assert dimensions.tool_id == 3
    assert dimensions.tool_type == "SG-a-S"


@pytest.mark.unit
def test_new_public_symbols_are_exported() -> None:
    dimensions = get_static_dimensions("twofg7")

    assert isinstance(dimensions, GripperDimensions)
    assert dimensions.product_code == 0xC0
