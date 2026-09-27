"""خطاهای دروازهٔ دسترسی؛ تعریف اصلی در لایه CRUD است."""

from errors.crud import (
    ACTOR_NOT_FOUND,
    PERMISSION_DENIED,
    ActorNotFoundError,
    PermissionDeniedError,
)

__all__ = [
    "ACTOR_NOT_FOUND",
    "PERMISSION_DENIED",
    "ActorNotFoundError",
    "PermissionDeniedError",
]
