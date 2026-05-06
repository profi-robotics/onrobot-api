"""Runtime retry/timeout policy for gripper operations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperationPolicy:
    poll_interval_s: float = 0.1
    busy_timeout_s: float = 3.0
    detect_timeout_s: float = 2.0
    vacuum_timeout_s: float = 4.0
