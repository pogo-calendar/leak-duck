import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import PublishedData, ScraperSettings
from src.published import read_published_json

PUBLISHED = PublishedData("owner", "repository")
SETTINGS = ScraperSettings(retries=1, delay=0)


class PublishedDataTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.data_dir = Path(temporary_directory.name)
        environment = patch.dict(
            "os.environ", {"LEAK_DUCK_PUBLISHED_DIR": str(self.data_dir)}
        )
        environment.start()
        self.addCleanup(environment.stop)

    def test_reads_the_local_checkout_without_network_access(self) -> None:
        (self.data_dir / "archives").mkdir()
        (self.data_dir / "archives" / "archive_2026.json").write_text(
            json.dumps({"Event": []}), encoding="utf-8"
        )

        with patch("src.fetch.requests.get") as get:
            data = read_published_json(
                PUBLISHED, "archives/archive_2026.json", SETTINGS
            )

        self.assertEqual(data, {"Event": []})
        get.assert_not_called()

    def test_missing_local_file_is_unpublished(self) -> None:
        self.assertIsNone(read_published_json(PUBLISHED, "events.json", SETTINGS))

    def test_malformed_local_file_is_raised(self) -> None:
        (self.data_dir / "events.json").write_text("{", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_published_json(PUBLISHED, "events.json", SETTINGS)


if __name__ == "__main__":
    unittest.main()
