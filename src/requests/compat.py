"""
requests.compat
~~~~~~~~~~~~~~~

This module provides a compatibility layer for external packages and
standard library imports. It also maintains deprecated Python 2 era
aliases for backward compatibility until the next major version.

As of Requests 3.0, this module will be significantly reduced.
"""

import importlib
import sys
import warnings

# ----------------------
# urllib3 Version Check
# ----------------------
# Runtime dependency: Detect urllib3 major version for compatibility handling.
# urllib3 2.x changed string encoding behavior (utf-8 vs latin-1), requiring
# different code paths. See utils.py::super_len for usage.
# Tested in: tests covering file uploads and body encoding
from urllib3 import __version__ as urllib3_version

try:
    is_urllib3_1 = int(urllib3_version.split(".")[0]) == 1
except (TypeError, AttributeError):
    # If version parsing fails, assume urllib3 1.x behavior for safety
    is_urllib3_1 = True

# -------------------
# Character Detection
# -------------------


def _resolve_char_detection():
    """Find supported character detection libraries."""
    chardet = None
    for lib in ("chardet", "charset_normalizer"):
        if chardet is None:
            try:
                chardet = importlib.import_module(lib)
            except ImportError:
                pass
    return chardet


chardet = _resolve_char_detection()

# -------------------
# JSON Module Support
# -------------------
# Requests preferentially uses simplejson if available for performance,
# but falls back to the standard library json module.
has_simplejson = False
try:
    import simplejson as json

    has_simplejson = True
except ImportError:
    import json

if has_simplejson:
    from simplejson import JSONDecodeError
else:
    from json import JSONDecodeError

# -----------------------
# Standard Library Imports
# -----------------------
# These are re-exported for backward compatibility and to provide a single
# import location for common dependencies.
from collections import OrderedDict
from collections.abc import Callable, Mapping, MutableMapping
from http import cookiejar as cookielib
from http.cookies import Morsel
from io import StringIO
from urllib.parse import (
    quote,
    quote_plus,
    unquote,
    unquote_plus,
    urldefrag,
    urlencode,
    urljoin,
    urlparse,
    urlsplit,
    urlunparse,
)
from urllib.request import (
    getproxies,
    getproxies_environment,
    parse_http_list,
    proxy_bypass,
    proxy_bypass_environment,
)

# -----------------------------
# Python 3 Built-ins Re-exports
# -----------------------------
# Exposed for backward compatibility with code that imports from compat
str = str
bytes = bytes

# -----------------------------------
# Deprecation Layer for Python 2 Era
# -----------------------------------
# These symbols are deprecated and will be removed in Requests 3.0
_DEPRECATED_COMPAT = {
    "is_py2": False,
    "is_py3": True,
    "basestring": str,
    "integer_types": (int,),
    "builtin_str": str,
    "numeric_types": (int, float),
}


def __getattr__(name):
    if name in _DEPRECATED_COMPAT:
        warnings.warn(
            (
                f"requests.compat.{name} is deprecated and will be removed in the next major release; "
                "use Python 3 built-ins directly."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        return _DEPRECATED_COMPAT[name]
    raise AttributeError(name)
