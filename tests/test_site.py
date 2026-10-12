import json
import unittest

from src.config import load_config
from src.manifest import MANIFEST_NAME
from src.paths import PROJECT_ROOT

DOCS_PATH = PROJECT_ROOT / "site" / "docs.json"
ARCHIVE_PATH = "archives/archive_{year}.json"


class SiteDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.docs = json.loads(DOCS_PATH.read_text(encoding="utf-8"))

    def test_documents_exactly_the_published_files(self) -> None:
        published = {
            f"{scraper.file_name}.json" for scraper in load_config().scrapers.values()
        } | {ARCHIVE_PATH, MANIFEST_NAME}
        documented = [endpoint["path"] for endpoint in self.docs["endpoints"]]

        self.assertEqual(len(documented), len(set(documented)))
        self.assertEqual(set(documented), published)

    def test_every_endpoint_is_fully_described(self) -> None:
        ids = [endpoint["id"] for endpoint in self.docs["endpoints"]]
        self.assertEqual(len(ids), len(set(ids)))

        for endpoint in self.docs["endpoints"]:
            with self.subTest(endpoint=endpoint["id"]):
                for key in ("title", "summary", "structure"):
                    self.assertTrue(endpoint[key].strip())
                self.assertTrue(endpoint["fields"])
                for field in endpoint["fields"]:
                    self.assertTrue(field["name"].strip())
                    self.assertTrue(field["description"].strip())

    def test_changelog_is_newest_first(self) -> None:
        dates = [release["date"] for release in self.docs["changelog"]]
        self.assertEqual(dates, sorted(dates, reverse=True))
        for release in self.docs["changelog"]:
            self.assertTrue(release["entries"])


if __name__ == "__main__":
    unittest.main()
