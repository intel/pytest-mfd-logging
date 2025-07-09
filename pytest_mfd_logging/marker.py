# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Amber marker utility."""

import pytest

MBT_Waypoints = pytest.mark.MBT_Waypoints
MBT_AI = pytest.mark.MBT_AI
AI = pytest.mark.AI


def __getattr__(marker: str) -> None:
    """
    Check if marker is one of predefined.

    :param marker: Selected marker
    :raises UnrecognizedMarkerError when marker not recognized
    """
    if marker not in dir():
        from pytest_mfd_logging.exceptions import UnrecognizedMarkerError

        raise UnrecognizedMarkerError(f"Marker {marker} was not recognized.")
