---
description: Compile raw sources into the wiki. Reads raw/web/, raw/papers/, and
  raw/local/ for sources that don't yet have a wiki/sources/<slug>.md entry, summarises
  each, links them into wiki/pages/, and updates wiki/index.md and wiki/log.md. Also
  runs adopt_drop.py as a pre-flight step to adopt any PDFs in raw/drop/.
---

# /ingest — Compile raw sources into the wiki

## When to use

After running the inbox fetcher, or when new files have been added to `raw/` manually.
Also when asked to "ingest", "summarise the new sources", or "add this to the wiki".

## Pre-flight: drop zone adoption

Before discovering uningested sources, check whether the drop zone contains
any PDFs waiting to be adopted.

1. Read `drop_zone.path` from `vault.config.yml` (default: `raw/drop`).
2. Scan for files with supported types (`.pdf`, `.md`) in the drop zone directory.
3. If any are found:
   a. Run: `python3 skills/inbox-fetcher/scripts/adopt_drop.py --vault <vault_root>`
   b. Report which slugs were adopted. If the script exits with code 2, also
      report the skipped file(s) and reason (slug collision) before proceeding.
   c. Ask once (batch prompt):
      > "Any tags or focus notes before I ingest these?
      > Format: `<slug>: tags: <t1>, <t2> | note: <text>` — one entry per line."
      > Example: `lecun-path: tags: autonomy, ml | note: focus on world models`"
   d. If the user provides tags or notes, update each affected
      `raw/local/<slug>/index.md` frontmatter before reading the PDF.
4. Successfully adopted slugs now appear as uningested sources in
   `raw/local/` and will be discovered in the step below.

If `drop_zone.enabled: false` in `vault.config.yml`, skip this step silently.

## Discover targets

If no slug is given: scan `raw/web/`, `raw/papers/`, and `raw/local/` for subdirectories
that have an `index.md` but no corresponding `wiki/sources/<slug>.md`. These are the
uningested sources.

If a slug is given (`/ingest arxiv-2405-12345`): target that source only.

Confirm with the user before ingesting more than one source at a time:
> "Found N new sources: [list]. Ingest all?"

## Protocol

### Pre-ingest check

Before writing any new `wiki/pages/` entry, scan the existing pages directory
for a file whose name closely matches the proposed concept name (case-insensitive,
ignore articles and punctuation). If a close match exists:

- **Update the existing page** rather than creating a new one.
- Cite the new source alongside any existing citations already on that page.
- Do not create a second page for the same concept under a different slug.

If two sources being ingested in the same session both reference the same
emerging concept, create the page once during the first source and update
it during the second. Track which pages were created or updated this session
to avoid proposing duplicates mid-session.

### Web articles

Source: `raw/web/<slug>/index.md` (no `fetch_method` field, or `fetch_method: html`).

1. Read `index.md` — get `source_url`, `title`, `tags`, `note`.
2. Read the article body.
3. Write `wiki/sources/<slug>.md` with a summary in your own words.
4. Propagate `tags` into the source frontmatter.
   If `note` is present, address that topic explicitly in the summary — not just
   acknowledge it.

### PDFs

Source: `raw/papers/<slug>/index.md` with `fetch_method: pdf`, **or**
`raw/local/<slug>/index.md` with `fetch_method: local-pdf`.

1. Read `index.md` — get `title`, `tags`, `note`.
   - For `fetch_method: pdf`: also read `source_url`.
   - For `fetch_method: local-pdf`: no `source_url` field; omit it everywhere.
2. Read `paper.pdf` using the Read tool — pages 1–5. If the paper has more than
   10 pages, also read the last 2 pages.
3. Infer the title from the first visible heading; fall back to the `title` in
   `index.md` frontmatter.
4. Write `wiki/sources/<slug>.md` with the same schema as web sources.
   - For `fetch_method: pdf`: include `source_path: raw/papers/<slug>/` and
     `fetch_method: pdf` in the wiki source frontmatter.
   - For `fetch_method: local-pdf`: include `source_path: raw/local/<slug>/` and
     `fetch_method: local-pdf` in the wiki source frontmatter.
     Do **not** include a `source_url` field.
5. Propagate `tags` and `note` as with other source types.

### Local Markdown files

Source: `raw/local/<slug>/index.md` with `fetch_method: local-md`.

1. Read `index.md` — get `title`, `source_url` (if present), `tags`, `note`.
2. Read `content.md` in full (plain text; no page limit).
3. Infer real title from content if better than `index.md` title
   (first H1 heading takes precedence over the filename-derived title).
4. Write `wiki/sources/<slug>.md`:
   - Include `source_url` only if present in `index.md`.
   - `source_path: raw/local/<slug>/`
   - `fetch_method: local-md`
5. Propagate `tags` and `note` as with other source types.

## Guards

- **≤3 new pages before confirm.** If ingesting a source would require creating more
  than 3 new `wiki/pages/` entries for emerging concepts, stop and list the proposed
  pages. Ask: "Create all three?" before writing any.
- **≤15 files per operation (invariant #6).** If a single ingest would touch more
  than 15 files, split across sessions. Report the count and ask which sources to
  prioritise.

## Completion steps

After every ingest, regardless of how many sources:

1. Update `wiki/index.md` — add a line under `## Sources` for each new source.
2. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <slug>` for each source.
3. Report to the user: sources ingested, pages created or updated, any guards triggered.
