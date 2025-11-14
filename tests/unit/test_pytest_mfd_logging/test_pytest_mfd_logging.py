# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Tests for `pytest_mfd_logging` package."""

import pytest
from _pytest.mark import Mark
from _pytest.nodes import Node
from pytest_mfd_logging import amber_vars
import json

from pytest_mfd_logging.pytest_mfd_logging import (
    pytest_make_parametrize_id,
    _get_marker,
    pytest_json_runtest_metadata,
    pytest_runtestloop,
    _create_empty_live_results_file,
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

    def test_pytest_runtestloop_without_items_attribute(self, mocker):
        """Test that pytest_runtestloop returns early when session has no items attribute."""
        mock_session = mocker.create_autospec(pytest.Session)

        assert pytest_runtestloop(mock_session) is None

    def test_pytest_runtestloop_with_items_attribute_but_no_items(self, mocker):
        """Test that pytest_runtestloop works when session has items attribute but no items."""
        mock_session = mocker.create_autospec(pytest.Session)
        mock_session.items = []

        assert pytest_runtestloop(mock_session) is None

    def test_create_empty_live_results_file_without_items_attribute(self, mocker, tmp_path):
        """Test that _create_empty_live_results_file handles session without items attribute."""
        # Set up a temporary results file
        results_file = tmp_path / "results.json"
        mocker.patch.object(amber_vars, "RESULTS_JSON_PATH", str(results_file))
        mock_session = object()

        # Verify that hasattr returns False to ensure we test the right branch
        assert not hasattr(mock_session, "items")

        _create_empty_live_results_file(mock_session)

        with open(results_file) as f:
            data = json.load(f)

        assert data == {"tests": []}

    def test_create_empty_live_results_file_with_items_attribute(self, mocker, tmp_path):
        """Test that _create_empty_live_results_file works with session having items."""
        # Set up a temporary results file
        results_file = tmp_path / "results.json"
        mocker.patch.object(amber_vars, "RESULTS_JSON_PATH", str(results_file))
        mock_item1 = mocker.create_autospec(pytest.Function)
        mock_item1.nodeid = "test1::test_function1"
        mock_item2 = mocker.create_autospec(pytest.Function)
        mock_item2.nodeid = "test2::test_function2"

        mock_session = mocker.create_autospec(pytest.Session)
        mock_session.items = [mock_item1, mock_item2]

        _create_empty_live_results_file(mock_session)

        with open(results_file) as f:
            data = json.load(f)

        expected_tests = [
            {"nodeid": "test1::test_function1", "outcome": "passed"},
            {"nodeid": "test2::test_function2", "outcome": "passed"},
        ]
        assert data == {"tests": expected_tests}

    def test_create_empty_live_results_file_with_non_function_items(self, mocker, tmp_path):
        """Test _create_empty_live_results_file with items that are not pytest.Function instances."""
        # Set up a temporary results file
        results_file = tmp_path / "results.json"
        mocker.patch.object(amber_vars, "RESULTS_JSON_PATH", str(results_file))

        # Create mock items that are NOT pytest.Function instances
        mock_item1 = mocker.Mock()
        mock_item1.nodeid = "test1::test_class"

        mock_item2 = mocker.Mock()
        mock_item2.nodeid = "test2::test_module"

        mock_session = mocker.create_autospec(pytest.Session)
        mock_session.items = [mock_item1, mock_item2]

        assert hasattr(mock_session, "items")
        assert len(mock_session.items) == 2
        assert not isinstance(mock_session.items[0], pytest.Function)
        assert not isinstance(mock_session.items[1], pytest.Function)

        _create_empty_live_results_file(mock_session)

        with open(results_file) as f:
            data = json.load(f)

        assert data == {"tests": []}
