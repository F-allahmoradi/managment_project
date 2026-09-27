"""ابزار MCP برای فهرست کاربران جدول users.

تک‌منظوره است: فقط SELECT چند ردیف با صفحه‌بندی. خواندن تکی، ویرایش،
حذف، نقش و پروژه در این فایل نیست.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_page_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import LIST_USERS
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_LIST_USERS
from services.user import fetch_users
from validators.user import validate_list_users


@run_tool("list_users")
def run_list_users(limit: int = 10, offset: int = 0) -> dict:
    """مسیر کامل فهرست کاربران را بدون دکوراتور MCP اجرا می‌کند.

    ورودی:
        limit: تعداد رکورد؛ پیش‌فرض ۱۰، سقف ۵۰.
        offset: جابه‌جایی؛ پیش‌فرض ۰.
    خروجی:
        دیکشنری موفقیت {status, message, records, limit, offset} یا پاکت خطا.
        هیچ ردیفی password_hash ندارد.
    فراخوانی‌ها:
        validate_list_users، fetch_users، format_success یا format_error،
        logged_tool.
    علت جدا بودن از دکوراتور:
        تست می‌تواند همین تابع را بدون بالا آوردن پروتکل MCP صدا بزند.
    """
    require_permission("User", "Read")
    parsed_limit, parsed_offset = validate_list_users(
        limit=limit,
        offset=offset,
    )
    records = fetch_users(parsed_limit, parsed_offset)
    return format_success(
        "کاربران فهرست شدند",
        records=records,
        limit=parsed_limit,
        offset=parsed_offset,
    )


def register(mcp: MCPServer) -> None:
    """ابزار list_users را روی نمونه سرور ثبت می‌کند.

    ورودی:
        mcp: سرور ساخته‌شده در server.py.
    خروجی:
        هیچ. اثر جانبی ثبت ابزار روی mcp است.
    فراخوانی‌ها:
        mcp.tool با annotations فقط‌خواندنی، و run_list_users.
    """
    register_page_tool(
        mcp,
        run_list_users,
        name="list_users",
        title=TITLE_LIST_USERS,
        description=LIST_USERS,
        annotations=READ_ONLY_CRUD,
    )
