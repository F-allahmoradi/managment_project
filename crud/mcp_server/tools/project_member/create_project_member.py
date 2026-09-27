"""ابزار MCP برای افزودن عضو به یک پروژه.

نقش داده‌شده نقش داخل پروژه است (عضو، ناظر، مدیر پروژه)، نه نقش سیستم.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_active_project_member, require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_PROJECT_MEMBER
from mcp_server.metadata import TITLE_CREATE_PROJECT_MEMBER, WRITE_CRUD
from services.project_member import insert_project_member
from validators.project_member import validate_create_project_member


@run_tool("create_project_member")
def run_create_project_member(
    project_id: int,
    user_id: int,
    project_role: Optional[str] = None,
    project_role_id: Optional[int] = None,
) -> dict:
    """مسیر کامل افزودن عضو را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("ProjectMember", "Update")
    parsed = validate_create_project_member(
        {
            "project_id": project_id,
            "user_id": user_id,
            "project_role": project_role,
            "project_role_id": project_role_id,
        }
    )
    require_active_project_member(actor["id"], parsed["project_id"])
    new_id = insert_project_member(parsed, actor_id=actor["id"])
    return format_success("عضو به پروژه اضافه شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_project_member را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_project_member",
        title=TITLE_CREATE_PROJECT_MEMBER,
        description=CREATE_PROJECT_MEMBER,
        annotations=WRITE_CRUD,
    )
    def create_project_member(
        project_id: int,
        user_id: int,
        project_role: Optional[str] = None,
        project_role_id: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف project_members درج می‌کند."""
        return run_create_project_member(
            project_id=project_id,
            user_id=user_id,
            project_role=project_role,
            project_role_id=project_role_id,
        )
