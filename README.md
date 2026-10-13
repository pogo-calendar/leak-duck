# Leak Duck 🦆

[![Scrape Leek Duck Data](https://github.com/pokelitee/leak-duck/actions/workflows/run_scrapers.yml/badge.svg)](https://github.com/pokelitee/leak-duck/actions/workflows/run_scrapers.yml)
![Last Updated](https://img.shields.io/github/last-commit/pokelitee/leak-duck/data)

A Python-based web scraper that automatically collects and updates Pokémon GO data from [leekduck.com](https://leekduck.com). This project uses GitHub Actions to run on a schedule and pushes the structured JSON data to a dedicated `data` branch.

---

## About The Project

This project provides a reliable, automated way to access up-to-date information for Pokémon GO. It scrapes the Leek Duck website for the latest details on Raid Bosses, Events, Field Research, Team GO Rocket lineups, and the current Egg Pool. The scraper is scheduled to run **every hour** via a GitHub Actions workflow (GitHub may delay scheduled runs during busy periods), ensuring the data is always fresh and reliable.

The scraped data is automatically committed and pushed to the `data` branch of this repository, making it easy to use as a free, simple API for your own projects.

---

## Features

- **Automated Scraping**: Runs automatically every hour using GitHub Actions.
- **Comprehensive Data**: Scrapes a wide range of Pokémon GO data, including:
  - **Raid Bosses**: Current Pokémon in all raid tiers.
  - **Events**: A categorized list of all current and upcoming in-game events.
  - **Field Research**: All available research tasks and their possible rewards.
  - **Team GO Rocket**: The complete lineups for Giovanni, Leaders, and Grunts.
  - **Egg Pool**: The current list of Pokémon hatching from each egg distance.
- **Data Archiving**: Automatically archives past events to yearly files for historical data, with a manually triggered backfill that rebuilds them from their source pages.
- **Failure-safe**: Uses retries, atomic writes, and output validation so a failed scraper never publishes an empty or invalid file. Files that pass validation are still published, and any failure marks the run as failed.
- **Organized**: A clean and modular project structure that is easy to understand and extend.

---

## API & Documentation

The JSON files are free API endpoints for your projects: no key, no sign-up, and CORS is enabled.

**➡️ Start at the [Leak Duck API site](https://pokelitee.github.io/leak-duck/)**

The site lists every endpoint with when it last changed, lets you browse and filter the live data, and holds the field reference and changelog. The reference is maintained in [`site/docs.json`](site/docs.json).

---

## Data Output

The scraped data is automatically committed and pushed to the `data` branch of this repository, which GitHub Pages serves as free JSON endpoints at `https://pokelitee.github.io/leak-duck/<file>` (for example, `https://pokelitee.github.io/leak-duck/events.json`). The older `https://raw.githubusercontent.com/pokelitee/leak-duck/data/<file>` URLs serve the same files.

**➡️ Browse the raw data files here: [https://github.com/pokelitee/leak-duck/tree/data](https://github.com/pokelitee/leak-duck/tree/data)**

The following files are generated:

- `raid_bosses.json` - All current Pokémon in Tier 1, 3, 5, Mega, and Shadow Raids. Shadow bosses share their tier's list and are marked with `is_shadow: true`.
- `research_tasks.json` - All available Field Research tasks and their possible rewards.
- `rocket_lineups.json` - The complete lineups for Team GO Rocket Leaders and Grunts.
- `egg_pool.json` - The current list of Pokémon hatching from each egg distance.
- `events.json` - All current and upcoming events.
- `archives/archive_YYYY.json` - Historical event data, organized by year.
  - _Note: Automated archiving of past events is handled by the script. Archiving began on **September 19, 2025**; events that ended earlier are included only if they were still listed on that date, so earlier coverage is partial._
  - _Archives were rebuilt from their source pages on **August 10, 2026**, so every record uses the current event schema. `description` is absent only for the few events whose Leek Duck page no longer exists. See the [API reference](https://pokelitee.github.io/leak-duck/#reference-archives) for the full compatibility contract._
- `manifest.json` - Every published file with its SHA-256, size, and when its content last changed.

Field-by-field descriptions of every file are on the [API site](https://pokelitee.github.io/leak-duck/#reference), along with a live data explorer.

---

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

- Python 3.12+
- pip

### Installation & Local Usage

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/pokelitee/leak-duck.git
    cd leak-duck
    ```

2.  **Create and activate a virtual environment:**

    ```sh
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**

    ```sh
    pip install -r requirements.txt
    ```

4.  **Run the scraper manually:**

    ```sh
    python -m src.main
    ```

    When run locally, the script will create two folders in your project root: `html/` and `json/`. These folders are included in the `.gitignore` and will not be committed to your repository.

    To write JSON somewhere else, set `LEAK_DUCK_OUTPUT_DIR` to the desired directory before running the command. An installed `leak-duck` command uses the current directory by default; `LEAK_DUCK_HOME` can set a different runtime root.

### Development Checks

Install the pinned development tools and run the same checks used by CI:

```sh
pip install -r requirements-dev.txt
ruff format --check .
ruff check .
python -m unittest discover -v
python -m compileall -q src tests
node --check site/assets/app.js
python scripts/check_package.py
```

CI has a 15-minute timeout and also builds the distributions, installs the wheel in a clean environment, and verifies bundled configuration, runtime paths, and the console entry point without scraping live sites.

Use `ruff format .` to apply formatting. The tests are offline and cover parser selectors, output validation, archive compatibility validation, fetch retries and failures, archive preservation, partial-failure handling, the manifest, and that `site/docs.json` documents exactly the published files.

### Previewing the API Site

To preview the site with locally scraped data, copy it next to the JSON output and serve that folder:

```sh
python -m src.main
cp -R site/. json/
python -m http.server --directory json
```

Then open http://localhost:8000/.

---

## Automation with GitHub Actions

This repository is configured to run the scraper automatically using GitHub Actions.

- **Workflow file:** `.github/workflows/run_scrapers.yml`
- **Trigger:** The workflow is scheduled to run every hour (GitHub may delay scheduled runs) and can also be triggered manually from the "Actions" tab in GitHub.
- **Process:**
  1.  The action checks out the `main` branch to get the latest scraper code.
  2.  It installs the pinned Python dependencies and runs the regression tests.
  3.  It checks out the `data` branch into a separate worktree; the archiver reads the published files from there rather than from raw.githubusercontent.com, whose cache can lag behind the latest push.
  4.  It runs the archiver and scrapers, writing each validated file into that worktree, then updates `manifest.json`. A file that fails validation is left untouched, and an event page that fails validation is skipped with a warning.
  5.  It commits and pushes only when the generated data changed, even if one scraper failed, so the other files stay fresh; the failure still marks the run as failed. If archiving fails, `events.json` is not republished. Concurrent publishers are serialized to avoid races.

**Note:** For the GitHub Action to work, you must **manually create the `data` branch** as a clean, orphan branch in your repository first.

### Deploying the API Site

- **Workflow file:** `.github/workflows/deploy_pages.yml`
- **Trigger:** After every scrape or backfill run, on pushes to `main` that change `site/`, and manually.
- **Process:** It combines the `data` branch with the `site/` folder and deploys the result with GitHub's Pages actions, so the `data` branch only ever holds data. The repository's Pages source must be set to **GitHub Actions**.

### Rebuilding the Archives

Archived events keep whatever the scraper captured when they ended, so improvements to the parser do not reach them on their own. The backfill workflow re-reads every archived event from its Leek Duck page and republishes the result.

- **Workflow file:** `.github/workflows/backfill_archives.yml`
- **Trigger:** Manual only, from the "Actions" tab. `dry_run` defaults to `true`, so the report can be reviewed before anything is published.
- **Behavior:** Identity, category, banner, and timestamps are always kept from the archive; only `description` and `details` are refreshed. Events whose page has been removed keep their original snapshot.

It can also be run locally, which writes to `json/archives/` instead of publishing:

```sh
python -m src.backfill 2025 2026 --dry-run
```

---

## Project Structure

```
leak-duck/
├── .github/
│   ├── workflows/
│   │   ├── backfill_archives.yml
│   │   ├── ci.yml
│   │   ├── deploy_pages.yml
│   │   └── run_scrapers.yml
│   ├── data-branch-readme.md
│   └── dependabot.yml
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── raid_boss_scraper.py
│   │   ├── research_scraper.py
│   │   ├── rocket_lineup_scraper.py
│   │   ├── egg_scraper.py
│   │   ├── event_scraper.py
│   │   └── event_page_scraper.py
│   ├── __init__.py
│   ├── archiver.py
│   ├── backfill.py
│   ├── config.json
│   ├── config.py
│   ├── fetch.py
│   ├── main.py
│   ├── manifest.py
│   ├── paths.py
│   ├── published.py
│   ├── validation.py
│   └── utils.py
├── site/
│   ├── assets/
│   │   ├── app.js
│   │   └── styles.css
│   ├── docs.json
│   └── index.html
├── tests/
│   ├── test_archiver.py
│   ├── test_backfill.py
│   ├── test_config.py
│   ├── test_fetch.py
│   ├── test_main.py
│   ├── test_manifest.py
│   ├── test_published.py
│   ├── test_scrapers.py
│   ├── test_site.py
│   └── test_validation.py
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements-dev.txt
└── requirements.txt
```

---

## Contributing

Follow the [organization contribution guide](https://github.com/pokelitee/.github/blob/main/CONTRIBUTING.md) and the development checks above. Changes to `main` require a pull request, passing `quality` CI, and resolved review conversations, including changes by administrators. GitHub deletes merged branches automatically. The intended live rulesets are tracked in `.github/rulesets/`; editing those files alone does not apply them.

The Pages environment only permits `main` deployments. Scraping, backfills, and deployment workflows only run from `main`. A failed scraper may still publish validated files from the other scrapers; this policy remains distinct from projects that publish complete snapshots atomically.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Acknowledgments

- All data is sourced from the fantastic resources at [leekduck.com](https://leekduck.com).
- **Disclaimer**: This project is for educational purposes and is not affiliated with Leek Duck or Niantic.
