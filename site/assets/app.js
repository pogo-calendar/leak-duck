// Renders the API site from docs.json (endpoint reference) and manifest.json
// (published files). Scraped data comes from a third-party site, so it is only
// ever inserted as text, never as HTML.

const BASE_URL = new URL(".", document.baseURI);
const ARCHIVE_PATTERN = /^archives\/archive_(\d{4})\.json$/;
const RECORDS_PER_PAGE = 25;

const $ = (id) => document.getElementById(id);

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "className" || key === "textContent" || key === "hidden") {
      node[key] = value;
    } else {
      node.setAttribute(key, value);
    }
  }
  node.append(...children.filter((child) => child != null));
  return node;
}

function absoluteUrl(path) {
  return new URL(path, BASE_URL).href;
}

// Patterns such as archive_{year}.json are shown as written, not URL-encoded.
function displayUrl(path) {
  return BASE_URL.href + path;
}

async function fetchJson(path) {
  const response = await fetch(new URL(path, BASE_URL));
  if (!response.ok) {
    throw new Error(`${path} returned HTTP ${response.status}`);
  }
  return response.json();
}

const relativeTime = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
const TIME_UNITS = [
  ["year", 31536000],
  ["month", 2592000],
  ["day", 86400],
  ["hour", 3600],
  ["minute", 60],
];

function describeAge(isoTime) {
  const seconds = (Date.parse(isoTime) - Date.now()) / 1000;
  for (const [unit, size] of TIME_UNITS) {
    if (Math.abs(seconds) >= size) {
      return relativeTime.format(Math.round(seconds / size), unit);
    }
  }
  return "just now";
}

function describeSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function freshness(fileInfo) {
  if (!fileInfo) return null;
  const updated = el("time", {
    datetime: fileInfo.updated_at,
    title: new Date(fileInfo.updated_at).toLocaleString(),
    textContent: describeAge(fileInfo.updated_at),
  });
  return el(
    "p",
    { className: "meta" },
    "Changed ",
    updated,
    ` · ${describeSize(fileInfo.size)}`,
  );
}

function copyButton(text) {
  const button = el("button", { type: "button", textContent: "Copy" });
  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Copy failed";
    }
    setTimeout(() => {
      button.textContent = "Copy";
    }, 1500);
  });
  return button;
}

function archiveYears(files) {
  return Object.keys(files)
    .map((path) => path.match(ARCHIVE_PATTERN)?.[1])
    .filter(Boolean)
    .sort()
    .reverse();
}

// Explorer choices: one per file, with one per archive year.
function explorerFiles(endpoints, files) {
  return endpoints.flatMap((endpoint) => {
    if (endpoint.id !== "archives") {
      return [{ label: endpoint.title, path: endpoint.path }];
    }
    return archiveYears(files).map((year) => ({
      label: `${endpoint.title} ${year}`,
      path: endpoint.path.replace("{year}", year),
    }));
  });
}

function renderEndpoints(endpoints, files) {
  const list = $("endpoint-list");
  list.replaceChildren(
    ...endpoints.map((endpoint) => {
      const isArchive = endpoint.id === "archives";
      const url = displayUrl(endpoint.path);
      const links = el(
        "p",
        { className: "card-links" },
        el("a", { href: `#reference-${endpoint.id}`, textContent: "Fields" }),
      );
      if (isArchive) {
        for (const year of archiveYears(files)) {
          links.append(
            el("a", {
              href: absoluteUrl(endpoint.path.replace("{year}", year)),
              textContent: year,
            }),
          );
        }
      } else {
        const explore = el("a", { href: "#explorer", textContent: "Explore" });
        explore.addEventListener("click", () => selectExplorerFile(endpoint.path));
        links.prepend(explore);
      }

      return el(
        "article",
        { className: "card" },
        el("h3", { textContent: endpoint.title }),
        el("p", { textContent: endpoint.summary }),
        el(
          "div",
          { className: "url-row" },
          el("code", { textContent: url }),
          isArchive ? null : copyButton(url),
        ),
        isArchive ? null : freshness(files[endpoint.path]),
        links,
      );
    }),
  );

  $("fetch-snippet").textContent =
    `const events = await fetch("${absoluteUrl("events.json")}")\n` +
    "  .then((response) => response.json());";
}

function renderReference(endpoints) {
  $("reference-list").replaceChildren(
    ...endpoints.map((endpoint) => {
      const rows = endpoint.fields.map((field) =>
        el(
          "tr",
          {},
          el("td", {}, el("code", { textContent: field.name })),
          el("td", {}, field.type ? el("code", { textContent: field.type }) : null),
          el("td", { textContent: field.description }),
        ),
      );
      const notes = endpoint.notes?.length
        ? el(
            "ul",
            { className: "notes" },
            ...endpoint.notes.map((note) => el("li", { textContent: note })),
          )
        : null;

      return el(
        "article",
        { className: "reference-entry", id: `reference-${endpoint.id}` },
        el("h3", {}, el("code", { textContent: endpoint.path })),
        el("p", { textContent: endpoint.structure }),
        el(
          "div",
          { className: "table-scroll" },
          el(
            "table",
            {},
            el(
              "thead",
              {},
              el(
                "tr",
                {},
                el("th", { scope: "col", textContent: "Field" }),
                el("th", { scope: "col", textContent: "Type" }),
                el("th", { scope: "col", textContent: "Description" }),
              ),
            ),
            el("tbody", {}, ...rows),
          ),
        ),
        notes,
      );
    }),
  );
}

function renderChangelog(changelog) {
  $("changelog-list").replaceChildren(
    ...changelog.map((release) =>
      el(
        "article",
        { className: "changelog-entry" },
        el("h3", {}, el("time", { datetime: release.date, textContent: release.date })),
        el("ul", {}, ...release.entries.map((entry) => el("li", { textContent: entry }))),
      ),
    ),
  );
}

// Every published file is an object of sections; arrays hold records directly,
// and objects (such as manifest.files) are split into one record per key.
function toSections(data) {
  return Object.entries(data).map(([name, value]) => {
    let records;
    if (Array.isArray(value)) {
      records = value;
    } else if (value && typeof value === "object") {
      records = Object.entries(value).map(([key, item]) => ({ [key]: item }));
    } else {
      records = [value];
    }
    return {
      name,
      records: records.map((record) => {
        const text = JSON.stringify(record, null, 2);
        return { text, searchText: text.toLowerCase() };
      }),
    };
  });
}

function renderSection(section, records) {
  const details = el(
    "details",
    {},
    el(
      "summary",
      {},
      section.name,
      " ",
      el("span", { className: "count", textContent: `(${records.length})` }),
    ),
  );
  const body = el("div", { className: "records" });
  details.append(body);

  let shown = 0;
  const showMore = () => {
    const next = records.slice(shown, shown + RECORDS_PER_PAGE);
    shown += next.length;
    body.querySelector(".more")?.remove();
    body.append(
      ...next.map((record) => el("pre", {}, el("code", { textContent: record.text }))),
    );
    if (shown < records.length) {
      const more = el("button", {
        type: "button",
        className: "more",
        textContent: `Show ${Math.min(RECORDS_PER_PAGE, records.length - shown)} more`,
      });
      more.addEventListener("click", showMore);
      body.append(more);
    }
  };
  // Records render on first open so large archives stay fast.
  details.addEventListener("toggle", () => {
    if (details.open && shown === 0) showMore();
  });
  return details;
}

const explorer = { sections: [], loadId: 0 };

function renderExplorer() {
  const query = $("explorer-filter").value.trim().toLowerCase();
  const matches = explorer.sections
    .map((section) => ({
      section,
      records: query
        ? section.records.filter((record) => record.searchText.includes(query))
        : section.records,
    }))
    .filter(({ records }) => records.length > 0);

  const total = matches.reduce((sum, { records }) => sum + records.length, 0);
  $("explorer-status").textContent = query
    ? `${total} matching record${total === 1 ? "" : "s"} in ${matches.length} section${matches.length === 1 ? "" : "s"}.`
    : `${total} records in ${matches.length} sections. Open a section to browse it.`;

  const results = matches.map(({ section, records }) => renderSection(section, records));
  // A narrow filter opens its few matching sections; opening fires "toggle".
  if (query && results.length <= 3) {
    for (const details of results) details.open = true;
  }
  $("explorer-results").replaceChildren(...results);
}

async function loadExplorerFile(path) {
  const loadId = ++explorer.loadId;
  $("explorer-status").textContent = `Loading ${path}…`;
  $("explorer-results").replaceChildren();
  try {
    const data = await fetchJson(path);
    if (loadId !== explorer.loadId) return;
    explorer.sections = toSections(data);
    renderExplorer();
  } catch (error) {
    if (loadId !== explorer.loadId) return;
    explorer.sections = [];
    $("explorer-status").textContent = `Could not load ${path}: ${error.message}`;
  }
}

function selectExplorerFile(path) {
  const select = $("explorer-file");
  if (select.value !== path) {
    select.value = path;
    loadExplorerFile(path);
  }
}

function setUpExplorer(choices) {
  const select = $("explorer-file");
  select.replaceChildren(
    ...choices.map((choice) => el("option", { value: choice.path, textContent: choice.label })),
  );
  select.addEventListener("change", () => loadExplorerFile(select.value));
  $("explorer-filter").addEventListener("input", renderExplorer);
  $("explorer-form").addEventListener("submit", (event) => event.preventDefault());
  if (choices.length > 0) loadExplorerFile(choices[0].path);
}

function showError(message) {
  const notice = $("load-error");
  notice.textContent = message;
  notice.hidden = false;
}

async function main() {
  const [docsResult, manifestResult] = await Promise.allSettled([
    fetchJson("docs.json"),
    fetchJson("manifest.json"),
  ]);
  if (docsResult.status === "rejected") {
    showError(`Could not load the API reference: ${docsResult.reason.message}`);
    return;
  }

  const { endpoints, changelog } = docsResult.value;
  let files = {};
  if (manifestResult.status === "fulfilled") {
    files = manifestResult.value.files ?? {};
  } else {
    showError(
      `Could not load manifest.json, so update times are unavailable: ${manifestResult.reason.message}`,
    );
  }

  renderEndpoints(endpoints, files);
  renderReference(endpoints);
  renderChangelog(changelog);
  setUpExplorer(explorerFiles(endpoints, files));
}

main();
