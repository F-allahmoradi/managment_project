"""اعتبارسنجی ورودی ابزارهای User.

ابزار MCP قبل از سرویس همین توابع را صدا می‌زند.
اسکیما در schemas/crud/user.py است تا مسیر tools → validators → services بماند.
"""

from logging_module import logged_step
from validators.common import parse_id, parse_page, writable_update


def validate_create_user(fields: dict) -> dict:
    """ورودی ثبت کاربر را با اسکیما بررسی می‌کند و دیکشنری تمیز برمی‌گرداند.

    ورودی:
        fields: فیلدهای خام ابزار MCP شامل password خام.
    خروجی:
        دیکشنری معتبر برای insert_user؛ هنوز شامل password خام است.
    فراخوانی‌ها:
        CreateUserInput.
    علت:
        ابزار نباید مستقیم اسکیما را صدا بزند.
        هش رمز کار سرویس است، نه اعتبارسنجی شکل ورودی.
    """
    from schemas.crud.user import CreateUserInput

    return CreateUserInput(**fields).model_dump()


def validate_get_user(user_id: int) -> int:
    """شناسه خواندن کاربر را با اسکیما بررسی می‌کند.

    ورودی:
        user_id: شناسه خام ابزار MCP.
    خروجی:
        شناسه معتبر برای fetch_user.
    فراخوانی‌ها:
        GetUserInput.
    علت:
        صفر، منفی، و بولین قبل از SELECT رد شوند.
    """
    from schemas.crud.user import GetUserInput

    return parse_id(GetUserInput, user_id)


def validate_list_users(limit=None, offset=None) -> tuple[int, int]:
    """صفحه‌بندی فهرست کاربران را با اسکیما بررسی می‌کند.

    ورودی:
        limit: تعداد رکورد خام یا None برای پیش‌فرض ۱۰.
        offset: جابه‌جایی خام یا None برای پیش‌فرض ۰.
    خروجی:
        تاپل (limit, offset) پس از اسکیما؛ سقف ۵۰ در خود مدل است.
    فراخوانی‌ها:
        ListUsersInput.
    علت:
        نوع غلط، بولین، حد منفی، و limit بالای ۵۰ قبل از SELECT رد شوند.
    """
    from schemas.crud.user import ListUsersInput

    return parse_page(ListUsersInput, limit=limit, offset=offset)


def validate_update_user(fields: dict) -> dict:
    """ورودی به‌روزرسانی کاربر را با اسکیما بررسی می‌کند.

    ورودی:
        fields: فیلدهای خام ابزار MCP شامل id و ستون‌های اختیاری.
    خروجی:
        دیکشنری {id, ...فیلدهای غیرتهی قابل‌نوشتن} برای update_user.
        اگر password آمده باشد هنوز خام است.
    فراخوانی‌ها:
        UpdateUserInput.
    علت:
        شناسه نامعتبر و نبود فیلد قابل‌نوشتن قبل از UPDATE رد شوند.
        password_hash از کلاینت برای تغییر نمی‌آید.
    """
    from schemas.crud.user import UpdateUserInput

    return writable_update(UpdateUserInput(**fields))


def validate_delete_user(user_id: int) -> int:
    """شناسه حذف کاربر را با اسکیما بررسی می‌کند.

    ورودی:
        user_id: شناسه خام ابزار MCP.
    خروجی:
        شناسه معتبر برای delete_user.
    فراخوانی‌ها:
        DeleteUserInput.
    علت:
        صفر، منفی، و بولین قبل از DELETE رد شوند.
    """
    from schemas.crud.user import DeleteUserInput

    return parse_id(DeleteUserInput, user_id)


validate_create_user = logged_step("validate")(validate_create_user)
validate_get_user = logged_step("validate")(validate_get_user)
validate_list_users = logged_step("validate")(validate_list_users)
validate_update_user = logged_step("validate")(validate_update_user)
validate_delete_user = logged_step("validate")(validate_delete_user)
