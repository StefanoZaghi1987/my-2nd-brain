---
name: inbox-fetcher
description: Processes a queue of URLs listed in inbox.md for a second brain vault, downloading each page as clean markdown in raw/web/<slug>/index.md with images in an assets/ subdirectory. Use this skill whenever the user mentions "inbox", "fetch", "process links", "scrape URLs", "download articles", or adds URLs to inbox.md. Run this BEFORE any ingest operation so the agent has clean raw files to work from. Handles HTML articles via trafilatura, direct PDF downloads, and per-URL failures (paywalls, JS-rendered pages, timeouts) gracefully without blocking the rest of the queue. Walled domains (X/Twitter, LinkedIn, Threads, Facebook, Instagram) are flagged for an agent-driven Playwright MCP fallback instead of being attempted with trafilatura. Arxiv abstract/html URLs are rewritten to the PDF endpoint so the paper itself is archived, not the landing page. Also provides adopt_drop.py, which adopts copy-pasted PDFs from raw/drop/ into raw/local/<slug>/ as a pre-flight step for /ingest.
provides: fetch
config_section: fetch
requires:
  python: ">=3.10"
  packages: [trafilatura, requests, python-slugify]
---

# Inbox Fetcher

Processes a queue of URLs from `inbox.md` into clean markdown files under `raw/web/`, ready for ingest into the wiki.

## When to use this skill

Trigger whenever the user:

- Says "process the inbox", "fetch the inbox", "scrape the links", "download these URLs"
- Adds URLs to `inbox.md` and asks to prepare them
- Asks to ingest web content and the vault has an `inbox.md` file
- Wants to refresh or re-fetch a URL already in the inbox

This skill is a **pre-ingest step**. After it runs, the user (or the agent following the vault's `CLAUDE.md`) performs the actual ingest — reading the new files in `raw/` and compiling them into the wiki.

## Vault assumptions

The skill expects this layout:

```
<vault>/
├── inbox.md              queue of URLs (checkbox format)
├── raw/
│   ├── web/              HTML article output
│   └── papers/           direct PDF downloads
└── .claude/
    └── skills/
        └── inbox-fetcher/
            ├── SKILL.md
            └── scripts/
                └── fetch_inbox.py
```

The skill creates `raw/web/` and `raw/papers/` if they don't exist.

## Inbox format

`inbox.md` uses GitHub-flavored task list syntax, readable in Obsidian and parseable with regex:

```markdown
# Inbox

## To process

- [ ] https://www.anthropic.com/engineering/agent-skills
- [ ] https://example.com/paper-x.pdf
  - tags: agent-skills, spec
  - note: focus on composition

## Processed

- [x] https://old-url.com → `raw/web/old-url-slug/` (2026-04-15)
```

Rules:

- Only lines matching `- [ ] <URL>` at the start (unchecked) are processed.
- Indented sub-bullets (`- tags: tag1, tag2` and `- note: focus on X`) are parsed by the script and written into the raw source's `index.md` frontmatter. The ingest step reads them from there via tag/note propagation.
- After a successful fetch, the line moves to "Processed" and gets marked `- [x]` with the output path and date.
- Failed fetches get an inline `⚠ <reason>` suffix and stay unchecked so the user can decide.

## How to run it

From the vault root:

```bash
python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
```

Or from anywhere:

```bash
python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --vault /path/to/vault
```

Use `--dry-run` to see what would be processed without actually fetching.

The script is idempotent: already-processed URLs (marked `[x]`) are skipped. To re-fetch a URL, un-check it manually in `inbox.md`.

## What the script does per URL

1. **URL rewriting (pre-fetch).** Certain URLs are rewritten to reach the actual content instead of a landing page. Today: arxiv — any `arxiv.org/abs/<id>`, `arxiv.org/html/<id>`, or `arxiv.org/pdf/<id>` (with or without `.pdf`, with or without a `vN` version suffix) is rewritten to `arxiv.org/pdf/<id>.pdf` so we archive the paper itself. The slug becomes `arxiv-<id>` verbatim (no slugify — preserves the canonical ID). The inbox line still tracks the URL you wrote.
2. **PDF detection.** If the (rewritten) URL path ends in `.pdf` or the server returns `Content-Type: application/pdf`, download as-is to `raw/papers/<slug>.pdf`.
3. **HTML extraction.** Otherwise, use `trafilatura` to fetch and extract clean markdown with metadata (title, author, publish date, language).
4. **Slug generation.** For rewritten URLs, use the override slug (e.g. `arxiv-2405.12345`). Otherwise prefer the article title, fallback to `<hostname>-<hash8>`.
5. **Image download.** Parse `![alt](url)` patterns, download each image into `raw/web/<slug>/assets/` with a hash-based filename, rewrite paths to local.
6. **Frontmatter.** Prepend YAML with `source_url`, `title`, `author`, `fetched`, `language`.
7. **Inbox update.** On success, move to "Processed". On failure, append ⚠ with reason.

## Dependencies

Python 3.10+ and:

```bash
pip install trafilatura requests python-slugify
```

If a dependency is missing, the script prints a clear install command and exits with code 1.

## Edge cases

- **Walled domain (preflight).** Hosts in `WALLED_DOMAINS` (X/Twitter, LinkedIn, Threads, Facebook, Instagram) are skipped upfront — trafilatura would fail anyway. Marked `⚠ walled domain (<host>) — try playwright`. Agent follows up with the Playwright MCP fallback (see below).
- **Paywall / 403 / login wall (non-walled host).** Extraction returns empty. Marked `⚠ extraction empty (likely paywall or JS-rendered) — try playwright`. Same Playwright fallback applies.
- **JS-rendered SPA.** Same as above — `try playwright` hint.
- **Very large PDFs (>50 MB).** Downloaded anyway, prints a warning.
- **Duplicate URL.** If already in "Processed", skipped with a message. Un-check manually to force re-fetch.
- **Network timeout.** Per-request timeout is 20s for HTML, 60s for PDFs. Failures don't block the queue.

## Playwright fallback

Any URL marked `⚠ ... — try playwright` in inbox.md is a hand-off from
the script to the agent. Use the `/playwright-fetch` command — it contains
the full per-URL protocol.

## Output contract

After a run, the script prints:

```
Processed 5 URLs:
  ✓ 3 HTML articles → raw/web/
  ✓ 1 PDF → raw/papers/
  ⚠ 1 failed (extraction empty): https://paywall-site.com/article
```

The agent reports this summary verbatim and asks the user whether to proceed with ingest on the new files.

## Drop zone adoption (`adopt_drop.py`)

Companion script for copy-pasted PDFs that arrive outside a URL.

**When to use:** called automatically by `/ingest` as a pre-flight step
when `raw/drop/` (or the configured `drop_zone.path`) contains `.pdf` files.
Skips silently when `drop_zone.enabled: false`. Can also be run manually.

**What it does per file:**
1. Derives a slug from the filename stem via `slugify()`.
2. Checks for collision: if `raw/local/<slug>/` already exists, skips with a warning.
3. Creates `raw/local/<slug>/`, moves the PDF to `paper.pdf`.
4. Writes a stub `index.md` with `fetch_method: local-pdf`, stub title, and today's date.
5. Prints `[ok] adopted  raw/local/<slug>/`.

**Run manually:**
```bash
python3 skills/inbox-fetcher/scripts/adopt_drop.py            # adopt (default: cwd)
python3 skills/inbox-fetcher/scripts/adopt_drop.py --vault /path/to/vault
python3 skills/inbox-fetcher/scripts/adopt_drop.py --dry-run  # preview only; no files moved
```

**Output contract (live run):**
```
Found 2 PDF(s) in drop zone.
  [ok] adopted  raw/local/attention-is-all-you-need/
  [ok] adopted  raw/local/lecun-path-to-autonomy/
Adopted 2, skipped 0.
```

**Output contract (dry run):**
```
Found 2 PDF(s) in drop zone.
  would adopt: attention-is-all-you-need.pdf -> raw/local/attention-is-all-you-need/
  would adopt: lecun-path-to-autonomy.pdf -> raw/local/lecun-path-to-autonomy/
```

Exit codes: `0` = all adopted (or nothing to do); `1` = bad `--vault` path; `2` = partial (≥1 skipped due to slug collision).

## Not in scope

- Re-extraction when HTML source changes (no versioning; user re-fetches manually).
- Authenticated scraping inside the Python script (cookies, API keys) — user downloads manually, or uses the Playwright MCP fallback interactively.
- Image OCR or figure extraction from PDFs.
- Scheduling / cron — user or the agent's own scheduler decides when to run.
- Unattended batch via Playwright — the fallback requires an interactive session with the agent (one confirmation per URL).
