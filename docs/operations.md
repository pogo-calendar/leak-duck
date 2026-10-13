# Operations

See the [README](../README.md) for quick start and documentation links. General contribution policy lives in the [organization guide](https://github.com/pokelitee/.github/blob/main/CONTRIBUTING.md).

## Runtime configuration

The scraper loads packaged [`src/config.json`](../src/config.json); there is no CLI configuration-file flag. In a checkout, edit that file to change source URLs, enabled scrapers, or fetch settings. Python callers can pass a path to `src.config.load_config`.

| Setting | Default | Purpose |
| --- | --- | --- |
| `scraper_settings.retries` | `3` | Total HTTP attempts, including the first request. |
| `scraper_settings.delay` | `5` | Delay between failed attempts in seconds. |
| `scraper_settings.timeout` | `15` | HTTP timeout in seconds. |
| `scraper_settings.cache_expiration_hours` | `1` | Downloaded HTML cache lifetime. |
| `scrapers.<class>.enabled` | `true` | Enable the configured resource scraper. |
| `scrapers.<class>.url` / `file_name` | Per resource | Source page and output filename stem. |
| `github.user` / `github.repo` | `pokelitee` / `leak-duck` | Published data source used for archives and existing snapshots. |

| Environment variable | Purpose |
| --- | --- |
| `LEAK_DUCK_HOME` | Runtime root for downloaded HTML and default JSON output. |
| `LEAK_DUCK_OUTPUT_DIR` | Override the JSON output directory. |
| `LEAK_DUCK_PUBLISHED_DIR` | Read existing published files from a local data-branch checkout instead of remote raw URLs. |

Without overrides, source checkouts use their repository root and installed packages use the current working directory. Downloads go to `html/` and output to `json/`. Run `leak-duck` or `python -m src.main`; failures produce a nonzero exit status.

## Automation and publication

This repository is configured to run the scraper automatically using GitHub Actions.

- **Workflow file:** `.github/workflows/run_scrapers.yml`
- **Trigger:** The workflow is scheduled to run every hour (GitHub may delay scheduled runs) and can also be triggered manually from the "Actions" tab in GitHub.
- **Process:**
  1.  The action checks out the `main` branch to get the latest scraper code.
  2.  It installs the pinned runtime dependencies and runs the regression tests.
  3.  It checks out the `data` branch into a separate worktree; the archiver reads the published files from there rather than from raw.githubusercontent.com, whose cache can lag behind the latest push.
  4.  It runs the archiver and scrapers, writing each validated file into that worktree, then updates `manifest.json`. A file that fails validation is left untouched, and an event page that fails validation is skipped with a warning.
  5.  It commits and pushes only when the generated data changed, even if one scraper failed, so the other files stay fresh; the failure still marks the run as failed. If archiving fails, `events.json` is not republished. Concurrent publishers are serialized to avoid races.

**Note:** For the GitHub Action to work, you must **manually create the `data` branch** as a clean, orphan branch in your repository first.

### Deploying the API Site

- **Workflow file:** `.github/workflows/deploy_pages.yml`
- **Trigger:** After non-cancelled scrape or backfill runs from `main`, on pushes to `main` that change `site/` or the deployment workflow, and manually. Failed runs may have published validated files, so they can also trigger deployment.
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

## Repository settings

Changes to `main` require a pull request, passing `quality` CI, and resolved review conversations, including changes by administrators. No approving review is required while there is one maintainer. GitHub automatically deletes merged branches.

The `data` branch contains generated output only and is protected against deletion and force pushes. Do not merge it into source branches or edit published JSON by hand. Validated files may publish after a partial scraper failure; preserve this policy when changing automation.

The Pages environment and publishing workflows permit only `main`. Live ruleset definitions are tracked in `.github/rulesets/`; editing those files does not apply the settings to GitHub.

## Manual workflow runs

```sh
gh workflow run run_scrapers.yml --repo pokelitee/leak-duck --ref main
gh workflow run backfill_archives.yml --repo pokelitee/leak-duck --ref main -f years="2025 2026" -F dry_run=true
```

Review the backfill report before dispatching again with `dry_run=false`. Local backfills also default to writing unless `--dry-run` is supplied; the workflow defaults to dry-run. Scrapes and backfills share a publisher concurrency group so they cannot race.

## Troubleshooting and recovery

- **Changed HTML or failed scraper:** inspect the failed resource, capture current HTML, and reproduce with offline tests. Validated files from other scrapers may already have published; a failed run does not imply that nothing changed.
- **Archive failure:** resolve it before expecting `events.json` to update. The event scraper is skipped to avoid losing ended events that could not be archived.
- **Stale data:** inspect the scraper run, `manifest.json` content-change times, and the Pages deployment. Unchanged content retains its previous change time.
- **Missing `data` branch in a fork:** bootstrap an orphan data branch before running publishing workflows. Keep it separate from source history and configure Pages to use GitHub Actions.
- **Backfill source page removed:** preserve the original archived snapshot; do not replace it with empty data.

For a reproducible older snapshot, use a full data commit SHA in raw GitHub URLs. Repair current output through the scraper/backfill workflow after fixing its source behavior; do not force-push `data` or hand-edit published JSON.
