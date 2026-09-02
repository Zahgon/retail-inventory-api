"""
Exception dispatch middleware.

Routes every exception escaping a view to the matching handler in
``app.core.errors.handlers``, reproducing the handler registration the previous
framework performed at application construction time:

    AppException             -> app_exception_handler
    RequestValidationError   -> validation_exception_handler
    Exception                -> generic_exception_handler

A handler that itself raises is re-dispatched to ``generic_exception_handler``,
which is what the previous framework's server-error layer did once the
request-level handler had failed.

That server-error layer also re-raised the exception once the 500 had been
written, so the exception reached the server itself.  Django's middleware
contract has no way to both answer and propagate, so the exception is parked on
the ASGI scope under ``SERVER_ERROR_KEY`` and re-raised by the ASGI entrypoint
in ``main`` after the response has been sent.
"""

from ..core.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from ..core.validation import RequestValidationError

SERVER_ERROR_KEY = "app.server_error"


class ExceptionHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, AppException):
            handler = app_exception_handler
        elif isinstance(exception, RequestValidationError):
            handler = validation_exception_handler
        else:
            return self._server_error(request, exception)

        try:
            return handler(request, exception)
        except Exception as handler_failure:
            return self._server_error(request, handler_failure)

    @staticmethod
    def _server_error(request, exception):
        scope = getattr(request, "scope", None)
        if scope is not None:
            scope[SERVER_ERROR_KEY] = exception
        return generic_exception_handler(request, exception)
