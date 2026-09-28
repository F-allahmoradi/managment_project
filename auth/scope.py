"""محدودهٔ پروژه و گفتگو: کدام ردیف را کاربر جاری می‌بیند.

گام ۴ فقط Resource/Action سراسری را می‌سنجد. عضویت فعال در
project_members پروژه را محدود می‌کند. عضویت در chat_members
فهرست پیام را محدود می‌کند تا غیرعضو گفتگو پیام را نبیند.
"""

from logging_module import logged_step

from auth.permissions import is_director
from errors.crud import ChatNotFoundError, PermissionDeniedError, ProjectNotFoundError
from services.project import fetch_active_membership, project_exists


def require_active_project_member(user_id: int, project_id: int) -> dict:
    """اگر کاربر عضو فعال پروژه نباشد خطا می‌دهد.

    مدیر کل بدون عضویت هم به همهٔ پروژه‌ها راه دارد.
    """
    if is_director(user_id):
        if not project_exists(project_id):
            raise ProjectNotFoundError(f"پروژه با شناسه {project_id} پیدا نشد")
        return {
            "id": None,
            "project_id": project_id,
            "user_id": user_id,
            "project_role_id": None,
            "is_active": True,
        }
    membership = fetch_active_membership(project_id, user_id)
    if membership is not None:
        return membership
    if not project_exists(project_id):
        raise ProjectNotFoundError(f"پروژه با شناسه {project_id} پیدا نشد")
    raise PermissionDeniedError("عضو فعال این پروژه نیستید")


def require_chat_member(user_id: int, chat_id: int) -> dict:
    """اگر کاربر عضو گفتگو نباشد خطا می‌دهد.

    ورودی:
        user_id: شناسه کاربر جاری.
        chat_id: شناسه گفتگوی هدف.
    خروجی:
        دیکشنری عضویت در صورت مجاز بودن.
    فراخوانی‌ها:
        chat_exists، fetch_chat_membership.
    علت:
        مجوز Message/Read سراسری است؛ محدوده می‌گوید کدام چت.
    خطاها:
        CHAT_NOT_FOUND اگر گفتگو نباشد.
        PERMISSION_DENIED اگر عضو نباشد.
    """
    from services.chat import chat_exists, fetch_chat_membership

    membership = fetch_chat_membership(chat_id, user_id)
    if membership is not None:
        return membership
    if not chat_exists(chat_id):
        raise ChatNotFoundError(f"گفتگو با شناسه {chat_id} پیدا نشد")
    raise PermissionDeniedError("عضو این گفتگو نیستید")


require_active_project_member = logged_step("authorize")(
    require_active_project_member
)
require_chat_member = logged_step("authorize")(require_chat_member)
