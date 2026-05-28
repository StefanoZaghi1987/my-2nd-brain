---
description: Compile raw sources into the wiki. Reads raw/web/ and raw/papers/ for
  sources that don't yet have a wiki/sources/<slug>.md entry, summarises each, links
  them into wiki/pages/, and updates wiki/index.md and wiki/log.md.
---

# /ingest — Compile raw sources into the wiki

## When to use

After running the inbox fetcher, or when new files have been added to `raw/` manually.
Also when asked to "ingest", "summarise the new sources", or "add this to the wiki".

## Discover targets

If no slug is given: scan `raw/web/` and `raw/papers/` for subdirectories that have an
`index.md` but no corresponding `wiki/sources/<slug>.md`. These are the uningested sources.

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

Source: `raw/papers/<slug>/index.md` with `fetch_method: pdf`.

1. Read `index.md` — get `source_url`, `title`, `tags`, `note`.
2. Read `paper.pdf` using the Read tool — pages 1–5. If the paper has more than
   10 pages, also read the last 2 pages.
3. Infer the title from the first visible heading; fall back to the slug.
4. Write `wiki/sources/<slug>.md` with the same schema as web sources,
   plus `fetch_method: pdf` in frontmatter.
5. Propagate `tags` and `note` as above.

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
