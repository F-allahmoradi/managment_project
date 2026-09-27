"""خطاهای معنایی لایه CRUD با کد پایدار برای پاسخ JSON.

هر کلاس یک error_code ثابت دارد تا ابزار MCP به‌جای متن خام،
کد قابل‌اتکا مثل USER_NOT_FOUND برگرداند. پیام برای انسان است؛
کد برای کلاینت.
"""

from pydantic import ValidationError
import psycopg2
from psycopg2.errors import QueryCanceled

INVALID_INPUT = "INVALID_INPUT"
USER_NOT_FOUND = "USER_NOT_FOUND"
ROLE_NOT_FOUND = "ROLE_NOT_FOUND"
PERMISSION_NOT_FOUND = "PERMISSION_NOT_FOUND"
USER_ROLE_NOT_FOUND = "USER_ROLE_NOT_FOUND"
ROLE_PERMISSION_NOT_FOUND = "ROLE_PERMISSION_NOT_FOUND"
PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
PROJECT_MEMBER_NOT_FOUND = "PROJECT_MEMBER_NOT_FOUND"
TASK_NOT_FOUND = "TASK_NOT_FOUND"
TASK_ITEM_NOT_FOUND = "TASK_ITEM_NOT_FOUND"
TASK_FOLLOW_UP_NOT_FOUND = "TASK_FOLLOW_UP_NOT_FOUND"
EXTERNAL_CONTACT_NOT_FOUND = "EXTERNAL_CONTACT_NOT_FOUND"
CHAT_NOT_FOUND = "CHAT_NOT_FOUND"
CHAT_MEMBER_NOT_FOUND = "CHAT_MEMBER_NOT_FOUND"
MESSAGE_NOT_FOUND = "MESSAGE_NOT_FOUND"
MESSAGE_RECIPIENT_NOT_FOUND = "MESSAGE_RECIPIENT_NOT_FOUND"
NOTIFICATION_NOT_FOUND = "NOTIFICATION_NOT_FOUND"
AUDIT_LOG_NOT_FOUND = "AUDIT_LOG_NOT_FOUND"
PERFORMANCE_ACTION_NOT_FOUND = "PERFORMANCE_ACTION_NOT_FOUND"
CONTENT_NOT_FOUND = "CONTENT_NOT_FOUND"
TEXT_ANALYSIS_NOT_FOUND = "TEXT_ANALYSIS_NOT_FOUND"
ISSUE_NOT_FOUND = "ISSUE_NOT_FOUND"
PERMISSION_DENIED = "PERMISSION_DENIED"
ACTOR_NOT_FOUND = "ACTOR_NOT_FOUND"
QUERY_TIMEOUT = "QUERY_TIMEOUT"
DATABASE_ERROR = "DATABASE_ERROR"


class CrudError(Exception):
    """پایه تمام خطاهای پیش‌بینی‌شده CRUD.

    ورودی:
        message: توضیح خوانا برای فیلد message در JSON.
    خروجی:
        Exception با attributeهای error_code و message.
    فراخوانی‌ها:
        هیچ؛ فقط والد است.
    علت:
        format_error با isinstance روی همین کلاس کد را برمی‌دارد.
    """

    error_code = DATABASE_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidInputError(CrudError):
    """ورودی نامعتبر است؛ مثلاً رشته خالی یا فیلد اجباری نیست.

    ورودی: توضیح فیلد و مقدار مشکل‌دار.
    خروجی: خطا با کد INVALID_INPUT؛ کوئری زده نمی‌شود.
    """

    error_code = INVALID_INPUT


class UserNotFoundError(CrudError):
    """کاربر با شناسه داده‌شده در users نیست.

    ورودی: توضیح شناسه پیدا‌نشده.
    خروجی: خطا با کد USER_NOT_FOUND.
    """

    error_code = USER_NOT_FOUND


class RoleNotFoundError(CrudError):
    """نقش با شناسه داده‌شده در roles نیست."""

    error_code = ROLE_NOT_FOUND


class PermissionNotFoundError(CrudError):
    """مجوز با شناسه داده‌شده در permissions نیست."""

    error_code = PERMISSION_NOT_FOUND


class UserRoleNotFoundError(CrudError):
    """اتصال کاربر-نقش با شناسه داده‌شده نیست."""

    error_code = USER_ROLE_NOT_FOUND


class RolePermissionNotFoundError(CrudError):
    """اتصال نقش-مجوز با شناسه داده‌شده نیست."""

    error_code = ROLE_PERMISSION_NOT_FOUND


class ProjectNotFoundError(CrudError):
    """پروژه با شناسه داده‌شده در projects نیست."""

    error_code = PROJECT_NOT_FOUND


class ProjectMemberNotFoundError(CrudError):
    """عضویت با شناسه داده‌شده در project_members نیست."""

    error_code = PROJECT_MEMBER_NOT_FOUND


class TaskNotFoundError(CrudError):
    """وظیفه با شناسه داده‌شده در tasks نیست."""

    error_code = TASK_NOT_FOUND


class TaskItemNotFoundError(CrudError):
    """زیرکار با شناسه داده‌شده در task_items نیست."""

    error_code = TASK_ITEM_NOT_FOUND


class TaskFollowUpNotFoundError(CrudError):
    """پیگیری با شناسه داده‌شده در task_follow_ups نیست."""

    error_code = TASK_FOLLOW_UP_NOT_FOUND


class ExternalContactNotFoundError(CrudError):
    """مخاطب خارجی با شناسه داده‌شده در external_contacts نیست."""

    error_code = EXTERNAL_CONTACT_NOT_FOUND


class ChatNotFoundError(CrudError):
    """گفتگو با شناسه داده‌شده در chats نیست."""

    error_code = CHAT_NOT_FOUND


class ChatMemberNotFoundError(CrudError):
    """عضویت با شناسه داده‌شده در chat_members نیست."""

    error_code = CHAT_MEMBER_NOT_FOUND


class MessageNotFoundError(CrudError):
    """پیام با شناسه داده‌شده در messages نیست."""

    error_code = MESSAGE_NOT_FOUND


class MessageRecipientNotFoundError(CrudError):
    """گیرنده با شناسه داده‌شده در message_recipients نیست."""

    error_code = MESSAGE_RECIPIENT_NOT_FOUND


class NotificationNotFoundError(CrudError):
    """اعلان با شناسه داده‌شده در notifications نیست."""

    error_code = NOTIFICATION_NOT_FOUND


class AuditLogNotFoundError(CrudError):
    """ردیف ممیزی با شناسه داده‌شده در audit_logs نیست."""

    error_code = AUDIT_LOG_NOT_FOUND


class PerformanceActionNotFoundError(CrudError):
    """اقدام تشویق یا تنبیه با شناسه داده‌شده در performance_actions نیست."""

    error_code = PERFORMANCE_ACTION_NOT_FOUND


class ContentNotFoundError(CrudError):
    """محتوا با شناسه داده‌شده در contents نیست."""

    error_code = CONTENT_NOT_FOUND


class TextAnalysisNotFoundError(CrudError):
    """تحلیل متن با شناسه داده‌شده در text_analyses نیست."""

    error_code = TEXT_ANALYSIS_NOT_FOUND


class IssueNotFoundError(CrudError):
    """مسئله با شناسه داده‌شده در issues نیست."""

    error_code = ISSUE_NOT_FOUND


class PermissionDeniedError(CrudError):
    """کاربر جاری مجوز resource/action لازم را ندارد."""

    error_code = PERMISSION_DENIED


class ActorNotFoundError(CrudError):
    """کاربر جاری MCP در users پیدا نشد."""

    error_code = ACTOR_NOT_FOUND


class QueryTimeoutError(CrudError):
    """کوئری از سقف ۱۰ ثانیه بیشتر طول کشید.

    ورودی: توضیح timeout.
    خروجی: خطا با کد QUERY_TIMEOUT.
    """

    error_code = QUERY_TIMEOUT


class DatabaseError(CrudError):
    """اتصال یا اجرای SQL شکست خورد.

    ورودی: پیام امن بدون جزئیات اتصال.
    خروجی: خطا با کد DATABASE_ERROR.
    """

    error_code = DATABASE_ERROR


def format_error(exc: BaseException) -> dict:
    """یک استثنا را به پاکت خطای JSON تبدیل می‌کند.

    ورودی:
        exc: خطای گرفته‌شده در ابزار یا سرویس.
    خروجی:
        دیکشنری {status, error_code, message} با status برابر error.
    فراخوانی‌ها:
        هیچ تابع دامنه؛ فقط isinstance روی نوع خطا.
    علت:
        ابزارها نباید هر کدام شکل JSON خطا را جدا بسازند.
    """
    if isinstance(exc, CrudError):
        return {
            "status": "error",
            "error_code": exc.error_code,
            "message": exc.message,
        }
    if isinstance(exc, ValidationError):
        return {
            "status": "error",
            "error_code": INVALID_INPUT,
            "message": str(exc),
        }
    if isinstance(exc, QueryCanceled) or isinstance(exc, QueryTimeoutError):
        return {
            "status": "error",
            "error_code": QUERY_TIMEOUT,
            "message": "زمان اجرای کوئری از ۱۰ ثانیه بیشتر شد",
        }
    if isinstance(exc, psycopg2.Error):
        return {
            "status": "error",
            "error_code": DATABASE_ERROR,
            "message": "اجرای کوئری در PostgreSQL ناموفق بود",
        }
    return {
        "status": "error",
        "error_code": DATABASE_ERROR,
        "message": "خطای پیش‌بینی‌نشده در عملیات CRUD",
    }


def format_success(message: str, **data) -> dict:
    """پاکت موفقیت JSON را با فیلدهای اضافه می‌سازد.

    ورودی:
        message: پیام خوانا.
        data: فیلدهای اختصاصی ابزار، مثل id یا records.
    خروجی:
        دیکشنری با status برابر success و بقیه کلیدها.
    فراخوانی‌ها:
        هیچ.
    علت:
        شکل موفقیت همهٔ ابزارها یکی بماند.
    """
    payload = {"status": "success", "message": message}
    payload.update(data)
    return payload
