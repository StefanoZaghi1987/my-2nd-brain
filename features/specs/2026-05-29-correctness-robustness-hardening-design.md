# Correctness & Robustness Hardening — Design Spec
**Date:** 2026-05-29
**Branch:** feat-hotfix (current)
**Status:** approved

---

## 0. Repo orientation

`D:\my-2nd-brain` is the **template/engine repo** that generates second-brain vaults
via `init_vault.py`. There is no `wiki/`, `raw/`, or `inbox.md` on disk here; those
are scaffolded by bootstrap into the target directory. Key layout:

```
init_vault.py                     Cross-platform bootstrapper / installer
CLAUDE.md                         LLM operating contract for deployed vaults
commands/                         Slash command protocols (Markdown, 15 files)
skills/
  inbox-fetcher/
    scripts/fetch_inbox.py        URL queue → raw/web|papers/<slug>/
    scripts/adopt_drop.py         Drop-zone → raw/local/<slug>/
    SKILL.md
  vault-linter/
    scripts/lint.py               14 deterministic checks
    SKILL.md
  view-builder/
    templates/                    7 view-kind templates + chart.py
  shared/
    vault_state.py                Config/state I/O — shared by all scripts
    linkutil.py                   Wikilink regex + resolver
    find_backlinks.py             Backlink finder (used by /merge, /split)
    review_scope.py               REVIEW scope enumerator (intentionally standalone)
tests/                            pytest suite (~100 tests)
features/
  specs/                          Design specs (this file)
  plans/                          Implementation plans
  backlog/                        Backlog.md task & milestone files
```

**Test import pattern** (used consistently):
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "<skill>" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
from <module> import <symbol>
```

**Run tests:** `pytest tests/ -v` from the repo root.

---

## 1. Problem

A deep-dive audit (session 2026-05-29) comparing this implementation against
Karpathy's LLM Wiki idea (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
found the engine feature-complete (Phase 4 shipped) but with a cluster of **latent
correctness/robustness bugs** and **stale documentation** that have not yet been
addressed:

1. **Three divergent hand-rolled YAML parsers** with different capabilities. The
   critical consequence: writing `walled_domains` as a natural YAML block list in
   `vault.config.yml` (the format any editor would suggest) silently produces an empty
   list — disabling all walled-domain protection with no error, warning, or hint.
2. **Windows console encoding crashes** in `fetch_inbox.py` and `lint.py`: raw
   `✓`/`⚠`/`·`/`→` printed to stdout without the UTF-8 guard that `init_vault.py`
   correctly applies, producing `UnicodeEncodeError` on cp1252 Windows consoles.
3. **`review_scope._parse_updated` not scoped to frontmatter**: MULTILINE regex matches
   `updated:` anywhere in a file body, mis-dating pages that mention a date in prose.
4. **`--vault` resolution inconsistency**: `fetch_inbox.py` and `adopt_drop.py` do not
   call `.resolve()`, so relative `--vault` invocations can leak relative paths into
   `inbox.md` records.
5. **`fetch_inbox` inbox CRLF corruption**: `splitlines()` + `"\n".join` silently
   rewrites CRLF inboxes to LF on Windows. Near-miss entries (unchecked lines that
   fail the pattern for reasons other than being checked) are silently dropped.
6. **`chart.py` has no dependency guard**: bare `ImportError` if matplotlib is absent,
   unlike all other scripts which give a friendly actionable message.
7. **State null round-trip**: `vault_state.read_state`/`write_state` stringify all
   values, so `last_lint: null` round-trips as the string `"null"` not `None`,
   corrupting downstream date-diff logic on first run.
8. **Stale and contradictory documentation** in `commands/review.md`,
   `CLAUDE.md`, `skills/view-builder/SKILL.md`, and `vault.config.yml`.

---

## 2. Goals

- Eliminate all silent-failure bugs (chiefly the YAML block-list trap and the CRLF
  corruption).
- Fix all Windows-specific crashes.
- Correct stale/contradictory documentation.
- Guard every fix with tests before migrating callers.
- **Zero behavior change** for correctly-formed existing vaults.

---

## 3. Non-goals

- Adding new features or operations (no retrieval layer, no new commands).
- Adding third-party dependencies (engine stays zero-dep for core operations).
- Refactoring test infrastructure.

---

## 4. Phase 5 — Correctness & Robustness

### 4.1 New module: `skills/shared/yamlmini.py` — unified zero-dep YAML parser

**The bug:** Three divergent parsers exist. `vault_state._parse_config_yaml` handles
2-level nesting + inline lists but **not block lists**. `lint.parse_frontmatter`
handles block lists but is flat. A third family of regex field extractors lives in
`adopt_drop`. The silent-empty-list trap: `walled_domains` as a block list in config
→ empty list → all walled domains pass through.

**Change:** Create `skills/shared/yamlmini.py` exposing:
- `parse_yaml(text: str) -> dict` — superset of both existing parsers: scalar type
  coercion, inline lists `[a, b, c]`, **block lists** (`  - item`), ≥2-level nested
  mappings. Built by **composing proven code** from both existing parsers — lift the
  block-list branch from `lint.parse_frontmatter`, nesting + coercion from
  `vault_state._parse_config_yaml`. No clean-sheet implementation.
- `parse_frontmatter(text: str) -> dict` — extracts the leading `---…---` block,
  then delegates to `parse_yaml`. Returns empty dict if no frontmatter.
- Raises `ValueError` on present-but-unparseable input (matches `vault_state`'s
  existing `load_config` contract). Does not silently return empty.

**Testing gate (do first):**
- Write characterization tests in `tests/test_yamlmini.py` that assert `parse_yaml`
  reproduces the current output of BOTH old parsers across every edge-case fixture
  in `tests/test_vault_state.py` and `tests/test_lint.py` (quoted values containing
  `:`, empty lists `[]`, inline tags `[a, b]`, block tags, comments `# ...`, scalars
  of all types). Capture any fixtures not yet covered before migrating.
- After characterization tests pass, add the headline new-capability test: a config
  with `walled_domains` written as a YAML block list parses to the full list (the
  direct regression guard for the silent-disable bug).

**Callers to migrate after tests pass:**
- `vault_state._parse_config_yaml` → `parse_yaml`; `load_config` uses it.
- `lint.parse_frontmatter` → `yamlmini.parse_frontmatter`.
- `adopt_drop`'s inline field extractors → `yamlmini.parse_frontmatter` (migrate only
  if all characterization fixtures pass; otherwise defer to a follow-up task).
- `review_scope` does **not** migrate — see §4.3.

Files: `skills/shared/yamlmini.py` (new), `skills/shared/vault_state.py`,
`skills/vault-linter/scripts/lint.py`,
`skills/inbox-fetcher/scripts/adopt_drop.py`,
`tests/test_yamlmini.py` (new).

Also update `init_vault.py` `SHARED_SCRIPTS` list (L364) to install `yamlmini.py`
into every generated vault.

### 4.2 State null round-trip fix

**The bug:** `vault_state.read_state` returns all values as strings, so
`last_lint: null` in `.lint/state.yaml` comes back as the string `"null"`,
not Python `None`. Downstream code that does `if state["last_lint"] is None:` on
first-run never triggers its first-run branch.

**Change:** In `vault_state.read_state`, coerce each value through the existing
`_parse_scalar` (already handles `"null"` → `None`). In `write_state`, write `None`
values as an empty string (or omit the key), not as the string `"null"`.

Add round-trip test: `{last_lint: null}` → `write_state` → `read_state` → `None`.

Files: `skills/shared/vault_state.py`, `tests/test_vault_state.py`.

### 4.3 Windows console encoding — `ensure_utf8_stdout()`

**The bug:** `fetch_inbox.py` and `lint.py` print raw `✓`/`⚠`/`·`/`→` to stdout
without a UTF-8 guard → `UnicodeEncodeError` on cp1252 Windows consoles.
`init_vault.py` already has the fix (L24-29) but inline.

**Change:** Add `ensure_utf8_stdout()` to `skills/shared/` (as a standalone function
in a new `skills/shared/console.py` or as an addition to an existing module — TBD
during implementation, but keep it in `shared/`). Call it at module top of
`fetch_inbox.py` and `lint.py`. **Leave `init_vault.py`'s inline copy as-is** — the
bootstrapper must not import from the payload it is about to install.

Pattern to replicate (from `init_vault.py` L24-29):
```python
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                   errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8",
                                   errors="replace", line_buffering=True)
```

Files: `skills/shared/console.py` (new), `skills/inbox-fetcher/scripts/fetch_inbox.py`,
`skills/vault-linter/scripts/lint.py`. Update `init_vault.py` `SHARED_SCRIPTS`
to install `console.py`.

### 4.4 `review_scope._parse_updated` — scope to frontmatter block

**The bug:** `re.search(r"^updated:...", text, re.MULTILINE)` matches anywhere in the
file, not just in the `---…---` frontmatter block.

**Change:** In `review_scope._parse_updated`, split out the frontmatter block first
(`text.split("---", 2)`), apply the existing regex only to the frontmatter string.
**Preserve the script's intentional self-containment** — no import of `shared/`.

Test: a page with `updated: 2020-01-01` only in its body prose returns the real
frontmatter date (or `None` if the frontmatter has none), not the body date.

Files: `skills/shared/review_scope.py`, `tests/test_review_scope.py`.

### 4.5 `--vault` resolution consistency

**The bug:** `fetch_inbox.py` and `adopt_drop.py` don't `.resolve()` the `--vault`
argument, so `python fetch_inbox.py --vault .` records relative paths in `inbox.md`.
`lint.py` and `init_vault.py` already call `.resolve()`.

**Change:** In both scripts, apply `.resolve()` immediately after the `Path(args.vault)`
construction, matching `lint.py`'s pattern (L850: `vault = Path(args.vault).resolve()`).

Test: a relative `--vault .` invocation records an absolute path in `inbox.md` output.

Files: `skills/inbox-fetcher/scripts/fetch_inbox.py`,
`skills/inbox-fetcher/scripts/adopt_drop.py`, `tests/test_fetch_inbox.py`,
`tests/test_adopt_drop.py`.

### 4.6 `fetch_inbox` inbox robustness

**Two fixes, no parsing-semantics change:**

**4.6a CRLF preservation.** `update_inbox` currently uses `splitlines()` +
`"\n".join(...)`, which silently converts CRLF → LF on Windows. Fix: detect the
original line separator (`"\r\n"` if `"\r\n"` appears in the raw text, else `"\n"`),
use it as the join separator on rewrite.

**4.6b Near-miss warning.** When a line matches `- [ ] ` but `UNCHECKED_PATTERN`
fails (e.g. `- [ ] https://x.com my note`), silently skip with no signal. Fix: emit
a `⚠ skipped: line looks like an unchecked entry but URL was not alone on the line`
warning into the processed output (same style as existing warnings), not a hard error.
Do **not** change `UNCHECKED_PATTERN` itself (the one-URL-per-line contract stands).

Files: `skills/inbox-fetcher/scripts/fetch_inbox.py`, `tests/test_fetch_inbox.py`.

### 4.7 `chart.py` dependency guard

**The bug:** top-level `import matplotlib` raises a bare `ImportError` if matplotlib
is absent. All other scripts provide a friendly, actionable message.

**Change:** wrap the import in a try/except block, print the message `"chart.py
requires matplotlib. Install it with: pip install matplotlib"` and `sys.exit(1)`,
matching the guard pattern in `fetch_inbox.py` (L48-51).

File: `skills/view-builder/templates/chart.py`.

### 4.8 Documentation corrections

**4.8a `commands/review.md`:** remove the stale "`/merge` … Phase 3, not yet
available" note (~L150). `/merge` is fully implemented and ships.

**4.8b `CLAUDE.md` skill-dispatch table:** add `SPLIT → find_backlinks.py` row
(only MERGE is listed today; both operations use the same script).

**4.8c `skills/view-builder/SKILL.md`:** reconcile the "reveal HTML deck" mentions.
Only Marp (`view-slides.md`) is implemented. State the current limitation: *"Slides
use Marp format. A reveal.js template is not yet available."* Remove or annotate all
"reveal" references so they don't imply a working template.

**4.8d `vault.config.yml`:** add a comment block above `lint:`, `ingest:`, and
`fetch: walled_domains` explaining which keys are read by Python scripts vs. honored
by the LLM/command layer:
```yaml
# Keys below are read by lint.py:
lint:
  ...

# Keys below are honored by the LLM command layer, not by any script:
# (auto_trigger_after_fetches, auto_trigger_after_days, reflect_reminder_days)
```
Also add an explicit inline comment on `walled_domains` noting that block-list
syntax is now supported (after §4.1 ships).

Files: `commands/review.md`, `CLAUDE.md`, `skills/view-builder/SKILL.md`,
`vault.config.yml`.

---

## 5. Verification

1. **Tests:** `pytest tests/ -q` — all existing ~100 tests pass plus new tests pass.
   Headline assertion: `walled_domains` as a block list parses to the full list.
2. **Bootstrap smoke test:** `python init_vault.py ./tmp-vault --yes` then run
   `fetch_inbox.py --vault ./tmp-vault --dry-run` and `lint.py --vault ./tmp-vault`
   on Windows PowerShell — confirm no `UnicodeEncodeError`, unicode symbols render.
3. **Config robustness:** write `walled_domains` as a block list in the generated
   `vault.config.yml`; confirm it parses correctly (not an empty list).
4. **CRLF round-trip:** save a CRLF `inbox.md`, run fetch, confirm line endings
   preserved in output.
5. **review_scope:** a page with `updated:` in body prose only is not mis-scoped.
6. **state null:** delete `.lint/state.yaml`, run lint, confirm `last_lint` is stored
   then read back as a date, not the string `"null"`.

---

## 6. Process

- Decompose into small atomic Backlog.md tasks (one per §4.x subsection).
- Group under new milestone **Phase 5 — Correctness Hardening**.
- TDD: characterization tests written and passing **before** each caller migration.
- Spec lives at `features/specs/2026-05-29-correctness-robustness-hardening-design.md`.
- Implementation plan lives at `features/plans/2026-05-29-correctness-robustness-hardening.md`.
