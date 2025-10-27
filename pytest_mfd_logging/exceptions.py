# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Logging module exceptions."""


class UnrecognizedMarkerError(AttributeError):
    """Unrecognized Marker Error."""


class ExternalIdValidationError(Exception):
    """External ID marker validation error."""
