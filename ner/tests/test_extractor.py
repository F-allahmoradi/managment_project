"""تست استخراج موجودیت؛ مدل زبانی در تست شبیه‌سازی می‌شود."""

from pathlib import Path
from unittest.mock import patch
import sys
import unittest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.config import (
    load_discourse_catalog,
    load_discourse_discovery,
    load_intent_catalog,
    load_rhetoric_catalog,
    load_topic_catalog,
)
from business_logic.extractor import (
    extract_discourse,
    extract_entities,
    extract_intent,
    extract_keywords,
    extract_rhetoric,
    extract_sentiment,
    extract_topics,
    _discourses_prompt,
    _intents_prompt,
    _rhetorics_prompt,
    _topics_prompt,
)
from business_logic.layers.span import drop_entity_copy_keywords
from errors.crud import CONFIG_ERROR, INVALID_INPUT, LLM_ERROR, ConfigError, LlmError
from mcp_server.tools.extract.extract_entities import run_extract_entities
from schemas.input import ExtractEntitiesInput
from tests.sample import SAMPLE_TEXT


def _mentions(*items) -> dict:
    return {"mentions": list(items)}


class ExtractorTests(unittest.TestCase):
    """خروجی مدل پس از قفل نوع باید ذکر معتبر شود."""

    def test_llm_payload_fills_mentions(self) -> None:
        fake = _mentions(
            {
                "type": "PERSON",
                "canonical_name": "سارا احمدی",
                "mention_text": "سارا احمدی",
                "confidence": 0.95,
            },
            {
                "type": "UNIT",
                "canonical_name": "واحد مالی",
                "mention_text": "واحد مالی",
                "confidence": 0.9,
            },
        )
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_entities(SAMPLE_TEXT)
        types = {item.type for item in result.mentions}
        self.assertEqual(types, {"PERSON", "UNIT"})
        self.assertEqual(result.extracted_count, 2)
        self.assertEqual(result.canonical_count, 2)
        self.assertEqual(result.table, "entity_mentions")

    def test_unknown_type_is_dropped(self) -> None:
        fake = _mentions(
            {
                "type": "ACTION",
                "canonical_name": "پیگیری",
                "mention_text": "پیگیری",
                "confidence": 0.9,
            },
            {
                "type": "ROLE",
                "canonical_name": "مدیر پروژه",
                "mention_text": "مدیر پروژه",
                "confidence": 0.9,
            },
        )
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_entities(SAMPLE_TEXT)
        self.assertEqual([item.type for item in result.mentions], ["ROLE"])

    def test_mention_not_in_text_is_dropped(self) -> None:
        fake = _mentions(
            {
                "type": "PERSON",
                "canonical_name": "شخص خیالی",
                "mention_text": "شخص خیالی",
                "confidence": 0.8,
            }
        )
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_entities(SAMPLE_TEXT)
        self.assertEqual(result.extracted_count, 0)

    def test_time_fills_occurred_at_from_persian_mention(self) -> None:
        fake = _mentions(
            {
                "type": "TIME",
                "canonical_name": "۱۷ شهریور ۱۴۰۴",
                "mention_text": "۱۷ شهریور ۱۴۰۴",
                "confidence": 0.8,
            }
        )
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_entities(SAMPLE_TEXT)
        self.assertEqual(result.mentions[0].type, "TIME")
        self.assertEqual(result.mentions[0].occurred_at, "2025-09-08 00:00:00")

    def test_time_parses_hour_from_mention(self) -> None:
        fake = _mentions(
            {
                "type": "TIME",
                "canonical_name": "۲۵ شهریور ۱۴۰۴ ساعت ۱۶",
                "mention_text": "چهارشنبه ۲۵ شهریور ۱۴۰۴ ساعت ۱۶",
                "confidence": 0.9,
            }
        )
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_entities(SAMPLE_TEXT)
        self.assertEqual(result.mentions[0].occurred_at, "2025-09-16 16:00:00")

    def test_duplicate_span_is_collapsed(self) -> None:
        fake = _mentions(
            {
                "type": "PLACE",
                "canonical_name": "کارگاه جنوبی",
                "mention_text": "کارگاه جنوبی",
                "confidence": 0.9,
            },
            {
                "type": "PLACE",
                "canonical_name": "کارگاه جنوبی",
                "mention_text": "کارگاه جنوبی",
                "confidence": 0.7,
            },
        )
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_entities(SAMPLE_TEXT)
        self.assertEqual(result.extracted_count, 1)

    def test_empty_text_is_invalid(self) -> None:
        with self.assertRaises(Exception):
            ExtractEntitiesInput(text="   ")

    def test_tool_rejects_blank_text(self) -> None:
        payload = run_extract_entities(text="  ")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], INVALID_INPUT)

    def test_tool_returns_mentions(self) -> None:
        fake = _mentions(
            {
                "type": "ORG",
                "canonical_name": "پارس‌سازه",
                "mention_text": "شرکت پارس‌سازه",
                "confidence": 0.9,
            }
        )
        with patch("business_logic.extractor.complete_json", return_value=fake):
            payload = run_extract_entities(text=SAMPLE_TEXT)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["mentions"][0]["type"], "ORG")
        self.assertNotIn("writes_postgres", payload)

    def test_llm_error_is_mapped(self) -> None:
        with patch(
            "business_logic.extractor.complete_json",
            side_effect=LlmError("اتصال به سرویس مدل زبانی برقرار نشد"),
        ):
            payload = run_extract_entities(text=SAMPLE_TEXT)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], LLM_ERROR)

    def test_missing_api_key_is_config_error(self) -> None:
        with patch(
            "business_logic.extractor.complete_json",
            side_effect=ConfigError("کلید مدل زبانی در متغیر NER_LLM_API_KEY نیست"),
        ):
            payload = run_extract_entities(text=SAMPLE_TEXT)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], CONFIG_ERROR)

    def test_topics_and_keywords_are_extracted(self) -> None:
        topics_fake = {
            "topics": [
                {
                    "code": "finance.payment.delay",
                    "is_primary": True,
                    "mention_text": "پرداخت پیمانکار",
                    "confidence": 0.92,
                },
                {
                    "code": "unknown.topic",
                    "is_primary": False,
                    "mention_text": "پرداخت",
                    "confidence": 0.5,
                },
            ]
        }
        keywords_fake = {
            "keywords": [
                {
                    "phrase": "پرداخت پیمانکار",
                    "mention_text": "پرداخت پیمانکار",
                    "confidence": 0.88,
                },
                {
                    "phrase": "عبارت خیالی",
                    "mention_text": "عبارت خیالی",
                    "confidence": 0.8,
                },
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=topics_fake):
            topics = extract_topics(SAMPLE_TEXT)
        with patch("business_logic.extractor.complete_json", return_value=keywords_fake):
            keywords = extract_keywords(SAMPLE_TEXT)
        self.assertEqual(topics.topic_count, 1)
        self.assertEqual(topics.topics[0].code, "finance.payment.delay")
        self.assertEqual(topics.topics[0].path, ["مالی", "پرداخت", "تأخیر پرداخت"])
        self.assertEqual(
            topics.topics[0].path_codes,
            ["finance", "finance.payment", "finance.payment.delay"],
        )
        self.assertEqual(topics.topics[0].parent_code, "finance.payment")
        self.assertTrue(topics.topics[0].is_primary)
        self.assertEqual(keywords.keyword_count, 1)
        self.assertEqual(keywords.keywords[0].phrase, "پرداخت پیمانکار")

    def test_near_topic_codes_map_to_catalog(self) -> None:
        fake = {
            "topics": [
                {
                    "code": "finance.delay",
                    "is_primary": True,
                    "mention_text": "تأخیر",
                    "confidence": 0.8,
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_topics("سه هفته تأخیر در پرداخت")
        self.assertEqual(result.topic_count, 1)
        self.assertEqual(result.topics[0].code, "finance.payment.delay")

    def test_project_text_always_gets_a_topic(self) -> None:
        fake = {"topics": [{"code": "contractor", "is_primary": True, "confidence": 0.7}]}
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_topics("پیمانکار بی‌هماهنگی برق را قطع کرد")
        codes = {item.code for item in result.topics}
        self.assertGreaterEqual(result.topic_count, 1)
        self.assertTrue(codes & {"tech.hardware", "procurement", "management", "legal"})

    def test_empty_topic_payload_falls_back_to_cues(self) -> None:
        with patch("business_logic.extractor.complete_json", return_value={"topics": []}):
            result = extract_topics("سرور پشتیبان از دیشب قطع است.")
        codes = {item.code for item in result.topics}
        self.assertIn("tech.hardware", codes)

    def test_out_of_domain_text_is_still_named(self) -> None:
        fake = {"topics": [{"code": "management", "is_primary": True, "confidence": 0.9}]}
        with patch("business_logic.extractor.complete_json", return_value=fake):
            with patch("business_logic.extractor.persist_discovered_topics"):
                result = extract_topics("برای تربیت فرزند باید صبور بود و حد مشخص گذاشت.")
        self.assertEqual(result.topic_count, 1)
        self.assertTrue(result.topics[0].discovered)
        self.assertIn("تربیت فرزند", result.topics[0].name)
        self.assertIn("در درخت حوزه نبود", result.message)

    def test_discovered_topic_without_english_code_is_kept(self) -> None:
        fake = {
            "topics": [
                {
                    "name": "تربیت فرزند",
                    "discovered": True,
                    "definition": "آموزش و حدگذاری برای رفتار فرزند",
                    "is_primary": True,
                    "confidence": 0.8,
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            with patch("business_logic.extractor.persist_discovered_topics"):
                result = extract_topics("برای تربیت فرزند باید صبور بود و حد مشخص گذاشت.")
        self.assertEqual(result.topic_count, 1)
        self.assertEqual(result.topics[0].name, "تربیت فرزند")
        self.assertTrue(result.topics[0].discovered)
        self.assertTrue(result.topics[0].code)

    def test_discovered_topic_is_kept(self) -> None:
        fake = {
            "topics": [
                {
                    "code": "parenting",
                    "name": "تربیت فرزند",
                    "discovered": True,
                    "definition": "آموزش و حدگذاری برای رفتار فرزند",
                    "is_primary": True,
                    "mention_text": "تربیت فرزند",
                    "confidence": 0.85,
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            with patch("business_logic.extractor.persist_discovered_topics"):
                result = extract_topics("برای تربیت فرزند باید صبور بود و حد مشخص گذاشت.")
        self.assertEqual(result.topic_count, 1)
        self.assertEqual(result.topics[0].code, "parenting")
        self.assertEqual(result.topics[0].name, "تربیت فرزند")
        self.assertTrue(result.topics[0].discovered)
        self.assertIn("در درخت حوزه نبود", result.message)

    def test_topics_prompt_explains_each_node(self) -> None:
        prompt = _topics_prompt()
        hardware = next(
            item for item in load_topic_catalog() if item["code"] == "tech.hardware"
        )
        self.assertIn("تجهیزات فیزیکی", hardware["definition"])
        self.assertIn(hardware["definition"], prompt)
        self.assertIn("management is fallback only", prompt)
        self.assertIn("discovered=true", prompt)
        self.assertIn("Never return an empty topics array", prompt)
        self.assertIn("تربیت فرزند", prompt)
        self.assertIn("    definition:", prompt)
        self.assertIn("    not:", prompt)
        self.assertIn("    yes:", prompt)
        self.assertIn("finance.payment.delay", prompt)

    def test_sentiment_and_emotions_are_extracted(self) -> None:
        fake = {
            "sentiment": {
                "polarity": "negative",
                "intensity": "high",
                "mention_text": "هنوز تسک",
                "confidence": 0.91,
            },
            "emotions": [
                {
                    "emotion": "worry",
                    "intensity": "medium",
                    "mention_text": "قطع شد",
                    "confidence": 0.8,
                },
                {
                    "emotion": "not-an-emotion",
                    "intensity": "high",
                    "mention_text": "قطع شد",
                    "confidence": 0.9,
                },
            ],
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_sentiment(SAMPLE_TEXT)
        self.assertIsNotNone(result.sentiment)
        self.assertEqual(result.sentiment.polarity, "negative")
        self.assertEqual(result.sentiment.polarity_name, "منفی")
        self.assertEqual(result.sentiment.intensity, "high")
        self.assertEqual(result.emotion_count, 1)
        self.assertEqual(result.emotions[0].emotion, "worry")

    def test_unknown_polarity_is_dropped(self) -> None:
        fake = {
            "sentiment": {"polarity": "mixed", "intensity": "high", "confidence": 0.9},
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_sentiment(SAMPLE_TEXT)
        self.assertIsNone(result.sentiment)

    def test_keyword_that_copies_an_entity_is_dropped(self) -> None:
        mentions_fake = _mentions(
            {
                "type": "UNIT",
                "canonical_name": "واحد مالی",
                "mention_text": "واحد مالی",
                "confidence": 0.9,
            }
        )
        keywords_fake = {
            "keywords": [
                {
                    "phrase": "واحد مالی",
                    "mention_text": "واحد مالی",
                    "confidence": 0.9,
                },
                {
                    "phrase": "گزارش پیشرفت",
                    "mention_text": "گزارش پیشرفت",
                    "confidence": 0.8,
                },
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=mentions_fake):
            entities = extract_entities(SAMPLE_TEXT)
        with patch("business_logic.extractor.complete_json", return_value=keywords_fake):
            keywords = extract_keywords(SAMPLE_TEXT)
        kept = drop_entity_copy_keywords(keywords.keywords, entities.mentions)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].phrase, "گزارش پیشرفت")

    def test_unknown_topic_is_named_from_text(self) -> None:
        fake = {
            "topics": [{"code": "not-a-topic", "mention_text": "تربیت", "confidence": 0.9}],
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            with patch("business_logic.extractor.persist_discovered_topics"):
                result = extract_topics("برای تربیت فرزند باید صبور بود و حد مشخص گذاشت.")
        self.assertEqual(result.topic_count, 1)
        self.assertTrue(result.topics[0].discovered)
        self.assertTrue(result.topics[0].name)

    def test_discourse_and_intent_are_extracted_separately(self) -> None:
        discourse_fake = {
            "discourses": [
                {
                    "code": "issue",
                    "is_primary": True,
                    "mention_text": "سرور پشتیبان",
                    "confidence": 0.93,
                    "slots": {"چیز درگیر": "سرور پشتیبان"},
                },
                {
                    "code": "request",
                    "is_primary": False,
                    "mention_text": "درخواست کرده",
                    "confidence": 0.8,
                },
                {
                    "code": "problem",
                    "is_primary": False,
                    "mention_text": "قطع شد",
                    "confidence": 0.7,
                },
            ]
        }
        intent_fake = {
            "intents": [
                {
                    "code": "report_problem",
                    "is_primary": True,
                    "mention_text": "قطع شد",
                    "confidence": 0.9,
                },
                {
                    "code": "question",
                    "is_primary": False,
                    "mention_text": "درخواست",
                    "confidence": 0.4,
                },
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=discourse_fake):
            discourses = extract_discourse(SAMPLE_TEXT)
        with patch("business_logic.extractor.complete_json", return_value=intent_fake):
            intents = extract_intent(SAMPLE_TEXT)
        self.assertEqual(discourses.discourse_count, 2)
        self.assertEqual(discourses.discourses[0].code, "request")
        self.assertTrue(discourses.discourses[0].is_primary)
        self.assertEqual(discourses.discourses[1].code, "issue")
        self.assertEqual(intents.intent_count, 1)
        self.assertEqual(intents.intents[0].code, "report_problem")
        self.assertTrue(intents.intents[0].is_primary)

    def test_discourse_alias_problem_maps_to_issue(self) -> None:
        fake = {
            "discourses": [
                {
                    "code": "مشکل",
                    "is_primary": True,
                    "mention_text": "قطع شد",
                    "confidence": 0.88,
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_discourse(SAMPLE_TEXT)
        self.assertEqual(result.discourse_count, 1)
        self.assertEqual(result.discourses[0].code, "issue")
        self.assertEqual(result.discourses[0].name, "مسئله")

    def test_unknown_intent_is_dropped(self) -> None:
        fake = {
            "intents": [{"code": "warn", "mention_text": "قطع شد", "confidence": 0.9}],
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_intent(SAMPLE_TEXT)
        self.assertEqual(result.intent_count, 0)

    def test_catalog_keeps_genre_and_slot_descriptions(self) -> None:
        issue = next(item for item in load_discourse_catalog() if item["code"] == "issue")
        self.assertIn("اختلال یا مانع فعلی", issue["description"])
        required = {slot["name"]: slot["description"] for slot in issue["required_slots"]}
        self.assertIn("بیان‌کننده", required)
        self.assertTrue(required["شرح اختلال یا مانع"])
        complaint = next(item for item in load_intent_catalog() if item["code"] == "complaint")
        self.assertIn("مشتکی‌عنه", complaint["description"])
        discourse_prompt = _discourses_prompt()
        self.assertIn("required slots:", discourse_prompt)
        self.assertIn("آمر دارای اختیار:", discourse_prompt)
        self.assertIn("description:", discourse_prompt)
        self.assertIn("شاکی:", _intents_prompt())
        self.assertIn("Intended meaning", _intents_prompt("پرداخت قفل شده"))
        self.assertIn("Irony/sarcasm", _intents_prompt())

    def test_rhetoric_irony_fills_intended_meaning(self) -> None:
        fake = {
            "rhetorics": [
                {
                    "code": "irony",
                    "is_primary": True,
                    "mention_text": "قطع شد",
                    "confidence": 0.9,
                    "slots": {"ظاهر": "چه عالی", "مقصود": "سرور دوباره قطع شده"},
                }
            ],
            "intended_meaning": "سرور دوباره قطع شده و گوینده معترض است",
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_rhetoric("چه عالی، باز هم سرور قطع شد.")
        self.assertEqual(result.rhetoric_count, 1)
        self.assertEqual(result.rhetorics[0].code, "irony")
        self.assertTrue(result.rhetorics[0].is_primary)
        self.assertEqual(
            result.intended_meaning,
            "سرور دوباره قطع شده و گوینده معترض است",
        )
        self.assertEqual(result.rhetorics[0].slots["ظاهر"], "چه عالی")
        prompt = _rhetorics_prompt()
        self.assertIn("literal is fallback only", prompt)
        self.assertIn("طعنه", prompt)
        irony = next(item for item in load_rhetoric_catalog() if item["code"] == "irony")
        self.assertIn("خلاف ظاهر", irony["definition"])

    def test_unknown_rhetoric_is_dropped(self) -> None:
        fake = {
            "rhetorics": [{"code": "pun", "mention_text": "قطع شد", "confidence": 0.9}],
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_rhetoric(SAMPLE_TEXT)
        self.assertEqual(result.rhetoric_count, 0)

    def test_discovery_policy_is_loaded(self) -> None:
        discovery = load_discourse_discovery()
        self.assertTrue(discovery["enabled"])
        self.assertTrue(discovery["do_not_force_fit"])
        self.assertGreaterEqual(discovery["min_required_slots"], 2)
        prompt = _discourses_prompt()
        self.assertIn("Open discovery:", prompt)
        self.assertIn("discovered=true", prompt)

    def test_structured_new_discourse_is_kept(self) -> None:
        text = "متعهد می‌شوم قطعه را به کارگاه جنوبی برسانم."
        fake = {
            "discourses": [
                {
                    "code": "commitment",
                    "name": "تعهد",
                    "discovered": True,
                    "definition": "اعلام پایبندی گوینده به انجام یک کار",
                    "is_primary": True,
                    "mention_text": "متعهد می‌شوم قطعه را به کارگاه جنوبی برسانم",
                    "confidence": 0.88,
                    "required_slots": [
                        {"name": "متعهد", "description": "کسی که پایبندی را اعلام می‌کند"},
                        {"name": "عمل تعهدشده", "description": "کاری که قول داده شده"},
                    ],
                    "slots": {
                        "متعهد": "متعهد می‌شوم",
                        "عمل تعهدشده": "قطعه را به کارگاه جنوبی برسانم",
                    },
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            with patch("business_logic.extractor.persist_discovered_discourses"):
                result = extract_discourse(text)
        self.assertEqual(result.discourse_count, 1)
        self.assertEqual(result.discourses[0].code, "commitment")
        self.assertEqual(result.discourses[0].name, "تعهد")
        self.assertTrue(result.discourses[0].discovered)
        self.assertTrue(result.discourses[0].is_primary)
        self.assertEqual(result.discourses[0].slots["متعهد"], "متعهد می‌شوم")
        self.assertIsNotNone(result.discourses[0].type_schema)
        self.assertIn("نوع کشف‌شده", result.message)

    def test_unknown_discourse_without_structure_is_dropped(self) -> None:
        fake = {
            "discourses": [
                {
                    "code": "not_a_genre",
                    "mention_text": "سرور پشتیبان",
                    "confidence": 0.9,
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_discourse(SAMPLE_TEXT)
        self.assertEqual(result.discourse_count, 0)

    def test_discovered_synonym_is_not_forced_as_new_type(self) -> None:
        fake = {
            "discourses": [
                {
                    "code": "server_fault",
                    "name": "مسئله",
                    "discovered": True,
                    "definition": "اختلال سرور",
                    "mention_text": "سرور پشتیبان",
                    "confidence": 0.9,
                    "required_slots": [{"name": "چیز درگیر"}, {"name": "شرح اختلال یا مانع"}],
                    "slots": {
                        "چیز درگیر": "سرور پشتیبان",
                        "شرح اختلال یا مانع": "قطع شد",
                    },
                }
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            result = extract_discourse(SAMPLE_TEXT)
        self.assertEqual(result.discourse_count, 1)
        self.assertEqual(result.discourses[0].code, "issue")
        self.assertFalse(result.discourses[0].discovered)

    def test_discovered_type_is_kept_instead_of_message_fallback(self) -> None:
        text = "متعهد می‌شوم قطعه را به کارگاه جنوبی برسانم."
        fake = {
            "discourses": [
                {
                    "code": "message",
                    "is_primary": True,
                    "mention_text": "متعهد می‌شوم",
                    "confidence": 0.4,
                },
                {
                    "code": "pledge",
                    "name": "تعهد",
                    "discovered": True,
                    "definition": "اعلام پایبندی به انجام کار",
                    "mention_text": "متعهد می‌شوم قطعه را به کارگاه جنوبی برسانم",
                    "confidence": 0.84,
                    "required_slots": [
                        {"name": "متعهد"},
                        {"name": "عمل تعهدشده"},
                    ],
                    "slots": {
                        "متعهد": "متعهد می‌شوم",
                        "عمل تعهدشده": "قطعه را به کارگاه جنوبی برسانم",
                    },
                },
            ]
        }
        with patch("business_logic.extractor.complete_json", return_value=fake):
            with patch("business_logic.extractor.persist_discovered_discourses"):
                result = extract_discourse(text)
        codes = [item.code for item in result.discourses]
        self.assertIn("pledge", codes)
        self.assertNotIn("message", codes)
        self.assertTrue(result.discourses[0].discovered)

    def test_persist_keeps_previous_discovered_type(self) -> None:
        from business_logic.layers.discovery import persist_discovered_discourses
        from schemas.output import DiscourseHit, DiscourseTypeSchema

        target = _ROOT / "tests" / "_tmp_discovered_discourses.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: target.unlink(missing_ok=True))
        target.write_text(
            "discourses:\n  - code: apology\n    name: عذرخواهی\n    definition: پوزش\n    discovered: true\n",
            encoding="utf-8",
        )
        hit = DiscourseHit(
            code="pledge",
            name="تعهد",
            is_primary=True,
            mention_text="متعهد می‌شوم",
            confidence=0.9,
            discovered=True,
            type_schema=DiscourseTypeSchema(
                code="pledge",
                name="تعهد",
                definition="اعلام پایبندی",
                required_slots=[{"name": "متعهد", "description": ""}],
            ),
        )
        persist_discovered_discourses([hit], path=target)
        loaded = target.read_text(encoding="utf-8")
        self.assertIn("apology", loaded)
        self.assertIn("pledge", loaded)
        persist_discovered_discourses([hit], path=target)
        again = yaml.safe_load(target.read_text(encoding="utf-8"))
        codes = [row["code"] for row in again["discourses"]]
        self.assertEqual(codes.count("pledge"), 1)
        self.assertIn("apology", codes)


if __name__ == "__main__":
    unittest.main()
