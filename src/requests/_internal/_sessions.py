"""
requests._internal._sessions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Internal session helpers for requests.sessions. Keep self-contained and
avoid importing public requests modules.

NOTE: Transitional wiring for next major version.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Mapping


def merge_setting(request_setting, session_setting, dict_class=OrderedDict):
    """Determines appropriate setting for a given request, taking into account
    the explicit setting on that request, and the setting in the session. If a
    setting is a dictionary, they will be merged together using `dict_class`
    """

    if session_setting is None:
        return request_setting

    if request_setting is None:
        return session_setting

    # Bypass if not a dictionary (e.g. verify)
    if not (
        isinstance(session_setting, Mapping) and isinstance(request_setting, Mapping)
    ):
        return request_setting

    merged_setting = dict_class(_to_key_val_list(session_setting))
    merged_setting.update(_to_key_val_list(request_setting))

    # Remove keys that are set to None. Extract keys first to avoid altering
    # the dictionary during iteration.
    none_keys = [k for (k, v) in merged_setting.items() if v is None]
    for key in none_keys:
        del merged_setting[key]

    return merged_setting


def merge_hooks(request_hooks, session_hooks, dict_class=OrderedDict):
    """Properly merges both requests and session hooks.

    This is necessary because when request_hooks == {'response': []}, the
    merge breaks Session hooks entirely.
    """
    if session_hooks is None or session_hooks.get("response") == []:
        return request_hooks

    if request_hooks is None or request_hooks.get("response") == []:
        return session_hooks

    return merge_setting(request_hooks, session_hooks, dict_class)


# Local copy to avoid importing from public utils and creating cycles.

def _to_key_val_list(value):
    if isinstance(value, Mapping):
        return value.items()
    return list(value)
