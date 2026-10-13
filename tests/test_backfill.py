import io
import unittest
from contextlib import redirect_stdout
from typing import Any
from unittest.mock import Mock, patch

import requests

from src.backfill import ArchiveBackfiller
from src.config import PublishedData, ScraperSettings


def archived_event(**overrides: Any) -> dict[str, Any]:
    event: dict[str, Any] = {
        "title": "Archived Event",
        "article_url": "https://example.invalid/events/archived/",
        "banner_url": "banner-url",
        "category": "Event",
        "details": {
            "bonuses": ["2x Stardust"],
            "spawns": [{"name": "Zubat", "asset_url": None, "shiny_available": False}],
        },
        "is_local_time": False,
        "start_time": 1,
        "end_time": 2,
    }
    event.update(overrides)
    return event


EVENT_PAGE = (
    '<div class="page-content"><div class="header-page">Title</div>'
    "<p>Recovered description.</p>"
    '<h2 class="event-section-header" id="spawns">Spawns</h2>'
    '<ul class="pkmn-list"><li class="pkmn-list-item">'
    '<div class="pkmn-name">Zubat</div>'
    '<div class="pkmn-list-img"><img src="zubat.png"></div>'
    "</li></ul></div>"
)


class ArchiveBackfillerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backfiller = ArchiveBackfiller(
            PublishedData("owner", "repository"),
            ScraperSettings(retries=1, delay=0),
            [2025],
            delay=0,
        )

    @staticmethod
    def response(text: str = "", status_code: int = 200) -> Mock:
        response = Mock(spec=requests.Response)
        response.status_code = status_code
        response.text = text
        response.raise_for_status.return_value = None
        return response

    def test_recovers_description_and_sprites_from_a_live_page(self) -> None:
        event = archived_event()
        with patch("src.fetch.requests.get", return_value=self.response(EVENT_PAGE)):
            rebuilt, outcome = self.backfiller._backfill_event(event)

        self.assertEqual(outcome, "description recovered")
        self.assertEqual(rebuilt["description"], "Recovered description.")
        self.assertEqual(rebuilt["details"]["spawns"][0]["name"], "Zubat")
        self.assertTrue(rebuilt["details"]["spawns"][0]["asset_url"])

    def test_preserves_archived_identity_and_times(self) -> None:
        event = archived_event()
        with patch("src.fetch.requests.get", return_value=self.response(EVENT_PAGE)):
            rebuilt, _ = self.backfiller._backfill_event(event)

        for key in ("title", "category", "article_url", "banner_url", "start_time"):
            self.assertEqual(rebuilt[key], event[key])

    def test_missing_page_keeps_the_snapshot(self) -> None:
        event = archived_event()
        with patch(
            "src.fetch.requests.get", return_value=self.response(status_code=404)
        ):
            rebuilt, outcome = self.backfiller._backfill_event(event)

        self.assertEqual(outcome, "missing")
        self.assertEqual(rebuilt, archived_event())

    def test_existing_description_survives_a_page_without_one(self) -> None:
        event = archived_event(description="Original description.")
        page = '<div class="page-content"><div class="header-page">Title</div></div>'
        with patch("src.fetch.requests.get", return_value=self.response(page)):
            rebuilt, _ = self.backfiller._backfill_event(event)

        self.assertEqual(rebuilt["description"], "Original description.")

    def test_retries_a_slow_page_before_giving_up(self) -> None:
        backfiller = ArchiveBackfiller(
            PublishedData("owner", "repository"),
            ScraperSettings(retries=2, delay=0),
            [2025],
            delay=0,
        )
        with (
            redirect_stdout(io.StringIO()),
            patch(
                "src.fetch.requests.get",
                side_effect=[requests.ReadTimeout("slow"), self.response(EVENT_PAGE)],
            ),
        ):
            rebuilt, outcome = backfiller._backfill_event(archived_event())

        self.assertEqual(outcome, "description recovered")
        self.assertEqual(rebuilt["description"], "Recovered description.")

    def test_network_failures_are_not_silently_swallowed(self) -> None:
        from src.backfill import ArchiveBackfillError

        with patch(
            "src.fetch.requests.get",
            side_effect=requests.ConnectionError("temporary outage"),
        ):
            with self.assertRaises(ArchiveBackfillError):
                self.backfiller._backfill_event(archived_event())


if __name__ == "__main__":
    unittest.main()
