# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Tests for `pytest_mfd_logging` package."""

import pytest
from _pytest.mark import Mark
from _pytest.nodes import Node

from pytest_mfd_logging.pytest_mfd_logging import (
    pytest_make_parametrize_id,
    _get_marker,
    pytest_json_runtest_metadata,
)


class TestPytestMfdLogging:
    def test_pytest_make_parametrize_id_int(self):
        expected_output = "|param = 1|"

        assert expected_output == pytest_make_parametrize_id(None, 1, "param")  # noqa

    def test_pytest_make_parametrize_id_dict(self):
        expected_output = "|param_dict = {'a': 1, 'b': 2}|"

        assert expected_output == pytest_make_parametrize_id(None, {"a": 1, "b": 2}, "param_dict")  # noqa

    def test__get_marker(self, mocker):
        item = mocker.create_autospec(pytest.Item)
        item.own_markers = [Mark(name="some marker", args=..., kwargs=...), Mark(name="MBT_AI", args=..., kwargs=...)]
        assert _get_marker(item) == "MBT_AI"

        parent_node = mocker.create_autospec(Node)
        parent_node.own_markers = [
            Mark(name="some marker", args=..., kwargs=...),
            Mark(name="AI", args=..., kwargs=...),
        ]
        item.own_markers.pop(1)
        item.parent = parent_node
        assert _get_marker(item) == "AI"

    def test_pytest_json_runtest_metadata(self, mocker):
        call_info_mock = mocker.create_autospec(pytest.CallInfo)
        item = mocker.create_autospec(pytest.Item)
        item.parent = None

        item.own_markers = [Mark(name="some marker", args=..., kwargs=...), Mark(name="MBT_AI", args=..., kwargs=...)]
        assert pytest_json_runtest_metadata(item, call_info_mock) == {"created_with": "MBT_AI"}

        item.own_markers = []
        assert pytest_json_runtest_metadata(item, call_info_mock) == {"created_with": "MN"}
