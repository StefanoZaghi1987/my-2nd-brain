# Vault Semantic REVIEW Operation — Implementation Plan (Phase 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/review` — a report-only LLM-judgment health pass that covers contradictions, claim↔source faithfulness, and summary quality; the semantic counterpart to the deterministic LINT operation.

**Architecture:** Four deliverables: (1) `commands/review.md` defining the 9-step protocol and three checks; (2) `CLAUDE.md` additions registering REVIEW as the tenth operation; (3) `init_vault.py` bootstrapping `.review/` state directory and registering the command; (4) an optional `skills/shared/review_scope.py` stdlib helper for efficient changed-page scoping. REVIEW is LLM-only (no Python execution path) — its only testable artifact is the scope helper.

**Tech Stack:** Markdown (commands/review.md, CLAUDE.md); Python 3.10+ stdlib (review_scope.py, init_vault.py); pytest. No new pip dependencies.

**Backlog milestone:** m-1 — tasks task-0072 through task-0075.

**Prerequisite:** Phase 1 plan (`2026-05-29-vault-hardening-plan.md`) should be complete so that CLAUDE.md already has 9 operations and no hooks claim before Phase 2 adds the 10th.

---

## File Map

| File | Action | Task(s) |
|---|---|---|
| `commands/review.md` | Create: 9-step protocol, 3 checks, scoping rules, output schema | Task 1 |
| `CLAUDE.md` | Modify: add REVIEW section + dispatch row + unattended CAN + no-auto-trigger note | Task 2 |
| `init_vault.py` | Modify: add `review.md` to COMMANDS; create `.review/` dir + state stub; update .gitignore template | Task 3 |
| `skills/shared/review_scope.py` | Create: stdlib-only scope helper (optional but recommended) | Task 4 |
| `tests/test_review_scope.py` | Create: 3 test cases for the scope helper | Task 4 |

---

## Task 1 — Author commands/review.md (task-0072)

The REVIEW command protocol. This is a Markdown file that instructs the LLM how to run a semantic health pass. It is the most important deliverable of Phase 2.

**Files:** Create `commands/review.md`

- [ ] **Step 1: Examine an existing command for format reference**

  Open `commands/reflect.md` — it is another LLM-only, report-writing operation and is the closest structural analog. Note the frontmatter schema, section headings, and step numbering style.

- [ ] **Step 2: Create commands/review.md**

  Create `commands/review.md` with this exact content:

  ```markdown
  ---
  description: Semantic health pass over the vault wiki. Runs three LLM-judgment
    checks (contradictions, claim-source faithfulness, summary quality) that the
    deterministic LINT cannot cover. Report-only — proposes fixes, never applies
    them. Scoped to changed pages by default to keep token cost bounded.
  ---

  # /review — Semantic health pass

  Run when you want to catch contradictions between pages, verify that wiki
  claims actually trace to their cited sources, or surface thin/copied summaries.
  This is the LLM-judgment counterpart to the deterministic `/lint`.

  ## When to use

  - After ingesting several new sources that touch overlapping topics.
  - When a `/lint` run surfaces near-duplicate pages (`check_duplicates`) and
    you want to check whether they actually contradict each other.
  - Periodically on a slow-growing vault, or whenever you suspect paraphrase
    drift has crept in.
  - `/review --all` for a full sweep (expensive — confirm with the user first).

  ## Scoping

  | Invocation | Scope |
  |---|---|
  | `/review` (default) | Pages with `updated` newer than `last_review` in `.review/state.yaml`. If no prior run, covers all pages. |
  | `/review <topic-or-tag>` | Pages matching that tag, or pages that link to the named topic page. |
  | `/review --all` | All wiki pages. Expensive — ask the user to confirm before starting. |

  ## Three checks

  ### Check A — Contradictions

  For each pair of pages in scope that both mention the same named entity
  (person, organisation, project, date, version number):

  - Read the relevant claim in each page.
  - If the two claims are mutually inconsistent (e.g. different founding years,
    conflicting capability descriptions, opposing conclusions), record a finding.
  - **Finding format:**
    ```
    Entity: <name>
    Page A: wiki/pages/foo.md — "<claim text>" (cites: raw/web/foo-slug/)
    Page B: wiki/pages/bar.md — "<claim text>" (cites: raw/papers/bar-slug/)
    Proposed resolution: <one-sentence suggestion, e.g. "check source X — it
    was published later and supersedes the earlier claim">
    ```

  ### Check B — Claim↔source faithfulness

  For a sample of pages from the scope (up to `review.max_faithfulness_pages`
  pages, default 10; configurable in `vault.config.yml`):

  - For each claim that cites a `raw/` source via a `[[wiki/sources/...]]` link
    or a direct `raw/` path:
    - Read the cited source.
    - Verify the claim is a faithful paraphrase of what the source says.
  - Flag cases where:
    - The paraphrase has drifted and no longer reflects the source.
    - The citation points to a source that doesn't mention the claim.
    - A claim appears to have no traceable support at all (Invariant #2 breach).
  - **Finding format:**
    ```
    Page: wiki/pages/foo.md
    Claim: "<claim text>"
    Cited source: raw/web/foo-slug/
    Issue: <paraphrase drift | wrong citation | unsupported claim>
    Proposed action: <edit the claim | re-read the source | add a citation>
    ```

  ### Check C — Summary quality

  For all pages in scope, flag summaries that are:
  - **Thin**: fewer than ~3 substantive sentences of actual content.
  - **Copied**: appear to reproduce source text verbatim (violates Invariant #3).
  - **Unlinked**: contain no `[[wikilink]]` cross-references to other pages
    (the deterministic linter's `missing_cross_references` check is the
    cheaper complement; this check catches cases it misses).
  - **Finding format:** advisory; list the page, the issue, and a suggestion.

  ## Protocol

  1. Read `.review/state.yaml` to determine `last_review` date and prior scope.
     If the file is absent or `last_review` is null, treat this as the first run.
  2. Determine scope (see Scoping table above). For `/review --all`, ask the user
     to confirm before proceeding — state the approximate page count.
  3. Run Check A (contradictions) across all scoped page pairs that share named
     entities. Avoid O(n²) full cross-product: focus on entity clusters (pages
     sharing the same tag or linking to the same entity page).
  4. Run Check B (faithfulness) on a sample of up to `max_faithfulness_pages`
     pages from the scope, prioritising pages updated most recently.
  5. Run Check C (summary quality) across all scoped pages.
  6. Write `.review/report.md` with findings grouped by check:
     ```markdown
     # Review Report — YYYY-MM-DD
     Scope: <scope description>
     Pages reviewed: N

     ## Contradictions
     (findings or "None found.")

     ## Claim↔Source Faithfulness
     Sampled: N pages
     (findings or "None found.")

     ## Summary Quality
     (findings or "None found.")
     ```
     Each finding includes severity (blocking / advisory), pages involved,
     claim text, source citation, and proposed action. **Never auto-apply.**
  7. Update `.review/state.yaml`:
     ```yaml
     last_review: YYYY-MM-DD
     scope: changed|tag:<tag>|topic:<slug>|all
     findings_count: N
     last_exit_code: 0   # 0 = clean, 1 = findings, 2 = error
     ```
  8. Append to `wiki/log.md` (Invariant #6):
     `## [YYYY-MM-DD] review | scope: <scope> | findings: N`
  9. Suggest next actions based on findings:
     - Contradictions → "consider `/merge` to reconcile, or edit the claims manually"
     - Faithfulness failures → "consider `/refresh <source>` or editing the claim"
     - Summary quality → "consider expanding the summary or adding cross-links"

  ## Unattended mode

  `/review` **is available unattended**: it reads pages and sources, writes
  `.review/report.md` and `.review/state.yaml`, and updates `wiki/log.md`.
  It never modifies `wiki/pages/`, `wiki/sources/`, or any other structural file.

  ## Output files

  - `.review/report.md` — findings report (human-readable)
  - `.review/state.yaml` — last-run metadata for scoping future runs
  - `wiki/log.md` — append-only log entry (Invariant #6)
  ```

- [ ] **Step 3: Verify the file was created correctly**

  ```bash
  head -5 commands/review.md
  grep -c "###" commands/review.md
  ```
  Expected: frontmatter starts with `---`, three `###` sections (Checks A, B, C).

- [ ] **Step 4: Commit**

  ```bash
  git add commands/review.md
  git commit -m "feat(review): add /review command — semantic health pass (contradictions, faithfulness, quality)"
  ```

---

## Task 2 — Add REVIEW operation to CLAUDE.md (task-0073)

Register REVIEW as the tenth operation in the authoritative contract.

**Files:** Modify `CLAUDE.md`

**Prerequisite:** Phase 1 Task 8 must be done (CLAUDE.md already has 9 operations in the dispatch table; no hooks claim).

- [ ] **Step 1: Add the REVIEW section to the operations list**

  In `CLAUDE.md`, find the REFLECT operation section. After it, insert a new REVIEW section:

  ```markdown
  ### REVIEW
  User says "review the vault", "check for contradictions", "review my sources",
  or runs `/review [scope]` → run the semantic health pass. Three checks:
  contradictions (pages making conflicting claims about the same entity),
  claim↔source faithfulness (wiki claims traceable to their cited raw/ sources),
  and summary quality (thin, copied, or unlinked summaries). Report-only —
  proposes fixes, never applies them. See `commands/review.md` for the full
  protocol with scoping options and output format.

  Cost note: Check B reads source files and should be scoped to avoid excessive
  token spend. Default scope covers only pages changed since the last review.
  `/review --all` is available but requires user confirmation.
  ```

- [ ] **Step 2: Add REVIEW to the dispatch table**

  Find the dispatch table. Currently ends with:
  ```markdown
  | FORGET    | (LLM only)     | —                              |
  ```
  (After Phase 1 Task 8. If that task isn't done yet, the table ends with REFRESH.)

  Add after FORGET:
  ```markdown
  | REVIEW    | (LLM only)     | —                              |
  ```

  Update the section heading from "Nine operations" to "Ten operations" (or from the current count to +1).

- [ ] **Step 3: Update the unattended mode CAN list**

  Find the unattended mode section. In the "You CAN" list, add:
  ```
  run REVIEW, update .review/report.md and .review/state.yaml
  ```

- [ ] **Step 4: Add a no-auto-trigger note**

  Either in the REVIEW section or in the Session start section, add:
  ```
  REVIEW has no auto-trigger. Unlike LINT, it consumes LLM tokens and must
  be invoked explicitly. There is no `fetches_since_last_review` counter.
  ```

- [ ] **Step 5: Verify operation count is consistent**

  ```bash
  grep -n "Ten operations\|Nine operations" CLAUDE.md
  grep -c "^| [A-Z]" CLAUDE.md
  ```
  Expected: heading says "Ten operations"; table has 10 data rows.

- [ ] **Step 6: Commit**

  ```bash
  git add CLAUDE.md
  git commit -m "feat(review): register REVIEW as the tenth operation in CLAUDE.md"
  ```

---

## Task 3 — Bootstrap .review/ in init_vault.py; register command (task-0074)

Every vault bootstrapped after this change should have the `.review/` directory and `review.md` command pre-installed.

**Files:** Modify `init_vault.py`

- [ ] **Step 1: Locate the COMMANDS list**

  Open `init_vault.py`. Find the `COMMANDS` list (around line 86-89). It looks like:
  ```python
  COMMANDS = [
      "save", "view", "reflect", "forget", "lint", "promote",
      "refresh", "ingest", "fetch", "hot", "playwright-fetch",
  ]
  ```

- [ ] **Step 2: Add review.md to COMMANDS**

  ```python
  COMMANDS = [
      "save", "view", "reflect", "forget", "lint", "promote",
      "refresh", "ingest", "fetch", "hot", "playwright-fetch", "review",
  ]
  ```

- [ ] **Step 3: Add .review/ directory creation**

  Find the `DIRS` list (around lines 63-79) where vault directories are created. Add:
  ```python
  vault / ".review",
  ```
  alongside `.lint/`.

- [ ] **Step 4: Add .review/state.yaml stub**

  Find where `.lint/state.yaml` is written. In `init_vault.py` there is a `_LINT_STATE`
  constant (around line 155) and a call `_write_if_absent(vault / ".lint" / "state.yaml",
  _LINT_STATE, ".lint/state.yaml")` (line ~222). Add a parallel constant and call:

  ```python
  _REVIEW_STATE = """\
  last_review: null
  scope: null           # changed | tag:<tag> | topic:<slug> | all
  findings_count: 0
  last_exit_code: 0     # 0 = clean, 1 = findings, 2 = error
  """
  ```

  In `write_base_files()` (around line 218), after the `.lint/` lines, add:
  ```python
  _write_if_absent(vault / ".review" / "state.yaml", _REVIEW_STATE, ".review/state.yaml")
  ```
  Note: the function is `_write_if_absent` (with leading underscore), not `write_if_absent`.

- [ ] **Step 5: Add .review/ to .gitignore template**

  Find the `_GITIGNORE` constant in `init_vault.py` (around line 169). The current
  template does NOT include `.lint/` — append `.review/` at the end:
  ```
  # Vault runtime output (do not commit lint/review reports)
  .lint/
  .review/
  ```
  Add these lines before the closing `"""` of `_GITIGNORE`.

- [ ] **Step 6: Smoke-test bootstrap**

  ```bash
  python init_vault.py /tmp/vault-review-test
  ls /tmp/vault-review-test/.review/
  ls /tmp/vault-review-test/.claude/commands/ | grep review
  cat /tmp/vault-review-test/.review/state.yaml
  ```
  Expected: `.review/state.yaml` present with four commented fields; `review.md` present in `.claude/commands/`.

- [ ] **Step 7: Run existing bootstrap tests**

  ```bash
  pytest tests/ -v -k "vault" 2>&1 | tail -20
  ```
  Expected: all pass.

- [ ] **Step 8: Commit**

  ```bash
  git add init_vault.py
  git commit -m "feat(review): bootstrap .review/ dir + state stub; register review.md in COMMANDS"
  ```

---

## Task 4 — Add review_scope.py scope helper (task-0075)

A small stdlib-only script that enumerates pages modified since `last_review`. This makes the REVIEW command's default scoping efficient and testable — the LLM invokes it to get the scope list rather than walking frontmatter manually.

**Files:** Create `skills/shared/review_scope.py`, create `tests/test_review_scope.py`, modify `init_vault.py`

- [ ] **Step 1: Write the tests first**

  Create `tests/test_review_scope.py`:
  ```python
  """Tests for review_scope.py — page scoping for the REVIEW operation."""
  import sys
  from pathlib import Path
  from datetime import date
  import pytest

  # Adjust import path for the test runner
  sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
  from review_scope import get_changed_pages


  def _write_page(path: Path, updated: str) -> None:
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(
          f"---\ntype: page\ncreated: 2026-01-01\nupdated: {updated}\ntags: []\n---\n\nContent.\n",
          encoding="utf-8",
      )


  def test_returns_all_pages_when_no_prior_review(tmp_path):
      """With last_review=null, every wiki page is in scope."""
      wiki = tmp_path / "wiki" / "pages"
      _write_page(wiki / "page-a.md", "2026-01-01")
      _write_page(wiki / "page-b.md", "2026-03-15")

      result = get_changed_pages(tmp_path, last_review=None)
      names = {p.name for p in result}
      assert names == {"page-a.md", "page-b.md"}


  def test_filters_to_pages_newer_than_last_review(tmp_path):
      """Only pages updated after last_review are returned."""
      wiki = tmp_path / "wiki" / "pages"
      _write_page(wiki / "old.md", "2026-01-01")
      _write_page(wiki / "recent.md", "2026-05-20")

      result = get_changed_pages(tmp_path, last_review=date(2026, 3, 1))
      names = {p.name for p in result}
      assert "recent.md" in names
      assert "old.md" not in names


  def test_returns_empty_when_nothing_changed(tmp_path):
      """Returns empty list when no pages were updated after last_review."""
      wiki = tmp_path / "wiki" / "pages"
      _write_page(wiki / "stale.md", "2026-01-01")

      result = get_changed_pages(tmp_path, last_review=date(2026, 6, 1))
      assert result == []
  ```

- [ ] **Step 2: Run tests to confirm they fail**

  ```bash
  pytest tests/test_review_scope.py -v
  ```
  Expected: ImportError (module doesn't exist yet).

- [ ] **Step 3: Implement review_scope.py**

  Create `skills/shared/review_scope.py`:
  ```python
  #!/usr/bin/env python3
  """
  review_scope.py — Enumerate wiki pages modified since the last REVIEW run.

  Used by the /review command to determine the default scope: only pages
  whose frontmatter `updated` date is newer than `last_review` in
  .review/state.yaml. Reuses the same frontmatter parser logic as lint.py
  so the date comparison is consistent.

  Usage:
      python review_scope.py <vault_root> [--since YYYY-MM-DD]

  Exit codes:
      0 — pages found (list to stdout, one path per line)
      1 — no pages in scope
      2 — error (vault not found, bad date, etc.)
  """
  from __future__ import annotations
  import sys
  import re
  from pathlib import Path
  from datetime import date


  def _parse_updated(text: str) -> date | None:
      """Extract the `updated: YYYY-MM-DD` field from YAML frontmatter."""
      m = re.search(r"^updated:\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
      if not m:
          return None
      try:
          return date.fromisoformat(m.group(1))
      except ValueError:
          return None


  def get_changed_pages(vault: Path, last_review: date | None) -> list[Path]:
      """Return wiki pages updated after last_review. All pages if last_review is None."""
      pages_dir = vault / "wiki" / "pages"
      if not pages_dir.exists():
          return []

      result = []
      for page in pages_dir.rglob("*.md"):
          if page.name.startswith("."):
              continue
          if last_review is None:
              # First run — all pages are in scope
              result.append(page)
              continue
          updated = _parse_updated(page.read_text(encoding="utf-8", errors="ignore"))
          if updated is not None and updated > last_review:
              result.append(page)
      return sorted(result)


  def _read_last_review(vault: Path) -> date | None:
      """Read last_review from .review/state.yaml. Returns None if absent or null."""
      state_path = vault / ".review" / "state.yaml"
      if not state_path.exists():
          return None
      m = re.search(r"^last_review:\s*(\d{4}-\d{2}-\d{2})",
                    state_path.read_text(encoding="utf-8"), re.MULTILINE)
      if not m:
          return None
      try:
          return date.fromisoformat(m.group(1))
      except ValueError:
          return None


  def main() -> int:
      import argparse
      parser = argparse.ArgumentParser(description="List wiki pages in REVIEW scope.")
      parser.add_argument("vault", help="Vault root path")
      parser.add_argument("--since", help="Override last_review date (YYYY-MM-DD)",
                          default=None)
      args = parser.parse_args()

      vault = Path(args.vault)
      if not vault.is_dir():
          print(f"ERROR: vault not found: {vault}", file=sys.stderr)
          return 2

      if args.since:
          try:
              last_review: date | None = date.fromisoformat(args.since)
          except ValueError:
              print(f"ERROR: invalid date format: {args.since}", file=sys.stderr)
              return 2
      else:
          last_review = _read_last_review(vault)

      pages = get_changed_pages(vault, last_review)
      if not pages:
          return 1
      for p in pages:
          print(p)
      return 0


  if __name__ == "__main__":
      sys.exit(main())
  ```

- [ ] **Step 4: Run tests to confirm they pass**

  ```bash
  pytest tests/test_review_scope.py -v
  ```
  Expected: all 3 tests pass.

- [ ] **Step 5: Add to init_vault.py shared scripts install**

  Open `init_vault.py`. Find the section that installs shared scripts (where `vault_state.py` is copied into `.claude/skills/shared/`). Add `review_scope.py` to the same list.

- [ ] **Step 6: Verify install**

  ```bash
  python init_vault.py /tmp/vault-scope-test
  ls /tmp/vault-scope-test/.claude/skills/shared/
  ```
  Expected: `review_scope.py` present alongside `vault_state.py`.

- [ ] **Step 7: Run all tests**

  ```bash
  pytest tests/ -v
  ```
  Expected: all pass.

- [ ] **Step 8: Commit**

  ```bash
  git add skills/shared/review_scope.py tests/test_review_scope.py init_vault.py
  git commit -m "feat(review): add review_scope.py — stdlib helper for efficient changed-page scoping"
  ```

---

## Final verification (Phase 2)

- [ ] All tests pass:
  ```bash
  pytest tests/ -v
  ```

- [ ] `commands/review.md` is installed by `init_vault.py`:
  ```bash
  python init_vault.py /tmp/vault-verify
  cat /tmp/vault-verify/.claude/commands/review.md | head -5
  ```
  Expected: frontmatter with REVIEW description.

- [ ] `.review/` state stub exists:
  ```bash
  cat /tmp/vault-verify/.review/state.yaml
  ```
  Expected: four fields with inline comments.

- [ ] CLAUDE.md has 10 operations in the table:
  ```bash
  grep -c "^| [A-Z]" CLAUDE.md
  ```
  Expected: 10.

- [ ] REVIEW appears in unattended CAN list:
  ```bash
  grep -A 10 "You CAN" CLAUDE.md | grep -i review
  ```
  Expected: at least one match.
