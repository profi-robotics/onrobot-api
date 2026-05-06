from __future__ import annotations

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    marker_names = {"unit", "integration", "hardware"}
    for item in items:
        assigned = {marker.name for marker in item.iter_markers()}
        if assigned.isdisjoint(marker_names):
            item.add_marker(pytest.mark.unit)
