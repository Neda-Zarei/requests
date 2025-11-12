import io

import requests


def test_HTTP_308_ALLOW_REDIRECT_POST_with_body_preserved(httpbin):
    # Similar to existing 307 tests but for 308
    byte_str = b"test-308"
    r = requests.post(
        httpbin("redirect-to"),
        data=io.BytesIO(byte_str),
        params={"url": "post", "status_code": 308},
    )
    assert r.status_code == 200
    assert r.history[0].status_code == 308
    assert r.history[0].is_redirect
    assert r.json()["data"] == byte_str.decode("utf-8")


def test_HTTP_303_rewrite_to_get(httpbin):
    # Ensure 303 always rewrites to GET regardless of original method
    r = requests.put(httpbin("status", "303"))
    assert r.status_code == 200
    assert r.request.method == "GET"
    assert r.history[0].status_code == 303
    assert r.history[0].is_redirect

