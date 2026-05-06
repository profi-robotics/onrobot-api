from __future__ import annotations

import pytest

from onrobot.rg2 import CONN_ERR as RG_CONN_ERR
from onrobot.rg2 import RET_OK as RG_RET_OK
from onrobot.rg2 import RG
from onrobot.vgc10 import CONN_ERR as VG_CONN_ERR
from onrobot.vgc10 import RET_FAIL as VG_RET_FAIL
from onrobot.vgc10 import RET_OK as VG_RET_OK
from onrobot.vgc10 import VG


class _FakeCB:
    def __init__(self) -> None:
        self.connected = True
        self.vg10_connected = False
        self.vgc10_connected = True
        self.calls = []
        self.vacuum = {"a_vacuum": 0.0, "b_vacuum": 0.0}

    def cb_is_device_connected(self, t_index, device_id):  # noqa: ANN001, ANN201
        self.calls.append(("cb_is_device_connected", t_index, device_id))
        if not self.connected:
            return False
        if device_id == 0x10:
            return self.vg10_connected
        if device_id == 0x11:
            return self.vgc10_connected
        return self.connected

    def rg_grip(self, t_index, width, force):  # noqa: ANN001, ANN201
        return None

    def rg_get_busy(self, t_index):  # noqa: ANN001, ANN201
        return False

    def rg_get_grip_detected(self, t_index):  # noqa: ANN001, ANN201
        return True

    def rg_stop(self, t_index):  # noqa: ANN001, ANN201
        return None

    def rg_get_s1_triggered(self, t_index):  # noqa: ANN001, ANN201
        return False

    def rg_get_s2_triggered(self, t_index):  # noqa: ANN001, ANN201
        return False

    def rg_get_speed(self, t_index):  # noqa: ANN001, ANN201
        return 10.0

    def rg_get_depth(self, t_index):  # noqa: ANN001, ANN201
        return 2.0

    def rg_get_relative_depth(self, t_index):  # noqa: ANN001, ANN201
        return 1.0

    def rg_get_width(self, t_index):  # noqa: ANN001, ANN201
        return 30.0

    def rg_get_fingertip_offset(self, t_index):  # noqa: ANN001, ANN201
        return 1.0

    def rg_set_fingertip_offset(self, t_index, offset):  # noqa: ANN001, ANN201
        return None

    def cb_reset_tool_power(self):  # noqa: ANN201
        return None

    def vg10_grip(self, t_index, channel, vacuum):  # noqa: ANN001, ANN201
        self.calls.append(("vg10_grip", t_index, channel, vacuum))
        if channel == 0:
            self.vacuum["a_vacuum"] = vacuum
        if channel == 1:
            self.vacuum["b_vacuum"] = vacuum
        return None

    def vg10_release(self, t_index, channel_a, channel_b):  # noqa: ANN001, ANN201
        self.calls.append(("vg10_release", t_index, channel_a, channel_b))
        if channel_a:
            self.vacuum["a_vacuum"] = 0.0
        if channel_b:
            self.vacuum["b_vacuum"] = 0.0
        return None

    def vg10_get_all_double_variables(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("vg10_get_all_double_variables", t_index))
        return [self.vacuum["a_vacuum"], self.vacuum["b_vacuum"]]

    def vg10_get_vacuum(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("vg10_get_vacuum", t_index))
        return dict(self.vacuum)

    def vg10_get_operation_counter(self, t_index):  # noqa: ANN001, ANN201
        self.calls.append(("vg10_get_operation_counter", t_index))
        return 48

    def vg10_idle(self, t_index, channel_a, channel_b):  # noqa: ANN001, ANN201
        self.calls.append(("vg10_idle", t_index, channel_a, channel_b))
        return None


class _FakeDevice:
    Global_cbip = "192.168.1.5"

    def __init__(self) -> None:
        self.cb = _FakeCB()

    def get_compute_box(self):
        return self.cb


class _FakeStatusClient:
    def __init__(self) -> None:
        self.disconnected = False

    def get_device_variable(self, *, device_id, product_code):  # noqa: ANN001, ANN201
        if device_id == 0 and product_code == 0x11:
            return {"a_vacuum": 12.0}
        return None

    def disconnect(self):  # noqa: ANN201
        self.disconnected = True


@pytest.mark.unit
def test_rg_compatibility_codes() -> None:
    dev = _FakeDevice()
    rg = RG(dev)
    assert rg.move(0, 10.0, 20.0, True) == RG_RET_OK
    dev.cb.connected = False
    assert rg.move(0, 10.0, 20.0, True) == RG_CONN_ERR


@pytest.mark.unit
def test_vg_compatibility_codes() -> None:
    dev = _FakeDevice()
    vg = VG(dev)
    assert vg.release(waiting=True) == VG_RET_OK
    dev.cb.connected = False
    assert vg.release(waiting=False) == VG_CONN_ERR


@pytest.mark.unit
def test_vg_supports_vg10_and_vgc10_detection() -> None:
    dev = _FakeDevice()
    vg = VG(dev)

    assert vg.is_connected()
    assert vg.is_vgc10() is True
    assert vg.is_vg10() is False

    dev.cb.vgc10_connected = False
    dev.cb.vg10_connected = True

    assert vg.is_connected()
    assert vg.is_vg10() is True
    assert vg.is_vgc10() is False


@pytest.mark.unit
def test_vg_grip_validates_vacuum_range() -> None:
    vg = VG(_FakeDevice())

    assert vg.grip(vacuumA=0, vacuumB=10) == VG_RET_FAIL
    assert vg.grip(vacuumA=10, vacuumB=81) == VG_RET_FAIL


@pytest.mark.unit
def test_vg_full_surface_methods_map_to_xmlrpc() -> None:
    dev = _FakeDevice()
    vg = VG(dev)

    vg.grip_vacuum(vacuum_a=12, vacuum_b=14, wait=True)
    assert vg.get_vacuum() == {"a_vacuum": 12.0, "b_vacuum": 14.0}
    assert vg.get_vacuum_a() == 12.0
    assert vg.get_vacuum_b() == 14.0
    assert vg.get_all_double_variables() == [12.0, 14.0]
    assert vg.get_operation_counter() == 48
    vg.idle_vacuum(channel_a=True, channel_b=False)
    vg.release_vacuum(channel_a=True, channel_b=True, wait=True)

    assert ("vg10_grip", 0, 0, 12.0) in dev.cb.calls
    assert ("vg10_grip", 0, 1, 14.0) in dev.cb.calls
    assert ("vg10_idle", 0, True, False) in dev.cb.calls
    assert ("vg10_release", 0, True, True) in dev.cb.calls
    assert ("vg10_get_operation_counter", 0) in dev.cb.calls


@pytest.mark.unit
def test_vg_status_snapshot_filters_vgc10_product_code() -> None:
    vg = VG(_FakeDevice())
    client = _FakeStatusClient()
    vg._status_client = client  # noqa: SLF001

    assert vg.get_status_snapshot() == {"a_vacuum": 12.0}
    assert vg.get_status_snapshot(t_index=1) is None
    vg.stop_status_stream()
    assert client.disconnected is True
