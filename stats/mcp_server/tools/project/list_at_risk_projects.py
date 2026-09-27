"""ابزار MCP برای فهرست پروژه‌های در معرض تأخیر کاربر جاری."""

from mcp.server.mcpserver import MCPServer

from auth.gate import require_permission
from business_logic.analyst import at_risk_projects
from errors.crud import format_error, format_success
from logging_module import logged_tool
from mcp_server.docstrings import LIST_AT_RISK_PROJECTS
from mcp_server.metadata import READ_ONLY_STATS, TITLE_LIST_AT_RISK_PROJECTS
from schemas.input import validate_pagination


@logged_tool("list_at_risk_projects")
def run_list_at_risk_projects(limit: int = 10, offset: int = 0) -> dict:
    """مسیر کامل فهرست پروژه‌های در معرض تأخیر را اجرا می‌کند."""
    try:
        actor = require_permission("Project", "Read")
        parsed = validate_pagination(limit=limit, offset=offset)
        records = at_risk_projects(actor["id"], parsed["limit"], parsed["offset"])
        return format_success(
            "پروژه‌های در معرض تأخیر فهرست شدند",
            records=records,
            limit=parsed["limit"],
            offset=parsed["offset"],
        )
    except Exception as exc:
        return format_error(exc)


def register(mcp: MCPServer) -> None:
    """ابزار list_at_risk_projects را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="list_at_risk_projects",
        title=TITLE_LIST_AT_RISK_PROJECTS,
        description=LIST_AT_RISK_PROJECTS,
        annotations=READ_ONLY_STATS,
    )
    def list_at_risk_projects(limit: int = 10, offset: int = 0) -> dict:
        """ابزار MCP: پروژه‌های عقب‌افتادهٔ عضو فعال بودن را می‌خواند."""
        return run_list_at_risk_projects(limit=limit, offset=offset)
