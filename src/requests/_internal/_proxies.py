"""Internal proxy resolution helpers (non-public API).

This module was split from requests.utils. It preserves the exact behavior of
Requests' public proxy-related helpers but is not part of the public API.

Do not import from this module outside of requests' own code. External users
should continue importing from `requests.utils`.
"""
from __future__ import annotations

import os
import socket
from contextlib import contextmanager
from typing import Dict, Optional

from ..compat import getproxies
from ..compat import urlparse

# NOTE ABOUT IMPORT CYCLES:
# We avoid importing requests.utils at module import time to prevent cycles.
# Where needed (proxy_bypass), we import within functions.


@contextmanager
def _set_environ(env_name, value):
    """A local copy of requests.utils.set_environ to avoid import cycle.

    It mirrors the exact behavior used by should_bypass_proxies.
    """
    value_changed = value is not None
    if value_changed:
        old_value = os.environ.get(env_name)
        os.environ[env_name] = value
    try:
        yield
    finally:
        if value_changed:
            if old_value is None:
                del os.environ[env_name]
            else:
                os.environ[env_name] = old_value


# Helper imports from utils done lazily inside functions to avoid cycles


def _is_ipv4_address(string_ip: str) -> bool:
    try:
        import socket as _socket

        _socket.inet_aton(string_ip)
    except OSError:
        return False
    return True


def _is_valid_cidr(string_network: str) -> bool:
    if string_network.count("/") == 1:
        try:
            mask = int(string_network.split("/")[1])
        except ValueError:
            return False

        if mask < 1 or mask > 32:
            return False

        try:
            socket.inet_aton(string_network.split("/")[0])
        except OSError:
            return False
    else:
        return False
    return True


def _address_in_network(ip: str, net: str) -> bool:
    import struct

    ipaddr = struct.unpack("=L", socket.inet_aton(ip))[0]
    netaddr, bits = net.split("/")
    from ..utils import dotted_netmask  # safe import: utils imports this file lazily via re-export

    netmask = struct.unpack("=L", socket.inet_aton(dotted_netmask(int(bits))))[0]
    network = struct.unpack("=L", socket.inet_aton(netaddr))[0] & netmask
    return (ipaddr & netmask) == (network & netmask)


def should_bypass_proxies(url: str, no_proxy: Optional[str]):
    """
    Returns whether we should bypass proxies or not.

    :rtype: bool
    """

    # Prioritize lowercase environment variables over uppercase
    # to keep a consistent behaviour with other http projects (curl, wget).
    def get_proxy(key):
        return os.environ.get(key) or os.environ.get(key.upper())

    # First check whether no_proxy is defined. If it is, check that the URL
    # we're getting isn't in the no_proxy list.
    no_proxy_arg = no_proxy
    if no_proxy is None:
        no_proxy = get_proxy("no_proxy")
    parsed = urlparse(url)

    if parsed.hostname is None:
        # URLs don't always have hostnames, e.g. file:/// urls.
        return True

    if no_proxy:
        # We need to check whether we match here. We need to see if we match
        # the end of the hostname, both with and without the port.
        no_proxy = (host for host in no_proxy.replace(" ", "").split(",") if host)

        if _is_ipv4_address(parsed.hostname):
            for proxy_ip in no_proxy:
                if _is_valid_cidr(proxy_ip):
                    if _address_in_network(parsed.hostname, proxy_ip):
                        return True
                elif parsed.hostname == proxy_ip:
                    # If no_proxy ip was defined in plain IP notation instead of cidr notation &
                    # matches the IP of the index
                    return True
        else:
            host_with_port = parsed.hostname
            if parsed.port:
                host_with_port += f":{parsed.port}"

            for host in no_proxy:
                if parsed.hostname.endswith(host) or host_with_port.endswith(host):
                    # The URL does match something in no_proxy, so we don't want
                    # to apply the proxies on this URL.
                    return True

    # Use utils.proxy_bypass and mimic set_environ context manager semantics
    with _set_environ("no_proxy", no_proxy_arg):
        # parsed.hostname can be `None` in cases such as a file URI.
        try:
            from ..utils import proxy_bypass  # Local import to avoid cycle

            bypass = proxy_bypass(parsed.hostname)
        except (TypeError, socket.gaierror):
            bypass = False

    if bypass:
        return True

    return False


def get_environ_proxies(url: str, no_proxy: Optional[str] = None) -> Dict[str, str]:
    """
    Return a dict of environment proxies.

    :rtype: dict
    """
    if should_bypass_proxies(url, no_proxy=no_proxy):
        return {}
    else:
        return getproxies()


def select_proxy(url: str, proxies: Optional[Dict[str, str]]):
    """Select a proxy for the url, if applicable.

    :param url: The url being for the request
    :param proxies: A dictionary of schemes or schemes and hosts to proxy URLs
    """
    proxies = proxies or {}
    urlparts = urlparse(url)
    if urlparts.hostname is None:
        return proxies.get(urlparts.scheme, proxies.get("all"))

    proxy_keys = [
        urlparts.scheme + "://" + urlparts.hostname,
        urlparts.scheme,
        "all://" + urlparts.hostname,
        "all",
    ]
    proxy = None
    for proxy_key in proxy_keys:
        if proxy_key in proxies:
            proxy = proxies[proxy_key]
            break

    return proxy
