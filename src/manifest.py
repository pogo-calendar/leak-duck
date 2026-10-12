import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.utils import write_json_atomic

MANIFEST_NAME = "manifest.json"


def _timestamp(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_previous(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        return {}
    try:
        files = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
        if not isinstance(files, dict):
            raise ValueError("files must be an object")
        return files
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(
            f"Could not read {manifest_path}; rebuilding it with new timestamps: {e}",
            flush=True,
        )
        return {}


def update_manifest(directory: Path, now: datetime | None = None) -> None:
    """Record each published JSON file's hash, size, and last content change.

    ``updated_at`` only moves when a file's content changes, so an unchanged
    run rewrites an identical manifest and produces no data commit.
    """
    manifest_path = directory / MANIFEST_NAME
    previous = _load_previous(manifest_path)
    changed_at = _timestamp(now or datetime.now(UTC))

    files: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.rglob("*.json")):
        relative = path.relative_to(directory).as_posix()
        if relative == MANIFEST_NAME or any(
            part.startswith(".") for part in path.relative_to(directory).parts
        ):
            continue

        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        prior = previous.get(relative)
        prior_updated_at = (
            prior.get("updated_at")
            if isinstance(prior, dict) and prior.get("sha256") == digest
            else None
        )
        files[relative] = {
            "sha256": digest,
            "size": len(content),
            "updated_at": (
                prior_updated_at if isinstance(prior_updated_at, str) else changed_at
            ),
        }

    write_json_atomic(manifest_path, {"files": files})
    print(f"Updated {manifest_path} ({len(files)} files)", flush=True)
