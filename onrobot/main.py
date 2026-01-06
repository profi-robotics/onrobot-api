#!/usr/bin/env python3

from onrobot.device import Device
from onrobot.twofg import TWOFG
from onrobot.vgc10 import VG
from onrobot.rg2 import RG

if __name__ == '__main__':
    device = Device()
    gripper_2FG7 = TWOFG(device)
    gripper_RG2 = RG(device)
    gripper_VGC10 = VG(device)
