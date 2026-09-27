"""رتبه‌بندی کسینوس بدون سرویس مدل."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from business_logic.repository import as_pgvector
from business_logic.similarity import cosine, rank_hits
from errors.crud import InvalidInputError


class SimilarityTests(unittest.TestCase):
    """hitهای یک تحلیل باید در یک نتیجه جمع شوند."""

    def test_identical_vectors_are_one(self) -> None:
        self.assertAlmostEqual(cosine([1, 0], [1, 0]), 1.0)

    def test_pgvector_literal_has_locked_width(self) -> None:
        from business_logic.config import EMBEDDING_DIMENSIONS

        literal = as_pgvector([0.0] * EMBEDDING_DIMENSIONS)
        self.assertTrue(literal.startswith("["))
        self.assertTrue(literal.endswith("]"))
        self.assertEqual(literal.count(",") + 1, EMBEDDING_DIMENSIONS)
        with self.assertRaises(InvalidInputError):
            as_pgvector([0.0, 1.0])

    def test_rank_groups_same_analysis(self) -> None:
        rows = [
            {
                "analysis_id": 1,
                "source_type": "content",
                "source_id": 9,
                "kind": "intent",
                "record_id": 4,
                "chunk_index": 0,
                "embedded_text": "نیت: شکایت",
                "embedding": [1.0, 0.0],
            },
            {
                "analysis_id": 1,
                "source_type": "content",
                "source_id": 9,
                "kind": "raw",
                "record_id": None,
                "chunk_index": 0,
                "embedded_text": "متن شکایت",
                "embedding": [0.8, 0.2],
            },
            {
                "analysis_id": 2,
                "source_type": "content",
                "source_id": 10,
                "kind": "entity",
                "record_id": 7,
                "chunk_index": 0,
                "embedded_text": "موجودیت: فرد",
                "embedding": [0.0, 1.0],
            },
        ]
        grouped = rank_hits([1.0, 0.0], rows, limit=5)
        self.assertEqual(grouped[0]["analysis_id"], 1)
        self.assertEqual(grouped[0]["source_id"], 9)
        kinds = {item["kind"] for item in grouped[0]["hits"]}
        self.assertEqual(kinds, {"intent", "raw"})
        self.assertNotIn("embedding", grouped[0])

    def test_rank_uses_sql_score_without_embedding(self) -> None:
        grouped = rank_hits(
            [1.0, 0.0],
            [
                {
                    "analysis_id": 3,
                    "source_type": "message",
                    "source_id": 11,
                    "kind": "raw",
                    "record_id": None,
                    "chunk_index": 0,
                    "embedded_text": "گزارش. قطعی سرور",
                    "score": 0.91,
                }
            ],
            limit=3,
        )
        self.assertEqual(grouped[0]["analysis_id"], 3)
        self.assertAlmostEqual(grouped[0]["score"], 0.91)


if __name__ == "__main__":
    unittest.main()
