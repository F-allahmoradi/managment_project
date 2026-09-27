"""راه‌اندازی سرور MCP آمار و چرخه حیات آن.

ثبت ابزارها در register.py است. گزارش متنی اینجا نیست.
"""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer as FastMCP

from mcp_server.metadata import (
    SERVER_DESCRIPTION,
    SERVER_INSTRUCTIONS,
    SERVER_NAME,
    SERVER_TITLE,
)
from mcp_server.register import register_stats_tools

mcp = FastMCP(
    name=SERVER_NAME,
    title=SERVER_TITLE,
    description=SERVER_DESCRIPTION,
    instructions=SERVER_INSTRUCTIONS,
)

setup_logging()
register_stats_tools(mcp)


def main() -> None:
    """سرور آمار را با انتقال stdio اجرا می‌کند."""
    mcp.run()


if __name__ == "__main__":
    main()
