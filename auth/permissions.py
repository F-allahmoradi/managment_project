"""بررسی مجوز ریز از زنجیره user_roles → role_permissions → permissions."""

from repository import user_has_permission_record


def user_has_permission(user_id: int, resource: str, action: str) -> bool:
    """اگر کاربر از طریق نقش فعال، این Resource/Action را داشته باشد True است."""
    return user_has_permission_record(user_id, resource, action)


def is_director(user_id: int) -> bool:
    """مدیر کل با UserRole/Create همهٔ پروژه‌ها را می‌بیند."""
    return user_has_permission(user_id, "UserRole", "Create")


def is_org_manager(user_id: int) -> bool:
    """مدیر سازمان (نقش سیستمی مدیر پروژه) اعضای پروژهٔ خودش را می‌چیند."""
    return user_has_permission(user_id, "ProjectMember", "Update")
