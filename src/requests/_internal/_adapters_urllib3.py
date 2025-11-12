"""
Internal urllib3 adapter glue for Requests.

This is NOT a public API. It may change without notice.

Contains helpers to build and configure urllib3 pool/proxy managers and TLS
verification wiring used by HTTPAdapter.
"""
from __future__ import annotations

import os
import typing as _t

from urllib3.poolmanager import PoolManager, proxy_from_url

from ..auth import _basic_auth_str
from ..compat import urlparse
from ..exceptions import InvalidSchema
from ..utils import DEFAULT_CA_BUNDLE_PATH, extract_zipped_paths, get_auth_from_url

try:
    from urllib3.contrib.socks import SOCKSProxyManager
except ImportError:

    def SOCKSProxyManager(*args, **kwargs):  # type: ignore[no-redef]
        raise InvalidSchema("Missing dependencies for SOCKS support.")


def build_poolmanager(
    num_pools: int,
    maxsize: int,
    block: bool,
    strict: object | None,
    pool_kwargs: dict | None = None,
) -> PoolManager:
    """Create a urllib3 PoolManager with the given configuration.

    The `strict` parameter is ignored but accepted for compatibility with older
    urllib3 conditionals that may exist in Requests code paths.
    """
    kwargs = dict(pool_kwargs or {})
    return PoolManager(
        num_pools=num_pools,
        maxsize=maxsize,
        block=block,
        **kwargs,
    )


def proxy_headers(proxy: str) -> dict:
    headers: dict[str, str] = {}
    username, password = get_auth_from_url(proxy)
    if username:
        headers["Proxy-Authorization"] = _basic_auth_str(username, password)
    return headers


def build_proxy_manager(
    proxy_url: str,
    num_pools: int,
    maxsize: int,
    block: bool,
    strict: object | None,
    proxy_headers: dict | None,
    proxy_kwargs: dict | None = None,
):
    """Return a ProxyManager or SOCKSProxyManager for the given proxy_url."""
    proxy_kwargs = dict(proxy_kwargs or {})

    if proxy_url.lower().startswith("socks"):
        username, password = get_auth_from_url(proxy_url)
        return SOCKSProxyManager(
            proxy_url,
            username=username,
            password=password,
            num_pools=num_pools,
            maxsize=maxsize,
            block=block,
            **proxy_kwargs,
        )

    return proxy_from_url(
        proxy_url,
        proxy_headers=proxy_headers,
        num_pools=num_pools,
        maxsize=maxsize,
        block=block,
        **proxy_kwargs,
    )


def urllib3_request_context(
    request: "_t.Any",
    verify: "bool | str | None",
    client_cert: "_t.Tuple[str, str] | str | None",
) -> "(_t.Dict[str, _t.Any], _t.Dict[str, _t.Any])":
    """Build host params and pool kwargs for urllib3 connection pools.

    Mirrors previous private helper in requests.adapters.
    """
    host_params: dict[str, _t.Any] = {}
    pool_kwargs: dict[str, _t.Any] = {}
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


def configure_cert_verify(conn, url: str, verify, cert) -> None:
    """Configure certificate verification on a urllib3 connection object.

    This preserves Requests behavior across urllib3 1.x and 2.x.
    """
    if url.lower().startswith("https") and verify:
        cert_loc = None

        # Allow self-specified cert location.
        if verify is not True:
            cert_loc = verify

        if not cert_loc:
            cert_loc = extract_zipped_paths(DEFAULT_CA_BUNDLE_PATH)

        if not cert_loc or not os.path.exists(cert_loc):
            raise OSError(
                f"Could not find a suitable TLS CA certificate bundle, invalid path: {cert_loc}"
            )

        conn.cert_reqs = "CERT_REQUIRED"

        if not os.path.isdir(cert_loc):
            conn.ca_certs = cert_loc
        else:
            conn.ca_cert_dir = cert_loc
    else:
        conn.cert_reqs = "CERT_NONE"
        conn.ca_certs = None
        conn.ca_cert_dir = None

    if cert:
        if not isinstance(cert, str):
            conn.cert_file = cert[0]
            conn.key_file = cert[1]
        else:
            conn.cert_file = cert
            conn.key_file = None
        if conn.cert_file and not os.path.exists(conn.cert_file):
            raise OSError(
                f"Could not find the TLS certificate file, invalid path: {conn.cert_file}"
            )
        if conn.key_file and not os.path.exists(conn.key_file):
            raise OSError(
                f"Could not find the TLS key file, invalid path: {conn.key_file}"
            )
