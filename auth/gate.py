"""دروازهٔ نازک Resource/Action برای ابزارهای MCP.

مجوز سراسری از نقش سیستم می‌آید. محدودهٔ پروژه در auth/scope.py
است: کدام پروژه را کاربر عضو فعال‌ش می‌بیند یا عوض می‌کند.
"""

from logging_module import logged_step

from auth.errors import ActorNotFoundError, PermissionDeniedError
from auth.permissions import user_has_permission
from auth.principal import resolve_actor
from auth.scope import require_active_project_member, require_chat_member

__all__ = [
    "require_permission",
    "require_project_permission",
    "require_active_actor",
    "try_actor_id",
    "require_active_project_member",
    "require_chat_member",
]


def require_active_actor() -> dict:
    """کاربر جاری را اگر فعال باشد برمی‌گرداند؛ مجوز Resource/Action نمی‌خواهد.

    اعلان داخل پنل فقط مال خود همان کاربر است؛ نقش جدا برای خواندن
    صندوق اعلان لازم نیست.
    """
    actor = resolve_actor()
    if not actor["is_active"]:
        raise PermissionDeniedError("حساب کاربر جاری غیرفعال است")
    return actor


def try_actor_id():
    """شناسه بازیگر جاری را اگر محیط تنظیم باشد برمی‌گرداند، وگرنه None."""
    try:
        actor = resolve_actor()
    except (PermissionDeniedError, ActorNotFoundError):
        return None
    if not actor["is_active"]:
        return None
    return actor["id"]


def require_permission(resource: str, action: str) -> dict:
    """اگر کاربر جاری مجوز را نداشته باشد خطا می‌دهد.

    ورودی:
        resource: مثل User یا Project.
        action: مثل Create یا Read.
    خروجی:
        دیکشنری بازیگر جاری در صورت مجاز بودن.
    فراخوانی‌ها:
        resolve_actor، user_has_permission.
    علت:
        ابزارها بعد از وصل شدن نقش نباید باز بمانند.
    خطاها:
        PERMISSION_DENIED اگر بازیگر نباشد، غیرفعال باشد، یا مجوز نباشد.
        ACTOR_NOT_FOUND اگر متغیر محیط به کاربر ناموجود اشاره کند.
    """
    actor = resolve_actor()
    if not actor["is_active"]:
        raise PermissionDeniedError("حساب کاربر جاری غیرفعال است")
    if not user_has_permission(actor["id"], resource, action):
        raise PermissionDeniedError(
            f"مجوز {resource}/{action} برای این کاربر نیست"
        )
    return actor


def require_project_permission(
    resource: str,
    action: str,
    project_id: int,
) -> dict:
    """مجوز سراسری و عضویت فعال در همان پروژه را با هم می‌سنجد.

    ورودی:
        resource: مثل Project یا ProjectMember.
        action: مثل Read یا Update.
        project_id: شناسه پروژه هدف.
    خروجی:
        دیکشنری بازیگر جاری در صورت مجاز بودن.
    فراخوانی‌ها:
        require_permission، require_active_project_member.
    علت:
        محمد با Project/Update فقط پروژهٔ خودش را عوض کند.
    """
    actor = require_permission(resource, action)
    require_active_project_member(actor["id"], project_id)
    return actor


require_active_actor = logged_step("authorize")(require_active_actor)
require_permission = logged_step("authorize")(require_permission)
require_project_permission = logged_step("authorize")(require_project_permission)
