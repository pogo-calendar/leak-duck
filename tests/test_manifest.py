import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from src.manifest import MANIFEST_NAME, update_manifest

FIRST_RUN = datetime(2026, 10, 12, 17, 0, tzinfo=UTC)
SECOND_RUN = datetime(2026, 10, 12, 18, 0, tzinfo=UTC)


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.data_dir = Path(temporary_directory.name)

    def write(self, relative: str, data: object) -> None:
        path = self.data_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")

    def manifest(self) -> dict[str, dict[str, object]]:
        manifest_path = self.data_dir / MANIFEST_NAME
        return json.loads(manifest_path.read_text(encoding="utf-8"))["files"]

    def test_lists_published_files_including_archives(self) -> None:
        self.write("events.json", {"Event": []})
        self.write("archives/archive_2026.json", {})

        update_manifest(self.data_dir, FIRST_RUN)

        files = self.manifest()
        self.assertEqual(set(files), {"events.json", "archives/archive_2026.json"})
        self.assertEqual(files["events.json"]["updated_at"], "2026-10-12T17:00:00Z")
        self.assertEqual(files["events.json"]["size"], len('{"Event": []}'))

    def test_unchanged_files_keep_their_timestamp(self) -> None:
        self.write("events.json", {"Event": []})
        self.write("raid_bosses.json", {"1-Star Raids": []})
        update_manifest(self.data_dir, FIRST_RUN)

        self.write("raid_bosses.json", {"1-Star Raids": [{"name": "Clefairy"}]})
        update_manifest(self.data_dir, SECOND_RUN)

        files = self.manifest()
        self.assertEqual(files["events.json"]["updated_at"], "2026-10-12T17:00:00Z")
        self.assertEqual(
            files["raid_bosses.json"]["updated_at"], "2026-10-12T18:00:00Z"
        )

    def test_removed_files_are_dropped(self) -> None:
        self.write("events.json", {})
        update_manifest(self.data_dir, FIRST_RUN)

        (self.data_dir / "events.json").unlink()
        update_manifest(self.data_dir, SECOND_RUN)

        self.assertEqual(self.manifest(), {})

    def test_malformed_manifest_is_rebuilt(self) -> None:
        self.write("events.json", {})
        (self.data_dir / MANIFEST_NAME).write_text("{", encoding="utf-8")

        update_manifest(self.data_dir, FIRST_RUN)

        self.assertEqual(
            self.manifest()["events.json"]["updated_at"], "2026-10-12T17:00:00Z"
        )


if __name__ == "__main__":
    unittest.main()
