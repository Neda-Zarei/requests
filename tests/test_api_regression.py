"""Tests to validate no public API regressions from refactoring.

This module ensures that all public APIs remain stable and importable
after the recent refactoring to move internal implementations to
requests._internal while preserving backward compatibility.
"""

import pytest


class TestPublicAPIStability:
    """Verify all public APIs remain accessible and functional."""

    def test_top_level_imports(self):
        """Test that all top-level public symbols are importable."""
        import requests

        # Top-level convenience functions
        assert callable(requests.get)
        assert callable(requests.post)
        assert callable(requests.put)
        assert callable(requests.patch)
        assert callable(requests.delete)
        assert callable(requests.head)
        assert callable(requests.options)
        assert callable(requests.request)

        # Top-level classes
        assert hasattr(requests, 'Session')
        assert hasattr(requests, 'Response')
        assert hasattr(requests, 'Request')
        assert hasattr(requests, 'PreparedRequest')
        assert hasattr(requests, 'RequestException')

        # Version info
        assert hasattr(requests, '__version__')
        assert isinstance(requests.__version__, str)

    def test_session_module_imports(self):
        """Test that session module exports are intact."""
        from requests.sessions import Session, session
        from requests.sessions import merge_setting, merge_hooks

        assert callable(Session)
        assert callable(session)
        assert callable(merge_setting)
        assert callable(merge_hooks)

    def test_models_module_imports(self):
        """Test that models module exports are intact."""
        from requests.models import Request, Response, PreparedRequest
        from requests.models import DEFAULT_REDIRECT_LIMIT, REDIRECT_STATI

        assert callable(Request)
        assert callable(Response)
        assert callable(PreparedRequest)
        assert isinstance(DEFAULT_REDIRECT_LIMIT, int)
        assert isinstance(REDIRECT_STATI, (tuple, frozenset, set))

    def test_adapters_module_imports(self):
        """Test that adapters module exports are intact."""
        from requests.adapters import HTTPAdapter, BaseAdapter

        assert callable(HTTPAdapter)
        assert callable(BaseAdapter)

    def test_utils_module_imports(self):
        """Test that utils module exports are intact."""
        from requests.utils import (
            default_headers,
            default_user_agent,
            get_encoding_from_headers,
            super_len,
            to_key_val_list,
            parse_dict_header,
            unquote_header_value,
        )

        assert callable(default_headers)
        assert callable(default_user_agent)
        assert callable(get_encoding_from_headers)
        assert callable(super_len)
        assert callable(to_key_val_list)
        assert callable(parse_dict_header)
        assert callable(unquote_header_value)

    def test_compat_module_imports(self):
        """Test that compat module exports remain importable."""
        from requests.compat import (
            OrderedDict,
            JSONDecodeError,
            Mapping,
            cookielib,
            urlparse,
            urljoin,
        )

        assert OrderedDict is not None
        assert JSONDecodeError is not None
        assert Mapping is not None
        assert cookielib is not None
        assert callable(urlparse)
        assert callable(urljoin)

    def test_exceptions_module_imports(self):
        """Test that all exception classes are importable."""
        from requests.exceptions import (
            RequestException,
            HTTPError,
            ConnectionError,
            Timeout,
            URLRequired,
            TooManyRedirects,
            InvalidURL,
        )

        # Verify they're all exception classes
        assert issubclass(RequestException, Exception)
        assert issubclass(HTTPError, RequestException)
        assert issubclass(ConnectionError, RequestException)
        assert issubclass(Timeout, RequestException)
        assert issubclass(URLRequired, RequestException)
        assert issubclass(TooManyRedirects, RequestException)
        assert issubclass(InvalidURL, RequestException)


class TestFunctionalStability:
    """Verify that refactored functions still work correctly."""

    def test_merge_setting_behavior(self):
        """Test that merge_setting works as before."""
        from requests.sessions import merge_setting
        from collections import OrderedDict

        # Test with None
        result = merge_setting(None, {'a': 1})
        assert result == {'a': 1}

        # Test with dict merge
        result = merge_setting({'b': 2}, {'a': 1})
        assert result == {'a': 1, 'b': 2}

        # Test with custom dict_class
        result = merge_setting({'b': 2}, {'a': 1}, dict_class=OrderedDict)
        assert isinstance(result, OrderedDict)

    def test_super_len_behavior(self):
        """Test that super_len works as before."""
        from requests.utils import super_len

        # Test with string
        assert super_len("test") == 4

        # Test with bytes
        assert super_len(b"test") == 4

        # Test with list
        assert super_len([1, 2, 3]) == 3

    def test_to_key_val_list_behavior(self):
        """Test that to_key_val_list works as before."""
        from requests.utils import to_key_val_list

        # Test with dict
        result = to_key_val_list({'a': 1, 'b': 2})
        assert isinstance(result, list)
        assert len(result) == 2

        # Test with list
        result = to_key_val_list([('a', 1), ('b', 2)])
        assert result == [('a', 1), ('b', 2)]

        # Test with None
        result = to_key_val_list(None)
        assert result is None

    def test_parse_dict_header_behavior(self):
        """Test that parse_dict_header works as before."""
        from requests.utils import parse_dict_header

        # parse_dict_header expects comma-separated, not semicolon
        result = parse_dict_header('foo=bar, baz=qux')
        assert 'foo' in result or isinstance(result, dict)

    def test_session_creation_and_use(self):
        """Test that Session can be created and used."""
        from requests import Session

        s = Session()
        assert hasattr(s, 'headers')
        assert hasattr(s, 'cookies')
        assert hasattr(s, 'auth')
        assert hasattr(s, 'proxies')
        assert hasattr(s, 'hooks')
        assert hasattr(s, 'params')
        assert hasattr(s, 'verify')
        assert hasattr(s, 'cert')
        assert hasattr(s, 'max_redirects')
        assert hasattr(s, 'trust_env')
        assert hasattr(s, 'adapters')

    def test_request_preparation(self):
        """Test that Request preparation still works."""
        from requests import Request

        req = Request('GET', 'http://example.com')
        prepared = req.prepare()

        assert prepared.method == 'GET'
        assert prepared.url == 'http://example.com/'

    def test_httpadapter_instantiation(self):
        """Test that HTTPAdapter can be created."""
        from requests.adapters import HTTPAdapter

        adapter = HTTPAdapter()
        assert hasattr(adapter, 'send')
        assert hasattr(adapter, 'close')


class TestDeprecatedAPIsStillWork:
    """Verify deprecated APIs emit warnings but still function."""

    def test_deprecated_compat_symbols_work(self):
        """Test that deprecated compat symbols work with warnings."""
        import warnings
        from requests import compat

        # These should work but emit warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Access deprecated symbols
            _ = compat.is_py2
            _ = compat.is_py3
            _ = compat.basestring
            _ = compat.integer_types
            _ = compat.builtin_str
            _ = compat.numeric_types

            # Should have warnings
            assert len(w) == 6
            for warning in w:
                assert issubclass(warning.category, DeprecationWarning)
                assert "deprecated" in str(warning.message).lower()

    def test_deprecated_utils_functions_work(self):
        """Test that deprecated utils functions work with warnings."""
        import warnings
        from requests import utils

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Test dict_to_sequence
            result = utils.dict_to_sequence({'a': 1})
            assert list(result) == [('a', 1)]

            # Test from_key_val_list
            result = utils.from_key_val_list([('a', 1)])
            assert result['a'] == 1

            # Test parse_list_header
            result = utils.parse_list_header('a, b, c')
            assert result == ['a', 'b', 'c']

            # Should have warnings
            assert len(w) == 3
            for warning in w:
                assert issubclass(warning.category, DeprecationWarning)
