"""
requests.models
~~~~~~~~~~~~~~~

This module contains the primary objects that power Requests.
"""

import datetime

from ..status_codes import codes

#: The set of HTTP status codes that indicate an automatically
#: processable redirect.
REDIRECT_STATI = (
    codes.moved,  # 301
    codes.found,  # 302
    codes.other,  # 303
    codes.temporary_redirect,  # 307
    codes.permanent_redirect,  # 308
)

DEFAULT_REDIRECT_LIMIT = 30
CONTENT_CHUNK_SIZE = 10 * 1024
ITER_CHUNK_SIZE = 512

# Import for backward compatibility
from ..compat import urlencode

# Import classes from submodules for re-export
from .request import (
    Request,
    PreparedRequest,
    RequestEncodingMixin,
    RequestHooksMixin,
)
from .response import Response
