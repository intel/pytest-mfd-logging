# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Tests for `marker` file."""

import pytest

from pytest_mfd_logging import marker
from pytest_mfd_logging.exceptions import UnrecognizedMarkerError


class TestMarker:
    def test___get_attr__(self):
        getattr(marker, "MBT_AI")
        getattr(marker, "MBT_Waypoints")
        getattr(marker, "AI")

        with pytest.raises(UnrecognizedMarkerError):
            getattr(marker, "wrong name")
