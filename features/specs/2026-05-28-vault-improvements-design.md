# Vault Improvements Design

**Date:** 2026-05-28
**Scope:** Personal research vault, single-user, single-domain

---

## Context

This spec covers a set of improvements to the LLM Wiki vault implementation, addressing four confirmed bugs, five missing features, and an architectural foundation that makes all of them cohesive.

The vault is based on Andrej Karpathy's LLM Wiki pattern: a human-curated `raw/` directory of immutable sources, compiled by an agent into `wiki/`. The agent handles reading, writing, linking, and reflecting. The human curates.

---

## Architectural Approach: Hybrid Config + Skill Manifest

The implementation adopts a hybrid architecture with three layers:

### 1. `vault.config.yml` — the knob layer

A file at the vault root holding every value that legitimately varies between vaults. Currently these values are hardcoded in Python scripts and CLAUDE.md. The config file becomes the single source of truth.

```yaml
vault:
  version: 1

inbox:
  processed_section: "## Processed"
  tags_propagation: true

fetch:
  html_timeout_seconds: 20
  pdf_timeout_seconds: 60
  max_pdf_size_mb: 50
  pdf_enabled: true
  walled_domains:
    - x.com
    - twitter.com
    - mobile.twitter.com
    - linkedin.com
    - www.linkedin.com
    - threads.net
    - facebook.com
    - www.facebook.com
    - instagram.com
    - www.instagram.com

lint:
  stale_source_days: 180
  view_stale_days: 30
  auto_trigger_after_ingests: 5
  auto_trigger_after_days: 7

ingest:
  max_new_pages_before_confirm: 3
  max_files_per_operation: 15
```

Loading contract: every Python script calls `load_config(vault_root)` once at startup. Falls back to hardcoded defaults when the file is absent, so existing vaults keep working.

### 2. Skill manifest fields — formalize what's already there

Each `SKILL.md` gains three frontmatter fields:

```yaml
provides: fetch          # operation this skill backs
config_section: fetch    # vault.config.yml block it reads (null if none)
requires:
  python: ">=3.10"
  packages: [trafilatura, requests, python-slugify]
```

`init-vault.sh` reads `requires.packages` from all installed skill manifests to drive its dependency check, replacing the current hardcoded package list.

### 3. CLAUDE.md as the router — plus a dispatch table

CLAUDE.md remains the agent's operating contract. A new "## Skill dispatch" section makes explicit which operations have Python backing and which are LLM-only:

| Operation | Skill | Backed by |
|-----------|-------|-----------|
| FETCH | inbox-fetcher | scripts/fetch_inbox.py |
| LINT | vault-linter | scripts/lint.py |
| VIEW | view-builder | templates/ + LLM |
| INGEST | (LLM only) | — |
| QUERY | (LLM only) | — |
| REFLECT | (LLM only) | — |
| PROMOTE | (LLM only) | — |
| REFRESH | (LLM only) | — |

---

## Section 1: Foundation

### `skills/shared/vault_state.py`

A new shared module providing:

- `load_config(vault_root: Path) -> dict` — reads `vault.config.yml`, returns nested dict, falls back to defaults if absent, raises a clear error if the file is malformed.
- `read_state(vault_root: Path) -> dict` — reads `.lint/state.yaml`, returns empty dict if absent.
- `write_state(vault_root: Path, updates: dict) -> None` — patch semantics: merges updates into existing state, preserving unmentioned keys.

Standard library only. Imported by both `fetch_inbox.py` and `lint.py` via a path relative to the script's own location.

### Script migration

Both `fetch_inbox.py` and `lint.py` replace all hardcoded constants with values from `load_config()` and all `.lint/state.yaml` reads/writes with `read_state()` / `write_state()`.

`fetch_inbox.py` additionally calls `write_state(vault, {"ingests_since_last_lint": n + 1})` after any run where at least one URL succeeded. This wires the auto-lint trigger that was previously aspirational.

### `init-vault.sh` additions

- Generates `vault.config.yml` at the vault root on first run (skipped if exists).
- Copies `skills/shared/vault_state.py` into `.claude/skills/shared/` on every run (always refreshed, same as skill scripts).
- Adds `skills/shared/` to the `DIRS` array.

---

## Section 2: Bug Fixes

### Bug #1 — Inbox section name mismatch

Resolved by the config layer: `inbox.processed_section` in `vault.config.yml` defaults to `"## Processed"`. `fetch_inbox.py` reads this value instead of the hardcoded `"## Processati"`. The `inbox.md` template in `init-vault.sh` is updated from `## Done` to `## Processed`.

**Migration note for existing vaults:** vaults bootstrapped before this change will have `## Done` in their `inbox.md`. After adding `vault.config.yml`, set `inbox.processed_section: "## Done"` to match the existing section header, or rename the section in `inbox.md` to `## Processed`.

### Bug #2 — Lint auto-trigger counter not wired

Resolved by `vault_state.py`: `fetch_inbox.py` increments `ingests_since_last_lint` via `write_state()` after successful fetches. `commands/lint.md` documents the auto-trigger condition the agent checks at session start.

### Bug #3 — `/lint` command missing

New file `commands/lint.md` following the structure of the four existing command files. Documents both the explicit `/lint` trigger and the auto-trigger logic referencing `vault.config.yml` key names. `init-vault.sh` install loop extended to include `lint`.

### Bug #4 — `based_on` dead links not caught by linter

Two additions to `lint.py`:

- `strip_wikilink(s: str) -> str` helper — removes leading `[[` and trailing `]]`. Extracted from inline logic in `check_view_staleness()` and used by both that function and the new check.
- `check_based_on_links(pages, vault)` — iterates all view pages, reads `based_on` frontmatter list, resolves each entry via the existing `normalize_link_target()`. Unresolvable entries produce **blocking** findings under check name `based_on_dead_links`.

---

## Section 3: PDF Ingest + Tags/Notes Propagation

### PDF folder structure

PDF fetches now produce a folder matching the web article convention:

```
raw/papers/<slug>/
  paper.pdf
  index.md      ← frontmatter + single reference line
```

`index.md` frontmatter: `source_url`, `title` (inferred or "Untitled"), `fetched`, `fetch_method: pdf`, `tags` (if present), `note` (if present).

`fetch_pdf()` accepts `tags` and `note` parameters. `FetchResult.out_path` points to the folder.

The linter gains two advisory checks (no findings for empty `raw/papers/`):
- `missing_pdf_index` — `raw/papers/` subdirectory without an `index.md`.
- `legacy_flat_pdf` — flat `.pdf` file directly inside `raw/papers/` (pre-convention artifact).

### Tags and notes propagation

`InboxEntry` gains two optional fields: `tags: list[str]` and `note: str | None`.

`find_unchecked_entries()` parses indented sub-bullets following each URL line:
- `  - tags: tag1, tag2` → `entry.tags`
- `  - note: focus on the evaluation section` → `entry.note`

Both `fetch_html()` and `fetch_pdf()` write these values into the raw `index.md` frontmatter. Tags as inline YAML list; note as quoted string. Both omitted entirely when empty/None.

CLAUDE.md INGEST section gains two protocol branches:

**PDF branch:** when `fetch_method: pdf` is present in `raw/` index.md, read `paper.pdf` via the Read tool (pages 1–5; also last 2 pages if total > 10). Infer title from first heading or use slug.

**Tags/note branch:** after reading any raw source, propagate `tags` to `wiki/sources/<slug>.md` frontmatter. Treat `note` as a focus directive: the source summary must address the note topic explicitly.

---

## Section 4: New Operations

### PROMOTE (`/promote`)

Promotes insights from a saved conversation into wiki pages. Makes the conversation a first-class citable source via a `wiki/sources/conv-<slug>.md` entry.

Arguments: `/promote [conversation-slug] [target-page]`. Both optional.

Protocol:
1. Read conversation file (most recent if no slug given).
2. Identify substantive synthesis claims not already in the target page.
3. Present candidate claims to user one by one — no writes without per-claim confirmation.
4. For each confirmed claim: append to `wiki/pages/<target>.md` citing `[[wiki/sources/conv-<slug>]]`.
5. Create `wiki/sources/conv-<slug>.md` with `type: source`, `source_path: conversations/<slug>.md`, one-line summary of what was promoted.
6. Add `promoted_to` list to conversation frontmatter with target pages and date.
7. Update `index.md` and `log.md`.

Not available in unattended mode.

CLAUDE.md Frontmatter section is extended to document `conversations/<slug>.md` as a valid `source_path` prefix for conversation-derived sources.

### REFRESH (`/refresh`)

Re-fetches a source whose content has changed and re-ingests it without losing the citation graph.

Arguments: `/refresh <source>` — slug, wiki path, raw path, or URL (same forms as `/forget`).

Protocol:
1. Resolve slug; read `source_url` from `wiki/sources/<slug>.md`.
2. Add URL back to `inbox.md` as unchecked entry under "To process".
3. Instruct user to run the fetcher — it overwrites the raw folder.
4. Re-ingest: rewrite `wiki/sources/<slug>.md` with updated summary; bump `updated` date.
5. Scan `wiki/pages/` citing this source; add `needs-review` to the `tags` list in the frontmatter of any page that contains claims citing this source — not inline annotation, not a comment, a frontmatter tag the linter and the user can query.
6. Append to `log.md`: `## [YYYY-MM-DD] refresh | <slug>`.

Step 5 flags only — no automatic prose rewriting.

Both operations are registered in CLAUDE.md as operations #8 (PROMOTE) and #9 (REFRESH). The "Seven operations" heading becomes "Nine operations".

---

## Section 5: Polish

### Concept-map text fallback

`skills/view-builder/templates/view-concept-map.md` gains a `<details>` block immediately after the Mermaid diagram:

```markdown
<details>
<summary>Text fallback</summary>

- Node A → Node B
- Node A → Node C

</details>
```

Renders as collapsible in Obsidian/GitHub; degrades to visible plain text elsewhere. The view-builder SKILL.md gains a rule: both Mermaid block and adjacency list must be populated from the same data — same nodes, same edges.

### Skill manifest + dispatch table

All three SKILL.md files gain `provides`, `config_section`, and `requires` frontmatter fields (see Architectural Approach above). `init-vault.sh` dependency check is updated to read `requires.packages` from installed skill manifests via `grep`/`sed`, replacing the hardcoded package list.

CLAUDE.md gains a "## Skill dispatch" table section (see Architectural Approach above).

---

## Invariants — unchanged

All six vault invariants from CLAUDE.md remain intact:

1. Never write to `raw/` (except user-directed deletion via FORGET).
2. Every claim cites a source — extended to include `[[wiki/sources/conv-<slug>]]` for promoted conversations.
3. Paraphrase, don't copy.
4. User curates, agent maintains.
5. Touch ≤15 files per operation.
6. Update `index.md` and `log.md` after any writing operation.

---

## Backlog task summary

| Milestone | Tasks | Description |
|-----------|-------|-------------|
| foundation | TASK-0001–0005 | vault.config.yml, vault_state.py, script migration |
| bug-fixes | TASK-0006–0007 | /lint command, based_on dead links |
| features | TASK-0008–0020 | PDF, tags, promote, refresh, concept-map, manifests |

Dependency waves:
- **Wave 1 (sequential):** TASK-0001 → TASK-0002 → TASK-0003 → TASK-0004 + TASK-0005 (parallel)
- **Wave 2 (parallelizable):** TASK-0006–0016 once Wave 1 is done
- **Wave 3 (independent):** TASK-0017–0020 at any time
