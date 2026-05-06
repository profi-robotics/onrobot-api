"""Shared physical dimension metadata for supported OnRobot grippers."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class GripperDimensions:
    """Physical gripper dimensions and live TCP-relevant values in millimeters."""

    key: str
    display_name: str
    product_code: int
    unit: str = "mm"
    body_length_mm: float | None = None
    body_width_mm: float | None = None
    body_depth_mm: float | None = None
    body_height_mm: float | None = None
    body_diameter_mm: float | None = None
    folded_length_mm: float | None = None
    folded_width_mm: float | None = None
    folded_depth_mm: float | None = None
    unfolded_length_mm: float | None = None
    unfolded_width_mm: float | None = None
    unfolded_depth_mm: float | None = None
    current_width_mm: float | None = None
    current_depth_mm: float | None = None
    relative_depth_mm: float | None = None
    min_width_mm: float | None = None
    max_width_mm: float | None = None
    min_open_mm: float | None = None
    max_open_mm: float | None = None
    max_depth_mm: float | None = None
    finger_length_mm: float | None = None
    finger_height_mm: float | None = None
    fingertip_offset_mm: float | None = None
    finger_orientation: str | None = None
    tool_id: int | None = None
    tool_type: str | None = None
    static_source: str | None = None
    live_source: str | None = None
    source_urls: tuple[str, ...] = ()

    def with_live_values(self, **values) -> GripperDimensions:
        """Return a copy enriched with live values."""
        return replace(self, **values)


_DIMENSIONS: dict[str, GripperDimensions] = {
    "twofg7": GripperDimensions(
        key="twofg7",
        display_name="OnRobot 2FG7",
        product_code=0xC0,
        body_length_mm=144.0,
        body_width_mm=90.0,
        body_depth_mm=71.0,
        static_source="OnRobot 2FG7 datasheet",
        source_urls=("https://onrobot.com/storage/datasheets/datasheet_2fg7.pdf",),
    ),
    "rg2": GripperDimensions(
        key="rg2",
        display_name="OnRobot RG2",
        product_code=0x20,
        body_length_mm=213.0,
        body_width_mm=149.0,
        body_depth_mm=36.0,
        static_source="OnRobot RG2 datasheet",
        source_urls=("https://onrobot.com/storage/datasheets/datasheet_rg2.pdf",),
    ),
    "vgc10": GripperDimensions(
        key="vgc10",
        display_name="OnRobot VGC10",
        product_code=0x11,
        body_length_mm=101.0,
        body_width_mm=100.0,
        body_depth_mm=100.0,
        static_source="OnRobot VGC10 datasheet",
        source_urls=("https://onrobot.com/storage/datasheets/datasheet_vgc10.pdf",),
    ),
    "vg10": GripperDimensions(
        key="vg10",
        display_name="OnRobot VG10",
        product_code=0x10,
        folded_length_mm=105.0,
        folded_width_mm=146.0,
        folded_depth_mm=146.0,
        unfolded_length_mm=105.0,
        unfolded_width_mm=390.0,
        unfolded_depth_mm=390.0,
        static_source="OnRobot VG10 datasheet",
        source_urls=("https://onrobot.com/storage/datasheets/datasheet_vg10.pdf",),
    ),
    "sg": GripperDimensions(
        key="sg",
        display_name="OnRobot Soft Gripper",
        product_code=0x50,
        body_height_mm=84.0,
        body_diameter_mm=98.0,
        static_source="OnRobot SG datasheet",
        source_urls=("https://onrobot.com/storage/datasheets/soft-gripper.pdf",),
    ),
}


def get_static_dimensions(key: str) -> GripperDimensions:
    """Return static dimension metadata for a supported gripper key."""
    return _DIMENSIONS[key]
