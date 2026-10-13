"""Build and check an installed scraper wheel without fetching live data."""

import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="leak-duck-package-") as directory:
        temporary = Path(directory)
        distribution = temporary / "dist"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--outdir",
                str(distribution),
                str(ROOT),
            ],
            check=True,
        )
        environment = temporary / "venv"
        venv.EnvBuilder(with_pip=False).create(environment)
        binary_dir = environment / ("Scripts" if sys.platform == "win32" else "bin")
        python = binary_dir / ("python.exe" if sys.platform == "win32" else "python")
        wheel = next(distribution.glob("*.whl"))
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "--python",
                str(python),
                "install",
                "-r",
                str(ROOT / "requirements.txt"),
                str(wheel),
            ],
            check=True,
        )
        command = binary_dir / (
            "leak-duck.exe" if sys.platform == "win32" else "leak-duck"
        )
        if not command.is_file():
            raise RuntimeError("Installed console command is missing")
        smoke_environment = os.environ.copy()
        for key in (
            "LEAK_DUCK_HOME",
            "LEAK_DUCK_OUTPUT_DIR",
            "LEAK_DUCK_PUBLISHED_DIR",
        ):
            smoke_environment.pop(key, None)
        subprocess.run(
            [
                str(python),
                "-c",
                "from importlib.metadata import distribution; "
                "from pathlib import Path; "
                "from src.config import load_config; "
                "from src.paths import data_dir; "
                "assert load_config().settings.retries > 0; "
                "assert data_dir() == Path.cwd() / 'json'; "
                "entry = next(e for e in distribution('leak-duck').entry_points "
                "if e.group == 'console_scripts' and e.name == 'leak-duck'); "
                "assert callable(entry.load())",
            ],
            cwd=temporary,
            env=smoke_environment,
            check=True,
        )


if __name__ == "__main__":
    main()
