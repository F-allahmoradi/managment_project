"""کاتالوگ زمین بازی: یک بخش برای هر MCP، نه برای هر tool."""

from pathlib import Path
import sys
import unittest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from playground.hub import SECTIONS, catalog, extract_nlp, load_nlp_sample, load_search_samples, snapshot


class HubCatalogTests(unittest.TestCase):
    """بخش‌ها باید سرور MCP باشند."""

    def test_one_section_per_mcp(self) -> None:
        ids = [item["id"] for item in SECTIONS]
        self.assertEqual(
            ids,
            [
                "embedding",
                "ner",
                "crud",
                "meeting",
                "finance",
                "stats",
                "reminder",
                "nlp",
            ],
        )
        servers = [item["server"] for item in SECTIONS]
        self.assertEqual(len(servers), len(set(servers)))
        packed = catalog()
        self.assertEqual(packed["status"], "success")
        self.assertEqual(len(packed["sections"]), 8)
        embedding = next(item for item in SECTIONS if item["id"] == "embedding")
        self.assertEqual(embedding["ui"], "embedding")
        self.assertEqual(embedding["server"], "management-embedding")
        nlp = next(item for item in SECTIONS if item["id"] == "nlp")
        self.assertEqual(nlp["ui"], "nlp-extract")
        self.assertEqual(nlp["server"], "management-nlp")
        packed = snapshot("nlp")
        self.assertEqual(packed["status"], "error")
        self.assertEqual(packed["error_code"], "NOT_FOUND")
        sample = load_nlp_sample()
        self.assertEqual(sample["status"], "success")
        self.assertIn("واحد مالی", sample["text"])
        self.assertTrue(callable(extract_nlp))
        html = (_ROOT / "playground/static/index.html").read_text(encoding="utf-8")
        self.assertIn('id="btn-nlp-extract"', html)
        self.assertIn('id="nlp-text"', html)
        self.assertIn('id="search-samples"', html)
        self.assertIn('id="source-type"', html)
        self.assertIn('id="index-error"', html)
        app_py = (_ROOT / "playground/app.py").read_text(encoding="utf-8")
        self.assertIn("/api/mcp/nlp/extract", app_py)
        self.assertIn("/api/search-samples", app_py)
        samples = load_search_samples()
        self.assertEqual(samples["status"], "success")
        labels = [item["label"] for item in samples["samples"]]
        self.assertIn("تأخیر پرداخت", labels)
        self.assertIn("کنترل منفی", labels)
        self.assertIn("دام آمار", labels)
        self.assertGreaterEqual(len(samples["samples"]), 8)


if __name__ == "__main__":
    unittest.main()
