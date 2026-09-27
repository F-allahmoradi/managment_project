"""بررسی مجوز ریز از زنجیره user_roles → role_permissions → permissions."""

from repository import user_has_permission_record


def user_has_permission(user_id: int, resource: str, action: str) -> bool:
    """اگر کاربر از طریق نقش فعال، این Resource/Action را داشته باشد True است."""
    return user_has_permission_record(user_id, resource, action)
