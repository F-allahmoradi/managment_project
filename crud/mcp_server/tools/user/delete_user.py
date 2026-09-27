"""ابزار MCP برای حذف یک کاربر از users.

تک‌منظوره است: فقط DELETE یک ردیف موجود. ساخت، خواندن، ویرایش، نقش
و پروژه در این فایل نیست.
"""

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool, register_id_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import DELETE_USER
from mcp_server.metadata import DESTRUCTIVE_CRUD, TITLE_DELETE_USER
from services.user import delete_user
from validators.user import validate_delete_user


@run_tool("delete_user")
def run_delete_user(id: int) -> dict:
    """مسیر کامل حذف کاربر را بدون دکوراتور MCP اجرا می‌کند.

    ورودی:
        id: شناسه کاربر در users.
    خروجی:
        دیکشنری موفقیت {status, id, message} یا پاکت خطا.
    فراخوانی‌ها:
        validate_delete_user، delete_user، format_success یا format_error،
        logged_tool.
    علت جدا بودن از دکوراتور:
        تست می‌تواند همین تابع را بدون بالا آوردن پروتکل MCP صدا بزند.
    """
    actor = require_permission("User", "Delete")
    user_id = validate_delete_user(id)
    deleted_id = delete_user(user_id, actor_id=actor["id"])
    return format_success("کاربر حذف شد", id=deleted_id)


def register(mcp: MCPServer) -> None:
    """ابزار delete_user را روی نمونه سرور ثبت می‌کند.

    ورودی:
        mcp: سرور ساخته‌شده در server.py.
    خروجی:
        هیچ. اثر جانبی ثبت ابزار روی mcp است.
    فراخوانی‌ها:
        mcp.tool با annotations نوشتنی مخرب، و run_delete_user.
    """
    register_id_tool(
        mcp,
        run_delete_user,
        name="delete_user",
        title=TITLE_DELETE_USER,
        description=DELETE_USER,
        annotations=DESTRUCTIVE_CRUD,
    )
