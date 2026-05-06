"""OnRobot gripper control via XML-RPC API."""

from onrobot.detection import DetectedGripper, detect_gripper, detect_gripper_type
from onrobot.device import Device
from onrobot.dimensions import GripperDimensions, get_static_dimensions
from onrobot.rg2 import RG
from onrobot.sg import SG
from onrobot.status_client import OnRobotStatusClient
from onrobot.twofg import TWOFG
from onrobot.vgc10 import VG
from onrobot.gripper_profiles import (
    DEFAULT_GRIPPER_TYPE,
    GripperProfile,
    get_gripper_profile,
    gripper_profile_options,
)
from onrobot.errors import (
    OnRobotError,
    OnRobotConnectionError,
    OnRobotTimeoutError,
    OnRobotValidationError,
)
from onrobot.policies import OperationPolicy

__version__ = "0.1.0"
__all__ = [
    "Device",
    "RG",
    "SG",
    "TWOFG",
    "VG",
    "OnRobotStatusClient",
    "DetectedGripper",
    "GripperDimensions",
    "GripperProfile",
    "OperationPolicy",
    "OnRobotError",
    "OnRobotConnectionError",
    "OnRobotTimeoutError",
    "OnRobotValidationError",
    "DEFAULT_GRIPPER_TYPE",
    "detect_gripper",
    "detect_gripper_type",
    "get_gripper_profile",
    "get_static_dimensions",
    "gripper_profile_options",
]
