#!/usr/bin/env python3

import time
import threading
import urllib.error
import urllib.request
from onrobot.device import Device
from onrobot.gripper_profiles import get_gripper_profile
import numpy as np

'''
XML-RPC library for controlling OnRobot devcies from Doosan robots

Global_cbip holds the IP address of the compute box, needs to be defined by the end user
'''

# Device ID
TWOFG_ID = 0xC0

# Connection
CONN_ERR = -2   # Connection failure
RET_OK = 0      # Okay
RET_FAIL = -1   # Error

GRIPPER_PROFILE = get_gripper_profile("twofg7")


class TWOFG():
    '''
    This class is for handling the 2FG device
    '''
    cb = None

    def __init__(self, dev):
        self.cb = dev.getCB()
        self._lock = threading.Lock()  # Thread safety for XML-RPC calls
        self._cb_ip = getattr(dev, "Global_cbip", None)
        self._status_client = None
        self._profile = GRIPPER_PROFILE

    @property
    def profile(self):
        """Return the gripper profile that defines the type defaults."""
        return self._profile

    def _call_xmlrpc(self, method_name, *args):
        """Thread-safe wrapper for XML-RPC calls."""
        with self._lock:
            method = getattr(self.cb, method_name)
            return method(*args)

    def _call_rest(self, path, timeout_s=2.0):
        if not self._cb_ip:
            raise RuntimeError("Compute box IP is not configured")
        url = f"http://{self._cb_ip}/{path.lstrip('/')}"
        with self._lock:
            request = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                return response.read().decode("utf-8")

    def start_status_stream(
        self,
        on_update=None,
        timeout_s=2.0,
    ):
        if not self._cb_ip:
            return False
        if self._status_client is None:
            from onrobot.status_client import OnRobotStatusClient
            self._status_client = OnRobotStatusClient(
                self._cb_ip,
                on_update=on_update,
            )
        try:
            self._status_client.connect(timeout_s=timeout_s)
            return True
        except Exception:
            return False

    def stop_status_stream(self):
        client = self._status_client
        if client is None:
            return
        client.disconnect()

    def get_status_snapshot(self, t_index=0):
        client = self._status_client
        if client is None:
            return None
        return client.get_device_variable(device_id=t_index, product_code=TWOFG_ID)

    def _normalize_finger_orientation(self, orientation):
        if isinstance(orientation, bool):
            return orientation
        if isinstance(orientation, str):
            cleaned = orientation.strip().lower()
            if cleaned in {"outward", "out", "outside"}:
                return True
            if cleaned in {"inward", "in", "inside"}:
                return False
            return None
        if isinstance(orientation, (int, float)):
            value = int(orientation)
            if value < 0:
                return None
            if value == 2:
                return True
            if value == 1:
                return False
            return bool(value)
        return None

    def get_finger_orientation(self, t_index=0):
        '''
        Returns with current finger orientation

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @return: Finger orientation flag (device-specific)
        @rtype: int
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        try:
            return self._call_xmlrpc('twofg_finger_orientation_outward', t_index)
        except Exception:
            return RET_FAIL

    def get_finger_orientation_label(self, t_index=0):
        '''
        Returns finger orientation as a human-friendly label

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @return: "inward" or "outward" when available
        @rtype: str
        '''
        raw = self.get_finger_orientation(t_index)
        orientation = self._normalize_finger_orientation(raw)
        if orientation is None:
            return None
        return "outward" if orientation else "inward"

    def set_finger_orientation(self, t_index=0, orientation=None, outward=None):
        '''
        Sets finger orientation

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @param orientation: Orientation label ("inward"/"outward") or numeric flag
        @param outward: Boolean flag for outward orientation (True=outward)
        @rtype: int
        @return: RET_OK on success, RET_FAIL on error
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        resolved = None
        if outward is not None:
            resolved = bool(outward)
        else:
            resolved = self._normalize_finger_orientation(orientation)
        if resolved is None:
            return RET_FAIL
        try:
            self._call_xmlrpc('twofg_set_finger_orientation', t_index, float(resolved))
            return RET_OK
        except Exception:
            pass
        try:
            rest_value = "true" if resolved else "false"
            self._call_rest(
                f"api/dc/twofg/set_finger_orientation/{t_index}/{rest_value}"
            )
            return RET_OK
        except (urllib.error.URLError, RuntimeError, Exception):
            return RET_FAIL

    def isConnected(self, t_index=0):
        '''
        Returns with True if 2FG device is connected, False otherwise

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @return: True if connected, False otherwise
        @rtype: bool
        '''
        try:
            IsTwoFG = self._call_xmlrpc(
                'cb_is_device_connected', t_index, TWOFG_ID)
        except (TimeoutError, Exception):
            IsTwoFG = False

        if IsTwoFG is False:
            print("No 2FG device connected on the given instance")
            return False
        else:
            return True

    def isBusy(self, t_index=0):
        '''
        Gets if the gripper is busy or not

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @type t_index: int

        @rtype: bool
        @return: True if busy, False otherwise
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        return self._call_xmlrpc('twofg_get_busy', t_index)

    def isGripped(self, t_index=0):
        '''
        Gets if the gripper is gripping or not

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @type t_index: int

        @rtype: bool
        @return: True if gripped, False otherwise
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        return self._call_xmlrpc('twofg_get_grip_detected', t_index)

    def getStatus(self, t_index=0):
        '''
        Gets the status of the gripper

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @type t_index: int

        @rtype: int
        @return: Status code of the device
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        status = self._call_xmlrpc('twofg_get_status', t_index)
        return status

    def get_ext_width(self, t_index=0):
        '''
        Returns with current external width

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @return: External width in mm
        @rtype: float
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        extWidth = self._call_xmlrpc('twofg_get_external_width', t_index)
        return extWidth

    def get_min_ext_width(self, t_index=0):
        '''
        Returns with current minimum external width

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @return: Minimum external width in mm
        @rtype: float
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        extMinWidth = self._call_xmlrpc(
            'twofg_get_min_external_width', t_index)
        return extMinWidth

    def get_max_ext_width(self, t_index=0):
        '''
        Returns with current maximum external width

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @return: Maximum external width in mm
        @rtype: float
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        extMaxWidth = self._call_xmlrpc(
            'twofg_get_max_external_width', t_index)
        return extMaxWidth

    def get_force(self, t_index=0):
        '''
        Returns with current force

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @return: Force in N
        @rtype: float
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        currForce = self._call_xmlrpc('twofg_get_force', t_index)
        return currForce

    def stop(self, t_index=0):
        '''
        Stop the grippers movement

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @type t_index: int
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR
        self.cb.twofg_stop(t_index)

    def grip(
        self,
        t_index=0,
        t_width=GRIPPER_PROFILE.open_width_default,
        n_force=GRIPPER_PROFILE.force_default,
        p_speed=GRIPPER_PROFILE.speed_default,
        f_wait=True,
    ):
        '''
        Makes an external grip with the gripper to the desired position

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @param t_width: The width to move the gripper to in mm's
        @type t_width: float
        @param n_force: The force to move the gripper width in N
        @type n_force: float
        @param p_speed: The speed of the gripper in %
        @type p_speed: int
        @type f_wait: bool
        @param f_wait: wait for the grip to end or not?
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR

        profile = self._profile

        # Sanity check
        max_width = self.get_max_ext_width(t_index)
        min_width = self.get_min_ext_width(t_index)

        # Check if we got valid width limits (not error codes)
        if max_width == CONN_ERR or min_width == CONN_ERR:
            print(
                "Unable to retrieve gripper width limits - gripper may not be properly configured")
            return RET_FAIL

        if t_width > max_width or t_width < min_width:
            print("Invalid 2FG width parameter, " +
                  str(max_width)+" - "+str(min_width) + " is valid only")
            return RET_FAIL

        if n_force > profile.force_max or n_force < profile.force_min:
            print(
                "Invalid 2FG force parameter, "
                f"{profile.force_min}-{profile.force_max} is valid only"
            )
            return RET_FAIL
        if p_speed > profile.speed_max or p_speed < profile.speed_min:
            print(
                "Invalid 2FG speed parameter, "
                f"{profile.speed_min}-{profile.speed_max} is valid only"
            )
            return RET_FAIL

        self._call_xmlrpc('twofg_grip_external', t_index, float(
            t_width), int(n_force), int(p_speed))

        if f_wait:
            tim_cnt = 0
            fbusy = self.isBusy(t_index)
            while (fbusy):
                time.sleep(0.1)
                fbusy = self.isBusy(t_index)
                tim_cnt += 1
                if tim_cnt > 30:
                    print("2FG external grip command timeout")
                    break
            else:
                # Grip detection
                grip_tim = 0
                gripped = self.isGripped(t_index)
                while (not gripped):
                    time.sleep(0.1)
                    gripped = self.isGripped(t_index)
                    grip_tim += 1
                    if grip_tim > 20:
                        print("2FG external grip detection timeout")
                        break
                else:
                    return RET_OK
                return RET_FAIL
            return RET_FAIL
        else:
            return RET_OK

    def move(self, t_index, t_width=20.0, f_wait=True):
        '''
        Moves the gripper to the desired position

        @param t_index: The position of the device (0 for single, 1 for dual primary, 2 for dual secondary)
        @param t_width: The width to move the gripper to in mm's
        @type t_width: float
        @type f_wait: bool
        @param f_wait: wait for the grip to end or not?
        '''
        if self.isConnected(t_index) is False:
            return CONN_ERR

        max_width = self.get_max_ext_width(t_index)
        min_width = self.get_min_ext_width(t_index)

        # Check if we got valid width limits (not error codes)
        if max_width == CONN_ERR or min_width == CONN_ERR:
            print(
                "Unable to retrieve gripper width limits - gripper may not be properly configured")
            return RET_FAIL

        if t_width > max_width or t_width < min_width:
            print("Invalid 2FG diameter parameter, " +
                  str(max_width)+" - "+str(min_width) + " is valid only")
            return RET_FAIL

        self._call_xmlrpc('twofg_grip_external', t_index,
                          float(t_width), 100, 80)

        if f_wait:
            tim_cnt = 0
            fbusy = self.isBusy(t_index)
            while (fbusy):
                time.sleep(0.1)
                fbusy = self.isBusy(t_index)
                tim_cnt += 1
                if tim_cnt > 30:
                    print("2FG external grip command timeout")
                    break
            else:
                return RET_OK
            return RET_FAIL
        else:
            return RET_OK


if __name__ == '__main__':
    device = Device()
    device.getCB()
    gripper_2FG7 = TWOFG(device)
    print("Connection check: ", gripper_2FG7.isConnected())
