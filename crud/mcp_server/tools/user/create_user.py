"""ابزار MCP برای ثبت یک کاربر جدید در users.

تک‌منظوره است: فقط INSERT. خواندن، ویرایش، حذف، نقش و پروژه در این فایل نیست.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_USER
from mcp_server.metadata import TITLE_CREATE_USER, WRITE_CRUD
from services.user import insert_user
from validators.user import validate_create_user


@run_tool("create_user")
def run_create_user(**fields) -> dict:
    """مسیر کامل ثبت کاربر را بدون دکوراتور MCP اجرا می‌کند.

    ورودی:
        fields: همان فیلدهای CreateUserInput به‌صورت kwargs.
    خروجی:
        دیکشنری موفقیت {status, id, message} یا پاکت خطا.
    فراخوانی‌ها:
        validate_create_user، insert_user، format_success یا format_error،
        logged_tool.
    علت جدا بودن از دکوراتور:
        تست می‌تواند همین تابع را بدون بالا آوردن پروتکل MCP صدا بزند.
    """
    actor = require_permission("User", "Create")
    parsed = validate_create_user(fields)
    new_id = insert_user(parsed, actor_id=actor["id"])
    return format_success("کاربر ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_user را روی نمونه سرور ثبت می‌کند.

    ورودی:
        mcp: سرور ساخته‌شده در server.py.
    خروجی:
        هیچ. اثر جانبی ثبت ابزار روی mcp است.
    فراخوانی‌ها:
        mcp.tool با annotations نوشتنی، و run_create_user.
    """

    @mcp.tool(
        name="create_user",
        title=TITLE_CREATE_USER,
        description=CREATE_USER,
        annotations=WRITE_CRUD,
    )
    def create_user(
        first_name: str,
        last_name: str,
        username: str,
        password: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        is_active: bool = True,
    ) -> dict:
        """ابزار MCP: یک کاربر جدید در users درج می‌کند.

        ورودی ابزار:
            فیلدهای CreateUserInput؛ password_hash از کلاینت نیست.
        خروجی ابزار:
            دیکشنری {status, id, message} یا پاکت خطا با error_code.
        فراخوانی‌ها:
            run_create_user.
        """
        return run_create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            phone=phone,
            email=email,
            is_active=is_active,
        )
