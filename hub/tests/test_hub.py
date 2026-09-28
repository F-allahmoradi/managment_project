"""آزمون مسیر HTTP، بازیگر درخواست، و بالا آمدن دامنه crud."""

from hub.bootstrap import install_hub_import_path

install_hub_import_path()

import os
import threading
import time
import unittest

from auth.http import (
    INVALID_INPUT,
    PERMISSION_DENIED,
    UNAUTHENTICATED,
    extract_bearer,
    http_status_for,
)
from auth.sessions import AuthError, register_account
from auth.principal import reset_request_actor, resolve_actor, set_request_actor
from hub.config import load_settings
from hub.analysis import (
    analyze_source,
    commit_analysis,
    drop_entity_copy_keywords,
    get_preview_job,
    pack_save_fields,
    planned_layers,
    preview_source,
    reset_extract_runtime,
    start_preview_job,
)
from hub.pool import DomainPool
from hub.registry import DASHBOARD_ROUTES, merge_route_arguments


class HttpContractTests(unittest.TestCase):
    def test_bearer_token_is_taken_from_authorization_header(self) -> None:
        self.assertEqual(extract_bearer("Bearer abc.def"), "abc.def")
        self.assertIsNone(extract_bearer("Basic abc"))
        self.assertIsNone(extract_bearer(None))

    def test_error_envelope_maps_to_stable_http_status(self) -> None:
        self.assertEqual(http_status_for({"status": "success"}), 200)
        self.assertEqual(
            http_status_for({"status": "error", "error_code": UNAUTHENTICATED}),
            401,
        )
        self.assertEqual(
            http_status_for({"status": "error", "error_code": PERMISSION_DENIED}),
            403,
        )
        self.assertEqual(
            http_status_for({"status": "error", "error_code": "PROJECT_NOT_FOUND"}),
            404,
        )
        self.assertEqual(
            http_status_for({"status": "error", "error_code": INVALID_INPUT}),
            422,
        )

    def test_dashboard_path_id_overrides_body(self) -> None:
        route = next(item for item in DASHBOARD_ROUTES if item["path"] == "/api/v1/projects/{id}")
        arguments = merge_route_arguments(route, {"id": "12"}, {"id": 3, "name": "آلفا"})
        self.assertEqual(arguments["id"], 12)
        self.assertEqual(arguments["name"], "آلفا")

    def test_default_domains_cover_dashboard_services(self) -> None:
        previous = os.environ.pop("API_DOMAINS", None)
        try:
            domains = load_settings()["domains"]
        finally:
            if previous is not None:
                os.environ["API_DOMAINS"] = previous
        for route in DASHBOARD_ROUTES:
            self.assertIn(route["domain"], domains)

    def test_register_rejects_short_password_before_database(self) -> None:
        with self.assertRaises(AuthError) as caught:
            register_account(
                {
                    "first_name": "آزما",
                    "last_name": "ورود",
                    "username": "short_pass_user",
                    "password": "1234567",
                }
            )
        self.assertEqual(caught.exception.error_code, INVALID_INPUT)
        self.assertIn("۸", caught.exception.message)


class ActorContextTests(unittest.TestCase):
    def test_request_actor_overrides_environment(self) -> None:
        import auth.principal as principal

        def fake_fetch(where_sql, params):
            return {"id": params[0], "username": "ada", "is_active": True}

        original = principal.fetch_actor_record
        principal.fetch_actor_record = fake_fetch
        os.environ["MCP_ACTOR_USER_ID"] = "99"
        token = set_request_actor(4)
        try:
            actor = resolve_actor()
        finally:
            reset_request_actor(token)
            principal.fetch_actor_record = original
            os.environ.pop("MCP_ACTOR_USER_ID", None)
        self.assertEqual(actor["id"], 4)
        self.assertEqual(actor["username"], "ada")


class CrudWorkerTests(unittest.TestCase):
    def test_crud_domain_publishes_project_tools(self) -> None:
        pool = DomainPool(("crud",), 90)
        try:
            pool.start()
            catalog = pool.catalog()
        finally:
            pool.stop()
        self.assertEqual(len(catalog), 1)
        self.assertTrue(catalog[0]["ready"], catalog[0]["message"])
        names = {tool["name"] for tool in catalog[0]["tools"]}
        self.assertIn("list_projects", names)
        self.assertIn("list_notifications", names)
        self.assertTrue(pool.tool_info("crud", "list_projects")["read_only"])


class AnalysisPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_extract_runtime()

    def test_default_domains_include_extract_services(self) -> None:
        previous = os.environ.pop("API_DOMAINS", None)
        try:
            domains = load_settings()["domains"]
        finally:
            if previous is not None:
                os.environ["API_DOMAINS"] = previous
        for name in ("ner", "nlp", "embedding"):
            self.assertIn(name, domains)

    def test_entity_copy_keywords_are_dropped(self) -> None:
        keywords = drop_entity_copy_keywords(
            [{"phrase": "سارا احمدی", "confidence": 0.9}, {"phrase": "تأخیر پرداخت", "confidence": 0.8}],
            [{"canonical_name": "سارا احمدی", "mention_text": "سارا احمدی", "normalized_name": "سارا احمدی"}],
        )
        self.assertEqual([item["phrase"] for item in keywords], ["تأخیر پرداخت"])

    def test_pack_save_fields_keeps_successful_layers(self) -> None:
        packed = pack_save_fields(
            "message",
            12,
            {
                "entities": {"status": "success", "mentions": [{"type": "PERSON", "canonical_name": "سارا"}]},
                "keywords": {"status": "success", "keywords": [{"phrase": "سارا"}, {"phrase": "پرداخت"}]},
                "topics": {"status": "error", "message": "مدل نیامد"},
                "sentiment": {
                    "status": "success",
                    "sentiment": {"polarity": "negative"},
                    "emotions": [{"emotion": "worry"}],
                },
                "discourse": {"status": "success", "discourses": [{"code": "report"}]},
                "intent": {"status": "success", "intents": [{"code": "follow_up"}]},
                "rhetoric": {
                    "status": "success",
                    "rhetorics": [{"code": "literal", "is_primary": True}],
                    "intended_meaning": "",
                },
                "facts": {"status": "success", "facts": [{"kind": "status", "name": "تأخیر"}]},
                "quotes": {"status": "error", "message": "نقل‌قول نیامد"},
                "frame": {
                    "status": "success",
                    "frame": {"title": "کمبود نیرو", "scope": "unit", "scope_name": "واحدی"},
                },
            },
        )
        self.assertEqual(packed["source_id"], 12)
        self.assertEqual(packed["keywords"][0]["phrase"], "پرداخت")
        self.assertEqual(packed["topics"], [])
        self.assertEqual(packed["quotes"], [])
        self.assertEqual(packed["sentiment"]["polarity"], "negative")
        self.assertEqual(packed["frame"]["title"], "کمبود نیرو")
        self.assertIsNone(packed["intended_meaning"])
        self.assertEqual(packed["entities"], [])
        self.assertEqual(packed["explicitness"], None)

    def test_analyze_source_saves_then_embeds(self) -> None:
        calls = []
        saved_args = {}

        class FakePool:
            def call(self, domain, tool, arguments, actor_id):
                calls.append((domain, tool, arguments.get("source_id") or arguments.get("analysis_id")))
                if tool == "extract_rhetoric":
                    return {
                        "status": "success",
                        "rhetorics": [{"code": "irony", "is_primary": True}],
                        "intended_meaning": "سرور قطع است",
                    }
                if tool.startswith("extract_"):
                    return {"status": "success"}
                if tool == "save_text_analysis":
                    saved_args.update(arguments)
                    return {"status": "success", "id": 44}
                if tool == "index_text_analysis":
                    return {"status": "success", "indexed": 3}
                raise AssertionError(tool)

        result = analyze_source(
            FakePool(),
            ("crud", "ner", "nlp", "embedding"),
            7,
            "message",
            9,
        )
        self.assertEqual(result["id"], 44)
        self.assertEqual(result["embedding"]["indexed"], 3)
        self.assertEqual(saved_args["intended_meaning"], "سرور قطع است")
        self.assertIn(("ner", "extract_entities", 9), calls)
        self.assertIn(("nlp", "extract_facts", 9), calls)
        self.assertIn(("nlp", "extract_frame", 9), calls)
        self.assertIn(("embedding", "index_text_analysis", 44), calls)

    def test_preview_source_does_not_save(self) -> None:
        calls = []

        class FakePool:
            def call(self, domain, tool, arguments, actor_id):
                calls.append(tool)
                if tool == "extract_rhetoric":
                    return {"status": "success", "rhetorics": [{"code": "literal", "is_primary": True}]}
                if tool.startswith("extract_"):
                    return {"status": "success", "mentions": [{"canonical_name": "سارا"}]}
                raise AssertionError(tool)

        result = preview_source(FakePool(), ("ner", "nlp"), 3, "message", 8)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["fields"]["source_id"], 8)
        self.assertNotIn("save_text_analysis", calls)
        self.assertEqual(len(result["planned_layers"]), 10)

    def test_all_mcp_extract_layers_are_planned(self) -> None:
        keys = [item.key for item in planned_layers(("ner", "nlp"))]
        self.assertEqual(
            keys,
            [
                "rhetoric",
                "entities",
                "keywords",
                "topics",
                "sentiment",
                "discourse",
                "intent",
                "facts",
                "quotes",
                "frame",
            ],
        )

    def test_preview_cache_skips_second_model_calls(self) -> None:
        calls = []

        class FakePool:
            def call(self, domain, tool, arguments, actor_id):
                calls.append(tool)
                if tool.startswith("extract_"):
                    return {"status": "success"}
                raise AssertionError(tool)

        pool = FakePool()
        preview_source(pool, ("ner", "nlp"), 3, "message", 8)
        first = list(calls)
        preview_source(pool, ("ner", "nlp"), 3, "message", 8)
        self.assertEqual(len(first), 10)
        self.assertEqual(calls, first)

    def test_preview_job_first_snapshot_is_not_ready(self) -> None:
        gate = threading.Event()

        class FakePool:
            def call(self, domain, tool, arguments, actor_id):
                gate.wait(2)
                if tool.startswith("extract_"):
                    return {"status": "success", "mentions": [{"canonical_name": "سارا"}]}
                raise AssertionError(tool)

        started = start_preview_job(FakePool(), ("ner",), 4, "message", 21)
        self.assertEqual(started["phase"], "running")
        self.assertFalse(started["ready"])
        self.assertEqual((started.get("fields") or {}).get("mentions") or [], [])
        gate.set()
        snapshot = started
        for _ in range(80):
            snapshot = get_preview_job(started["job_id"], 4)
            if snapshot.get("ready"):
                break
            time.sleep(0.01)
        self.assertTrue(snapshot.get("ready"))
        self.assertEqual(snapshot["phase"], "done")

    def test_preview_job_polls_until_layers_complete(self) -> None:
        class FakePool:
            def call(self, domain, tool, arguments, actor_id):
                if tool.startswith("extract_"):
                    return {"status": "success", "message": tool}
                raise AssertionError(tool)

        started = start_preview_job(FakePool(), ("ner", "nlp"), 4, "message", 11)
        self.assertEqual(started["status"], "success")
        job_id = started["job_id"]
        snapshot = started
        for _ in range(80):
            snapshot = get_preview_job(job_id, 4)
            if snapshot.get("phase") == "done":
                break
            time.sleep(0.01)
        self.assertEqual(snapshot["phase"], "done")
        self.assertTrue(snapshot.get("ready"))
        self.assertEqual(len(snapshot["completed_layers"]), 10)
        self.assertEqual(len(snapshot["planned_layers"]), 10)

    def test_commit_analysis_saves_confirmed_fields(self) -> None:
        seen = {}

        class FakePool:
            def call(self, domain, tool, arguments, actor_id):
                seen["tool"] = tool
                seen["fields"] = arguments
                if tool == "save_text_analysis":
                    return {"status": "success", "id": 5}
                return {"status": "success"}

        result = commit_analysis(FakePool(), ("crud",), 3, {"source_type": "message", "source_id": 8})
        self.assertEqual(result["id"], 5)
        self.assertEqual(seen["tool"], "save_text_analysis")
        self.assertEqual(seen["fields"]["source_id"], 8)

    def test_analyze_source_rejects_unknown_source(self) -> None:
        result = analyze_source(None, ("ner",), 1, "report", 3)
        self.assertEqual(result["error_code"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
