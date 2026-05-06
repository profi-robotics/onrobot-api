from __future__ import annotations

import pytest

from onrobot.gripper_profiles import (
    GripperProfile,
    available_gripper_profiles,
    get_gripper_profile,
    gripper_profile_options,
)


@pytest.mark.unit
def test_gripper_profile_constructor_keeps_original_required_fields() -> None:
    profile = GripperProfile(
        key="custom",
        display_name="Custom",
        force_min=1.0,
        force_max=2.0,
        force_default=1.5,
        speed_min=1,
        speed_max=100,
        speed_default=50,
        open_width_default=10.0,
        close_width_default=0.0,
        calibration_width=0.0,
    )

    assert profile.capability == "width_force"


@pytest.mark.unit
def test_rg2_profile_metadata() -> None:
    profile = get_gripper_profile("rg2")

    assert profile.display_name == "OnRobot RG2"
    assert profile.capability == "width_force"
    assert profile.force_min == 3.0
    assert profile.force_max == 40.0
    assert profile.open_width_default == 110.0


@pytest.mark.unit
def test_soft_gripper_profile_metadata() -> None:
    profile = get_gripper_profile("sg")

    assert profile.display_name == "OnRobot Soft Gripper"
    assert profile.capability == "soft_width"
    assert profile.open_width_default == 75.0
    assert profile.close_width_default == 56.0
    assert profile.gentle_default is False


@pytest.mark.unit
def test_vg10_profile_metadata() -> None:
    profile = get_gripper_profile("vg10")

    assert profile.display_name == "OnRobot VG10"
    assert profile.capability == "vacuum"
    assert profile.vacuum_min == 1
    assert profile.vacuum_max == 80
    assert profile.vacuum_default == 40


@pytest.mark.unit
def test_vgc10_profile_metadata() -> None:
    profile = get_gripper_profile("vgc10")

    assert profile.display_name == "OnRobot VGC10"
    assert profile.capability == "vacuum"
    assert profile.vacuum_min == 1
    assert profile.vacuum_max == 80
    assert profile.vacuum_default == 40
    assert profile.vacuum_hold_threshold_ratio == 0.8


@pytest.mark.unit
def test_gripper_profile_options_are_sorted() -> None:
    keys = [profile.key for profile in available_gripper_profiles()]
    options = gripper_profile_options()

    assert keys == ["rg2", "sg", "twofg7", "vg10", "vgc10"]
    assert [option["value"] for option in options] == keys
