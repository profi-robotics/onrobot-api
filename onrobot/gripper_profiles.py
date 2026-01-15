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


DEFAULT_GRIPPER_TYPE = "twofg7"

_PROFILES: dict[str, GripperProfile] = {
    "twofg7": GripperProfile(
        key="twofg7",
        display_name="OnRobot 2FG7",
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
