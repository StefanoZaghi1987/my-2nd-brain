# Markdown Drop-Zone Ingestion — Design Spec
**Date:** 2026-05-29
**Branch:** feat-ingest
**Status:** draft

---

## 1. Problem

The drop zone (`raw/drop/`) currently supports only `.pdf` files. Any other file
type is explicitly ignored with `[!] ignored (not a PDF)`. Users who take notes
in Obsidian, save web pages as Markdown via browser extensions, or export
documents from other PKMs have no supported entry path for `.md` files.

---

## 2. Goal

Extend the drop zone to accept `.md` files alongside `.pdf` files. A user drops
any combination of PDFs and Markdown files into `raw/drop/`, runs `/ingest`, and
both types are automatically adopted and ingested into the wiki — with zero
editing required at drop time.

---

## 3. Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Drop folder | Same `raw/drop/` for all types | One place to remember; routed by extension |
| Dispatch | Type-handler registry (`HANDLERS` dict) | Open/closed: new types add one function + one dict entry; no orchestrator surgery |
| Raw storage | `raw/local/<slug>/content.md` + `index.md` | Mirrors `paper.pdf` + `index.md` pattern; raw content untouched |
| Title resolution | Cascade: frontmatter `title:` → first `# H1` → filename stem | Extracts best available signal without requiring any user action |
| URL resolution | Check frontmatter `source_url`, `url`, `link`, `source` | Covers MarkDownload, Obsidian Web Clipper, and common variants |
| Original file | Copied untouched to `content.md` | Preserves all original frontmatter, metadata, and syntax for LLM at ingest time |
| Ingest branch | New `local-md` branch reads `content.md` in full (no page limit) | Plain text; no PDF page-range needed |
| Fetch method | `fetch_method: local-md` | Discriminator consistent with `local-pdf`; branches every downstream operation |

---

## 4. Vault Structure

No new directories. `raw/drop/` and `raw/local/` already exist.

### `raw/local/<slug>/` structure for Markdown sources

```
raw/local/my-obsidian-note/
  index.md      ← vault-standard stub (written by adopt_drop.py)
  content.md    ← original .md file, byte-for-byte untouched
```

**`index.md` stub** written by `adopt_md()`:

```yaml
---
fetch_method: local-md
title: "My Obsidian Note"
fetched: 2026-05-29
source_url: https://...          # omitted if not found in original frontmatter
tags: []
---

Content: [[content.md]]
```

### Comparison with existing source types

| Field | `raw/papers/<slug>/` | `raw/local/<slug>/` (PDF) | `raw/local/<slug>/` (MD) |
|---|---|---|---|
| `fetch_method` | `pdf` | `local-pdf` | `local-md` |
| `source_url` | present | absent | present if extractable |
| raw content file | `paper.pdf` | `paper.pdf` | `content.md` |
| title source | URL metadata or slug | filename stem | cascade (see §5) |

---

## 5. `adopt_drop.py` Changes

### Type-handler registry

Replace the two-bucket split (`pdf_files` / `non_pdfs`) with a registry:

```python
HANDLERS: dict[str, Callable[[Path, Path, bool], AdoptResult]] = {
    ".pdf": adopt_pdf,
    ".md":  adopt_md,
}
```

Orchestrator logic in `process_drop_zone()`:

```python
supported   = [f for f in all_files if f.suffix.lower() in HANDLERS]
unsupported = [f for f in all_files if f.suffix.lower() not in HANDLERS]

for f in unsupported:
    print(f"  [!] ignored (unsupported type): {f.name}")

for f in supported:
    handler = HANDLERS[f.suffix.lower()]
    r = handler(f, local_dir, dry_run=dry_run)
    results.append(r)
```

### New extraction helpers (pure functions, no new dependencies)

```python
def extract_title_from_md(path: Path) -> str | None:
    """
    1. Parse YAML frontmatter → return title: value if present.
    2. Scan lines for first ^# (.+) heading → return match.
    3. Return None (caller falls back to title_from_slug).
    """

def extract_source_url_from_md(path: Path) -> str | None:
    """
    Check frontmatter for keys: source_url, url, link, source.
    Return first non-empty value found, or None.
    """
```

### New handler: `adopt_md()`

Mirrors `adopt_pdf()` in shape — same signature, same return type, same rollback
pattern (copy content first; write index.md; only on full success keep the copy
and remove the original from drop zone).

```
1. slug_from_filename(md_path.name) → slug
2. Collision check: if raw/local/<slug>/ exists → skip with AdoptResult(ok=False)
3. mkdir raw/local/<slug>/
4. Read original to extract_title_from_md() → title (fallback: title_from_slug)
5. Read original to extract_source_url_from_md() → source_url (may be None)
6. Write index.md stub (omit source_url line if None)
7. On index.md write success: rename original → raw/local/<slug>/content.md (atomic, mirrors adopt_pdf)
8. On any failure before rename: remove partial index.md + dir → raise (original stays in raw/drop/)
```

### Updated output summary

```
Found 2 PDF(s) and 1 Markdown file(s) in drop zone.
  [ok] adopted  raw/local/attention-is-all-you-need/
  [ok] adopted  raw/local/lecun-path-to-autonomy/
  [ok] adopted  raw/local/my-obsidian-note/
Adopted 3, skipped 0.
```

Dry-run output:

```
Found 2 PDF(s) and 1 Markdown file(s) in drop zone.
  would adopt: attention-is-all-you-need.pdf -> raw/local/attention-is-all-you-need/
  would adopt: lecun-path-to-autonomy.pdf    -> raw/local/lecun-path-to-autonomy/
  would adopt: my-obsidian-note.md           -> raw/local/my-obsidian-note/
```

---

## 6. Enhanced `/ingest` Command

### Pre-flight block (existing, updated wording only)

Step 2 currently reads "Scan for `*.pdf` files". Update to:

> Scan for files with supported types (`.pdf`, `.md`) in the drop zone.

No other changes to the pre-flight block — `adopt_drop.py` reports all adopted
slugs regardless of type; the batch tags/notes prompt applies to all of them.

### New source type branch: `local-md`

Added alongside the existing `local-pdf` branch:

```
fetch_method: local-md

1. Read index.md — get title, source_url (if present), tags, note.
2. Read content.md in full (plain text; no page limit).
3. Infer real title from content if better than index.md title
   (first H1 heading takes precedence over the filename-derived title).
4. Write wiki/sources/<slug>.md:
   - Include source_url only if present in index.md.
   - source_path: raw/local/<slug>/
   - fetch_method: local-md
5. Propagate tags and note as with other source types.
```

---

## 7. `CLAUDE.md` Changes

### Vault structure diagram

```
raw/
  web/<slug>/         Web articles converted to markdown
  papers/<slug>/      PDFs fetched via URL
  local/<slug>/       PDFs or Markdown files copy-pasted by the user
  drop/               Drop zone — paste files here; emptied by /ingest
```

### INGEST — source type branches

Add `local-md` branch (mirrors content of §6 above).

### Invariant #1 clarification

No change needed — the existing note already covers `adopt_drop.py` writing to
`raw/local/`; the Markdown extension uses the same script.

---

## 8. Linter Changes

### `check_drop_zone` / `drop_zone_not_empty` (advisory, existing)

Function `check_drop_zone` (`lint.py:372`) currently filters for `.pdf` only.
Update to check any file whose extension is in `HANDLERS` (`.pdf`, `.md`).
Report counts per type in the finding detail:

```
Drop zone has 2 PDF(s) and 1 Markdown file(s) — run /ingest to adopt them.
```

Single-type case still reads naturally:

```
Drop zone has 1 Markdown file(s) — run /ingest to adopt them.
```

### Existing `check_pdf_index` check

No change needed — the function (`lint.py:343`) validates that every subdirectory
under `raw/papers/` and `raw/local/` has an `index.md`. It does **not** assert
that `paper.pdf` exists. Markdown sources (which have `content.md` instead)
satisfy this check automatically.

---

## 9. Files to Create or Modify

| File | Action |
|---|---|
| `skills/inbox-fetcher/scripts/adopt_drop.py` | **Modify** — registry, `adopt_md()`, extraction helpers |
| `commands/ingest.md` | **Modify** — update pre-flight wording, add `local-md` protocol branch |
| `CLAUDE.md` | **Modify** — vault structure diagram, add `local-md` source type branch |
| `skills/vault-linter/scripts/lint.py` | **Modify** — update `DROP_ZONE_NOT_EMPTY` check |
| `skills/inbox-fetcher/SKILL.md` | **Modify** — document Markdown adoption |
| `skills/vault-linter/SKILL.md` | **Modify** — update check description |

Total: 6 files. Within invariant #5 (≤15 files per operation).

---

## 10. Out of Scope

- Non-Markdown, non-PDF types (`.epub`, `.docx`, `.txt`) — registry makes adding
  them a one-session task in the future; not addressed here
- Parsing Logseq-specific syntax (e.g. block references `((uuid))`) — the LLM
  reads `content.md` as-is at ingest time
- Automatic slug renaming for poor filenames (e.g. `export-final-v3.md`) — user
  renames before dropping
- Updating `init_vault.py` — no new directories or config keys are introduced
