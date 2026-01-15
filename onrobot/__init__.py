"""OnRobot gripper control via XML-RPC API."""

from onrobot.device import Device
from onrobot.rg2 import RG
from onrobot.status_client import OnRobotStatusClient
from onrobot.twofg import TWOFG
from onrobot.vgc10 import VG
from onrobot.gripper_profiles import (
    DEFAULT_GRIPPER_TYPE,
    GripperProfile,
    get_gripper_profile,
    gripper_profile_options,
)

__version__ = "0.1.0"
__all__ = [
    "Device",
    "RG",
    "TWOFG",
    "VG",
    "OnRobotStatusClient",
    "GripperProfile",
    "DEFAULT_GRIPPER_TYPE",
    "get_gripper_profile",
    "gripper_profile_options",
]
