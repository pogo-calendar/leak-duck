from src.archiver import EventArchiver
from src.config import Config, ScraperConfig, load_config
from src.scrapers import (
    EggScraper,
    EventScraper,
    RaidBossScraper,
    ResearchScraper,
    RocketLineupScraper,
)
from src.scrapers.base_scraper import BaseScraper

SCRAPER_CLASSES: dict[str, type[BaseScraper]] = {
    "RaidBossScraper": RaidBossScraper,
    "ResearchScraper": ResearchScraper,
    "RocketLineupScraper": RocketLineupScraper,
    "EggScraper": EggScraper,
}


def build_scraper(name: str, scraper: ScraperConfig, config: Config) -> BaseScraper:
    if name == "EventScraper":
        return EventScraper(
            scraper.url,
            scraper.file_name,
            config.settings,
            published=config.published,
            check_existing_events=scraper.check_existing,
        )
    return SCRAPER_CLASSES[name](scraper.url, scraper.file_name, config.settings)


def main() -> None:
    print("=== Starting Leak Duck Scrapers ===", flush=True)
    config = load_config()
    print("Configuration loaded", flush=True)

    failures: list[str] = []
    archived = False
    try:
        EventArchiver(config.published, config.settings).run()
        archived = True
        print("Event archiver completed", flush=True)
    except Exception as e:
        failures.append(f"EventArchiver: {e}")
        print(f"✗ ERROR running EventArchiver: {e}", flush=True)

    for name, scraper in config.scrapers.items():
        if not scraper.enabled:
            continue
        if name == "EventScraper" and not archived:
            # Republishing events.json would drop ended events that the failed
            # archiver never moved into an archive.
            print("Skipping EventScraper because archiving failed", flush=True)
            continue
        print(f"--- Running {name} ---", flush=True)
        try:
            build_scraper(name, scraper, config).run()
            print(f"Successfully ran {name}", flush=True)
        except Exception as e:
            failures.append(f"{name}: {e}")
            print(f"✗ ERROR running {name}: {e}", flush=True)

    if failures:
        raise RuntimeError("One or more scrapers failed: " + "; ".join(failures))

    print("=== All scrapers finished ===", flush=True)


if __name__ == "__main__":
    main()
