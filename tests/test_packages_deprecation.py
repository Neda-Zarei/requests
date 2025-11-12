import importlib
import warnings

import pytest


def _import_and_warn(target):
    # Ensure we capture DeprecationWarning from importing requests.packages.*
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        with pytest.warns(DeprecationWarning):
            mod = importlib.import_module(target)
            assert mod is not None
            return mod


def test_deprecation_warning_for_urllib3():
    mod = _import_and_warn("requests.packages.urllib3")
    # Should be the same module object as direct import
    import urllib3 as direct

    assert mod is direct


def test_deprecation_warning_for_idna():
    mod = _import_and_warn("requests.packages.idna")
    import idna as direct

    assert mod is direct


def test_deprecation_warning_for_chardet_or_charset_normalizer():
    # Try chardet alias first; fall back to charset_normalizer if applicable.
    try:
        mod = _import_and_warn("requests.packages.chardet")
        # Direct import should prefer chardet if present
        import chardet as direct

        assert mod is direct
    except ModuleNotFoundError:
        # When chardet is not installed, requests.compat may alias to charset_normalizer
        # The aliasing in requests.packages maps both the resolved lib name and
        # "chardet" to the same imported module object.
        mod = _import_and_warn("requests.packages.chardet")
        try:
            import charset_normalizer as direct
        except ModuleNotFoundError:
            pytest.skip("Neither chardet nor charset_normalizer available")
        assert mod is direct
