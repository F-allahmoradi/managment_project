"""ابزار MCP برای افزودن شرکت‌کننده. قانون XOR مثل پیام."""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.participants import insert_participant
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import CREATE_MEETING_PARTICIPANT
from mcp_server.metadata import TITLE_CREATE_MEETING_PARTICIPANT, WRITE_MEETING
from validators.participant import validate_create_meeting_participant


@logged_tool("create_meeting_participant")
def run_create_meeting_participant(
    meeting_id: int,
    user_id: Optional[int] = None,
    external_contact_id: Optional[int] = None,
    role: Optional[str] = None,
) -> dict:
    """مسیر کامل افزودن شرکت‌کننده را بدون دکوراتور MCP اجرا می‌کند."""
    try:
        actor = require_permission("Meeting", "Update")
        parsed = validate_create_meeting_participant(
            {
                "meeting_id": meeting_id,
                "user_id": user_id,
                "external_contact_id": external_contact_id,
                "role": role,
            }
        )
        new_id = insert_participant(parsed, actor_id=actor["id"])
        return format_success("شرکت‌کننده جلسه ثبت شد", id=new_id)
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار create_meeting_participant را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_meeting_participant",
        title=TITLE_CREATE_MEETING_PARTICIPANT,
        description=CREATE_MEETING_PARTICIPANT,
        annotations=WRITE_MEETING,
    )
    def create_meeting_participant(
        meeting_id: int,
        user_id: Optional[int] = None,
        external_contact_id: Optional[int] = None,
        role: Optional[str] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف meeting_participants با قانون XOR درج می‌کند."""
        return run_create_meeting_participant(
            meeting_id=meeting_id,
            user_id=user_id,
            external_contact_id=external_contact_id,
            role=role,
        )
