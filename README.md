# Leak Duck

[![Update Data](https://github.com/pokelitee/leak-duck/actions/workflows/update-data.yml/badge.svg)](https://github.com/pokelitee/leak-duck/actions/workflows/update-data.yml)
![Last Updated](https://img.shields.io/github/last-commit/pokelitee/leak-duck/data)

A Python scraper that collects Pokémon GO events and game data from [Leek Duck](https://leekduck.com). GitHub Actions runs hourly, although scheduled runs may be delayed. Source code lives on `main`, generated JSON on `data`, and GitHub Pages serves the API.

## API

Browse the [live API site](https://pokelitee.github.io/leak-duck/) for endpoints, field descriptions, a data explorer, and the changelog. JSON endpoints need no API key and support browser requests through CORS.

The base URL is `https://pokelitee.github.io/leak-duck/`. The older `https://raw.githubusercontent.com/pokelitee/leak-duck/data/` URLs serve the same resource files. Replace `data` with a full commit SHA to pin a raw GitHub snapshot.

- `raid_bosses.json` - All current Pokémon in Tier 1, 3, 5, Mega, and Shadow Raids. Shadow bosses share their tier's list and are marked with `is_shadow: true`.
- `research_tasks.json` - All available Field Research tasks and their possible rewards.
- `rocket_lineups.json` - The complete lineups for Team GO Rocket Leaders and Grunts.
- `egg_pool.json` - The current list of Pokémon hatching from each egg distance.
- `events.json` - All current and upcoming events.
- `archives/archive_YYYY.json` - Historical event data, organized by year.
- `manifest.json` - Every published file with its SHA-256, size, and when its content last changed.

Archive coverage before September 19, 2025 is partial. See the [archive reference](https://pokelitee.github.io/leak-duck/#reference-archives) for historical coverage and compatibility details.

## Getting started

Use Python 3.12+. Activate the environment with `.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` in bash.

```sh
git clone https://github.com/pokelitee/leak-duck.git
cd leak-duck
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -r requirements/runtime.txt
python -m pip install --no-deps -e .
leak-duck
```

You can also run `python -m src.main` from the checkout without installing the package. Local runs write downloaded HTML to `html/` and JSON to `json/`; both are ignored by Git.

`LEAK_DUCK_HOME` overrides the runtime root, and `LEAK_DUCK_OUTPUT_DIR` overrides the JSON output directory. An installed package defaults to the current working directory; a source checkout defaults to its repository root.

## Architecture

Resource scrapers share fetching and validation utilities; orchestration manages event archiving and the publication manifest. Each validated file can publish independently, including after another scraper fails. See [Development](docs/development.md#architecture) for the module layout.

## Documentation

- [API reference](https://pokelitee.github.io/leak-duck/#reference): the published data contract, maintained in [site/docs.json](site/docs.json).
- [Development](docs/development.md): local checks, architecture, site preview, and dependencies.
- [Operations](docs/operations.md): configuration, scraping, archiving, backfills, and recovery.
- [Data branch guide](.github/data-branch-readme.md): the README copied into published snapshots.

## Contributing

Follow the [organization contribution guide](https://github.com/pokelitee/.github/blob/main/CONTRIBUTING.md) and the [development guide](docs/development.md). Use a short-lived branch and a pull request into `main`.

## License

Source code is licensed under the [MIT License](LICENSE). Data comes from [Leek Duck](https://leekduck.com). This project is not affiliated with Leek Duck or Niantic.
