# Vault Hardening, Semantic REVIEW, and MERGE — Design Spec
**Date:** 2026-05-29
**Branch:** feat-hotfix → feat-review → feat-merge (one branch per phase)
**Status:** draft

---

## 1. Problem

A deep-dive audit (session 2026-05-29) against Karpathy's LLM-Wiki idea
(https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) revealed three
independent gaps:

1. **Correctness & honesty** — 11 confirmed defects/inconsistencies ranging from
   one high-severity bug that breaks `/ingest` in every deployed vault, to
   doc-vs-code drift that erodes CLAUDE.md as the authoritative contract.
2. **Missing Karpathy-core capability** — Karpathy names *contradiction* detection as
   a core lint target. Every other target he lists is covered (`stale_sources`,
   `orphans`, `missing_cross_references`, `gaps`). Contradictions are excluded by
   the deterministic-only LINT rule, which is the right rule — but leaves a semantic
   health pass with no home in the architecture.
3. **Unclosed loop** — `check_duplicates` flags near-duplicate pages; nothing
   resolves them. FORGET cascade-removes sources; nothing merges/reconciles the
   pages they informed.

---

## 2. Goals

- Ship a vault engine where every documented behavior matches code and every CLAUDE.md
  rule is mechanically enforceable.
- Introduce `/review`: an LLM-judgment health pass (contradictions,
  claim↔source faithfulness, summary quality) that preserves LINT's deterministic
  guarantee by living in a separate operation.
- Introduce `/merge`: closes the duplicate-resolution loop the linter opens, and
  serves as the natural sink for REVIEW contradiction findings.

---

## 3. Non-goals

- Adding a graph/backlink view (Obsidian already provides this; low marginal value).
- Building a standing cross-source synthesis operation (overlaps `/view`; deferred).
- Re-implementing hooks infrastructure (vestigial claim removed; optional upgrade
  noted in §4.10 but not implemented).

---

## 4. Phase 1 — Correctness & Honesty

### 4.1 Fix `/ingest` path bug (HIGH SEVERITY)

`commands/ingest.md:23` calls `adopt_drop.py` with bare `skills/...` path; in a
deployed vault scripts live under `.claude/skills/...` so the call fails silently.
Same in `skills/inbox-fetcher/SKILL.md:164-166`.

**Change:** replace every `skills/inbox-fetcher/scripts/adopt_drop.py` invocation
in command/skill files with `.claude/skills/inbox-fetcher/scripts/adopt_drop.py`.

Files: `commands/ingest.md`, `skills/inbox-fetcher/SKILL.md`.

### 4.2 Fix `/forget` missing local-source branch

`commands/forget.md` step 5 deletes `raw/web/<slug>/` and `raw/papers/<slug>/` but
omits `raw/local/<slug>/` — the raw folder added when copy-paste PDF/MD ingestion
was introduced. Local sources leave orphaned raw folders after `/forget`.

**Change:** add `raw/local/<slug>/` to the deletion step, alongside the existing
`raw/web/` and `raw/papers/` branches. Mirror the authoritative text in
`CLAUDE.md` FORGET step 5 (lines 160-163).

Files: `commands/forget.md`.

### 4.3 Enforce `max_pdf_mb` in `fetch_inbox.py`

`fetch_inbox.py` reads `max_pdf_mb` from config and prints a warning if the
`Content-Length` header exceeds the limit — but then downloads in full anyway
(line 188). When the `Content-Length` header is absent, `size = 0` and the check
is silently skipped.

**Change:**
- After the size check, `return FetchResult(success=False, reason=f"PDF too large
  ({size_mb:.1f} MB > {max_mb} MB limit)")` instead of continuing.
- When `Content-Length` is absent: download in a streaming loop, abort and clean up
  if the accumulated byte count exceeds the limit.

Tests: add two cases — oversized with header, oversized discovered mid-stream.

Files: `skills/inbox-fetcher/scripts/fetch_inbox.py`, `tests/test_fetch_inbox.py`.

### 4.4 Honour `inbox.tags_propagation` config flag

`fetch_inbox.py` always propagates `tags`/`note` from inbox sub-bullets into
`raw/` frontmatter. The `inbox.tags_propagation` config key (present since the
first design doc) is read but never checked.

**Change:** wrap the propagation block in:
```python
if config.get("inbox", {}).get("tags_propagation", True):
```
so operators can disable it. Default `True` preserves current behavior.

Tests: add a case with `tags_propagation: false` in config; confirm tags absent.

Files: `skills/inbox-fetcher/scripts/fetch_inbox.py`, `tests/test_fetch_inbox.py`.

### 4.5 Fix stale flat-PDF documentation

`fetch_inbox.py` module docstring (line 12) and `skills/inbox-fetcher/SKILL.md:93`
both say PDFs are written to `raw/papers/<slug>.pdf` (flat file). Since the
copy-paste-PDF phase the fetcher actually writes a folder: `raw/papers/<slug>/paper.pdf`
+ `index.md`. The linter's `check_pdf_index` flags the flat layout as legacy.

**Change:** update the docstring and SKILL.md prose to reflect the current folder
layout (`raw/papers/<slug>/` with `paper.pdf` + `index.md`).

Files: `skills/inbox-fetcher/scripts/fetch_inbox.py`, `skills/inbox-fetcher/SKILL.md`.

### 4.6 Graceful degradation in `lint.py`

A single failing check function (uncaught exception) aborts the entire lint run
with exit 2. One edge-case in one check kills the whole health report.

**Change:** wrap each check invocation in the `all_checks` loop (line ~805) in a
try/except; on exception, append an `advisory` finding with message
`"check crashed: <check_name>: <exc>"` and continue. Exit 2 only when no checks
completed at all.

Tests: inject a mock check that raises; assert overall run exits 1 (not 2) and
contains the crash advisory.

Files: `skills/vault-linter/scripts/lint.py`, `tests/test_lint.py`.

### 4.7 Cross-filesystem robustness in `adopt_drop.py`

`adopt_drop.py` moves adopted files with `Path.rename()` (line 147). On Windows,
`rename()` fails when source and destination are on different volumes; on Linux it
raises `OSError: [Errno 18] Invalid cross-device link`.

**Change:** replace `src.rename(dst)` with a `shutil.move(str(src), str(dst))`
wrapper; add a docstring comment explaining why shutil is needed rather than
`Path.rename`.

Tests: mock a cross-device `rename()` failure; assert `shutil.move` is called as
fallback and adoption succeeds.

Files: `skills/inbox-fetcher/scripts/adopt_drop.py`, `tests/test_adopt_drop.py`.

### 4.8 Collapse `init-vault.sh` to a thin shim

`init-vault.sh` is a full bootstrapper that is missing `adopt_drop.py`, missing
`raw/local` and `raw/drop` directory creation, and has stale text. The Python
bootstrapper (`init_vault.py`) is the maintained path. Rather than re-synchronising
two parallel implementations, reduce the bash script to a shim that delegates to
`init_vault.py`, killing the source of the drift permanently.

**Change:** replace `init-vault.sh` body with:
```bash
#!/usr/bin/env bash
# Thin shim — delegates to the canonical Python bootstrapper.
# Kept for users who reach for a .sh script by habit or convention.
python3 init_vault.py "$@"
```
Add a one-line comment explaining why this is a shim, not the implementation.

Files: `init-vault.sh`.

### 4.9 Reconcile `CLAUDE.md` doc drift

Several CLAUDE.md inconsistencies accumulate after prior phases:

| Issue | Fix |
|---|---|
| Dispatch table lists 8 rows; header says "Nine operations"; FORGET missing | Add FORGET row: `FORGET \| (LLM only) \| —` |
| Line 33 promises "hooks" under `.claude/`; none exist anywhere | Remove; replace with "Settings" or drop the sub-item |
| Session-start step 3 checks `compass.md` age against `lint.reflect_reminder_days` (consumed by LLM) — accurate but should be explicit | No change needed; already correct |

Files: `CLAUDE.md`.

### 4.10 Fix check-count in vault-linter SKILL.md

`skills/vault-linter/SKILL.md` says "15 deterministic checks"; `lint.py` has 14
(`all_checks` list, verified against function definitions). One-line fix.

Optional upgrade (not implemented in this phase): add a real `PreToolUse` hook in
`.claude/settings.json` that blocks any `Write`/`Edit` tool call whose path starts
with `raw/`, enforcing Invariant #1 mechanically instead of by instruction alone.
Noting here so it can be a standalone future task.

Files: `skills/vault-linter/SKILL.md`.

### 4.11 Fix SKILL.md adopt_drop.py path

Same root cause as 4.1 but in documentation rather than a live command invocation.

Files: `skills/inbox-fetcher/SKILL.md` (lines 164-166 example invocations).

---

## 5. Phase 2 — `/review` (semantic, report-only)

### 5.1 Architecture decision

| Decision | Choice | Rationale |
|---|---|---|
| Location | Separate `/review` operation, not part of LINT | Keeps LINT's deterministic guarantee; matches the det-vs-LLM split in the dispatch table |
| Output | `.review/report.md` + `.review/state.yaml` | Mirrors `.lint/` pattern; distinct namespace, distinct cost model |
| Execution model | Report-only; proposes fixes, never applies | Unattended-safe; matches REFLECT/LINT posture |
| Cost control | Scope to pages with `updated` newer than `last_review`; `/review <topic\|tag>` for cluster scope | Bounds tokens without a lossy heuristic; no O(n²) pairwise scan |
| Unattended | CAN run (reads + writes report); CANNOT apply any fix | No structural changes; pure observation |

### 5.2 Three checks

**Check A — Contradictions.** For each pair of pages that both mention the same
named entity (person, organisation, date, version number): surface any claims where
the two pages make mutually inconsistent statements. Report as: entity, page A
claim + source citation, page B claim + source citation, proposed resolution.

**Check B — Claim↔source faithfulness.** For sampled wiki pages (default: up to
10 pages per run; configurable via `review.max_faithfulness_pages` in
`vault.config.yml`): for each claim that cites a `raw/` source, verify the cited
source actually supports the claim. Flag cases where the paraphrase has drifted,
the citation points to the wrong source, or the claim has no traceable support in
the source. Enforces Invariants #2 (every claim cites a source) and #3
(paraphrase, don't copy) from the read side.

**Check C — Summary quality.** Flag summaries that are thin (< ~3 substantive
sentences), appear to copy source text verbatim (violating Invariant #3), or lack
any cross-links to other wiki pages. Advisory only; the linter's
`missing_cross_references` check is the deterministic complement.

### 5.3 `commands/review.md` protocol

```
1. Read `.review/state.yaml` to determine `last_review` date and prior scope.
2. Determine scope:
   - Default: all pages with `updated` > `last_review` (or all pages if no prior run).
   - Explicit: `/review <topic|tag>` → pages matching that tag or linking to that topic page.
   - Full: `/review --all` → entire wiki (expensive; ask user to confirm).
3. Run Check A (contradictions) across scoped pages.
4. Run Check B (faithfulness) — sample up to N pages from scope (configurable).
5. Run Check C (quality) across scoped pages.
6. Write `.review/report.md` with findings grouped by check.
   Each finding: severity (blocking/advisory), pages involved, claim text,
   source citation, proposed action (never auto-applied).
7. Update `.review/state.yaml`: `last_review`, `scope`, `findings_count`.
8. Update `wiki/log.md` (Invariant #6).
9. Suggest next actions:
   - Contradictions → "consider /merge or manual reconciliation"
   - Faithfulness failures → "consider /refresh <source> or editing the claim"
   - Quality → "consider expanding the summary"
```

### 5.4 State & template files

`.review/state.yaml` schema:
```yaml
last_review: YYYY-MM-DD
scope: changed|tag:<tag>|all
findings_count: 0
last_exit_code: 0   # 0 = clean, 1 = findings, 2 = error
```

`.review/report.md` header template:
```markdown
# Review Report — YYYY-MM-DD
Scope: <scope description>
Pages reviewed: N

## Contradictions
...

## Claim↔Source Faithfulness
...

## Summary Quality
...
```

### 5.5 CLAUDE.md additions

- New **REVIEW** section under "Nine operations" (now "Ten operations").
- Dispatch table row: `REVIEW | (LLM only) | —`
- Unattended mode "CAN" list: add `run REVIEW, update .review/report.md`.
- Session-start: no auto-trigger for REVIEW (unlike LINT — semantic cost is
  opt-in by design).

### 5.6 `init_vault.py` additions

- Add `review.md` to `COMMANDS` list.
- Create `.review/` dir with `.gitkeep` during bootstrap.
- Add `.review/state.yaml` stub (same pattern as `.lint/state.yaml`).
- Add `.review/` to `.gitignore` template.

### 5.7 Optional: scope helper script

A lightweight stdlib-only script (`skills/shared/review_scope.py`) that reads
wiki frontmatter `updated` fields and returns pages modified since a given date.
Reuses `parse_frontmatter` from `lint.py`. Kept optional — the LLM can determine
scope without it, but having it makes the operation consistent and testable.

---

## 6. Phase 3 — `/merge`

### 6.1 Architecture decision

| Decision | Choice | Rationale |
|---|---|---|
| New operation vs. extend `/forget` | New MERGE operation | Different semantics: FORGET removes, MERGE reconciles; separate commands keep protocols clean |
| Backlink rewriting | Dedicated helper script (`find_backlinks.py`) | Reuses `lint.py`'s `normalize_link_target`; testable in isolation; MERGE command invokes it |
| Fanout guard | ≤15 files (same as FORGET, same as Invariant #5) | Consistent with the rest of the engine |
| SPLIT | Covered in same `merge.md` command (inverse operation) | Same backlink logic; avoids a fourth command |
| Unattended | NOT available (structural: deletes pages, rewrites links) | Matches the engine's "structural changes require interactive confirmation" rule |

### 6.2 `commands/merge.md` protocol (MERGE)

```
1. Identify: user provides page-A (to be merged away) and page-B (canonical target).
   If invoked from a REVIEW contradiction finding, both pages are pre-populated.
2. Read both pages. Show a diff-style summary of overlapping and unique content.
3. Ask user to confirm: merge direction, which content to keep from each, final title.
4. Check backlink fanout: run find_backlinks.py against page-A.
   If > 15 files, report the list and stop — require user to pick a subset or proceed
   across multiple passes.
5. Draft the merged page content. Show it to the user; ask for approval.
6. Write the merged page to page-B (or a new slug if title changed).
7. Rewrite all backlinks to page-A → page-B using find_backlinks.py output.
8. Delete page-A.
9. Update wiki/index.md: remove page-A entry, update or add page-B entry.
10. Append to wiki/log.md.
11. Propose running lint to confirm zero dead links.
```

**SPLIT protocol (inverse):**
```
1. User provides the page to split and names the two new target pages.
2. Show page content; user marks which sections go to which target.
3. Write two new pages with the assigned content.
4. Rewrite backlinks: links to the original → link to whichever new page
   inherited the relevant section (ask per-link if ambiguous).
5. Delete the original page.
6. Update wiki/index.md and wiki/log.md.
```

### 6.3 `find_backlinks.py` helper

Small stdlib-only script (mirrors `lint.py`'s design philosophy).

```python
# find_backlinks.py <vault_root> <target_page_path>
# Prints all wiki files that link to target_page_path.
# Reuses normalize_link_target() logic from lint.py.
# Exit 0: found (list to stdout), 1: none found, 2: error.
```

Install location: `skills/shared/find_backlinks.py` (alongside `vault_state.py`).
Referenced by `commands/merge.md` as `.claude/skills/shared/find_backlinks.py`.

Tests: build a small wiki fixture with known link graph; assert correct backlink
lists for several targets; test fanout count.

### 6.4 CLAUDE.md additions

- New **MERGE** section under operations (now "Eleven operations").
- Dispatch table row: `MERGE | (LLM only) | find_backlinks.py`
- Explicitly NOT available unattended.

### 6.5 `init_vault.py` additions

- Add `merge.md` to `COMMANDS` list.
- Install `find_backlinks.py` alongside other shared scripts.

---

## 7. Design Decisions Summary

| Decision | Choice |
|---|---|
| Semantic checks location | Separate `/review` operation (not merged into LINT) |
| Cost control for REVIEW | Scope-based (changed pages / tag filter), not heuristic candidate-narrowing |
| REVIEW posture | Report-only, unattended-safe |
| New operation for duplicate resolution | MERGE (closes check_duplicates loop) |
| `init-vault.sh` | Collapsed to thin shim; no re-sync |
| Hooks claim | Removed from CLAUDE.md; optional hook upgrade noted but not built |
| Operation count after all phases | 11 (9 existing + REVIEW + MERGE) |

---

## 8. Verification

### Phase 1
- `pytest tests/` green (existing ~100 tests + new for 4.3, 4.4, 4.6, 4.7).
- `python init_vault.py <tmp>` and `./init-vault.sh <tmp>` produce identical vault
  structure including `adopt_drop.py`, `raw/local/`, `raw/drop/`.
- Drop a PDF into `raw/drop/` and run `/ingest` against a fresh vault; confirm no
  path-not-found error (validates 4.1).
- Force one lint check to throw (mock); confirm exit 1 with crash advisory, not exit 2.
- Grep CLAUDE.md for "hooks" → zero matches; grep dispatch table for "FORGET" → one match.
- Grep SKILL.md for "15" → zero matches near the check-count sentence.

### Phase 2
- Seed a test vault with: two pages making conflicting date claims about the same
  org; one page with a claim citing a source that doesn't support it.
- Run `/review`; confirm `.review/report.md` flags both; confirm no auto-changes.
- Run `/review tag:ai`; confirm only tagged pages are reviewed.
- Run in unattended mode; confirm report is written and nothing in `wiki/` is modified.

### Phase 3
- Seed two near-duplicate pages with 5 inbound links each.
- Run `/merge`; confirm one canonical page remains, all 10 backlinks rewritten,
  `wiki/index.md` updated, `lint.py` reports zero dead links.
- Create a fixture with 20 inbound links; confirm fanout guard halts and reports.
- Confirm a `shareable: true` view whose `based_on` includes one merged page is
  left untouched with a warning.
