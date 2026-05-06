"""Shared gripper profile defaults for OnRobot devices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class GripperProfile:
    """Describes the tuning bounds used for a specific gripper type."""

    key: str
    display_name: str
    force_min: float
    force_max: float
    force_default: float
    speed_min: int
    speed_max: int
    speed_default: int
    open_width_default: float
    close_width_default: float
    calibration_width: float
    capability: str = "width_force"
    vacuum_min: int = 1
    vacuum_max: int = 80
    vacuum_default: int = 40
    vacuum_hold_threshold_ratio: float = 0.8
    gentle_default: bool = False


DEFAULT_GRIPPER_TYPE = "twofg7"

_PROFILES: dict[str, GripperProfile] = {
    "twofg7": GripperProfile(
        key="twofg7",
        display_name="OnRobot 2FG7",
        capability="width_force",
        force_min=20.0,
        force_max=140.0,
        force_default=20.0,
        speed_min=10,
        speed_max=100,
        speed_default=10,
        open_width_default=25.0,
        close_width_default=5.0,
        calibration_width=5.0,
    ),
    "rg2": GripperProfile(
        key="rg2",
        display_name="OnRobot RG2",
        force_min=3.0,
        force_max=40.0,
        force_default=20.0,
        speed_min=0,
        speed_max=100,
        speed_default=50,
        open_width_default=110.0,
        close_width_default=0.0,
        calibration_width=0.0,
        capability="width_force",
    ),
    "sg": GripperProfile(
        key="sg",
        display_name="OnRobot Soft Gripper",
        capability="soft_width",
        force_min=0.0,
        force_max=0.0,
        force_default=0.0,
        speed_min=0,
        speed_max=100,
        speed_default=50,
        open_width_default=75.0,
        close_width_default=56.0,
        calibration_width=56.0,
        gentle_default=False,
    ),
    "vg10": GripperProfile(
        key="vg10",
        display_name="OnRobot VG10",
        force_min=0.0,
        force_max=0.0,
        force_default=0.0,
        speed_min=0,
        speed_max=100,
        speed_default=50,
        open_width_default=0.0,
        close_width_default=40.0,
        calibration_width=0.0,
        capability="vacuum",
        vacuum_min=1,
        vacuum_max=80,
        vacuum_default=40,
        vacuum_hold_threshold_ratio=0.8,
    ),
    "vgc10": GripperProfile(
        key="vgc10",
        display_name="OnRobot VGC10",
        capability="vacuum",
        force_min=0.0,
        force_max=0.0,
        force_default=0.0,
        speed_min=0,
        speed_max=100,
        speed_default=50,
        open_width_default=0.0,
        close_width_default=40.0,
        calibration_width=0.0,
        vacuum_min=1,
        vacuum_max=80,
        vacuum_default=40,
        vacuum_hold_threshold_ratio=0.8,
    ),
}


def get_gripper_profile(key: str | None) -> GripperProfile:
    """Return the profile matching *key*, falling back to the default."""
    normalized = (key or "").lower()
    return _PROFILES.get(normalized, _PROFILES[DEFAULT_GRIPPER_TYPE])


def available_gripper_profiles() -> Iterable[GripperProfile]:
    """Yield all configured gripper profiles in deterministic order."""
    return (_PROFILES[k] for k in sorted(_PROFILES))


def gripper_profile_options() -> list[dict[str, str]]:
    """Return Mantine-friendly select options for the available grippers."""
    return [
        {"value": profile.key, "label": profile.display_name}
        for profile in available_gripper_profiles()
    ]
