"""Internal multipart helpers for Requests.

This module is NOT part of the public API and may change without notice.
It provides the multipart/form-data assembly used by PreparedRequest.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

# We intentionally keep the urllib3 interaction isolated here to avoid
# leaking implementation details throughout requests.models.
try:
    from urllib3.fields import RequestField  # type: ignore
    from urllib3.filepost import (  # type: ignore
        choose_boundary as _urllib3_choose_boundary,
        encode_multipart_formdata as _urllib3_encode_multipart_formdata,
    )
except Exception:  # pragma: no cover - urllib3 is a hard dependency in tests
    RequestField = None  # type: ignore
    _urllib3_choose_boundary = None  # type: ignore
    _urllib3_encode_multipart_formdata = None  # type: ignore

from ..compat import basestring
from ..utils import guess_filename, to_key_val_list


def choose_multipart_boundary() -> str:
    """Return a multipart boundary string.

    Delegates to urllib3's boundary chooser to preserve semantics.
    """
    if _urllib3_choose_boundary is None:  # Fallback for unexpected import issues
        import uuid

        return uuid.uuid4().hex
    return _urllib3_choose_boundary()


def encode_multipart_formdata(
    data: Optional[Union[Dict[str, Any], Iterable[Tuple[str, Any]]]],
    files: Optional[Union[Dict[str, Any], Iterable[Tuple[str, Any]]]],
    boundary: Optional[str] = None,
) -> Tuple[bytes, str]:
    """Build the body for a multipart/form-data request.

    This mirrors the historical behavior in requests.models._encode_files
    and defers actual encoding to urllib3 to preserve exact formatting
    and header generation semantics.
    """
    if not files:
        raise ValueError("Files must be provided.")
    elif isinstance(data, basestring):
        raise ValueError("Data must not be a string.")

    new_fields: List[Any] = []
    fields = to_key_val_list(data or {})
    files_kv = to_key_val_list(files or {})

    # Normalize simple form fields
    for field, val in fields:
        if isinstance(val, basestring) or not hasattr(val, "__iter__"):
            val = [val]
        for v in val:
            if v is not None:
                # Don't call str() on bytes: in Py3 it all goes wrong.
                if not isinstance(v, bytes):
                    v = str(v)

                new_fields.append(
                    (
                        field.decode("utf-8") if isinstance(field, bytes) else field,
                        v.encode("utf-8") if isinstance(v, str) else v,
                    )
                )

    # Normalize file fields
    for k, v in files_kv:
        # support for explicit filename
        ft = None
        fh = None
        if isinstance(v, (tuple, list)):
            if len(v) == 2:
                fn, fp = v
            elif len(v) == 3:
                fn, fp, ft = v
            else:
                fn, fp, ft, fh = v
        else:
            fn = guess_filename(v) or k
            fp = v

        if isinstance(fp, (str, bytes, bytearray)):
            fdata = fp
        elif hasattr(fp, "read"):
            fdata = fp.read()
        elif fp is None:
            continue
        else:
            fdata = fp

        # Build a RequestField for urllib3 to encode
        rf = RequestField(name=k, data=fdata, filename=fn, headers=fh)
        rf.make_multipart(content_type=ft)
        new_fields.append(rf)

    if boundary is not None:
        body, content_type = _urllib3_encode_multipart_formdata(new_fields, boundary)
    else:
        body, content_type = _urllib3_encode_multipart_formdata(new_fields)

    return body, content_type
