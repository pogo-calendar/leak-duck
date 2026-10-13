import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(__file__).resolve().with_name("config.json")


def runtime_root() -> Path:
    """Return the checkout root, or the current directory when installed."""
    configured_root = os.getenv("LEAK_DUCK_HOME")
    if configured_root:
        return Path(configured_root).expanduser().resolve()
    if (PROJECT_ROOT / ".git").exists():
        return PROJECT_ROOT
    return Path.cwd().resolve()


HTML_DIR = runtime_root() / "html"


def data_dir() -> Path:
    """Return the data output directory, independent of the current directory."""
    configured_dir = os.getenv("LEAK_DUCK_OUTPUT_DIR")
    if configured_dir:
        return Path(configured_dir).expanduser().resolve()
    return runtime_root() / "json"


def published_dir() -> Path | None:
    """Return a local checkout of the published data branch, when one is used."""
    configured_dir = os.getenv("LEAK_DUCK_PUBLISHED_DIR")
    return Path(configured_dir).expanduser().resolve() if configured_dir else None
