"""پوستهٔ مشترک ابزارهای CRUD؛ قانون دامنه اینجا نیست.

try/except و ثبت امضای تکراری id/list این‌جا جمع می‌شود.
مجوز، فیلدها، و اثر جانبی هر جدول در فایل همان ابزار می‌ماند.
"""

from __future__ import annotations

import functools
from collections.abc import Callable

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from errors.crud import format_error
from logging_module import logged_tool


def run_tool(name: str):
    """لاگ ابزار و تبدیل استثنا به پاکت خطا را یک‌بار می‌گذارد.

    ورودی:
        name: نام روی سیم پروتکل؛ همان logged_tool.
    خروجی:
        دکوراتور با حفظ امضا.
    علت:
        بدنهٔ run_* فقط قانون دامنه را بنویسد؛ try/except تکرار نشود.
    """

    def decorator(fn: Callable) -> Callable:
        @logged_tool(name)
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                return format_error(exc)

        return wrapper

    return decorator


def register_id_tool(
    mcp: MCPServer,
    run: Callable[..., dict],
    *,
    name: str,
    title: str,
    description: str,
    annotations: ToolAnnotations,
) -> None:
    """ابزار با امضای فقط id را روی سرور ثبت می‌کند.

    ورودی:
        mcp: سرور FastMCP.
        run: همان run_* تست‌پذیر.
        name و title و description و annotations: متادیتای روی سیم.
    خروجی:
        هیچ. اثر جانبی ثبت tool است.
    علت:
        get/delete/mark_read امضای یکسان دارند؛ فیلد create/update این‌جا نیست.
    """

    @mcp.tool(
        name=name,
        title=title,
        description=description,
        annotations=annotations,
    )
    def tool(id: int) -> dict:
        return run(id=id)

    tool.__name__ = name
    tool.__doc__ = description


def register_page_tool(
    mcp: MCPServer,
    run: Callable[..., dict],
    *,
    name: str,
    title: str,
    description: str,
    annotations: ToolAnnotations,
) -> None:
    """ابزار با امضای فقط limit/offset را روی سرور ثبت می‌کند.

    ورودی:
        mcp: سرور FastMCP.
        run: همان run_* تست‌پذیر.
        name و title و description و annotations: متادیتای روی سیم.
    خروجی:
        هیچ. اثر جانبی ثبت tool است.
    علت:
        فهرست بدون فیلتر اضافه امضای یکسان دارد؛ فیلتر پروژه/گفتگو این‌جا نیست.
    """

    @mcp.tool(
        name=name,
        title=title,
        description=description,
        annotations=annotations,
    )
    def tool(limit: int = 10, offset: int = 0) -> dict:
        return run(limit=limit, offset=offset)

    tool.__name__ = name
    tool.__doc__ = description
