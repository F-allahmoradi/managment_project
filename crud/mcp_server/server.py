"""راه‌اندازی سرور MCP کراد و چرخه حیات آن.

در MCP SDK نسخه ۲، FastMCP به MCPServer تغییر نام داده است. اینجا همان
کلاس با نام مستعار FastMCP ساخته می‌شود. ثبت ابزارها در register.py است.
گام یک auth و cache را نصب نمی‌کند؛ دروازهٔ نازک نقش در auth/gate.py است.
"""

from pathlib import Path
import sys

# ریشه پروژهٔ کراد روی sys.path تا اجرای مستقیم این فایل هم importها را پیدا کند.
_ROOT = Path(__file__).resolve().parent.parent
_REPO = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer as FastMCP

from mcp_server.metadata import (
    SERVER_DESCRIPTION,
    SERVER_INSTRUCTIONS,
    SERVER_NAME,
    SERVER_TITLE,
)
from mcp_server.register import register_crud_tools

mcp = FastMCP(
    name=SERVER_NAME,
    title=SERVER_TITLE,
    description=SERVER_DESCRIPTION,
    instructions=SERVER_INSTRUCTIONS,
)

setup_logging()
register_crud_tools(mcp)


def main() -> None:
    """سرور کراد را با انتقال stdio اجرا می‌کند.

    ورودی:
        هیچ. host MCP از stdin/stdout با کلاینت حرف می‌زند.
    خروجی:
        هیچ؛ تا قطع شدن فرآیند بلوکه می‌ماند.
    فراخوانی‌ها:
        FastMCP.run با transport پیش‌فرض stdio.
    """
    mcp.run()


if __name__ == "__main__":
    # اجرای مستقیم: python -m mcp_server.server از ریشه پوشه crud.
    main()
