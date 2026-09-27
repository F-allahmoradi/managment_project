"""کاربر جاری را برای ابزارها مشخص می‌کند.

درخواست HTTP شناسه را روی contextvar می‌گذارد تا هر درخواست کاربر خودش را
داشته باشد. سرور MCP هنوز از MCP_ACTOR_USER_ID و MCP_ACTOR_USERNAME می‌خواند.
اگر contextvar پر باشد، متغیر محیط نادیده گرفته می‌شود.
"""

from contextvars import ContextVar, Token
import os

from auth.errors import ActorNotFoundError, PermissionDeniedError
from repository import fetch_actor_record

_ACTOR_ID_ENV = "MCP_ACTOR_USER_ID"
_ACTOR_USERNAME_ENV = "MCP_ACTOR_USERNAME"
_request_actor_id: ContextVar[int | None] = ContextVar(
    "request_actor_user_id",
    default=None,
)


def set_request_actor(user_id: int) -> Token:
    """شناسه کاربر همین درخواست HTTP را تا پایان کار ابزار نگه می‌دارد."""
    if user_id < 1:
        raise PermissionDeniedError("شناسه کاربر جاری نامعتبر است")
    return _request_actor_id.set(user_id)


def reset_request_actor(token: Token) -> None:
    """contextvar بازیگر را به حالت قبل از این درخواست برمی‌گرداند."""
    _request_actor_id.reset(token)


def resolve_actor() -> dict:
    """کاربر جاری را از درخواست HTTP یا متغیر محیط به یک ردیف users تبدیل می‌کند."""
    override = _request_actor_id.get()
    if override is not None:
        return _fetch_actor(
            "id = %s",
            [override],
            f"کاربر جاری با شناسه {override} پیدا نشد",
        )
    raw_id = (os.environ.get(_ACTOR_ID_ENV) or "").strip()
    username = (os.environ.get(_ACTOR_USERNAME_ENV) or "").strip()
    if raw_id:
        try:
            actor_id = int(raw_id)
        except ValueError as exc:
            raise PermissionDeniedError("شناسه کاربر جاری نامعتبر است") from exc
        if actor_id < 1:
            raise PermissionDeniedError("شناسه کاربر جاری نامعتبر است")
        return _fetch_actor("id = %s", [actor_id], f"کاربر جاری با شناسه {actor_id} پیدا نشد")
    if username:
        return _fetch_actor(
            "username = %s",
            [username],
            f"کاربر جاری با نام کاربری {username} پیدا نشد",
        )
    raise PermissionDeniedError(
        "کاربر جاری تنظیم نشده است؛ MCP_ACTOR_USER_ID یا MCP_ACTOR_USERNAME لازم است"
    )


def _fetch_actor(where_sql: str, params: list, missing_message: str) -> dict:
    """یک ردیف users را برای بازیگر جاری می‌خواند."""
    row = fetch_actor_record(where_sql, params)
    if row is None:
        raise ActorNotFoundError(missing_message)
    return {"id": row["id"], "username": row["username"], "is_active": row["is_active"]}
