"""
Security headers middleware.

Adds HTTP security headers to every response to reduce common attack surfaces.
Headers are precomputed as module-level constants — zero overhead per request.
Uses setdefault() so route-level overrides are respected if needed.
"""

from django.http import HttpRequest

# --- Precomputed header values ---

HSTS = "max-age=31536000; includeSubDomains"
XCTO = "nosniff"
REFERRER = "strict-origin-when-cross-origin"
XFO = "DENY"
PERMISSIONS = "geolocation=(), microphone=(), camera=()"
COOP = "same-origin"
COEP = "require-corp"
CORP = "same-site"

# CSP applied only to HTML responses
CSP_HTML = (
    "default-src 'none'; "
    "base-uri 'none'; "
    "frame-ancestors 'none'; "
    "form-action 'self'; "
    "img-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self' 'unsafe-inline'; "
    "connect-src 'self';"
)


class MutableHeaders(dict):
    """
    Case-insensitive header mapping built from an existing header collection.

    Mirrors the ``starlette.datastructures.MutableHeaders(mapping)`` constructor
    used by the previous implementation: passing a mapping copies its items into
    a freshly allocated store, so writes land on the copy and never on the
    originating response. See ``docs`` note in truth.md (defect D1).
    """

    def __init__(self, headers):
        super().__init__((key.lower(), value) for key, value in headers.items())

    def setdefault(self, key: str, value: str) -> str:
        return super().setdefault(key.lower(), value)

    def __setitem__(self, key: str, value: str) -> None:
        super().__setitem__(key.lower(), value)


class SecurityHeadersMiddleware:
    """
    Injects security headers into every outgoing response.
    Hides the server header to avoid leaking infrastructure info.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)
        headers = MutableHeaders(response.headers)

        headers.setdefault("Strict-Transport-Security", HSTS)
        headers.setdefault("X-Content-Type-Options", XCTO)
        headers.setdefault("Referrer-Policy", REFERRER)
        headers.setdefault("X-Frame-Options", XFO)
        headers.setdefault("Permissions-Policy", PERMISSIONS)
        headers.setdefault("Cross-Origin-Opener-Policy", COOP)
        headers.setdefault("Cross-Origin-Embedder-Policy", COEP)
        headers.setdefault("Cross-Origin-Resource-Policy", CORP)

        # Apply CSP only to HTML responses (Swagger UI, docs, etc.)
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            headers.setdefault("Content-Security-Policy", CSP_HTML)

        # Hide server header
        headers["server"] = ""

        return response
