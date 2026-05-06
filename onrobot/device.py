#!/usr/bin/env python3

from __future__ import annotations

import logging
import xmlrpc.client

from onrobot.errors import OnRobotConnectionError

LOGGER = logging.getLogger(__name__)


class Device:
    """Generic Compute Box device connection wrapper."""

    cb = None

    def __init__(self, Global_cbip: str = "192.168.1.1"):  # noqa: N803
        self.Global_cbip = Global_cbip

    def get_compute_box(self):
        """Return XML-RPC proxy to the configured Compute Box."""
        try:
            self.cb = xmlrpc.client.ServerProxy(f"http://{self.Global_cbip}:41414/")
            return self.cb
        except TimeoutError as exc:
            LOGGER.error("Connection to Compute Box failed for %s", self.Global_cbip)
            raise OnRobotConnectionError("Connection to Compute Box failed") from exc

    def getCB(self):  # noqa: N802
        """Compatibility alias for legacy camelCase API."""
        return self.get_compute_box()


if __name__ == "__main__":
    device = Device()
    device.get_compute_box()
