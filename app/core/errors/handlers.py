"""
Defines custom exception handlers for the Django application,
including handling for application-specific exceptions and validation errors.
These handlers log the errors with relevant context and return standardized JSON responses to the client.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from ..responses import json_response
from ..validation import RequestValidationError
from . import AppException, ErrorDetail, ErrorResponse, ValidationException

logger = logging.getLogger(__name__)


def create_error_response(exception: AppException) -> Dict[str, Any]:
    """Helper function to create a standardized error response from an AppException."""
    response = ErrorResponse(
        error=ErrorDetail(
            code=exception.error_code,
            message=exception.message,
            timestamp=datetime.now(timezone.utc),
            details=exception.details,
        )
    )

    return response.model_dump(mode="json")


def app_exception_handler(request, exception: AppException):
    """Handle all custom application exceptions"""

    # Log the error with context and return JsonResponse
    logger.warning(
        f"Application error:{exception.error_code} - {exception.message}",
        extra={
            "error_code": exception.error_code,
            "status_code": exception.status_code,
            "path": request.path,
            "method": request.method,
            "details": exception.details,
        },
    )
    return json_response(
        status_code=exception.status_code,
        content=create_error_response(exception),
    )


def generic_exception_handler(request, exception: Exception):
    """Catch-all handler for unexpected exceptions"""

    # Log the error with context and return a generic JsonResponse
    logger.error(
        "Unexpected error",
        exc_info=exception,
        extra={
            "path": request.path,
            "method": request.method,
        },
    )
    return json_response(
        status_code=500,
        content=create_error_response(
            AppException(
                message="An unexpected error occurred",
                status_code=500,
                error_code="UNEXPECTED_ERROR",
            )
        ),
    )


def validation_exception_handler(request, exception: RequestValidationError):
    """Handle Pydantic/Django validation exceptions"""

    # log + return JsonResponse
    logger.warning(
        "Validation error",
        extra={
            "path": request.path,
            "method": request.method,
            "errors": exception.errors(),
        },
    )
    return json_response(
        status_code=422,
        content=create_error_response(
            ValidationException(details={"errors": exception.errors()})
        ),
    )
