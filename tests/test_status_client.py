from __future__ import annotations

import pytest

from onrobot.status_client import OnRobotStatusClient


@pytest.mark.unit
def test_status_client_ignores_malformed_payloads() -> None:
    client = OnRobotStatusClient("127.0.0.1")
    client._handle_message("bad-payload")  # noqa: SLF001
    assert client.latest_payload() == {}


@pytest.mark.unit
def test_status_client_survives_callback_exceptions() -> None:
    calls = {"count": 0}

    def _on_update(payload):
        calls["count"] += 1
        raise RuntimeError("boom")

    client = OnRobotStatusClient("127.0.0.1", on_update=_on_update)
    payload = {"devices": [{"deviceId": 0, "productCode": 0xC0, "variable": {"width": 10}}]}
    client._handle_message(payload)  # noqa: SLF001
    assert calls["count"] == 1
    assert client.get_device_variable(device_id=0, product_code=0xC0) == {"width": 10}
