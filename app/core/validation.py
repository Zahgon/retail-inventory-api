"""
Request binding and validation.

Django hands a view the raw strings it captured from the path and the query
string and leaves the body untouched.  The public contract of this API, on the
other hand, is the pydantic v2 error payload the service has always returned:
a list of ``{"type", "loc", "msg", "input", "ctx"}`` dictionaries whose ``loc``
is prefixed with the origin of the value — ``"path"``, ``"query"`` or
``"body"``.

The helpers below reproduce that binding step exactly, including

* the order in which sources are validated (path, then query, then body) and
  the fact that *all* failures are reported in a single response;
* validating query parameters from their raw string, so that ``input`` in the
  error payload is the string the client actually sent (``"101"``, not ``101``);
* decoding the body as JSON only when the request carries no content type or an
  ``application/...json`` one, and passing the raw bytes to the model
  otherwise;
* the synthetic ``missing`` error used for an absent body or query parameter,
  which pydantic itself never produces because it is never asked to.
"""

import email.message
import json
from typing import Any, Dict, List, Optional

from pydantic import TypeAdapter, ValidationError

#: Sentinel meaning "this parameter has no default and is therefore required".
REQUIRED = object()

Errors = List[Dict[str, Any]]


class RequestValidationError(Exception):
    """
    Raised when request binding fails.

    Mirrors the interface the error handlers rely on: ``errors()`` returns the
    list of pydantic-shaped dictionaries that ends up under
    ``error.details.errors`` in the response body.
    """

    def __init__(self, errors: Errors) -> None:
        super().__init__(errors)
        self._errors = errors

    def errors(self) -> Errors:
        return self._errors


def _relocate(exception: ValidationError, prefix: tuple) -> Errors:
    """Re-root pydantic error locations under the source of the value."""
    return [
        {**error, "loc": prefix + tuple(error.get("loc", ()))}
        for error in exception.errors(include_url=False)
    ]


def _missing(loc: tuple) -> Dict[str, Any]:
    return {"type": "missing", "loc": loc, "msg": "Field required", "input": None}


def validate_path(errors: Errors, name: str, raw: str, adapter: TypeAdapter) -> Any:
    """Coerce a captured path segment, collecting any failure."""
    try:
        return adapter.validate_python(raw)
    except ValidationError as exception:
        errors.extend(_relocate(exception, ("path", name)))
        return None


def validate_query(
    errors: Errors,
    request,
    name: str,
    adapter: TypeAdapter,
    default: Any = REQUIRED,
) -> Any:
    """Coerce a query parameter, collecting any failure."""
    if name not in request.GET:
        if default is REQUIRED:
            errors.append(_missing(("query", name)))
            return None
        return default

    try:
        return adapter.validate_python(request.GET[name])
    except ValidationError as exception:
        errors.extend(_relocate(exception, ("query", name)))
        return None


def _read_body(request) -> Any:
    """
    Decode the request body the way the API has always decoded it.

    Returns ``None`` for an empty body, the parsed JSON document when the
    content type says JSON, and the raw bytes otherwise — which is what makes a
    ``text/plain`` body fail with ``model_attributes_type`` rather than with a
    JSON decode error.

    A missing content type is deliberately *not* treated as JSON. The body is
    only decoded when the request says it is JSON, so a caller that forgets the
    header gets the same rejection it has always received.
    """
    raw: bytes = request.body
    if not raw:
        return None

    content_type: Optional[str] = request.headers.get("content-type")
    if not content_type:
        return raw

    # Django joins repeated request headers into one comma-separated value,
    # whereas the previous framework read the first one and ignored the rest.
    # Only the first value decides the media type; a comma never appears before
    # the parameter separator of a single content type.
    content_type = content_type.split(",")[0]

    message = email.message.Message()
    message["content-type"] = content_type
    if message.get_content_maintype() == "application":
        subtype = message.get_content_subtype()
        if subtype == "json" or subtype.endswith("+json"):
            return json.loads(raw)
    return raw


def validate_body(errors: Errors, request, adapter: TypeAdapter) -> Any:
    """Decode and validate the request body, collecting any failure."""
    try:
        body = _read_body(request)
    except json.JSONDecodeError as exception:
        errors.append(
            {
                "type": "json_invalid",
                "loc": ("body", exception.pos),
                "msg": "JSON decode error",
                "input": {},
                "ctx": {"error": exception.msg},
            }
        )
        return None

    if body is None:
        errors.append(_missing(("body",)))
        return None

    try:
        return adapter.validate_python(body)
    except ValidationError as exception:
        errors.extend(_relocate(exception, ("body",)))
        return None


def raise_for_errors(errors: Errors) -> None:
    """Raise a single validation error carrying everything that went wrong."""
    if errors:
        raise RequestValidationError(errors)
