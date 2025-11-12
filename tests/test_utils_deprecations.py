"""Tests for deprecated utils functions."""
import pytest
from collections import OrderedDict

from requests import utils


def test_dict_to_sequence_deprecated():
    """dict_to_sequence should emit DeprecationWarning."""
    with pytest.warns(DeprecationWarning, match="dict_to_sequence is deprecated"):
        result = utils.dict_to_sequence({"key": "val"})
        assert list(result) == [("key", "val")]


def test_from_key_val_list_deprecated():
    """from_key_val_list should emit DeprecationWarning."""
    with pytest.warns(DeprecationWarning, match="from_key_val_list is deprecated"):
        result = utils.from_key_val_list([("key", "val")])
        assert result == OrderedDict([("key", "val")])


def test_parse_list_header_deprecated():
    """parse_list_header should emit DeprecationWarning."""
    with pytest.warns(DeprecationWarning, match="parse_list_header is deprecated"):
        result = utils.parse_list_header('token, "quoted value"')
        assert result == ["token", "quoted value"]


def test_deprecated_functions_still_work():
    """Verify deprecated functions still return expected values."""
    # dict_to_sequence
    with pytest.warns(DeprecationWarning):
        d = {"a": 1, "b": 2}
        result = utils.dict_to_sequence(d)
        assert dict(result) == d

    # from_key_val_list
    with pytest.warns(DeprecationWarning):
        result = utils.from_key_val_list([("x", "y")])
        assert isinstance(result, OrderedDict)
        assert result["x"] == "y"

    # parse_list_header
    with pytest.warns(DeprecationWarning):
        result = utils.parse_list_header('a, b, "c, d"')
        assert len(result) == 3
        assert result[2] == "c, d"
