"""ذخیره playground نباید با بستهٔ هم‌نام nlp به ImportError بخورد."""

from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path, load_crud_symbol

ensure_import_path()

from errors.crud import PermissionDeniedError
from playground.app import (
    _save_issue,
    _save_issue_input_cls,
    _link_cause_input_cls,
    _save_task_input_cls,
    _link_task_input_cls,
    _set_importance_input_cls,
    _set_urgency_input_cls,
    _set_severity_input_cls,
    _add_impact_input_cls,
    _link_topic_input_cls,
    _link_entity_input_cls,
    _catalog_scoring,
    _suggested_entity_role,
    _save_fact_input_cls,
    _save_quote_input_cls,
)
from tests.sample import GOLD_FACTS, GOLD_FRAME, GOLD_QUOTES, SAMPLE_TEXT


class PlaygroundSaveImportTests(unittest.TestCase):
    """اسکیمای کراد جدا از schemas همنام nlp بار می‌شود."""

    def test_save_schema_loads_from_crud(self) -> None:
        model_cls = load_crud_symbol("schemas.crud.issue", "CreateIssueInput")
        parsed = model_cls(
            project_id=1,
            title="کاهش عملکرد واحد مالی",
            analysis_id=12,
        ).model_dump()
        self.assertEqual(parsed["title"], "کاهش عملکرد واحد مالی")
        self.assertEqual(parsed["analysis_id"], 12)
        self.assertEqual(parsed["status"], "جدید")
        from schemas.output import IssueFrameHit

        hit = IssueFrameHit(
            title="کاهش عملکرد واحد مالی",
            unit="واحد مالی",
            process="staffing",
            process_name="تأمین نیرو",
            scope="organizational",
            scope_name="سازمانی",
            about="کمبود نیروی متخصص",
            mention_text="کمبود نیروی متخصص",
            confidence=0.8,
        )
        self.assertEqual(hit.unit, "واحد مالی")

    def test_link_cause_schema_loads_from_crud(self) -> None:
        model_cls = load_crud_symbol("schemas.crud.issue", "LinkIssueCauseInput")
        parsed = model_cls(
            issue_id=10,
            cause_issue_id=11,
            cause_level="cause",
        ).model_dump()
        self.assertEqual(parsed["issue_id"], 10)
        self.assertEqual(parsed["cause_issue_id"], 11)
        self.assertEqual(parsed["cause_level"], "cause")
        with self.assertRaises(Exception):
            model_cls(issue_id=10, cause_issue_id=10)

    def test_save_input_cls_is_cached(self) -> None:
        first = _save_issue_input_cls()
        second = _save_issue_input_cls()
        self.assertIs(first, second)

    def test_save_without_actor_is_permission_denied(self) -> None:
        previous_id = os.environ.pop("MCP_ACTOR_USER_ID", None)
        previous_username = os.environ.pop("MCP_ACTOR_USERNAME", None)
        try:
            with self.assertRaises(PermissionDeniedError):
                _save_issue(
                    {
                        "text": "واحد مالی ۳۰ درصد کاهش عملکرد داشته است.",
                        "frame": {"title": "کاهش عملکرد واحد مالی"},
                    }
                )
        finally:
            if previous_id is None:
                os.environ.pop("MCP_ACTOR_USER_ID", None)
            else:
                os.environ["MCP_ACTOR_USER_ID"] = previous_id
            if previous_username is None:
                os.environ.pop("MCP_ACTOR_USERNAME", None)
            else:
                os.environ["MCP_ACTOR_USERNAME"] = previous_username

    def test_save_reuses_analysis_id_and_writes_issue(self) -> None:
        stored = {
            "id": 44,
            "title": "کاهش عملکرد واحد مالی",
            "project_id": 7,
            "status_name": "جدید",
            "analysis_ids": [21],
            "sources": [{"id": 1, "analysis_id": 21, "source_type": "content", "source_id": 3}],
        }
        with patch("auth.gate.require_permission", return_value={"id": 9}):
            with patch("playground.app._resolve_project_id", return_value=7):
                with patch("services.issue.insert_issue", return_value=stored) as insert_issue:
                    payload = _save_issue(
                        {
                            "text": "واحد مالی ۳۰ درصد کاهش عملکرد داشته است.",
                            "frame": {"title": "کاهش عملکرد واحد مالی"},
                            "analysis_id": 21,
                            "project_id": 7,
                        }
                    )
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["id"], 44)
        self.assertEqual(payload["analysis_id"], 21)
        self.assertTrue(payload["analysis_reused"])
        insert_issue.assert_called_once()
        fields, kwargs = insert_issue.call_args
        self.assertEqual(fields[0]["analysis_id"], 21)
        self.assertEqual(fields[0]["title"], "کاهش عملکرد واحد مالی")
        self.assertEqual(kwargs["created_by"], 9)
        self.assertEqual(payload["causes"], [])
        self.assertNotIn("task", payload)
        self.assertNotIn("scoring", payload)

    def test_save_without_analysis_id_saves_text_first(self) -> None:
        stored_analysis = {
            "id": 18,
            "source_type": "content",
            "source_id": 5,
        }
        stored_issue = {
            "id": 3,
            "title": "کاهش عملکرد واحد مالی",
            "project_id": 7,
            "analysis_ids": [18],
            "sources": [{"id": 1, "analysis_id": 18, "source_type": "content", "source_id": 5}],
        }
        with patch("auth.gate.require_permission", return_value={"id": 9}):
            with patch("playground.app._resolve_project_id", return_value=7):
                with patch(
                    "services.text_analysis.insert_text_analysis",
                    return_value=stored_analysis,
                ) as save_analysis:
                    with patch(
                        "services.issue.insert_issue",
                        return_value=stored_issue,
                    ) as insert_issue:
                        payload = _save_issue(
                            {
                                "text": "واحد مالی ۳۰ درصد کاهش عملکرد داشته است.",
                                "frame": {"title": "کاهش عملکرد واحد مالی"},
                                "project_id": 7,
                            }
                        )
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["analysis_id"], 18)
        self.assertEqual(payload["id"], 3)
        self.assertNotIn("analysis_reused", payload)
        save_analysis.assert_called_once()
        insert_issue.assert_called_once()
        self.assertEqual(insert_issue.call_args[0][0]["analysis_id"], 18)
        self.assertEqual(save_analysis.call_args[0][0]["facts"], [])
        self.assertEqual(save_analysis.call_args[0][0]["quotes"], [])


    def test_save_fact_schema_loads_from_crud(self) -> None:
        model_cls = load_crud_symbol("schemas.crud.text_analysis", "SaveFactInput")
        parsed = model_cls(
            id="q1",
            kind="quantity",
            name="کاهش عملکرد",
            value=30,
            unit="percent",
            role="total",
            grounding="explicit",
            mention_text="۳۰ درصد کاهش عملکرد",
        ).model_dump()
        self.assertEqual(parsed["fact_id"], "q1")
        self.assertEqual(parsed["kind"], "quantity")
        self.assertEqual(parsed["value"], 30)
        self.assertEqual(parsed["role"], "total")
        self.assertIs(_save_fact_input_cls(), _save_fact_input_cls())

    def test_save_quote_schema_loads_from_crud(self) -> None:
        model_cls = load_crud_symbol("schemas.crud.text_analysis", "SaveQuoteInput")
        parsed = model_cls(
            mode="indirect",
            attributed_to="واحد مالی",
            quoted_text="به دلیل کمبود نیروی متخصص 30 درصد کاهش عملکرد داریم",
            mention_text="گفت",
        ).model_dump()
        self.assertEqual(parsed["mode"], "indirect")
        self.assertEqual(parsed["attributed_to"], "واحد مالی")
        self.assertIn("کمبود نیروی متخصص", parsed["quoted_text"])
        self.assertIs(_save_quote_input_cls(), _save_quote_input_cls())

    def test_save_confirmed_facts_with_new_analysis(self) -> None:
        stored_analysis = {
            "id": 18,
            "source_type": "content",
            "source_id": 5,
            "facts": [
                {"fact_id": "q1", "kind": "quantity", "value": 30, "role": "total"},
                {"fact_id": "q2", "kind": "quantity", "value": 10, "role": "part"},
                {"fact_id": "q3", "kind": "quantity", "value": 20, "role": "remainder"},
                {"fact_id": "c1", "kind": "cause", "name": "کمبود نیروی متخصص"},
                {"fact_id": "c2", "kind": "cause", "name": "واحد بازاریابی"},
            ],
            "quotes": [
                {
                    "mode": "indirect",
                    "attributed_to": "واحد مالی",
                    "quoted_text": "به دلیل کمبود نیروی متخصص 30 درصد کاهش عملکرد داریم",
                }
            ],
        }
        stored_issue = {
            "id": 3,
            "title": "کاهش عملکرد واحد مالی",
            "project_id": 7,
            "analysis_ids": [18],
            "sources": [{"id": 1, "analysis_id": 18, "source_type": "content", "source_id": 5}],
        }
        with patch("auth.gate.require_permission", return_value={"id": 9}):
            with patch("playground.app._resolve_project_id", return_value=7):
                with patch(
                    "services.text_analysis.insert_text_analysis",
                    return_value=stored_analysis,
                ) as save_analysis:
                    with patch(
                        "services.issue.insert_issue",
                        return_value=stored_issue,
                    ):
                        payload = _save_issue(
                            {
                                "text": SAMPLE_TEXT,
                                "frame": {"title": "کاهش عملکرد واحد مالی"},
                                "project_id": 7,
                                "facts": GOLD_FACTS["facts"],
                                "quotes": GOLD_QUOTES["quotes"],
                            }
                        )
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["fact_count"], 5)
        self.assertEqual(len(payload["facts"]), 5)
        self.assertEqual(payload["quote_count"], 1)
        self.assertEqual(payload["quotes"][0]["attributed_to"], "واحد مالی")
        self.assertIn("5 فکت روی تحلیل ماند", payload["message"])
        self.assertIn("1 نقل‌قول روی تحلیل ماند", payload["message"])
        saved_facts = save_analysis.call_args[0][0]["facts"]
        roles = {item["role"] for item in saved_facts if item["kind"] == "quantity"}
        self.assertEqual(roles, {"total", "part", "remainder"})
        causes = {item["name"] for item in saved_facts if item["kind"] == "cause"}
        self.assertEqual(causes, {"کمبود نیروی متخصص", "واحد بازاریابی"})
        saved_quotes = save_analysis.call_args[0][0]["quotes"]
        self.assertEqual(saved_quotes[0]["attributed_to"], "واحد مالی")
        self.assertEqual(saved_quotes[0]["mode"], "indirect")

    def test_save_confirmed_facts_on_reused_analysis(self) -> None:
        stored_main = {
            "id": 10,
            "title": "کاهش عملکرد واحد مالی",
            "project_id": 7,
            "analysis_ids": [21],
            "sources": [{"id": 1, "analysis_id": 21}],
            "causes": [],
        }
        stored_facts = [
            {"fact_id": "q1", "kind": "quantity", "value": 30, "role": "total"},
            {"fact_id": "q2", "kind": "quantity", "value": 10, "role": "part"},
            {"fact_id": "q3", "kind": "quantity", "value": 20, "role": "remainder"},
            {"fact_id": "c1", "kind": "cause", "name": "کمبود نیروی متخصص"},
            {"fact_id": "c2", "kind": "cause", "name": "واحد بازاریابی"},
        ]
        stored_quotes = [
            {
                "mode": "indirect",
                "attributed_to": "واحد مالی",
                "quoted_text": "به دلیل کمبود نیروی متخصص 30 درصد کاهش عملکرد داریم",
            }
        ]
        with patch("auth.gate.require_permission", return_value={"id": 9}):
            with patch("playground.app._resolve_project_id", return_value=7):
                with patch(
                    "services.issue.insert_issue",
                    return_value=stored_main,
                ):
                    with patch(
                        "services.text_analysis.insert_text_analysis_facts",
                        return_value=stored_facts,
                    ) as attach_facts:
                        with patch(
                            "services.text_analysis.insert_text_analysis_quotes",
                            return_value=stored_quotes,
                        ) as attach_quotes:
                            payload = _save_issue(
                                {
                                    "text": SAMPLE_TEXT,
                                    "frame": {"title": "کاهش عملکرد واحد مالی"},
                                    "analysis_id": 21,
                                    "project_id": 7,
                                    "facts": GOLD_FACTS["facts"],
                                    "quotes": GOLD_QUOTES["quotes"],
                                }
                            )
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["analysis_reused"])
        self.assertEqual(payload["fact_count"], 5)
        values = {
            row["role"]: row["value"]
            for row in payload["facts"]
            if row["kind"] == "quantity"
        }
        self.assertEqual(values, {"total": 30, "part": 10, "remainder": 20})
        self.assertEqual(payload["quote_count"], 1)
        self.assertEqual(payload["quotes"][0]["attributed_to"], "واحد مالی")
        attach_facts.assert_called_once()
        self.assertEqual(attach_facts.call_args[0][0], 21)
        self.assertEqual(len(attach_facts.call_args[0][1]), 5)
        self.assertEqual(attach_facts.call_args[1]["created_by"], 9)
        attach_quotes.assert_called_once()
        self.assertEqual(attach_quotes.call_args[0][0], 21)
        self.assertEqual(attach_quotes.call_args[0][1][0]["attributed_to"], "واحد مالی")
        self.assertEqual(attach_quotes.call_args[1]["created_by"], 9)


    def test_save_confirmed_causes_creates_or_links_issues(self) -> None:
        stored_main = {
            "id": 10,
            "title": "کاهش عملکرد واحد مالی",
            "project_id": 7,
            "analysis_ids": [21],
            "sources": [{"id": 1, "analysis_id": 21}],
            "causes": [],
        }
        stored_staff = {
            "id": 11,
            "title": "کمبود نیروی متخصص",
            "project_id": 7,
            "analysis_ids": [21],
            "sources": [{"id": 2, "analysis_id": 21}],
            "causes": [],
        }
        link_staff = {
            "id": 1,
            "issue_id": 10,
            "cause_issue_id": 11,
            "cause_title": "کمبود نیروی متخصص",
            "cause_level_code": "cause",
            "cause_level_name": "علت",
        }
        link_marketing = {
            "id": 2,
            "issue_id": 10,
            "cause_issue_id": 12,
            "cause_title": "واحد بازاریابی",
            "cause_level_code": "cause",
            "cause_level_name": "علت",
        }
        with patch("auth.gate.require_permission", return_value={"id": 9}):
            with patch("playground.app._resolve_project_id", return_value=7):
                with patch(
                    "services.issue.insert_issue",
                    side_effect=[stored_main, stored_staff],
                ) as insert_issue:
                    with patch(
                        "services.issue.find_issue_in_project",
                        side_effect=[None, {"id": 12, "title": "واحد بازاریابی"}],
                    ) as find_issue:
                        with patch(
                            "services.issue.insert_issue_cause",
                            side_effect=[link_staff, link_marketing],
                        ) as link_cause:
                            payload = _save_issue(
                                {
                                    "text": SAMPLE_TEXT,
                                    "frame": {"title": "کاهش عملکرد واحد مالی"},
                                    "analysis_id": 21,
                                    "project_id": 7,
                                    "causes": [
                                        {
                                            "title": "کمبود نیروی متخصص",
                                            "cause_level": "cause",
                                        },
                                        {"title": "واحد بازاریابی"},
                                    ],
                                }
                            )
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["id"], 10)
        titles = [row["cause_title"] for row in payload["causes"]]
        self.assertEqual(titles, ["کمبود نیروی متخصص", "واحد بازاریابی"])
        self.assertFalse(payload["causes"][0]["reused"])
        self.assertTrue(payload["causes"][1]["reused"])
        self.assertEqual(payload["causes"][0]["cause_issue_id"], 11)
        self.assertEqual(payload["causes"][1]["cause_issue_id"], 12)
        self.assertIn("2 علت وصل شد", payload["message"])
        self.assertEqual(insert_issue.call_count, 2)
        self.assertEqual(find_issue.call_count, 2)
        self.assertEqual(link_cause.call_count, 2)
        self.assertEqual(link_cause.call_args_list[0][0][0]["issue_id"], 10)
        self.assertEqual(link_cause.call_args_list[0][0][0]["cause_issue_id"], 11)
        self.assertEqual(link_cause.call_args_list[1][0][0]["cause_issue_id"], 12)

    def test_link_cause_input_cls_is_cached(self) -> None:
        first = _link_cause_input_cls()
        second = _link_cause_input_cls()
        self.assertIs(first, second)

    def test_save_task_schema_loads_from_crud(self) -> None:
        model_cls = load_crud_symbol("schemas.crud.task", "CreateTaskInput")
        parsed = model_cls(
            project_id=1,
            title="تأمین نیروی متخصص واحد مالی",
            status="شروع نشده",
            priority="کم",
            importance="کم",
        ).model_dump()
        self.assertEqual(parsed["title"], "تأمین نیروی متخصص واحد مالی")
        link_cls = load_crud_symbol("schemas.crud.issue", "LinkIssueTaskInput")
        linked = link_cls(issue_id=10, task_id=20).model_dump()
        self.assertEqual(linked["issue_id"], 10)
        self.assertEqual(linked["task_id"], 20)

    def test_save_task_input_cls_is_cached(self) -> None:
        self.assertIs(_save_task_input_cls(), _save_task_input_cls())
        self.assertIs(_link_task_input_cls(), _link_task_input_cls())

    def test_save_confirmed_task_creates_and_links(self) -> None:
        stored_main = {
            "id": 10,
            "title": "کاهش عملکرد واحد مالی",
            "project_id": 7,
            "analysis_ids": [21],
            "sources": [{"id": 1, "analysis_id": 21}],
            "causes": [],
            "tasks": [],
        }
        link_task = {
            "id": 5,
            "issue_id": 10,
            "task_id": 33,
            "task_title": "تأمین نیروی متخصص واحد مالی",
            "analysis_ids": [21],
        }
        with patch("auth.gate.require_permission", return_value={"id": 9}):
            with patch("playground.app._resolve_project_id", return_value=7):
                with patch(
                    "services.issue.insert_issue",
                    return_value=stored_main,
                ):
                    with patch("services.task.insert_task", return_value=33) as create_task:
                        with patch(
                            "services.issue.insert_issue_task",
                            return_value=link_task,
                        ) as link:
                            with patch(
                                "services.task.fetch_task",
                                return_value={"id": 33, "priority_name": "کم"},
                            ):
                                with patch(
                                    "playground.app._attach_scoring",
                                    return_value={
                                        "importance": "زیاد",
                                        "urgency": "کم",
                                        "severity": "متوسط",
                                        "impacts": ["منابع انسانی", "کیفیت"],
                                        "status": "saved",
                                    },
                                ):
                                    with patch(
                                        "playground.app._suggest_issue_ner",
                                        return_value={"topics": [], "entities": []},
                                    ):
                                        payload = _save_issue(
                                            {
                                                "text": SAMPLE_TEXT,
                                                "frame": GOLD_FRAME["frame"],
                                                "analysis_id": 21,
                                                "project_id": 7,
                                                "task": {
                                                    "title": "تأمین نیروی متخصص واحد مالی"
                                                },
                                            }
                                        )
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["id"], 10)
        self.assertEqual(payload["task"]["task_id"], 33)
        self.assertEqual(payload["task"]["title"], "تأمین نیروی متخصص واحد مالی")
        self.assertTrue(payload["task"]["created"])
        self.assertEqual(payload["task"]["analysis_ids"], [21])
        self.assertIn("وظیفه وصل شد", payload["message"])
        create_task.assert_called_once()
        self.assertEqual(
            create_task.call_args[0][0]["title"],
            "تأمین نیروی متخصص واحد مالی",
        )
        self.assertEqual(create_task.call_args[1]["created_by"], 9)
        link.assert_called_once()
        self.assertEqual(link.call_args[0][0]["issue_id"], 10)
        self.assertEqual(link.call_args[0][0]["task_id"], 33)


    def test_scoring_schema_loads_from_crud(self) -> None:
        importance_cls = load_crud_symbol("schemas.crud.issue", "SetIssueImportanceInput")
        parsed = importance_cls(issue_id=10, importance="زیاد").model_dump()
        self.assertEqual(parsed["importance"], "زیاد")
        urgency_cls = load_crud_symbol("schemas.crud.issue", "SetIssueUrgencyInput")
        urgency = urgency_cls(issue_id=10, priority="کم").model_dump()
        self.assertEqual(urgency["priority"], "کم")
        severity_cls = load_crud_symbol("schemas.crud.issue", "SetIssueSeverityInput")
        severity = severity_cls(issue_id=10, severity="متوسط").model_dump()
        self.assertEqual(severity["severity"], "متوسط")
        impact_cls = load_crud_symbol("schemas.crud.issue", "AddIssueImpactInput")
        impact = impact_cls(issue_id=10, impact_type="کیفیت").model_dump()
        self.assertEqual(impact["impact_type"], "کیفیت")
        with self.assertRaises(Exception):
            importance_cls(issue_id=10)

    def test_scoring_input_cls_is_cached(self) -> None:
        self.assertIs(_set_importance_input_cls(), _set_importance_input_cls())
        self.assertIs(_set_urgency_input_cls(), _set_urgency_input_cls())
        self.assertIs(_set_severity_input_cls(), _set_severity_input_cls())
        self.assertIs(_add_impact_input_cls(), _add_impact_input_cls())

    def test_catalog_scoring_uses_seed_names(self) -> None:
        packed = _catalog_scoring("کم")
        self.assertEqual(packed["importance"], "زیاد")
        self.assertEqual(packed["urgency"], "کم")
        self.assertEqual(packed["severity"], "متوسط")
        self.assertEqual(
            [item["impact_type"] for item in packed["impacts"]],
            ["منابع انسانی", "کیفیت"],
        )

    def test_save_confirmed_task_writes_catalog_scoring(self) -> None:
        stored_main = {
            "id": 10,
            "title": "کاهش عملکرد واحد مالی",
            "project_id": 7,
            "analysis_ids": [21],
            "sources": [{"id": 1, "analysis_id": 21}],
            "causes": [],
            "tasks": [],
        }
        link_task = {
            "id": 5,
            "issue_id": 10,
            "task_id": 33,
            "task_title": "تأمین نیروی متخصص واحد مالی",
            "analysis_ids": [21],
        }
        scoring = {
            "importance": "زیاد",
            "urgency": "کم",
            "severity": "متوسط",
            "impacts": ["منابع انسانی", "کیفیت"],
            "status": "saved",
        }
        with patch("auth.gate.require_permission", return_value={"id": 9}):
            with patch("playground.app._resolve_project_id", return_value=7):
                with patch(
                    "services.issue.insert_issue",
                    return_value=stored_main,
                ):
                    with patch("services.task.insert_task", return_value=33):
                        with patch(
                            "services.issue.insert_issue_task",
                            return_value=link_task,
                        ):
                            with patch(
                                "services.task.fetch_task",
                                return_value={"id": 33, "priority_name": "کم"},
                            ) as fetch_task:
                                with patch(
                                    "playground.app._attach_scoring",
                                    return_value=scoring,
                                ) as attach_scoring:
                                    with patch(
                                        "playground.app._suggest_issue_ner",
                                        return_value={"topics": [], "entities": []},
                                    ):
                                        payload = _save_issue(
                                            {
                                                "text": SAMPLE_TEXT,
                                                "frame": GOLD_FRAME["frame"],
                                                "analysis_id": 21,
                                                "project_id": 7,
                                                "task": {
                                                    "title": "تأمین نیروی متخصص واحد مالی"
                                                },
                                            }
                                        )
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["scoring"]["importance"], "زیاد")
        self.assertEqual(payload["scoring"]["urgency"], "کم")
        self.assertEqual(payload["scoring"]["severity"], "متوسط")
        self.assertEqual(
            payload["scoring"]["impacts"],
            ["منابع انسانی", "کیفیت"],
        )
        self.assertIn("امتیاز مسئله ثبت شد", payload["message"])
        fetch_task.assert_called_once_with(33)
        attach_scoring.assert_called_once()
        self.assertEqual(attach_scoring.call_args[0][1], "کم")
        self.assertEqual(attach_scoring.call_args[0][2], 9)

    def test_attach_scoring_writes_catalog_fields(self) -> None:
        from playground.app import _attach_scoring

        with patch(
            "services.issue.set_issue_importance",
            return_value={"importance_name": "زیاد", "analysis_ids": [21]},
        ) as set_importance:
            with patch(
                "services.issue.set_issue_urgency",
                return_value={"priority_name": "کم", "analysis_ids": [21]},
            ) as set_urgency:
                with patch(
                    "services.issue.set_issue_severity",
                    return_value={"severity_name": "متوسط", "severity_code": "medium"},
                ) as set_severity:
                    with patch(
                        "services.issue.add_issue_impact",
                        side_effect=[
                            {
                                "impact_type_name": "منابع انسانی",
                                "impact_type_code": "hr",
                            },
                            {
                                "impact_type_name": "کیفیت",
                                "impact_type_code": "quality",
                            },
                        ],
                    ) as add_impact:
                        packed = _attach_scoring({"id": 10}, "کم", 9)
        self.assertEqual(packed["importance"], "زیاد")
        self.assertEqual(packed["urgency"], "کم")
        self.assertEqual(packed["severity"], "متوسط")
        self.assertEqual(packed["impacts"], ["منابع انسانی", "کیفیت"])
        self.assertEqual(set_importance.call_args[0][0]["importance"], "زیاد")
        self.assertEqual(set_urgency.call_args[0][0]["priority"], "کم")
        self.assertEqual(set_severity.call_args[0][0]["severity"], "متوسط")
        types = [call[0][0]["impact_type"] for call in add_impact.call_args_list]
        self.assertEqual(types, ["منابع انسانی", "کیفیت"])
        self.assertEqual(add_impact.call_count, 2)

    def test_ner_link_schema_loads_from_crud(self) -> None:
        topic_cls = load_crud_symbol("schemas.crud.issue", "LinkIssueTopicInput")
        parsed = topic_cls(issue_id=10, topic="finance.payment.delay").model_dump()
        self.assertEqual(parsed["topic"], "finance.payment.delay")
        entity_cls = load_crud_symbol("schemas.crud.issue", "LinkIssueEntityInput")
        entity = entity_cls(issue_id=10, entity_id=4, role="affected").model_dump()
        self.assertEqual(entity["role"], "affected")
        self.assertEqual(entity["entity_id"], 4)
        with self.assertRaises(Exception):
            topic_cls(issue_id=10)

    def test_ner_input_cls_is_cached(self) -> None:
        self.assertIs(_link_topic_input_cls(), _link_topic_input_cls())
        self.assertIs(_link_entity_input_cls(), _link_entity_input_cls())

    def test_unit_entity_is_suggested_as_affected(self) -> None:
        self.assertEqual(_suggested_entity_role("UNIT"), ("affected", "متأثر"))
        self.assertEqual(_suggested_entity_role("PERSON"), ("mentioned", "ذکرشده"))

    def test_save_after_scoring_returns_ner_suggestions(self) -> None:
        stored_main = {
            "id": 10,
            "title": "کاهش عملکرد واحد مالی",
            "project_id": 7,
            "analysis_ids": [21],
            "sources": [{"id": 1, "analysis_id": 21}],
            "causes": [],
            "tasks": [],
            "topics": [],
            "entities": [],
            "reused": False,
        }
        link_task = {
            "id": 5,
            "issue_id": 10,
            "task_id": 33,
            "task_title": "تأمین نیروی متخصص واحد مالی",
            "analysis_ids": [21],
        }
        suggestions = {
            "topics": [
                {
                    "topic_id": 3,
                    "code": "finance.payment.delay",
                    "name": "تأخیر پرداخت",
                }
            ],
            "entities": [
                {
                    "entity_id": 8,
                    "canonical_name": "واحد مالی",
                    "type": "UNIT",
                    "role": "affected",
                    "role_name": "متأثر",
                }
            ],
        }
        with patch("auth.gate.require_permission", return_value={"id": 9}):
            with patch("playground.app._resolve_project_id", return_value=7):
                with patch(
                    "services.issue.insert_issue",
                    return_value=stored_main,
                ):
                    with patch("services.task.insert_task", return_value=33):
                        with patch(
                            "services.issue.insert_issue_task",
                            return_value=link_task,
                        ):
                            with patch(
                                "services.task.fetch_task",
                                return_value={"id": 33, "priority_name": "کم"},
                            ):
                                with patch(
                                    "playground.app._attach_scoring",
                                    return_value={
                                        "importance": "زیاد",
                                        "urgency": "کم",
                                        "severity": "متوسط",
                                        "impacts": ["منابع انسانی", "کیفیت"],
                                        "status": "saved",
                                    },
                                ):
                                    with patch(
                                        "playground.app._suggest_issue_ner",
                                        return_value=suggestions,
                                    ) as suggest:
                                        payload = _save_issue(
                                            {
                                                "text": SAMPLE_TEXT,
                                                "frame": GOLD_FRAME["frame"],
                                                "analysis_id": 21,
                                                "project_id": 7,
                                                "task": {
                                                    "title": "تأمین نیروی متخصص واحد مالی"
                                                },
                                            }
                                        )
        self.assertEqual(payload["status"], "success")
        self.assertEqual(
            payload["suggested_topics"][0]["code"],
            "finance.payment.delay",
        )
        self.assertEqual(
            payload["suggested_entities"][0]["canonical_name"],
            "واحد مالی",
        )
        self.assertEqual(payload["suggested_entities"][0]["role"], "affected")
        self.assertEqual(payload["topics"], [])
        self.assertEqual(payload["entities"], [])
        suggest.assert_called_once_with(21)

    def test_save_confirmed_ner_links_topic_and_affected_unit(self) -> None:
        stored_main = {
            "id": 10,
            "title": "کاهش عملکرد واحد مالی",
            "project_id": 7,
            "analysis_ids": [21],
            "sources": [{"id": 1, "analysis_id": 21}],
            "causes": [],
            "tasks": [
                {"id": 5, "issue_id": 10, "task_id": 33, "task_title": "تأمین نیرو"}
            ],
            "importance": {"importance_name": "زیاد"},
            "urgency": {"priority_name": "کم"},
            "severity": {"severity_name": "متوسط"},
            "impacts": [
                {"impact_type_name": "منابع انسانی"},
                {"impact_type_name": "کیفیت"},
            ],
            "topics": [],
            "entities": [],
            "reused": True,
        }
        linked_topic = {
            "id": 1,
            "issue_id": 10,
            "topic_id": 3,
            "topic_code": "finance.payment.delay",
            "topic_name": "تأخیر پرداخت",
        }
        linked_entity = {
            "id": 2,
            "issue_id": 10,
            "entity_id": 8,
            "canonical_name": "واحد مالی",
            "entity_type": "UNIT",
            "role_code": "affected",
            "role_name": "متأثر",
        }
        with patch("auth.gate.require_permission", return_value={"id": 9}):
            with patch("playground.app._resolve_project_id", return_value=7):
                with patch(
                    "services.issue.insert_issue",
                    return_value=stored_main,
                ) as insert_issue:
                    with patch(
                        "playground.app._suggest_issue_ner",
                        return_value={
                            "topics": [{"topic_id": 3, "code": "finance.payment.delay"}],
                            "entities": [
                                {
                                    "entity_id": 8,
                                    "canonical_name": "واحد مالی",
                                    "role": "affected",
                                }
                            ],
                        },
                    ):
                        with patch(
                            "services.issue.insert_issue_topic",
                            return_value=linked_topic,
                        ) as link_topic:
                            with patch(
                                "services.issue.insert_issue_entity",
                                return_value=linked_entity,
                            ) as link_entity:
                                payload = _save_issue(
                                    {
                                        "text": SAMPLE_TEXT,
                                        "frame": GOLD_FRAME["frame"],
                                        "analysis_id": 22,
                                        "project_id": 7,
                                        "topics": [
                                            {
                                                "topic_id": 3,
                                                "code": "finance.payment.delay",
                                            }
                                        ],
                                        "entities": [
                                            {
                                                "entity_id": 8,
                                                "role": "affected",
                                            }
                                        ],
                                    }
                                )
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["reused"])
        self.assertEqual(payload["id"], 10)
        self.assertEqual(payload["topics"][0]["topic_code"], "finance.payment.delay")
        self.assertEqual(payload["entities"][0]["canonical_name"], "واحد مالی")
        self.assertEqual(payload["entities"][0]["role_code"], "affected")
        self.assertIn("موضوع و موجودیت به مسئله وصل شد", payload["message"])
        insert_issue.assert_called_once()
        self.assertEqual(insert_issue.call_args[0][0]["analysis_id"], 22)
        self.assertEqual(insert_issue.call_args[0][0]["title"], "کاهش عملکرد واحد مالی")
        link_topic.assert_called_once()
        self.assertEqual(link_topic.call_args[0][0]["issue_id"], 10)
        self.assertEqual(link_topic.call_args[0][0]["topic_id"], 3)
        link_entity.assert_called_once()
        self.assertEqual(link_entity.call_args[0][0]["entity_id"], 8)
        self.assertEqual(link_entity.call_args[0][0]["role"], "affected")
        self.assertNotIn("وظیفه وصل شد", payload["message"])


if __name__ == "__main__":
    unittest.main()
