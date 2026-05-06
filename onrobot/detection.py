"""Auto-detection helpers for supported OnRobot grippers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from onrobot.device import Device
from onrobot.dimensions import GripperDimensions, get_static_dimensions
from onrobot.errors import OnRobotConnectionError


@dataclass(frozen=True)
class DetectedGripper:
    """Result returned by gripper auto-detection."""

    key: str
    display_name: str
    product_code: int
    t_index: int
    client: Any | None
    dimensions: GripperDimensions


def _client_class_for(key: str):
    if key == "twofg7":
        from onrobot.twofg import TWOFG

        return TWOFG
    if key == "rg2":
        from onrobot.rg2 import RG

        return RG
    if key in {"vg10", "vgc10"}:
        from onrobot.vgc10 import VG

        return VG
    if key == "sg":
        from onrobot.sg import SG

        return SG
    raise KeyError(key)


_DETECTION_ORDER: tuple[str, ...] = ("twofg7", "rg2", "vgc10", "vg10", "sg")


def _get_compute_box(dev: Device):
    get_cb = getattr(dev, "get_compute_box", None) or getattr(dev, "getCB")
    return get_cb()


def detect_gripper(
    dev: Device,
    t_index: int = 0,
    create_client: bool = True,
) -> DetectedGripper:
    """Detect the connected supported gripper on *t_index*."""
    cb = _get_compute_box(dev)
    try:
        for key in _DETECTION_ORDER:
            dimensions = get_static_dimensions(key)
            if not bool(cb.cb_is_device_connected(t_index, dimensions.product_code)):
                continue
            client = _client_class_for(key)(dev) if create_client else None
            live_dimensions = (
                client.get_dimensions(t_index=t_index)
                if client is not None
                else dimensions
            )
            return DetectedGripper(
                key=key,
                display_name=dimensions.display_name,
                product_code=dimensions.product_code,
                t_index=t_index,
                client=client,
                dimensions=live_dimensions,
            )
    except OnRobotConnectionError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise OnRobotConnectionError("Failed to query connected gripper type") from exc
    raise OnRobotConnectionError("No supported OnRobot gripper detected")


def detect_gripper_type(dev: Device, t_index: int = 0) -> str:
    """Return the detected supported gripper key."""
    return detect_gripper(dev, t_index=t_index, create_client=False).key
