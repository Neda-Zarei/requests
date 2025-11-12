import importlib
import pkgutil
import sys


def test_py_typed_pkgutil():
    data = pkgutil.get_data("requests", "py.typed")
    assert data is not None, "py.typed should be present as package data"


def test_py_typed_importlib_resources():
    # Python >= 3.9 only path. Avoid using importlib_resources backport.
    if sys.version_info < (3, 9):
        return
    files = importlib.resources.files("requests")
    assert files.joinpath("py.typed").is_file(), "py.typed should exist in package"
