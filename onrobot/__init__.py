"""OnRobot gripper control via XML-RPC API."""

from onrobot.device import Device
from onrobot.rg2 import RG
from onrobot.status_client import OnRobotStatusClient
from onrobot.twofg import TWOFG
from onrobot.vgc10 import VG

__version__ = "0.1.0"
__all__ = ["Device", "RG", "TWOFG", "VG", "OnRobotStatusClient"]
