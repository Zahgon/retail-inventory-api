"""
Response helpers.

Every byte the API puts on the wire is produced here so the public contract
stays exactly what it has always been:

* JSON is rendered compactly — ``separators=(",", ":")``, no trailing newline,
  ``ensure_ascii=False`` and ``allow_nan=False``.
* The content type is a bare ``application/json`` with no ``charset``
  parameter, which is *not* what ``django.http.JsonResponse`` emits.
* ``Content-Length`` is written explicitly.  Responses that are not allowed to
  carry a body (1xx, 204 and 304) omit the header entirely but still advertise
  the content type, and empty-body redirects report ``Content-Length: 0``.
* Headers are emitted in the order the API has always emitted them: any
  route-specific header first, then ``Content-Length``, then ``Content-Type``.
  Header order is part of the bytes on the wire, so the response is assembled
  in that sequence rather than in the order Django happens to produce.
"""

import json
from typing import Any, Mapping, Optional

from django.http import HttpResponse

JSON_MEDIA_TYPE = "application/json"


def _body_allowed(status_code: int) -> bool:
    """Whether a response with this status code may carry a body."""
    return not (status_code < 200 or status_code in (204, 304))


def render_json(content: Any) -> bytes:
    """Serialise ``content`` the way the API has always serialised it."""
    return json.dumps(
        content,
        ensure_ascii=False,
        allow_nan=False,
        indent=None,
        separators=(",", ":"),
    ).encode("utf-8")


def json_response(
    content: Any,
    status_code: int = 200,
    headers: Optional[Mapping[str, str]] = None,
) -> HttpResponse:
    """Build a JSON response with the project's exact wire format."""
    if _body_allowed(status_code):
        body = render_json(content)
    else:
        body = b""

    response = HttpResponse(body, status=status_code, content_type=JSON_MEDIA_TYPE)
    del response["Content-Type"]
    for name, value in (headers or {}).items():
        response[name] = value
    if _body_allowed(status_code):
        response["Content-Length"] = str(len(body))
    response["Content-Type"] = JSON_MEDIA_TYPE
    return response


def no_content_response() -> HttpResponse:
    """204 response: content type advertised, no body and no Content-Length."""
    return json_response(None, 204)


def not_found_response() -> HttpResponse:
    """The response returned when no route matches the request path."""
    return json_response({"detail": "Not Found"}, 404)


def method_not_allowed_response(allow: str) -> HttpResponse:
    """The response returned when a path matches but the method does not."""
    return json_response({"detail": "Method Not Allowed"}, 405, {"Allow": allow})


def temporary_redirect_response(request, location: str) -> HttpResponse:
    """
    307 redirect to an absolute URL, preserving the query string.

    A 307 (rather than Django's 301) is what keeps the method and body of the
    original request intact, which is what clients of this API rely on when
    they omit or add a trailing slash.
    """
    query_string: Optional[str] = request.META.get("QUERY_STRING")
    target = f"{location}?{query_string}" if query_string else location

    response = HttpResponse(b"", status=307)
    del response["Content-Type"]
    response["Content-Length"] = "0"
    response["Location"] = request.build_absolute_uri(target)
    return response
