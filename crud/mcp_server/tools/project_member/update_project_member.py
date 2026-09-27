"""ابزار MCP برای تغییر نقش داخل پروژه یا فعال/غیرفعال کردن عضویت."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import UPDATE_PROJECT_MEMBER
from mcp_server.metadata import TITLE_UPDATE_PROJECT_MEMBER, WRITE_CRUD
from services.project_member import fetch_project_member, update_project_member
from validators.project_member import validate_update_project_member


@run_tool("update_project_member")
def run_update_project_member(id: int, **fields) -> dict:
    """مسیر کامل به‌روزرسانی عضویت را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("ProjectMember", "Update")
    parsed = validate_update_project_member({"id": id, **fields})
    existing = fetch_project_member(parsed["id"])
    require_active_project_member(actor["id"], existing["project_id"])
    row_id = update_project_member(parsed, actor_id=actor["id"])
    return format_success("عضویت پروژه به‌روزرسانی شد", id=row_id)


def register(mcp: MCPServer) -> None:
    """ابزار update_project_member را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="update_project_member",
        title=TITLE_UPDATE_PROJECT_MEMBER,
        description=UPDATE_PROJECT_MEMBER,
        annotations=WRITE_CRUD,
    )
    def update_project_member_tool(
        id: int,
        project_role: Optional[str] = None,
        project_role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        """ابزار MCP: نقش داخل پروژه یا فعال بودن عضویت را عوض می‌کند."""
        return run_update_project_member(
            id=id,
            project_role=project_role,
            project_role_id=project_role_id,
            is_active=is_active,
        )
