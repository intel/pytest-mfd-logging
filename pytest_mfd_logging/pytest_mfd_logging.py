# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Main module."""

import logging
import os
from collections import defaultdict
from configparser import ConfigParser
from io import StringIO
from pathlib import Path
from typing import Dict, Union, List, Any, Sequence, Optional, TYPE_CHECKING

import pytest
from jinja2 import Environment
from mfd_common_libs import log_levels, custom_logger, add_logging_level
from pytest_reporter_html1.plugin import TemplatePlugin

from . import amber_vars, marker
from .amber_log_filter import AmberLogFilter
from .amber_log_formatter import AmberLogFormatter

if TYPE_CHECKING:
    from _pytest.config.argparsing import Parser
    from _pytest.nodes import Item, Node
    from _pytest.runner import CallInfo

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


def pytest_addoption(parser: "Parser") -> None:
    """
    Create flags for configs.

    :param parser: Pytest parser
    """
    parser.addoption("--parsed-json-path", default=None, help="Parsed JSON files with logs destination folder.")
    parser.addoption(
        "--filter-out-levels",
        default=None,
        action="extend",
        nargs="+",
        type=str,
        help=(
            "Which log levels shouldn't be visible. "
            "Parameter accepts list of substrings of levels, "
            "for example '--filter-out-levels MFD BL DEBUG' will match all levels "
            "like MFD_STEP, MFD_DEBUG, BL_STEP, DEBUG, TEST_DEBUG and each level with matching substring."
        ),
    )


def _parse_phase(phase_details: Dict[str, Union[List, Dict, str, logging.LogRecord]], phase_name: str) -> str:
    """
    Get logs, parse them, add summary.

    :param phase_details: Dict containing all logs with its details for one phase of one test.
    :param phase_name: Name of phase.
    """
    long_repr = phase_details.get("longrepr", "")
    line = "-" * 20
    summarize = f"\n{line} {phase_name} {phase_details.get('outcome')} in {phase_details.get('duration')}s {line}"
    parsed_logs = _get_parsed_logs_for_phase(phase_details)
    return f"{parsed_logs}{long_repr}{summarize}\n\n"


def _get_parsed_logs_for_phase(phase_details: Dict[str, Union[List, Dict, str, logging.LogRecord]]) -> str:
    """
    Get logs and parse them.

    :param phase_details: Dict containing all logs with its details for one phase of one test.
    """
    logs = phase_details.get("log", [])
    if not logs:
        logs = phase_details.get("log_records", [])

    parsed_logs_buffer = StringIO()
    msg_formats = ["%(msg)", "%(message)"]
    for step in logs:
        # reporter plugin saves each log as LogRecord, json plugin as dict
        next_log = amber_vars.LOG_FORMAT % defaultdict(
            str, step.__dict__ if isinstance(step, logging.LogRecord) else step
        )

        if not any(msg in amber_vars.LOG_FORMAT for msg in msg_formats):
            # format declares only prefix, msg needs to be added - our default behaviour
            msg = step.getMessage() if isinstance(step, logging.LogRecord) else step.get("msg", "")
            next_log = AmberLogFormatter.get_prepared_message(formatted_prefix=next_log, message=msg)
        parsed_logs_buffer.write(f"\n{next_log}")

    parsed_logs = parsed_logs_buffer.getvalue()
    parsed_logs_buffer.close()
    return parsed_logs


def _create_log_file_for_test(test: Dict[str, Union[List, Dict, str]]) -> None:
    """
    Create file and log there all steps.

    :param test: Dict containing all logs with its details for one test.
    """
    os.makedirs(amber_vars.PARSED_JSON_PATH, exist_ok=True)
    test_name = f"{test.get('nodeid').split('::')[-1]}.txt"
    with open(Path(amber_vars.PARSED_JSON_PATH).joinpath(test_name), "w") as log_file:
        test_phases = ["setup", "call", "teardown"]
        for phase_name in test_phases:
            phase = test.get(phase_name)
            if phase is not None:
                log_file.write(_parse_phase(phase, phase_name.upper()))


@pytest.hookimpl(optionalhook=True)
def pytest_json_modifyreport(json_report: Dict[str, Union[List, Dict, str]]) -> None:
    """
    Parse json report and create files.

    Called after all tests.

    :param json_report: Dict containing all logs with its details.
    """
    if amber_vars.PARSED_JSON_PATH is None:
        return

    for test in json_report.get("tests"):
        _create_log_file_for_test(test)


def _remove_stream_handler() -> None:
    """Remove stream handler to print to console only logs captured by PyTest."""
    root_logger = logging.getLogger()
    stream_handler = next(
        (handler for handler in root_logger.handlers if isinstance(handler, logging.StreamHandler)), None
    )
    if stream_handler is None:
        return

    amber_vars.OLD_STREAM_HANDLER = stream_handler
    root_logger.removeHandler(stream_handler)


def _add_all_logging_levels() -> None:
    """Add all logging levels from mfd_common_libs.log_levels to be available in pytest.ini / cmd."""
    levels = [item for item in dir(log_levels) if not item.startswith("_")]
    for level in levels:
        custom_logger.add_logging_level(level, getattr(log_levels, level))


def _read_default_ini_file(section: str) -> Dict[str, str]:
    """
    Read ini file and return its data.

    :param section: Section of ini file.
    :return: Dict of param: value from requested section.
    """
    plugin_path = Path(os.path.dirname(os.path.realpath(__file__)))
    ini_path = plugin_path.joinpath("configs", "pytest.ini")
    parser = ConfigParser()
    parser.read(ini_path)
    log_params = [option for option in parser.options("pytest")]
    return {param: parser.get(section, param, raw=True) for param in log_params}


def pytest_configure(config: pytest.Config) -> None:
    """
    Perform initial configuration, it's called after command line parsing.

    :param config: The pytest config object.
    """
    logger_settings = _read_default_ini_file("pytest")
    logger_settings.update(config.inicfg)
    config.inicfg = logger_settings

    amber_vars.LOG_FORMAT = config.getini("log_format")
    amber_vars.PARSED_JSON_PATH = config.known_args_namespace.parsed_json_path
    amber_vars.FILTER_OUT_LEVELS = config.known_args_namespace.filter_out_levels
    _add_all_logging_levels()
    _remove_stream_handler()


@pytest.hookimpl()
def pytest_make_parametrize_id(config: pytest.Config, val: Any, argname: str) -> str:  # noqa
    """
    Print parameters with their values.

    :param config: Pytest config
    :param val: Value of argument
    :param argname: Name of argument
    :return: Formatted string with name of argument and its value
    """
    return f"|{argname} = {str(val)}|"


def _add_all_log_levels() -> None:
    """Add all log levels from mfd-common-libs to root logger."""
    from mfd_common_libs import add_logging_level

    for level in (lvl for lvl in dir(log_levels) if not lvl.startswith("_")):
        add_logging_level(level, getattr(log_levels, level))


def _apply_log_filter() -> None:
    """Apply log filter if --filter-out-levels parameter provided."""
    from _pytest.logging import _LiveLoggingStreamHandler, _FileHandler

    amber_log_filter = AmberLogFilter(filter_out_levels=amber_vars.FILTER_OUT_LEVELS)
    root_logger = logging.getLogger()

    live_logging_handler: Optional[_LiveLoggingStreamHandler] = next(
        (h for h in root_logger.handlers if isinstance(h, _LiveLoggingStreamHandler)), None
    )
    if live_logging_handler is not None:
        live_logging_handler.addFilter(amber_log_filter)

    file_logging_handler: Optional[_FileHandler] = next(
        (h for h in root_logger.handlers if isinstance(h, _FileHandler)), None
    )
    if file_logging_handler is not None:
        file_logging_handler.addFilter(amber_log_filter)


def _setup_logging_formatters(session: pytest.Session) -> None:
    """
    Overwrite formatters of PyTest loggers if format provided in ini is just a prefix (without msg/message).

    :param session: The pytest session object.
    """
    # if format is full log format (not only prefix) we will not overwrite formatters
    if any(msg in amber_vars.LOG_FORMAT for msg in ["%(msg)", "%(message)"]):
        return

    pytest_logging_plugin = session.config.pluginmanager.get_plugin("logging-plugin")
    pytest_logging_plugin.log_cli_handler.formatter = AmberLogFormatter(
        prev_formatter=pytest_logging_plugin.log_cli_handler.formatter
    )
    pytest_logging_plugin.log_file_handler.formatter = AmberLogFormatter(
        prev_formatter=pytest_logging_plugin.log_file_handler.formatter
    )

    _add_all_log_levels()
    if amber_vars.FILTER_OUT_LEVELS is not None:
        _apply_log_filter()


@pytest.hookimpl(trylast=True)
def pytest_sessionstart(session: pytest.Session) -> None:
    """
    Overwrite formatters.

    :param session: The pytest session object.
    """
    _setup_logging_formatters(session)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int | pytest.ExitCode) -> None:
    """
    Restore root logger after session.

    Called after whole test run finished, right before returning the exit status to the system.

    :param session: The pytest session object.
    :param exitstatus: The status which pytest will return to the system.
    """
    if amber_vars.OLD_STREAM_HANDLER is not None:
        logging.getLogger().addHandler(amber_vars.OLD_STREAM_HANDLER)


@pytest.hookimpl(trylast=True)
def pytest_reporter_loader(
    dirs: Union[str, os.PathLike, Sequence[Union[str, os.PathLike]]], config: pytest.Config
) -> Optional[Environment]:
    """
    Find TemplatePlugin instance from html1 plugin, add method to be seen in html templates.

    We can't just find plugin by name, because html1 is registering TemplatePlugin without explicitly passed name,
    this means that pytest is providing there random name, like 1987623.

    Jinja env changes explanation:
    - env.globals - method needs to be visible in template, that's why it needs to be added to globals

    :param dirs: From jinja docs - A path, or list of paths, to the directory that contains the templates.
                 This parameter is later passed to FileSystemLoader in reporter plugin.
    :param config: Pytest config.
    :return: Jinja's Environment
    """
    all_plugins = config.pluginmanager.get_plugins()
    template_plugin = next((plugin for plugin in all_plugins if isinstance(plugin, TemplatePlugin)), None)
    if template_plugin is None:
        return

    template_plugin.env.globals["_get_parsed_logs_for_phase"] = _get_parsed_logs_for_phase
    return template_plugin.env


@pytest.hookimpl()
def pytest_reporter_template_dirs(config: pytest.Config) -> List[Union[str, os.PathLike]]:
    """
    Return path to a template folder, to allow usage of templates without explicitly passing a path.

    :param config: Pytest config.
    :return: List of directories containing templates.
    """
    return [Path(__file__).parent / "templates"]


def _get_marker(item: "Item | Node") -> str | None:
    """
    Get marker.

    If marker is not present in the item check parent and so on.
    It's possible to mark function/class/module.

    :param item: PyTest Item or Node object
    :return: Marker name or None if test/class/module not marked
    """
    own_markers = getattr(item, "own_markers", [])
    _marker = next((own_m.name for own_m in own_markers if own_m.name in dir(marker)), None)
    if _marker is not None:
        return _marker

    if getattr(item, "parent") is not None:
        return _get_marker(item.parent)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item: "Item") -> None:
    """
    Check if custom marker present - if yes print log message.

    :param item: PyTest Item object
    """
    if (_marker := _get_marker(item)) is not None:
        logger.log(level=log_levels.TEST_INFO, msg=f"Test {item.nodeid} was implemented with {_marker}")
    else:
        logger.log(level=log_levels.TEST_INFO, msg=f"Test {item.nodeid} was implemented manually")


@pytest.hookimpl(optionalhook=True)
def pytest_json_runtest_metadata(item: "Item", call: "CallInfo") -> dict[str, Any]:
    """
    Add proper marker to metadata of json report.

    Called from `pytest_runtest_makereport`. Plugins can use this hook to add metadata based on the current test run.

    :param item: PyTest Item object
    :param call: PyTest Call info
    :return: Dict which will be added to the current test item's JSON metadata
    """
    _marker = _get_marker(item)
    return {"created_with": _marker if _marker is not None else "MN"}


"""
Collection flow (https://docs.pytest.org/en/stable/reference/reference.html):

The default collection phase is this (see individual hooks for full details):

1. Starting from session as the initial collector:
    a) pytest_collectstart(collector)
    b) report = pytest_make_collect_report(collector)
    c) pytest_exception_interact(collector, call, report) if an interactive exception occurred
    d) For each collected node:
        - If an item, pytest_itemcollected(item)
        - If a collector, recurse into it.
    e) pytest_collectreport(report)
2. pytest_collection_modifyitems(session, config, items)
    a) pytest_deselected(items) for any deselected items (may be called multiple times)
3. pytest_collection_finish(session)
4. Set session.items to the list of collected items
5. Set session.testscollected to the number of collected items
"""
