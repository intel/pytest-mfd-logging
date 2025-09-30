# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""File to keep all variables, which normally would be globals."""

import logging

import pytest

LOG_FORMAT: str | None = None
OLD_STREAM_HANDLER: logging.StreamHandler | None = None
PARSED_JSON_PATH: str | None = None
FILTER_OUT_LEVELS: list[str] | None = None
RESULTS_JSON_PATH: str | None = None
PYTEST_CONFIG: pytest.Config | None = None
PYTEST_METADATA: dict | None = None
