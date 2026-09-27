"""ایندکس و جستجو روی PostgreSQL با امبدینگ جعلی."""

from pathlib import Path
import asyncio
import os
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.config import EMBEDDING_DIMENSIONS
from business_logic.indexer import index_analysis
from business_logic.searcher import search_similar
from errors.crud import PERMISSION_DENIED
from mcp_server.metadata import (
    SERVER_NAME,
    TITLE_INDEX_TEXT_ANALYSIS,
    TITLE_SEARCH_SIMILAR,
)
from mcp_server.tools.index_text_analysis import run_index_text_analysis
from mcp_server.tools.search_similar import run_search_similar
from services.project import insert_project
from services.task import insert_task
from services.chat import insert_chat
from services.message import insert_message
from services.text_analysis import insert_text_analysis
from tests.conftest import (
    bind_actor_as_role,
    delete_temp_project,
    unique_chat_title,
    unique_project_name,
    unique_task_title,
)


def fake_embed(texts: list[str]) -> list[list[float]]:
    """بردار ۱۵۳۶تایی قطعی از روی متن می‌سازد تا تست به API وصل نشود."""
    vectors = []
    for text in texts:
        vec = [0.0] * EMBEDDING_DIMENSIONS
        for index, char in enumerate(text):
            vec[index % 8] += (ord(char) % 17) / 17
        if "شکایت" in text or "خسارت" in text:
            vec[0] += 3
        if "سارا" in text:
            vec[1] += 2
        vectors.append(vec)
    return vectors


class ServerPlumbingTests(unittest.TestCase):
    """ثبت ابزار بازیابی را بررسی می‌کند."""

    def test_metadata_names_management_embedding(self) -> None:
        from mcp_server.server import mcp

        self.assertEqual(SERVER_NAME, "management-embedding")
        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        self.assertEqual(set(by_name), {
            "index_text_analysis",
            "index_pending_analyses",
            "search_similar",
        })
        self.assertEqual(by_name["index_text_analysis"].title, TITLE_INDEX_TEXT_ANALYSIS)
        self.assertFalse(by_name["index_text_analysis"].annotations.read_only_hint)
        self.assertEqual(by_name["search_similar"].title, TITLE_SEARCH_SIMILAR)
        self.assertTrue(by_name["search_similar"].annotations.read_only_hint)


class SearchToolTests(unittest.TestCase):
    """ذخیره، ایندکس جعلی، و یافتن موارد مشابه."""

    def test_index_and_search_returns_same_source(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        project_id = None
        try:
            project_id = insert_project(
                {
                    "name": unique_project_name("امبد"),
                    "project_type": "نرم‌افزاری",
                    "project_status": "در حال اجرا",
                },
                created_by=ali.user_id,
            )
            chat_id = insert_chat(
                {
                    "title": unique_chat_title("امبد"),
                    "project_id": project_id,
                    "chat_type": "گفتگوی پروژه",
                },
                created_by=ali.user_id,
            )
            task_id = insert_task(
                {
                    "project_id": project_id,
                    "title": unique_task_title("امبد"),
                    "status": "شروع نشده",
                    "priority": "متوسط",
                    "importance": "متوسط",
                    "assigned_to_user_id": ali.user_id,
                },
                created_by=ali.user_id,
            )
            posted = insert_message(
                {
                    "chat_id": chat_id,
                    "task_id": task_id,
                    "text": "سارا تأخیر پرداخت پیمانکار را گزارش کرد و خسارت خواست.",
                    "recipient_user_id": ali.user_id,
                },
                sender_user_id=ali.user_id,
            )
            saved = insert_text_analysis(
                {
                    "source_type": "message",
                    "source_id": posted,
                    "model": "test-ner",
                    "mentions": [
                        {
                            "type": "PERSON",
                            "canonical_name": "سارا",
                            "normalized_name": f"سارا {posted}",
                            "mention_text": "سارا",
                            "start_offset": 0,
                            "end_offset": 4,
                            "confidence": 0.9,
                        }
                    ],
                    "intents": [
                        {
                            "code": "complaint",
                            "is_primary": True,
                            "confidence": 0.9,
                            "mention_text": "خسارت خواست",
                            "slots": {
                                "شاکی": "سارا",
                                "مشتکی‌عنه": "پیمانکار",
                                "مورد اختلاف": "تأخیر پرداخت",
                                "خواسته": "خسارت",
                            },
                        }
                    ],
                },
                created_by=ali.user_id,
            )
            indexed = index_analysis(saved["id"], ali.user_id, embed_fn=fake_embed)
            self.assertGreaterEqual(indexed["raw_count"], 1)
            self.assertEqual(indexed["entity_count"], 1)
            self.assertEqual(indexed["intent_count"], 1)
            self.assertEqual(indexed["intent_slot_count"], 4)
            found = search_similar(
                ali.user_id,
                "شکایت سارا از پیمانکار بابت خسارت",
                embed_fn=fake_embed,
            )
            self.assertGreaterEqual(found["hit_count"], 1)
            self.assertEqual(found["records"][0]["analysis_id"], saved["id"])
            self.assertEqual(found["records"][0]["source_type"], "message")
            self.assertTrue(
                {"raw", "entity", "intent", "intent_slot"}
                & set(found["records"][0]["kinds"])
            )
            outsider = bind_actor_as_role("مدیر پروژه")
            try:
                hidden = search_similar(
                    outsider.user_id,
                    "شکایت سارا از پیمانکار بابت خسارت",
                    embed_fn=fake_embed,
                )
                self.assertEqual(hidden["hit_count"], 0)
            finally:
                outsider.close()
        finally:
            if project_id is not None:
                delete_temp_project(project_id)
            ali.close()

    def test_index_tool_needs_actor(self) -> None:
        previous = os.environ.pop("MCP_ACTOR_USER_ID", None)
        try:
            result = run_index_text_analysis(analysis_id=1)
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["error_code"], PERMISSION_DENIED)
            missing = run_search_similar(query="سؤال آزمایشی")
            self.assertEqual(missing["status"], "error")
            self.assertEqual(missing["error_code"], PERMISSION_DENIED)
        finally:
            if previous is None:
                os.environ.pop("MCP_ACTOR_USER_ID", None)
            else:
                os.environ["MCP_ACTOR_USER_ID"] = previous


if __name__ == "__main__":
    unittest.main()
