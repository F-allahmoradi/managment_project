"""تست ثبت ابزار استخراج و پاکت JSON."""

from pathlib import Path
import asyncio
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from errors.crud import format_error, format_success
from mcp.server.mcpserver import MCPServer as FastMCP
from mcp_server.metadata import (
    SERVER_NAME,
    SERVER_TITLE,
    TITLE_EXTRACT_ENTITIES,
)
from mcp_server.register import register_ner_tools


class ServerPlumbingTests(unittest.TestCase):
    """ساخت سرور و ثبت فقط ابزار استخراج را بررسی می‌کند."""

    def test_metadata_names_management_ner(self) -> None:
        self.assertEqual(SERVER_NAME, "management-ner")
        self.assertEqual(SERVER_TITLE, "استخراج متن پروژه")

    def test_register_adds_extract_tool(self) -> None:
        mcp = FastMCP(name=SERVER_NAME)
        register_ner_tools(mcp)
        names = {tool.name for tool in mcp._tool_manager.list_tools()}
        self.assertEqual(
            names,
            {
                "extract_entities",
                "extract_keywords",
                "extract_topics",
                "extract_sentiment",
                "extract_discourse",
                "extract_intent",
                "extract_rhetoric",
            },
        )

    def test_server_module_lists_registered_tools(self) -> None:
        from mcp_server.server import mcp

        self.assertEqual(mcp.name, SERVER_NAME)
        names = {tool.name for tool in asyncio.run(mcp.list_tools())}
        self.assertEqual(
            names,
            {
                "extract_entities",
                "extract_keywords",
                "extract_topics",
                "extract_sentiment",
                "extract_discourse",
                "extract_intent",
                "extract_rhetoric",
            },
        )
        tool = next(item for item in asyncio.run(mcp.list_tools()) if item.name == "extract_entities")
        self.assertEqual(tool.title, TITLE_EXTRACT_ENTITIES)
        self.assertTrue(tool.annotations.read_only_hint)


class ErrorEnvelopeTests(unittest.TestCase):
    def test_success_envelope(self) -> None:
        payload = format_success("استخراج شد", extracted_count=3)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["extracted_count"], 3)

    def test_unknown_maps_to_database_error(self) -> None:
        payload = format_error(RuntimeError("boom"))
        self.assertEqual(payload["error_code"], "DATABASE_ERROR")


if __name__ == "__main__":
    unittest.main()
