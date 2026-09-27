"""ابزار MCP برای ثبت تشویق یا تنبیه روی کاربر.

امتیاز بدون مبلغ تراکنش نمی‌سازد. مبلغ بدون حساب رد می‌شود.
نوع از seed است؛ ابزار جدا برای نوع نیست.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_PERFORMANCE_ACTION
from mcp_server.metadata import TITLE_CREATE_PERFORMANCE_ACTION, WRITE_CRUD
from services.performance_action import insert_performance_action
from validators.performance_action import validate_create_performance_action


@run_tool("create_performance_action")
def run_create_performance_action(**fields) -> dict:
    """مسیر کامل ثبت اقدام عملکرد را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Performance", "Create")
    parsed = validate_create_performance_action(fields)
    if parsed.get("project_id") is not None:
        require_active_project_member(actor["id"], parsed["project_id"])
    new_id = insert_performance_action(parsed, created_by=actor["id"])
    return format_success("اقدام عملکرد ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_performance_action را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_performance_action",
        title=TITLE_CREATE_PERFORMANCE_ACTION,
        description=CREATE_PERFORMANCE_ACTION,
        annotations=WRITE_CRUD,
    )
    def create_performance_action(
        user_id: int,
        reason: str,
        action_type: Optional[str] = None,
        action_type_id: Optional[int] = None,
        project_id: Optional[int] = None,
        score: Optional[int] = None,
        amount: Optional[float] = None,
        account_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: تشویق یا تنبیه را درج می‌کند؛ امتیاز و تراکنش اثر جانبی‌اند."""
        return run_create_performance_action(
            user_id=user_id,
            reason=reason,
            action_type=action_type,
            action_type_id=action_type_id,
            project_id=project_id,
            score=score,
            amount=amount,
            account_id=account_id,
        )
