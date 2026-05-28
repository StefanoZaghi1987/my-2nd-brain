# Copy-Paste PDF Ingestion — Design Spec
**Date:** 2026-05-28
**Branch:** feat-ingest
**Status:** draft

---

## 1. Problem

The vault currently accepts PDF sources only through the URL-based inbox fetcher
(`fetch_inbox.py`). PDFs that arrive outside a URL — exported from a reference
manager, downloaded manually, received as attachments — have no supported entry
path. A user who drops such a file into the vault has no way to ingest it.

---

## 2. Goal

Allow the user to copy-paste PDF files into a dedicated drop zone folder
(`raw/drop/`), then run `/ingest` as the single entry point to adopt and
summarise them — with zero editing required at drop time.

---

## 3. Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Drop UX | Drop file only (Option A) | Zero friction at capture time |
| Entry point | `/ingest` pre-flight (not a new command) | One mental model |
| Raw-layer writes | New Python script `adopt_drop.py` | Keeps "scripts write raw/, LLM writes wiki/" invariant |
| Storage location | `raw/local/<slug>/` (not `raw/papers/`) | Provenance separation: `raw/papers/` = URL origin, `raw/local/` = filesystem origin |
| Tags / notes | Asked interactively at ingest time | Durable: written to `index.md` stub before PDF is read |
| Slug source | Filename stem via `slugify()` | Best available signal without a URL |

---

## 4. Vault Structure Changes

### New directories

```
raw/
  web/<slug>/        ← HTML articles fetched from URLs          (existing)
  papers/<slug>/     ← PDFs fetched from URLs                   (existing, unchanged)
  local/<slug>/      ← PDFs copy-pasted by the user             (NEW)
  drop/              ← staging area; empties after /ingest       (NEW)
```

### `raw/drop/` rules

- Only `.pdf` files are picked up; anything else is ignored with a warning printed to stdout.
- Files are **moved** (not copied) to `raw/local/<slug>/paper.pdf` — the drop zone is empty after a successful run.
- Slug collision (a `raw/local/<slug>/` folder already exists): skip with a warning, leave the file in `raw/drop/`.
- The directory is created by `init_vault.py` alongside the other `raw/` subdirs.

### `raw/local/<slug>/` structure

Identical to `raw/papers/<slug>/` except:

| Field | `raw/papers/<slug>/index.md` | `raw/local/<slug>/index.md` |
|---|---|---|
| `source_url` | present (origin URL) | **absent** |
| `fetch_method` | `pdf` | `local-pdf` |
| `title` | from URL metadata or slug | from filename stem (title-cased) |

Example stub `index.md` for `attention-is-all-you-need.pdf`:

```yaml
---
fetch_method: local-pdf
title: "Attention Is All You Need"
fetched: 2026-05-28
tags: []
---

PDF: [[paper.pdf]]
```

The `fetch_method: local-pdf` value is the authoritative marker distinguishing
local PDFs from URL-fetched ones at every layer (ingest, refresh, linter).

---

## 5. New Script: `adopt_drop.py`

**Location:** `skills/inbox-fetcher/scripts/adopt_drop.py`

**Responsibility:** raw-layer adoption — moves files from `raw/drop/` into
`raw/local/<slug>/` and writes a stub `index.md`. No wiki writes. No LLM.

### Interface

```bash
python3 skills/inbox-fetcher/scripts/adopt_drop.py             # vault = cwd
python3 skills/inbox-fetcher/scripts/adopt_drop.py --vault /p  # explicit path
python3 skills/inbox-fetcher/scripts/adopt_drop.py --dry-run   # preview only
```

Exit codes mirror `fetch_inbox.py`: `0` = all adopted, `2` = partial (some skipped).

### Algorithm (per file)

1. Read filename stem; run `slugify()` to produce slug.
2. Check for collision: if `raw/local/<slug>/` exists, print warning and skip.
3. Create `raw/local/<slug>/`.
4. Move `raw/drop/<filename>.pdf` → `raw/local/<slug>/paper.pdf`.
5. Derive stub title: slug → replace hyphens/underscores with spaces → title-case.
6. Write `raw/local/<slug>/index.md` with frontmatter (`fetch_method: local-pdf`,
   `title`, `fetched: <today>`).
7. Print: `✓ adopted  raw/local/<slug>/`.

### Output summary

```
Found 2 PDF(s) in drop zone.
  ✓ adopted  raw/local/attention-is-all-you-need/
  ✓ adopted  raw/local/lecun-path-to-autonomy/
Adopted 2, skipped 0.
```

### Dependencies

Standard library only — no `requests`, no `trafilatura`.
Uses `vault_state.py` for `load_config()` (same pattern as `fetch_inbox.py`).

---

## 6. Enhanced `/ingest` Command

`commands/ingest.md` gains a **Pre-flight block** inserted before the existing
"Discover targets" section.

### Pre-flight: drop zone adoption

```
1. Read drop_zone.path from vault.config.yml (default: raw/drop).
2. Scan for *.pdf files in the drop zone.
3. If any found:
   a. Run: python3 skills/inbox-fetcher/scripts/adopt_drop.py --vault <vault>
   b. Report: "Adopted N PDF(s): [slug, slug, ...]"
   c. Ask once (batch):
        "Any tags or focus notes before I ingest these?
         (e.g. lecun-path-to-autonomy: tags: autonomy, ml | note: focus on world models)"
   d. If the user provides tags/notes, update each affected raw/local/<slug>/index.md
      frontmatter before reading.
4. Proceed with normal ingest discovery — newly adopted slugs now appear
   as uningested sources.
```

The interactive tags/notes question is asked **after** adoption (files are
already safe in `raw/local/`) and **before** reading the PDF (so the focus
note can shape the summary). If the user skips, ingest proceeds without tags.

### PDF ingest protocol extension

The existing PDF protocol in `commands/ingest.md` applies unchanged to
`raw/local/<slug>/` with one addition:

> When `fetch_method: local-pdf`, omit `source_url` from
> `wiki/sources/<slug>.md` frontmatter. All other steps (read pages 1–5,
> infer real title from first heading, write summary) are identical.

The `source_path` in the wiki source frontmatter uses the new prefix:

```yaml
source_path: raw/local/<slug>/
```

---

## 7. `vault.config.yml` Additions

```yaml
drop_zone:
  path: "raw/drop"    # relative to vault root; change if you prefer a different location
  enabled: true
```

The `adopt_drop.py` script and `/ingest` both read `drop_zone.path` via
`load_config()`. Setting `enabled: false` causes the pre-flight step to be
silently skipped.

---

## 8. Linter Addition

**New check: `DROP_ZONE_NOT_EMPTY` (advisory)**

Condition: `raw/drop/` (or `drop_zone.path`) contains one or more `.pdf` files.

Message: `Drop zone has N unprocessed file(s) — run /ingest to adopt them.`

This fires when the user dropped files but forgot to run `/ingest`.
The check is advisory (not an error); it does not block a clean lint pass.

**Existing check: `PAPERS_MISSING_INDEX` (already present)**

The linter already checks that every `raw/papers/<slug>/` has an `index.md`.
The same check is extended to cover `raw/local/<slug>/` subdirectories.

---

## 9. `CLAUDE.md` Changes

### Vault structure diagram

Add two new lines:

```
raw/
  papers/             PDFs fetched via URL
  web/<slug>/         Web articles converted to markdown
  local/<slug>/       PDFs copy-pasted by the user    ← NEW
  drop/               Drop zone — paste PDFs here      ← NEW
```

### INGEST operation

Add a **drop zone branch** at the top of the INGEST section (before the
existing "source type branches") describing the pre-flight step and the
`local-pdf` source type branch.

### Source type branches

Add a new branch for **local PDFs** (`raw/local/<slug>/index.md`,
`fetch_method: local-pdf`):

```
1. Read index.md — get title, tags, note.
2. Read paper.pdf pages 1-5 (same as URL-fetched PDFs).
3. Write wiki/sources/<slug>.md — omit source_url field.
4. Carry tags and note as with other source types.
```

### Skill dispatch table

Add row:

| ADOPT | adopt_drop.py | — |

### Invariant #1 clarification

Invariant #1 ("Never write to `raw/`") already has one exception (FORGET
allows deletion). Add a second:

> `adopt_drop.py` writes to `raw/local/` — this is allowed because it is a
> script (not the LLM) and mirrors the same exception already granted to
> `fetch_inbox.py` writing to `raw/papers/`.

---

## 10. `init_vault.py` Changes

Two additions to the directory-creation step:

- Create `raw/local/` with a `.gitkeep`
- Create `raw/drop/` with a `.gitkeep`

One addition to the `vault.config.yml` template install: add the `drop_zone`
section.

One addition to the skills/commands installation loop: install `adopt_drop.py`
alongside `fetch_inbox.py`.

---

## 11. Files to Create or Modify

| File | Action |
|---|---|
| `skills/inbox-fetcher/scripts/adopt_drop.py` | **Create** |
| `commands/ingest.md` | **Modify** — add pre-flight block and `local-pdf` branch |
| `vault.config.yml` | **Modify** — add `drop_zone` section |
| `skills/vault-linter/scripts/lint.py` | **Modify** — add `DROP_ZONE_NOT_EMPTY` check, extend `PAPERS_MISSING_INDEX` to `raw/local/` |
| `skills/vault-linter/SKILL.md` | **Modify** — document new check |
| `skills/inbox-fetcher/SKILL.md` | **Modify** — document `adopt_drop.py` |
| `CLAUDE.md` | **Modify** — structure diagram, INGEST section, source type branches, skill dispatch, invariant #1 note |
| `init_vault.py` | **Modify** — create `raw/local/` and `raw/drop/`, install config section and script |

Total: 8 files. Within invariant #5 (≤15 files per operation).

---

## 12. Out of Scope

- Non-PDF local files (`.epub`, `.docx`, `.txt`) — not addressed here
- Automatic slug renaming if a filename is poor (e.g. `final_v3.pdf`) — user renames before dropping
- Re-adoption if a local PDF changes on disk — handled by `/refresh` (no URL to re-fetch; user replaces `paper.pdf` manually and runs `/refresh`)
- Batch metadata via sidecar files — dropped in favour of interactive ingest-time prompting
