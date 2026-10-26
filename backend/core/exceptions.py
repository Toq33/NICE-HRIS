"""Standardized API error format per docs/04-api-and-integrations.md."""
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework.views import exception_handler


def standard_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, DjangoValidationError):
        return Response(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Validation failed.",
                    "details": exc.message_dict if hasattr(exc, "message_dict") else {"non_field_errors": exc.messages},
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, DjangoPermissionDenied):
        return Response(
            {
                "error": {
                    "code": "permission_denied",
                    "message": str(exc) or "You do not have permission to perform this action.",
                    "details": {},
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    response = exception_handler(exc, context)
    if response is not None:
        code = getattr(exc, "default_code", "api_error")
        if isinstance(response.data, dict) and "detail" in response.data:
            message = str(response.data["detail"])
            details = {k: v for k, v in response.data.items() if k != "detail"}
        else:
            message = "Request failed validation or authorization."
            details = response.data if isinstance(response.data, dict) else {"errors": response.data}

        if isinstance(exc, Throttled):
            wait_secs = int(exc.wait) if exc.wait else 60
            details["retry_after_seconds"] = wait_secs
            response["Retry-After"] = str(wait_secs)

        response.data = {
            "error": {
                "code": str(code),
                "message": message,
                "details": details,
            }
        }
    return response
