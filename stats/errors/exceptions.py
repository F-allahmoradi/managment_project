"""خطاهای دامنهٔ آمار؛ تعریف اصلی در errors.crud است."""

from errors.crud import (
    INVALID_INPUT,
    PERMISSION_DENIED,
    PROJECT_NOT_FOUND,
    QUERY_TIMEOUT,
    InvalidInputError,
    PermissionDeniedError,
    ProjectNotFoundError,
    QueryTimeoutError,
)

__all__ = [
    "INVALID_INPUT",
    "PERMISSION_DENIED",
    "PROJECT_NOT_FOUND",
    "QUERY_TIMEOUT",
    "InvalidInputError",
    "PermissionDeniedError",
    "ProjectNotFoundError",
    "QueryTimeoutError",
]
