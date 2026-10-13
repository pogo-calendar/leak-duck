# Contributing

Follow the [organization contribution guide](https://github.com/pokelitee/.github/blob/main/CONTRIBUTING.md). Use the [README](README.md) for setup and API links.

## Local checks

Use Python 3.12+ and Node.js for the site syntax check. Activate the virtual environment from the setup instructions before running these commands.

Install the pinned development tools and run the same checks used by CI:

```sh
python -m pip install -r requirements-dev.txt
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

Dependabot checks Python dependencies and pinned GitHub Actions weekly. Keep `requirements.txt`, `requirements-dev.txt`, and package dependency declarations consistent when updating dependencies.
