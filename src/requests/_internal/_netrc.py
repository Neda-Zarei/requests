"""Internal netrc helpers (non-public API).

This module was split from requests.utils. It preserves the exact behavior of
Requests' public netrc-related helper but is not part of the public API.

Do not import from this module outside of requests' own code. External users
should continue importing from `requests.utils`.
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

from ..compat import urlparse

# mirror utils.NETRC_FILES for identical behavior
NETRC_FILES = (".netrc", "_netrc")


def get_netrc_auth(url: str, raise_errors: bool = False) -> Optional[Tuple[str, str]]:
    """Returns the Requests tuple auth for a given url from netrc."""

    netrc_file = os.environ.get("NETRC")
    if netrc_file is not None:
        netrc_locations = (netrc_file,)
    else:
        netrc_locations = (f"~/{f}" for f in NETRC_FILES)

    try:
        from netrc import NetrcParseError, netrc

        netrc_path = None

        for f in netrc_locations:
            loc = os.path.expanduser(f)
            if os.path.exists(loc):
                netrc_path = loc
                break

        # Abort early if there isn't one.
        if netrc_path is None:
            return None

        ri = urlparse(url)
        host = ri.hostname

        try:
            _netrc = netrc(netrc_path).authenticators(host)
            if _netrc:
                # Return with login / password
                login_i = 0 if _netrc[0] else 1
                return (_netrc[login_i], _netrc[2])
        except (NetrcParseError, OSError):
            # If there was a parsing error or a permissions issue reading the file,
            # we'll just skip netrc auth unless explicitly asked to raise errors.
            if raise_errors:
                raise

    # App Engine hackiness.
    except (ImportError, AttributeError):
        pass

    return None
