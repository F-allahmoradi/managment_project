"""فهرست کاربرانی که سطح دسترسی‌شان تعیین می‌شود.

مدیر کل همهٔ کاربران فعال را می‌بیند تا مدیر سازمان بسازد.
مدیر پروژه فقط ثبت‌نام‌شده‌های نقش کاربر را می‌بیند تا به پروژه‌اش
اضافه کند. ساخت حساب اینجا نیست؛ ثبت‌نام خود کاربر است.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_page_tool

from auth.gate import require_active_actor
from auth.permissions import user_has_permission
from errors.crud import PermissionDeniedError, format_success
from mcp_server.docstrings import LIST_ASSIGNABLE_USERS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_ASSIGNABLE_USERS
from services.user import fetch_assignable_users
from validators.user import validate_list_users


@run_tool("list_assignable_users")
def run_list_assignable_users(limit: int = 10, offset: int = 0) -> dict:
    """مسیر کامل فهرست کاربران قابل‌تعیین‌دسترسی را اجرا می‌کند."""
    actor = require_active_actor()
    is_director = user_has_permission(actor["id"], "UserRole", "Create")
    can_staff = user_has_permission(actor["id"], "ProjectMember", "Update")
    if not is_director and not can_staff:
        raise PermissionDeniedError("مجوز دیدن افراد برای تعیین دسترسی نیست")
    parsed_limit, parsed_offset = validate_list_users(limit=limit, offset=offset)
    records = fetch_assignable_users(
        parsed_limit,
        parsed_offset,
        registered_only=not is_director,
    )
    return format_success(
        "افراد قابل تعیین دسترسی فهرست شدند",
        records=records,
        limit=parsed_limit,
        offset=parsed_offset,
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_assignable_users را روی نمونه سرور ثبت می‌کند."""
    register_page_tool(
        mcp,
        run_list_assignable_users,
        name="list_assignable_users",
        title=TITLE_LIST_ASSIGNABLE_USERS,
        description=LIST_ASSIGNABLE_USERS,
        annotations=READ_ONLY_CRUD,
    )
