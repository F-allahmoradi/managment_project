"""راه‌اندازی سرور MCP تبدیل گفتار به متن."""

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
from mcp_server.register import register_stt_tools

mcp = FastMCP(
    name=SERVER_NAME,
    title=SERVER_TITLE,
    description=SERVER_DESCRIPTION,
    instructions=SERVER_INSTRUCTIONS,
)

setup_logging()
register_stt_tools(mcp)


def main() -> None:
    """سرور STT را با انتقال stdio اجرا می‌کند."""
    mcp.run()


if __name__ == "__main__":
    main()
