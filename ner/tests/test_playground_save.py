"""ذخیره playground نباید با بستهٔ هم‌نام ner به ImportError بخورد."""

from pathlib import Path
import os
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path, load_crud_symbol

ensure_import_path()

from errors.crud import PermissionDeniedError
from playground.app import _save_extract, _save_input_cls


class PlaygroundSaveImportTests(unittest.TestCase):
    """اسکیمای کراد جدا از schemas همنام ner بار می‌شود."""

    def test_save_schema_loads_from_crud(self) -> None:
        model_cls = load_crud_symbol(
            "schemas.crud.text_analysis",
            "SaveTextAnalysisInput",
        )
        parsed = model_cls(
            source_type="content",
            text="پیمانکار تا پایان هفته قطعه را می‌رساند.",
            mentions=[
                {
                    "type": "TIME",
                    "canonical_name": "پایان هفته",
                    "mention_text": "پایان هفته",
                    "start_offset": 12,
                    "end_offset": 22,
                    "confidence": 0.7,
                }
            ],
            keywords=[
                {
                    "phrase": "پایان هفته",
                    "mention_text": "پایان هفته",
                    "start_offset": 12,
                    "end_offset": 22,
                    "confidence": 0.7,
                }
            ],
            discourses=[
                {
                    "code": "issue",
                    "is_primary": True,
                    "mention_text": "قطعه را می‌رساند",
                    "confidence": 0.8,
                    "slots": {"چیز درگیر": "قطعه"},
                },
                {
                    "code": "commitment",
                    "name": "تعهد",
                    "discovered": True,
                    "definition": "اعلام پایبندی",
                    "is_primary": False,
                    "mention_text": "می‌رساند",
                    "confidence": 0.8,
                    "slots": {"متعهد": "می‌رساند"},
                    "type_schema": {
                        "code": "commitment",
                        "name": "تعهد",
                        "definition": "اعلام پایبندی",
                        "required_slots": [{"name": "متعهد", "description": ""}],
                    },
                },
            ],
            intents=[
                {
                    "code": "inform",
                    "is_primary": True,
                    "mention_text": "می‌رساند",
                    "confidence": 0.7,
                }
            ],
            rhetorics=[
                {
                    "code": "literal",
                    "is_primary": True,
                    "mention_text": "می‌رساند",
                    "confidence": 0.8,
                    "intended_meaning": "پیمانکار قطعه را می‌رساند",
                    "slots": {"محتوا": "می‌رساند"},
                }
            ],
        ).model_dump()
        self.assertEqual(parsed["source_type"], "content")
        self.assertEqual(parsed["mentions"][0]["type"], "TIME")
        self.assertEqual(parsed["keywords"][0]["phrase"], "پایان هفته")
        self.assertEqual(parsed["discourses"][0]["mention_text"], "قطعه را می‌رساند")
        self.assertTrue(parsed["discourses"][1]["discovered"])
        self.assertEqual(parsed["discourses"][1]["code"], "commitment")
        self.assertEqual(parsed["discourses"][1]["definition"], "اعلام پایبندی")
        self.assertEqual(parsed["discourses"][1]["slots"]["متعهد"], "می‌رساند")
        self.assertEqual(parsed["intents"][0]["mention_text"], "می‌رساند")
        self.assertEqual(parsed["rhetorics"][0]["code"], "literal")
        self.assertEqual(
            parsed["rhetorics"][0]["intended_meaning"],
            "پیمانکار قطعه را می‌رساند",
        )
        from schemas.output import EntityMentionHit

        hit = EntityMentionHit(
            type="PERSON",
            canonical_name="سارا",
            normalized_name="سارا",
            mention_text="سارا",
            start_offset=0,
            end_offset=4,
            confidence=1,
        )
        self.assertEqual(hit.type, "PERSON")

    def test_save_input_cls_is_cached(self) -> None:
        first = _save_input_cls()
        second = _save_input_cls()
        self.assertIs(first, second)

    def test_save_without_actor_is_permission_denied(self) -> None:
        previous_id = os.environ.pop("MCP_ACTOR_USER_ID", None)
        previous_username = os.environ.pop("MCP_ACTOR_USERNAME", None)
        try:
            with self.assertRaises(PermissionDeniedError):
                _save_extract(
                    {
                        "source_type": "content",
                        "text": "متن کوتاه برای ذخیره آزمایشی.",
                        "mentions": [],
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


if __name__ == "__main__":
    unittest.main()
