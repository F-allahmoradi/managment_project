"""ثبت ابزارهای آمار فقط‌خواندنی روی سرور MCP.

هیچ ابزار نوشتنی در این گام ثبت نمی‌شود.
"""

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer
from mcp_server.tools.communication.get_message_type_counts import (
    register as register_get_message_type_counts,
)
from mcp_server.tools.finance.get_project_costs import (
    register as register_get_project_costs,
)
from mcp_server.tools.finance.get_transaction_summary import (
    register as register_get_transaction_summary,
)
from mcp_server.tools.follow_up.get_follow_up_counts import (
    register as register_get_follow_up_counts,
)
from mcp_server.tools.follow_up.get_repeated_follow_ups import (
    register as register_get_repeated_follow_ups,
)
from mcp_server.tools.member.get_member_workload import (
    register as register_get_member_workload,
)
from mcp_server.tools.member.list_members_needing_attention import (
    register as register_list_members_needing_attention,
)
from mcp_server.tools.performance.get_member_scores import (
    register as register_get_member_scores,
)
from mcp_server.tools.performance.get_performance_dashboard import (
    register as register_get_performance_dashboard,
)
from mcp_server.tools.project.get_project_health import (
    register as register_get_project_health,
)
from mcp_server.tools.project.get_project_progress import (
    register as register_get_project_progress,
)
from mcp_server.tools.project.list_at_risk_projects import (
    register as register_list_at_risk_projects,
)
from mcp_server.tools.reminder.get_delivery_stats import (
    register as register_get_delivery_stats,
)
from mcp_server.tools.task.get_overdue_tasks import (
    register as register_get_overdue_tasks,
)
from mcp_server.tools.task.get_task_completion_stats import (
    register as register_get_task_completion_stats,
)
from mcp_server.tools.task.get_task_status_breakdown import (
    register as register_get_task_status_breakdown,
)


def register_stats_tools(mcp: MCPServer) -> None:
    """ابزارهای داشبورد فقط‌خواندنی را روی سرور ثبت می‌کند."""
    setup_logging()
    register_get_project_progress(mcp)
    register_get_project_health(mcp)
    register_list_at_risk_projects(mcp)
    register_get_overdue_tasks(mcp)
    register_get_task_status_breakdown(mcp)
    register_get_task_completion_stats(mcp)
    register_get_member_workload(mcp)
    register_list_members_needing_attention(mcp)
    register_get_follow_up_counts(mcp)
    register_get_repeated_follow_ups(mcp)
    register_get_message_type_counts(mcp)
    register_get_member_scores(mcp)
    register_get_performance_dashboard(mcp)
    register_get_project_costs(mcp)
    register_get_transaction_summary(mcp)
    register_get_delivery_stats(mcp)
