# Development

See the [README](../README.md) for quick start and documentation links. General contribution policy lives in the [organization guide](https://github.com/pokelitee/.github/blob/main/CONTRIBUTING.md).

## Setup and checks

Run the commands below from the repository root.

Use Python 3.12+ and Node.js for the site syntax check. Activate the virtual environment from the setup instructions before running these commands.

Install the pinned development tools and run the same checks used by CI:

```sh
python -m pip install -r requirements/dev.txt
python -m ruff format --check .
python -m ruff check .
python -m unittest discover -v
python -m compileall -q src tests
node --check site/assets/app.js
python scripts/check_package.py
```

CI has a 15-minute timeout and also builds the distributions, installs the wheel in a clean environment, and verifies bundled configuration, runtime paths, and the console entry point without scraping live sites.

Use `python -m ruff format .` to apply formatting. The tests are offline and cover parser selectors, output validation, archive compatibility validation, fetch retries and failures, archive preservation, partial-failure handling, the manifest, and that `site/docs.json` documents exactly the published files.

## Preview the API site

After scraping locally, copy the site into the JSON output and serve it:

```sh
python -c "import shutil; shutil.copytree('site', 'json', dirs_exist_ok=True)"
python -m http.server --directory json
```

Open [localhost:8000](http://localhost:8000/). These commands assume the default `json/` output directory.

## Architecture

- `src/scrapers/`: resource parsers and shared scraper behavior.
- `src/archiver.py` and `src/backfill.py`: event archiving and historical refreshes.
- `src/fetch.py`, `src/validation.py`, and `src/published.py`: fetching, output checks, and access to published snapshots.
- `src/main.py` and `src/manifest.py`: orchestration and publication metadata.
- `site/`: API explorer and field reference.
- `tests/` and `scripts/`: offline regression tests and package verification.
- `.github/`: CI, scraping, backfill, deployment, and repository policies.

Each validated file publishes independently. Failed scrapers preserve the corresponding published files while successful scrapers can still update theirs. The run reports failure whenever a scraper fails.

## Changing scrapers and schemas

Extend the shared scraper, fetch, and validation utilities. Add offline fixtures or selector tests for changed upstream HTML. A parser change must preserve valid published files when fetching or validation fails.

The API contract and changelog are maintained in [`site/docs.json`](../site/docs.json) and rendered by the API site. Update them with schema changes rather than copying field definitions into Markdown. Check event archive compatibility when changing event data.

`requirements/runtime.txt` pins scraper dependencies. `requirements/dev.txt` includes those dependencies and pins development tools. Package installation uses `pyproject.toml`; local checks and automation use the requirement files.

Dependabot checks Python dependencies and GitHub Actions weekly. Keep `requirements/runtime.txt`, `requirements/dev.txt`, and `pyproject.toml` consistent. The required PR check is `quality`; `.github/workflows/ci.yml` defines its checks.
