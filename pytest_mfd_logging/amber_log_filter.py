# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Separate file for amber filter."""

import logging
from typing import List, Set

from mfd_common_libs import log_levels


class AmberLogFilter(logging.Filter):
    """Custom Filter for logs based on level name."""

    def __init__(self, filter_out_levels: List[str], *args, **kwargs):
        """Init."""
        super().__init__(*args, **kwargs)
        known_log_levels = {level for level in dir(log_levels) if not level.startswith("_")}  # mfd log levels
        known_log_levels.update(logging._nameToLevel.keys())  # python logging log levels
        self._filter_out_levels: Set[str] = {
            level
            for level in known_log_levels
            if any(given_level.upper() in level for given_level in filter_out_levels)
        }

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        """Filter method called for each log."""
        return record.levelname not in self._filter_out_levels
