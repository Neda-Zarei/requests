"""
requests._internal._redirects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Internal redirect handling helpers for Requests.

WARNING: Internal-only module. No public API stability guarantees. The
functions here may change or be removed without notice.
"""
from __future__ import annotations

from typing import Iterable, Iterator, Optional

from .._internal_utils import to_native_string
from ..compat import urljoin, urlparse
from ..exceptions import ChunkedEncodingError, ContentDecodingError, TooManyRedirects
from ..status_codes import codes
from ..utils import DEFAULT_PORTS, requote_uri, rewind_body
from ..cookies import extract_cookies_to_jar, merge_cookies


def get_redirect_target(resp) -> Optional[str]:
    """Return redirect target URL if present and response is a redirect.

    Ensures proper decoding of non-ASCII Location headers following current
    behavior in SessionRedirectMixin.get_redirect_target.
    """
    if resp.is_redirect:
        location = resp.headers["location"]
        location = location.encode("latin1")
        return to_native_string(location, "utf8")
    return None


def rebuild_method(method: str, status_code: int, allowed_methods: Optional[Iterable[str]] = None) -> str:
    """Apply RFC-compliant method rewriting rules.

    - 303 -> GET (except HEAD stays HEAD per callers typically check)
    - 302 -> GET for historical reasons (except HEAD)
    - 301 -> POST to GET for historical reasons
    - 307/308 preserve method

    The allowed_methods parameter is unused for parity with potential future
    callers; present to match requested signature.
    """
    if status_code == codes.see_other and method != "HEAD":
        return "GET"
    if status_code == codes.found and method != "HEAD":
        return "GET"
    if status_code == codes.moved and method == "POST":
        return "GET"
    return method


def should_strip_auth(old_url: str, new_url: str) -> bool:
    """Whether Authorization should be dropped on cross-host/scheme changes.

    Mirrors SessionRedirectMixin.should_strip_auth behavior.
    """
    old_parsed = urlparse(old_url)
    new_parsed = urlparse(new_url)
    if old_parsed.hostname != new_parsed.hostname:
        return True

    # Allow http -> https on standard ports for backwards-compat
    if (
        old_parsed.scheme == "http"
        and old_parsed.port in (80, None)
        and new_parsed.scheme == "https"
        and new_parsed.port in (443, None)
    ):
        return False

    # Handle default port usage corresponding to scheme.
    changed_port = old_parsed.port != new_parsed.port
    changed_scheme = old_parsed.scheme != new_parsed.scheme
    default_port = (DEFAULT_PORTS.get(old_parsed.scheme, None), None)
    if (not changed_scheme and old_parsed.port in default_port and new_parsed.port in default_port):
        return False

    return changed_port or changed_scheme


def remove_headers_on_redirect(headers, to_netloc):
    """Compute headers to remove on redirect.

    Currently requests removes body headers on certain redirects in the caller
    code and always drops Cookie header. This function returns a set of header
    names that should be removed from the prepared request headers prior to
    following the redirect.

    For compatibility, we return the union of body-related headers when the
    redirect is not 307/308 (handled by caller) and Cookie header always.
    However, because the decision partly depends on status code, the caller
    still manages removal timing. For now, we expose a minimal helper that
    indicates Cookie header removal.
    """
    # Only behavior encoded explicitly in sessions: always drop Cookie prior to
    # following redirects, to avoid cookie duplication during merging logic.
    return {"Cookie"}


def normalize_redirect_url(url: str, base_url: str) -> str:
    """Ensure proper URL joining and normalization for relative redirects.

    - Support schemeless redirects beginning with // by borrowing scheme of base.
    - Preserve previous fragment rules are handled by caller; we just join and requote.
    """
    if url.startswith("//"):
        parsed_rurl = urlparse(base_url)
        url = ":".join([to_native_string(parsed_rurl.scheme), url])

    parsed = urlparse(url)
    if not parsed.netloc:
        url = urljoin(base_url, requote_uri(url))
    else:
        url = requote_uri(url)
    return to_native_string(url)


def resolve_redirects(
    resp,
    req,
    session,
    stream=False,
    verify=True,
    cert=None,
    proxies=None,
    allow_redirects=True,
    timeout=None,
    max_redirects=None,
    yield_requests=False,
    **adapter_kwargs,
) -> Iterator:
    """Generator that mirrors Session.resolve_redirects behavior.

    Delegates to session.send for follow-ups, preserves history and settings.
    The public API/behavior must remain identical to requests.Session.resolve_redirects.
    """
    hist = []
    url = get_redirect_target(resp)
    previous_fragment = urlparse(req.url).fragment

    # Redirect limit comes from session.max_redirects by default
    limit = session.max_redirects if max_redirects is None else max_redirects

    while url:
        prepared_request = req.copy()

        # Update history and keep track of redirects.
        hist.append(resp)
        resp.history = hist[1:]

        try:
            resp.content  # Consume socket so it can be released
        except (ChunkedEncodingError, ContentDecodingError, RuntimeError):
            resp.raw.read(decode_content=False)

        if len(resp.history) >= limit:
            raise TooManyRedirects(
                f"Exceeded {limit} redirects.", response=resp
            )

        # Release the connection back into the pool.
        resp.close()

        # Normalize URL and handle fragments
        # Handle redirection without scheme (see: RFC 1808 Section 4)
        if url.startswith("//"):
            parsed_rurl = urlparse(resp.url)
            url = ":".join([to_native_string(parsed_rurl.scheme), url])

        parsed = urlparse(url)
        if parsed.fragment == "" and previous_fragment:
            parsed = parsed._replace(fragment=previous_fragment)
        elif parsed.fragment:
            previous_fragment = parsed.fragment
        url = parsed.geturl()

        url = normalize_redirect_url(url, resp.url)

        prepared_request.url = to_native_string(url)

        # Method rewriting
        new_method = rebuild_method(prepared_request.method, resp.status_code)
        prepared_request.method = new_method

        # https://github.com/psf/requests/issues/1084
        if resp.status_code not in (codes.temporary_redirect, codes.permanent_redirect):
            # https://github.com/psf/requests/issues/3490
            purged_headers = ("Content-Length", "Content-Type", "Transfer-Encoding")
            for header in purged_headers:
                prepared_request.headers.pop(header, None)
            prepared_request.body = None

        # Header and cookie handling
        headers = prepared_request.headers
        # Always drop explicit Cookie header prior to merging cookies
        headers.pop("Cookie", None)

        # Extract cookies from the response into the new request's cookiejar
        extract_cookies_to_jar(prepared_request._cookies, req, resp.raw)
        merge_cookies(prepared_request._cookies, session.cookies)
        prepared_request.prepare_cookies(prepared_request._cookies)

        # Rebuild auth and proxy information.
        proxies = session.rebuild_proxies(prepared_request, proxies)
        session.rebuild_auth(prepared_request, resp)

        # Attempt to rewind consumed file-like object if needed
        rewindable = prepared_request._body_position is not None and (
            "Content-Length" in headers or "Transfer-Encoding" in headers
        )
        if rewindable:
            rewind_body(prepared_request)

        # Override the original request
        req = prepared_request

        if yield_requests:
            yield req
        else:
            resp = session.send(
                req,
                stream=stream,
                timeout=timeout,
                verify=verify,
                cert=cert,
                proxies=proxies,
                allow_redirects=False,
                **adapter_kwargs,
            )

            extract_cookies_to_jar(session.cookies, prepared_request, resp.raw)

            url = get_redirect_target(resp)
            yield resp

