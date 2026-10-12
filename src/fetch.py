import time
from collections.abc import Callable

import requests

from src.config import ScraperSettings

HEADERS = {"User-Agent": "leak-duck (+https://github.com/pokelitee/leak-duck)"}


class FetchError(RuntimeError):
    """Raised after a request exhausts its retries."""


def get_once(url: str, timeout: float) -> requests.Response:
    """GET ``url`` once, raising on connection failures and HTTP errors."""
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response


def get_if_exists(url: str, timeout: float) -> requests.Response | None:
    """GET ``url`` once, returning None when it does not exist (HTTP 404)."""
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response


def _with_retries[T](
    url: str, settings: ScraperSettings, request: Callable[[], T]
) -> T:
    for attempt in range(1, settings.retries + 1):
        print(f"Fetching {url} (attempt {attempt}/{settings.retries})...", flush=True)
        try:
            return request()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}", flush=True)
            if attempt == settings.retries:
                raise FetchError(
                    f"Failed to fetch {url} after {settings.retries} attempts"
                ) from e
            print(f"Retrying in {settings.delay} seconds...", flush=True)
            time.sleep(settings.delay)
    raise FetchError(f"No fetch attempts configured for {url}")


def get_with_retries(url: str, settings: ScraperSettings) -> requests.Response:
    """GET ``url``, retrying failed requests as configured."""
    return _with_retries(url, settings, lambda: get_once(url, settings.timeout))


def get_if_exists_with_retries(
    url: str, settings: ScraperSettings
) -> requests.Response | None:
    """Like ``get_if_exists``, retrying failed requests as configured."""
    return _with_retries(url, settings, lambda: get_if_exists(url, settings.timeout))
