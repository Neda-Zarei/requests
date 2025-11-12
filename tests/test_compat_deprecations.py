import pytest

import requests.compat as compat


def test_deprecated_alias_attribute_access_warns_and_returns_expected():
    with pytest.warns(DeprecationWarning):
        assert compat.is_py2 is False
    with pytest.warns(DeprecationWarning):
        assert compat.is_py3 is True
    with pytest.warns(DeprecationWarning):
        assert compat.basestring is str
    with pytest.warns(DeprecationWarning):
        assert compat.integer_types == (int,)
    with pytest.warns(DeprecationWarning):
        assert compat.builtin_str is str
    with pytest.warns(DeprecationWarning):
        assert compat.numeric_types == (int, float)


def test_deprecated_alias_from_import_warns_and_returns_expected():
    with pytest.warns(DeprecationWarning):
        from requests.compat import basestring as bs  # noqa: F401

        assert bs is str


def test_other_compat_members_do_not_warn():
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # Access a few representative non-deprecated members
        compat.urlparse
        compat.Mapping
        compat.JSONDecodeError
        # Ensure no DeprecationWarnings were captured from compat module
        compat_warnings = [i for i in w if issubclass(i.category, DeprecationWarning) and 'compat' in str(i.message)]
        assert not compat_warnings
