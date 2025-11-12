"""
requests._internal._adapters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Internal helpers used by requests.adapters. This module must not import
any public requests modules to avoid import cycles. Public modules should
import from here and re-export or delegate as needed.

NOTE: Transitional wiring for next major version cleanup.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse


def _urllib3_request_context(
    request,
    verify: "bool | str | None",
    client_cert: "tuple[str, str] | str | None",
    poolmanager,
):
    """Build host params and pool kwargs for urllib3 connection selection.

    This logic was previously embedded in requests.adapters.HTTPAdapter.
    It is preserved here without behavior changes and imported by the
    public module.
    """
    host_params = {}
    pool_kwargs = {}
    parsed_request_url = urlparse(request.url)
    scheme = parsed_request_url.scheme.lower()
    port = parsed_request_url.port

    cert_reqs = "CERT_REQUIRED"
    if verify is False:
        cert_reqs = "CERT_NONE"
    elif isinstance(verify, str):
        if not os.path.isdir(verify):
            pool_kwargs["ca_certs"] = verify
        else:
            pool_kwargs["ca_cert_dir"] = verify
    pool_kwargs["cert_reqs"] = cert_reqs
    if client_cert is not None:
        if isinstance(client_cert, tuple) and len(client_cert) == 2:
            pool_kwargs["cert_file"] = client_cert[0]
            pool_kwargs["key_file"] = client_cert[1]
        else:
            # According to our docs, we allow users to specify just the client
            # cert path
            pool_kwargs["cert_file"] = client_cert
    host_params = {
        "scheme": scheme,
        "host": parsed_request_url.hostname,
        "port": port,
    }
    return host_params, pool_kwargs
