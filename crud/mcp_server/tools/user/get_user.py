"""ابزار MCP برای خواندن یک کاربر با شناسه از users.

تک‌منظوره است: فقط SELECT یک ردیف. لیست، ویرایش، حذف، نقش و پروژه نیست.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import GET_USER
from mcp_server.metadata import READ_ONLY_CRUD, TITLE_GET_USER
from services.user import fetch_user
from validators.user import validate_get_user


@run_tool("get_user")
def run_get_user(id: int) -> dict:
    """مسیر کامل خواندن کاربر را بدون دکوراتور MCP اجرا می‌کند.

    ورودی:
        id: شناسه کاربر در users.
    خروجی:
        دیکشنری موفقیت {status, message, ...ستون‌های عمومی} یا پاکت خطا.
        password_hash در پاسخ نیست.
    فراخوانی‌ها:
        validate_get_user، fetch_user، format_success یا format_error،
        logged_tool.
    علت جدا بودن از دکوراتور:
        تست می‌تواند همین تابع را بدون بالا آوردن پروتکل MCP صدا بزند.
    """
    require_permission("User", "Read")
    user_id = validate_get_user(id)
    user = fetch_user(user_id)
    return format_success("کاربر خوانده شد", **user)


def register(mcp: MCPServer) -> None:
    """ابزار get_user را روی نمونه سرور ثبت می‌کند.

    ورودی:
        mcp: سرور ساخته‌شده در server.py.
    خروجی:
        هیچ. اثر جانبی ثبت ابزار روی mcp است.
    فراخوانی‌ها:
        mcp.tool با annotations فقط‌خواندنی، و run_get_user.
    """
    register_id_tool(
        mcp,
        run_get_user,
        name="get_user",
        title=TITLE_GET_USER,
        description=GET_USER,
        annotations=READ_ONLY_CRUD,
    )
