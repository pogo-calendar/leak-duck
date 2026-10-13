import io
import unittest
from unittest.mock import Mock, patch

from src.config import Config, PublishedData, ScraperConfig, ScraperSettings
from src.main import main


def config(*names: str) -> Config:
    return Config(
        published=PublishedData("owner", "repository"),
        settings=ScraperSettings(retries=1, delay=0),
        scrapers={name: ScraperConfig("offline", name, enabled=True) for name in names},
    )


class MainTests(unittest.TestCase):
    def run_main(self, archiver: Mock, scrapers: dict[str, Mock]) -> list[str]:
        built: list[str] = []
        self.update_manifest = Mock()

        def build(name: str, *_: object) -> Mock:
            built.append(name)
            return scrapers[name]

        with (
            patch("src.main.load_config", return_value=config(*scrapers)),
            patch("src.main.EventArchiver", return_value=archiver),
            patch("src.main.build_scraper", side_effect=build),
            patch("src.main.update_manifest", self.update_manifest),
        ):
            with self.assertRaises(RuntimeError):
                main()
        return built

    def test_archiver_failure_skips_only_the_event_scraper(self) -> None:
        archiver = Mock()
        archiver.run.side_effect = RuntimeError("offline")
        scrapers = {"RaidBossScraper": Mock(), "EventScraper": Mock()}

        built = self.run_main(archiver, scrapers)

        self.assertEqual(built, ["RaidBossScraper"])
        scrapers["RaidBossScraper"].run.assert_called_once()

    def test_scraper_failure_does_not_stop_the_others(self) -> None:
        scrapers = {"ResearchScraper": Mock(), "EventScraper": Mock()}
        scrapers["ResearchScraper"].run.side_effect = ValueError("bad markup")

        built = self.run_main(Mock(), scrapers)

        self.assertEqual(built, ["ResearchScraper", "EventScraper"])
        scrapers["EventScraper"].run.assert_called_once()
        self.update_manifest.assert_called_once()

    def test_unencodable_output_does_not_crash_a_legacy_console(self) -> None:
        console = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
        scrapers = {"ResearchScraper": Mock()}
        scrapers["ResearchScraper"].run.side_effect = ValueError("bad reward 🦆")

        with patch("sys.stdout", console):
            self.run_main(Mock(), scrapers)

        console.flush()
        output = console.buffer.getvalue().decode("cp1252")
        self.assertIn(r"ERROR running ResearchScraper: bad reward \U0001f986", output)


if __name__ == "__main__":
    unittest.main()
