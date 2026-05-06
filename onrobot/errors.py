"""Typed exceptions for onrobot API calls."""

from __future__ import annotations


class OnRobotError(Exception):
    """Base class for OnRobot API exceptions."""


class OnRobotConnectionError(OnRobotError):
    """Raised when communication with the Compute Box/device fails."""


class OnRobotTimeoutError(OnRobotError):
    """Raised when a gripper operation exceeds timeout policy."""


class OnRobotValidationError(OnRobotError):
    """Raised when input arguments are outside supported ranges."""
