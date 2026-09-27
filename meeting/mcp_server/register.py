"""ثبت ابزارهای جلسه روی سرور MCP.

ضبط و همگام‌سازی به پروژه در همین سرور است؛ contents در crud ساخته می‌شود.
"""

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer
from mcp_server.tools.generate_meetings.generate_meetings import (
    register as register_generate_meetings,
)
from mcp_server.tools.meeting.cancel_meeting import register as register_cancel_meeting
from mcp_server.tools.meeting.create_meeting import register as register_create_meeting
from mcp_server.tools.meeting.get_meeting import register as register_get_meeting
from mcp_server.tools.meeting.list_meetings import register as register_list_meetings
from mcp_server.tools.meeting.record_meeting import register as register_record_meeting
from mcp_server.tools.meeting.sync_meeting import register as register_sync_meeting
from mcp_server.tools.meeting_participant.create_meeting_participant import (
    register as register_create_meeting_participant,
)
from mcp_server.tools.meeting_schedule.create_meeting_schedule import (
    register as register_create_meeting_schedule,
)
from mcp_server.tools.meeting_schedule.get_meeting_schedule import (
    register as register_get_meeting_schedule,
)
from mcp_server.tools.meeting_schedule.list_meeting_schedules import (
    register as register_list_meeting_schedules,
)


def register_meeting_tools(mcp: MCPServer) -> None:
    """ابزارهای الگو، نمونه، شرکت‌کننده، تولید، ضبط و sync را ثبت می‌کند."""
    setup_logging()
    register_create_meeting_schedule(mcp)
    register_get_meeting_schedule(mcp)
    register_list_meeting_schedules(mcp)
    register_create_meeting(mcp)
    register_get_meeting(mcp)
    register_list_meetings(mcp)
    register_cancel_meeting(mcp)
    register_create_meeting_participant(mcp)
    register_generate_meetings(mcp)
    register_record_meeting(mcp)
    register_sync_meeting(mcp)
