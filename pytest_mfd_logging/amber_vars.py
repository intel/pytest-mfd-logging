# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""File to keep all variables, which normally would be globals."""

import logging
from typing import List, Optional

LOG_FORMAT: Optional[str] = None
OLD_STREAM_HANDLER: Optional[logging.StreamHandler] = None
PARSED_JSON_PATH: Optional[str] = None
FILTER_OUT_LEVELS: Optional[List[str]] = None
