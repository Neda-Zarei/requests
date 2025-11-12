"""
Internal encoding helpers for Requests.

This module is internal-only. There are no stability guarantees for its API or
behavior. Use requests.utils for the public, supported interfaces.
"""

from __future__ import annotations

import codecs
import re
from typing import Generator, Iterable, Optional, Union

from ..compat import chardet

# Null bytes used by guess_json_utf; keep same semantics as utils.py
_null = "\x00".encode("ascii")
_null2 = _null * 2
_null3 = _null * 3


def _parse_content_type_header(header: str) -> tuple[str, dict[str, str]]:
    """Returns content type and parameters from given header.

    This is a verbatim copy of the helper used by requests.utils, kept
    private here to avoid circular imports and to keep encoding helpers
    self-contained.
    """

    tokens = header.split(";")
    content_type, params = tokens[0].strip(), tokens[1:]
    params_dict: dict[str, str] = {}
    items_to_strip = '"\' '

    for param in params:
        param = param.strip()
        if param:
            key, value: Union[str, bool] = param, True
            index_of_equals = param.find("=")
            if index_of_equals != -1:
                key = param[:index_of_equals].strip(items_to_strip)
                value = param[index_of_equals + 1 :].strip(items_to_strip)
            params_dict[key.lower()] = str(value)
    return content_type, params_dict


def get_encoding_from_headers(headers) -> Optional[str]:
    """Returns encodings from given HTTP Header Dict.

    :param headers: dictionary to extract encoding from.
    :rtype: str
    """

    content_type = headers.get("content-type")

    if not content_type:
        return None

    content_type, params = _parse_content_type_header(content_type)

    if "charset" in params:
        return params["charset"].strip("'\"")

    if "text" in content_type:
        return "ISO-8859-1"

    if "application/json" in content_type:
        # Assume UTF-8 based on RFC 4627: https://www.ietf.org/rfc/rfc4627.txt since the charset was unset
        return "utf-8"

    return None


def stream_decode_response_unicode(
    iterator: Iterable[bytes], r
) -> Generator[Union[str, bytes], None, None]:
    """Stream decodes an iterator.

    This mirrors the behavior previously in requests.utils.stream_decode_response_unicode.
    """

    if r.encoding is None:
        # Pass-through bytes if no encoding is set
        yield from iterator
        return

    decoder = codecs.getincrementaldecoder(r.encoding)(errors="replace")
    for chunk in iterator:
        rv = decoder.decode(chunk)
        if rv:
            yield rv
    rv = decoder.decode(b"", final=True)
    if rv:
        yield rv


def guess_json_utf(data: bytes) -> Optional[str]:
    """
    :rtype: str
    """
    # JSON always starts with two ASCII characters, so detection is as
    # easy as counting the nulls and from their location and count
    # determine the encoding. Also detect a BOM, if present.
    sample = data[:4]
    if sample in (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE):
        return "utf-32"  # BOM included
    if sample[:3] == codecs.BOM_UTF8:
        return "utf-8-sig"  # BOM included, MS style (discouraged)
    if sample[:2] in (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE):
        return "utf-16"  # BOM included
    nullcount = sample.count(_null)
    if nullcount == 0:
        return "utf-8"
    if nullcount == 2:
        if sample[::2] == _null2:  # 1st and 3rd are null
            return "utf-16-be"
        if sample[1::2] == _null2:  # 2nd and 4th are null
            return "utf-16-le"
        # Did not detect 2 valid UTF-16 ascii-range characters
    if nullcount == 3:
        if sample[:3] == _null3:
            return "utf-32-be"
        if sample[1:] == _null3:
            return "utf-32-le"
        # Did not detect a valid UTF-32 ascii-range character
    return None
