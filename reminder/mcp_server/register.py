"""ثبت ابزارهای تعریف و ارسال یادآوری روی سرور MCP."""

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer
from mcp_server.tools.dispatch.retry_reminder import (
    register as register_retry_reminder,
)
from mcp_server.tools.dispatch.send_reminder import (
    register as register_send_reminder,
)
from mcp_server.tools.execution_log.list_execution_logs import (
    register as register_list_execution_logs,
)
from mcp_server.tools.follow_up_state.list_follow_up_states import (
    register as register_list_follow_up_states,
)
from mcp_server.tools.reminder.create_reminder import (
    register as register_create_reminder,
)
from mcp_server.tools.reminder.get_reminder import register as register_get_reminder
from mcp_server.tools.reminder.list_reminders import (
    register as register_list_reminders,
)
from mcp_server.tools.reminder.update_reminder import (
    register as register_update_reminder,
)


def register_reminder_tools(mcp: MCPServer) -> None:
    """ابزارهای تعریف و ارسال یادآوری را روی سرور ثبت می‌کند."""
    setup_logging()
    register_create_reminder(mcp)
    register_get_reminder(mcp)
    register_list_reminders(mcp)
    register_update_reminder(mcp)
    register_list_follow_up_states(mcp)
    register_send_reminder(mcp)
    register_retry_reminder(mcp)
    register_list_execution_logs(mcp)
