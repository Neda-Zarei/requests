"""
requests._internal._headers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Internal header helpers used by requests.utils. Keep this module free of
imports from public requests modules to avoid cycles.

NOTE: Transitional wiring; public names remain in requests.utils until
next major version.
"""
from __future__ import annotations

from urllib.parse import unquote


def parse_list_header(value):
    # Werkzeug-compatible list header parsing is provided via
    # requests.compat.parse_http_list in public utils. This module only
    # provides dict parsing helpers when utils prefers to import directly.
    raise NotImplementedError


# We reproduce utils.parse_dict_header and unquote_header_value here to allow
# public utils to import and re-export them without changing behavior.

def parse_dict_header(value):
    result = {}
    from urllib.request import parse_http_list as _parse_list_header

    for item in _parse_list_header(value):
        if "=" not in item:
            result[item] = None
            continue
        name, value = item.split("=", 1)
        if value[:1] == value[-1:] == '"':
            value = unquote_header_value(value[1:-1])
        result[name] = value
    return result


def unquote_header_value(value, is_filename: bool = False):
    if value and value[0] == value[-1] == '"':
        value = value[1:-1]
        if not is_filename or value[:2] != "\\\\":
            return value.replace("\\\\", "\\").replace('\\"', '"')
    return value
