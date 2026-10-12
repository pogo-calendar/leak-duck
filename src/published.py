import json
from typing import Any

from src.config import PublishedData, ScraperSettings
from src.fetch import get_if_exists_with_retries
from src.paths import published_dir


def read_published_json(
    published: PublishedData, path: str, settings: ScraperSettings
) -> Any | None:
    """Return published JSON, or None when it has not been published yet.

    CI reads a checkout of the data branch instead of raw.githubusercontent.com,
    whose CDN can serve a copy that predates the latest push and would let one
    run overwrite what the previous run published.

    Raises FetchError, OSError, or ValueError when the data cannot be read.
    """
    local_dir = published_dir()
    if local_dir is not None:
        local_path = local_dir / path
        if not local_path.exists():
            return None
        return json.loads(local_path.read_text(encoding="utf-8"))

    response = get_if_exists_with_retries(published.url(path), settings)
    return response.json() if response is not None else None
