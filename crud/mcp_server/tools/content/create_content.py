"""ابزار MCP برای ثبت متن یا متادیتای صوت، تصویر و فایل در contents.

آپلود واقعی روی S3 نیست. بایت فایل جدا ذخیره می‌شود و اینجا فقط storage_key می‌آید.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from mcp_server.runtime import run_tool

from auth.gate import require_permission
from errors.crud import format_success
from mcp_server.docstrings import CREATE_CONTENT
from mcp_server.metadata import TITLE_CREATE_CONTENT, WRITE_CRUD
from services.content import insert_content
from validators.content import validate_create_content


@run_tool("create_content")
def run_create_content(**fields) -> dict:
    """مسیر کامل ثبت محتوا را بدون دکوراتور MCP اجرا می‌کند."""
    actor = require_permission("Content", "Create")
    parsed = validate_create_content(fields)
    new_id = insert_content(parsed, created_by=actor["id"])
    return format_success("محتوا ثبت شد", id=new_id)


def register(mcp: MCPServer) -> None:
    """ابزار create_content را روی نمونه سرور ثبت می‌کند."""

    @mcp.tool(
        name="create_content",
        title=TITLE_CREATE_CONTENT,
        description=CREATE_CONTENT,
        annotations=WRITE_CRUD,
    )
    def create_content(
        content_kind: Optional[str] = None,
        content_kind_id: Optional[int] = None,
        text_body: Optional[str] = None,
        storage_key: Optional[str] = None,
        original_filename: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        duration_seconds: Optional[int] = None,
    ) -> dict:
        """ابزار MCP: یک ردیف contents برای متن، صوت، تصویر یا فایل درج می‌کند."""
        return run_create_content(
            content_kind=content_kind,
            content_kind_id=content_kind_id,
            text_body=text_body,
            storage_key=storage_key,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            duration_seconds=duration_seconds,
        )
