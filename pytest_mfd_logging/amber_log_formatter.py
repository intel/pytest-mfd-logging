# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Separate file for amber formatter."""

import logging
from colors import ansilen

from _pytest.logging import ColoredLevelFormatter

from mfd_common_libs import log_levels


class AmberLogFormatter(logging.Formatter):
    """Formatter for framework, used for console output."""

    def __init__(self, prev_formatter: logging.Formatter) -> None:
        """
        Init.

        :param prev_formatter: Formatter, which will be overwritten.
                               We will use this object, so basically we're making more like a wrapper here.
        """
        super().__init__()
        self._prev_formatter = prev_formatter
        self._add_mfd_level_colors()

    def _add_mfd_level_colors(self) -> None:
        """Add colors to the MFD's log_levels if previous formatter is pytest's colored formatter."""
        if not isinstance(self._prev_formatter, ColoredLevelFormatter):
            return

        self._prev_formatter.add_color_level(log_levels.MODULE_DEBUG, "Black")
        self._prev_formatter.add_color_level(log_levels.CMD, "blue")
        self._prev_formatter.add_color_level(log_levels.OUT, "white")
        self._prev_formatter.add_color_level(log_levels.TEST_PASS, "Green")
        self._prev_formatter.add_color_level(log_levels.TEST_FAIL, "Red")
        self._prev_formatter.add_color_level(log_levels.TEST_STEP, "Yellow")
        self._prev_formatter.add_color_level(log_levels.TEST_INFO, "yellow", "bold")
        self._prev_formatter.add_color_level(log_levels.TEST_DEBUG, "yellow")
        self._prev_formatter.add_color_level(log_levels.MFD_STEP, "Cyan")
        self._prev_formatter.add_color_level(log_levels.MFD_INFO, "cyan", "bold")
        self._prev_formatter.add_color_level(log_levels.MFD_DEBUG, "cyan")
        self._prev_formatter.add_color_level(log_levels.BL_STEP, "Purple")
        self._prev_formatter.add_color_level(log_levels.BL_INFO, "purple", "bold")
        self._prev_formatter.add_color_level(log_levels.BL_DEBUG, "purple")

    def formatMessage(self, record: logging.LogRecord) -> str:
        """
        Format and return log record.

        We assume that this formatter is used only with our predefined log format or similar prefix format,
        which uses fields like asctime, name, functime, levelname, but doesn't include msg/message.
        That's why this formatter will format prefix of log record with previous formatter
        and after that it will add msg with indentations.

        :param record: Log record.
        :return: Formatted message.
        """
        message = record.getMessage()
        # check if separator
        if len(set(message)) == 1:
            return message

        formatted_prefix = self._prev_formatter.format(record)
        return self.get_prepared_message(formatted_prefix, message)

    @staticmethod
    def get_prepared_message(formatted_prefix: str, message: str) -> str:
        """
        Extend message with proper indentations and return joined str with formatted prefix.

        :param formatted_prefix: Already formatted log's prefix with fields like asctime, ...
        :param message: Message, which will be extended with spaces to create column-like aligned text.
        :return: Joined formatted prefix and extended message.
        """
        indent_length = ansilen(formatted_prefix) + 1  # + 1 because of additional space before message
        msg_lines = message.splitlines(True)
        message = ""
        if msg_lines:
            message = "".join([msg_lines[0], *(f"{indent_length * ' '}{line}" for line in msg_lines[1:])])
        return f"{formatted_prefix} {message}"
