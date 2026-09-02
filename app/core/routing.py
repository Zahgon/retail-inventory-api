"""
Path and method dispatch.

Django's URL resolver matches on the path only, so the per-method behaviour of
the API is reproduced here.  The resolution order is the one this service has
always had:

1. exact path *and* method  -> the view runs;
2. exact path, other method, but a *later* route matches the same path with
   that method -> the later route runs.  This is why ``PATCH /products/search``
   is answered by the ``/products/{product_id}`` route (and reports ``search``
   as an unparseable identifier) instead of by a ``405``;
3. exact path, no route anywhere accepts the method -> ``405`` whose ``Allow``
   header names the methods of the **first** route registered for that path;
4. no path match, but the same path with the trailing slash added or removed
   does match -> ``307`` to that path;
5. otherwise -> ``404`` with the ``{"detail": "Not Found"}`` body.

Step 3 is why every ``405`` on ``/products/`` answers ``Allow: GET`` even though
that path also accepts ``POST``: each method was registered as its own route and
only the first one's method is advertised.  The documentation routes are the
exception -- they were registered once for both ``GET`` and ``HEAD``, so they
advertise both.
"""

from typing import Callable, Dict, Optional, Tuple

from django.urls import Resolver404, resolve

from .responses import (
    method_not_allowed_response,
    not_found_response,
    temporary_redirect_response,
)

Route = Tuple[str, Callable]
Fallthrough = Tuple[Callable, Dict[str, str]]


def route(
    *routes: Route,
    allow: Optional[str] = None,
    fallthrough: Optional[Fallthrough] = None,
) -> Callable:
    """
    Build a view that dispatches to the handler registered for the method.

    ``routes`` is given in registration order.  ``allow`` overrides the ``Allow``
    header for a path whose methods were registered as a single route rather than
    one route per method; when omitted the first entry's method is advertised.
    ``fallthrough`` names the ``(view, kwargs)`` a later route in the URL
    configuration matches for the same path, and is tried before giving up with a
    ``405``.
    """
    handlers = {method: handler for method, handler in routes}
    advertised = allow if allow is not None else routes[0][0]

    def dispatch(request, **kwargs):
        handler = handlers.get(request.method)
        if handler is None:
            if fallthrough is not None:
                later, later_kwargs = fallthrough
                return later(request, **later_kwargs)
            return method_not_allowed_response(advertised)
        return handler(request, **kwargs)

    dispatch.__name__ = routes[0][1].__name__
    dispatch.__doc__ = routes[0][1].__doc__
    return dispatch


def _path_exists(path: str) -> bool:
    """Whether any registered route matches ``path``, ignoring the method."""
    try:
        resolve(path)
    except Resolver404:
        return False
    return True


def not_found(request, exception=None):
    """
    Handler for unmatched paths, wired up as ``handler404`` in ``app.urls``.

    Before giving up it retries the request path with the trailing slash
    toggled, which is what turns ``POST /products/{id}/variants/`` into a 307
    towards ``POST /products/{id}/variants``.
    """
    path = request.path_info
    if path != "/":
        alternate = path.rstrip("/") if path.endswith("/") else path + "/"
        if alternate and _path_exists(alternate):
            return temporary_redirect_response(request, alternate)
    return not_found_response()
