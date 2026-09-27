"""ابزار MCP برای به‌روزرسانی یک کاربر در users.

تک‌منظوره است: فقط UPDATE یک ردیف موجود. ساخت کاربر جدید، حذف، نقش
و پروژه در این فایل نیست.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import UPDATE_USER
from mcp_server.metadata import TITLE_UPDATE_USER, WRITE_CRUD
from services.user import update_user
from validators.user import validate_update_user


@run_tool("update_user")
def run_update_user(id: int, **fields) -> dict:
    """مسیر کامل به‌روزرسانی کاربر را بدون دکوراتور MCP اجرا می‌کند.

    ورودی:
        id: شناسه کاربر در users.
        fields: فیلدهای اختیاری قابل‌نوشتن؛ None یعنی نیامده.
    خروجی:
        دیکشنری موفقیت {status, id, message} یا پاکت خطا.
    فراخوانی‌ها:
        validate_update_user، update_user، format_success یا format_error،
        logged_tool.
    علت جدا بودن از دکوراتور:
        تست می‌تواند همین تابع را بدون بالا آوردن پروتکل MCP صدا بزند.
    """
    actor = require_permission("User", "Update")
    parsed = validate_update_user({"id": id, **fields})
    user_id = update_user(parsed, actor_id=actor["id"])
    return format_success("کاربر به‌روزرسانی شد", id=user_id)


def register(mcp: MCPServer) -> None:
    """ابزار update_user را روی نمونه سرور ثبت می‌کند.

    ورودی:
        mcp: سرور ساخته‌شده در server.py.
    خروجی:
        هیچ. اثر جانبی ثبت ابزار روی mcp است.
    فراخوانی‌ها:
        mcp.tool با annotations نوشتنی غیرمخرب، و run_update_user.
    """

    @mcp.tool(
        name="update_user",
        title=TITLE_UPDATE_USER,
        description=UPDATE_USER,
        annotations=WRITE_CRUD,
    )
    def update_user_tool(
        id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        """ابزار MCP: یک کاربر موجود users را به‌روز می‌کند.

        ورودی ابزار:
            id اجباری؛ بقیه فیلدهای قابل‌نوشتن اختیاری‌اند.
            created_at و password_hash از کلاینت نیست.
        خروجی ابزار:
            دیکشنری {status, id, message} یا پاکت خطا با error_code.
        فراخوانی‌ها:
            run_update_user.
        """
        return run_update_user(
            id=id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            phone=phone,
            email=email,
            is_active=is_active,
        )
