# Vault MERGE Operation — Implementation Plan (Phase 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/merge` — an interactive operation that resolves near-duplicate pages (closing the loop the linter's `check_duplicates` opens) by merging two pages into one canonical page with full backlink rewriting, and a `/split` inverse.

**Architecture:** Two deliverables: (1) a stdlib-only `find_backlinks.py` helper script (the only testable artifact — MERGE itself is LLM-only) that enumerates all wiki files linking to a target page, reusing `lint.py`'s `normalize_link_target()` resolution logic; (2) `commands/merge.md` defining the MERGE and SPLIT protocols. CLAUDE.md and `init_vault.py` are updated to register the new operation.

**Tech Stack:** Python 3.10+ stdlib (find_backlinks.py, init_vault.py), pytest, Markdown. No new pip dependencies.

**Backlog milestone:** m-2 — tasks task-0076 through task-0079.

**Prerequisites:**
- Phase 1 plan (`2026-05-29-vault-hardening-plan.md`) complete — CLAUDE.md has 9 operations.
- Phase 2 plan (`2026-05-29-vault-review-plan.md`) complete — CLAUDE.md has 10 operations; MERGE will make it 11.

---

## File Map

| File | Action | Task(s) |
|---|---|---|
| `skills/shared/find_backlinks.py` | Create: stdlib-only backlink enumeration helper | Task 1 |
| `tests/test_find_backlinks.py` | Create: 5+ test cases for the helper | Task 1 |
| `commands/merge.md` | Create: MERGE (10-step) + SPLIT (6-step) protocols | Task 2 |
| `CLAUDE.md` | Modify: add MERGE section + dispatch row + unattended CANNOT note | Task 3 |
| `init_vault.py` | Modify: add `merge.md` to COMMANDS; install `find_backlinks.py` in shared | Task 4 |

---

## Task 1 — Add find_backlinks.py helper (task-0076)

The MERGE operation needs to find every `[[wikilink]]` pointing to a page before rewriting them. This helper is the only Python in Phase 3 — it must match `lint.py`'s link resolution exactly so backlinks found here are the same ones the linter tracks.

**Files:** Create `skills/shared/find_backlinks.py`, create `tests/test_find_backlinks.py`

- [ ] **Step 1: Read normalize_link_target in lint.py**

  Open `skills/vault-linter/scripts/lint.py` and read the `normalize_link_target` function (line 168). The function:
  - Takes `target: str`, `vault_root: Path`, `source_file: Path`
  - Tries target as-is, then with `.md` appended
  - Checks vault-relative first, then source-relative
  - Returns the resolved `Path` or `None`

  You will copy this function verbatim into `find_backlinks.py` to ensure identical resolution. Add a comment pointing to the source.

- [ ] **Step 2: Write the tests**

  Create `tests/test_find_backlinks.py`:

  ```python
  """Tests for find_backlinks.py — backlink enumeration for the MERGE operation."""
  import sys
  from pathlib import Path
  import pytest

  sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
  from find_backlinks import find_backlinks


  def _make_page(path: Path, links: list[str]) -> None:
      """Write a minimal wiki page with the given [[wikilinks]]."""
      path.parent.mkdir(parents=True, exist_ok=True)
      body = "\n".join(f"See [[{lnk}]]." for lnk in links)
      path.write_text(
          f"---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-01-01\ntags: []\n---\n\n{body}\n",
          encoding="utf-8",
      )


  def test_finds_direct_match(tmp_path):
      """A page that links to the target is returned."""
      target = tmp_path / "wiki" / "pages" / "alpha.md"
      linker = tmp_path / "wiki" / "pages" / "beta.md"
      _make_page(target, [])
      _make_page(linker, ["wiki/pages/alpha"])

      result = find_backlinks(tmp_path, target)
      assert linker in result


  def test_finds_match_via_md_extension(tmp_path):
      """Links written as [[wiki/pages/alpha.md]] resolve to the same target."""
      target = tmp_path / "wiki" / "pages" / "alpha.md"
      linker = tmp_path / "wiki" / "pages" / "gamma.md"
      _make_page(target, [])
      _make_page(linker, ["wiki/pages/alpha.md"])

      result = find_backlinks(tmp_path, target)
      assert linker in result


  def test_no_false_positives(tmp_path):
      """Pages that don't link to the target are not returned."""
      target = tmp_path / "wiki" / "pages" / "alpha.md"
      unrelated = tmp_path / "wiki" / "pages" / "delta.md"
      _make_page(target, [])
      _make_page(unrelated, ["wiki/pages/other"])

      result = find_backlinks(tmp_path, target)
      assert unrelated not in result


  def test_multiple_files_linking_same_target(tmp_path):
      """All files linking to the target are returned."""
      target = tmp_path / "wiki" / "pages" / "hub.md"
      a = tmp_path / "wiki" / "pages" / "a.md"
      b = tmp_path / "wiki" / "pages" / "b.md"
      c = tmp_path / "wiki" / "sources" / "s.md"
      _make_page(target, [])
      _make_page(a, ["wiki/pages/hub"])
      _make_page(b, ["wiki/pages/hub"])
      _make_page(c, ["wiki/pages/hub"])

      result = find_backlinks(tmp_path, target)
      assert len(result) == 3
      assert a in result and b in result and c in result


  def test_dot_containing_slug(tmp_path):
      """Slugs containing dots (e.g. arxiv IDs) are resolved correctly."""
      target = tmp_path / "wiki" / "sources" / "arxiv-2602.20867.md"
      linker = tmp_path / "wiki" / "pages" / "ref.md"
      _make_page(target, [])
      _make_page(linker, ["wiki/sources/arxiv-2602.20867"])

      result = find_backlinks(tmp_path, target)
      assert linker in result


  def test_returns_empty_when_no_backlinks(tmp_path):
      """Returns empty list when nothing links to the target."""
      target = tmp_path / "wiki" / "pages" / "orphan.md"
      _make_page(target, [])
      result = find_backlinks(tmp_path, target)
      assert result == []
  ```

- [ ] **Step 3: Run tests to confirm they fail**

  ```bash
  pytest tests/test_find_backlinks.py -v
  ```
  Expected: ImportError (module not created yet).

- [ ] **Step 4: Implement find_backlinks.py**

  Create `skills/shared/find_backlinks.py`:

  ```python
  #!/usr/bin/env python3
  """
  find_backlinks.py — Find all wiki files that link to a target page.

  Used by the /merge operation to enumerate backlinks before rewriting them.
  The link-resolution logic is copied verbatim from lint.py::normalize_link_target()
  so that backlinks found here match exactly what the linter tracks.

  Usage:
      python find_backlinks.py <vault_root> <target_page_path>

  Output:
      One absolute path per line to stdout for each file containing a backlink.

  Exit codes:
      0 — found one or more backlinks (list to stdout)
      1 — no backlinks found
      2 — error (bad arguments, vault not found, etc.)
  """
  from __future__ import annotations
  import re
  import sys
  from pathlib import Path


  # Copied from lint.py::normalize_link_target() to ensure identical resolution.
  # If lint.py's resolution logic changes, update here too.
  def normalize_link_target(target: str, vault_root: Path, source_file: Path) -> Path | None:
      """Resolve a [[link]] target into an absolute path, or None if unresolvable.

      Rules:
      - Try target as-is (vault-relative, then source-relative).
      - If not found, also try with .md appended — slugs like
        arxiv-2602.20867 look like they have an extension but don't.
      - This way both [[wiki/sources/foo]] and [[wiki/sources/foo.md]] work,
        and slugs containing dots resolve correctly.
      """
      target = target.strip()
      if not target:
          return None

      base = Path(target)
      candidates = [base]
      if base.suffix != ".md":
          candidates.append(base.with_name(base.name + ".md"))

      for cand in candidates:
          abs_vault = vault_root / cand
          if abs_vault.exists():
              return abs_vault
          abs_local = source_file.parent / cand
          if abs_local.exists():
              return abs_local
      return None


  _WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


  def find_backlinks(vault: Path, target: Path) -> list[Path]:
      """Return all wiki files that contain a [[wikilink]] resolving to target."""
      target = target.resolve()
      results: list[Path] = []

      wiki_dir = vault / "wiki"
      if not wiki_dir.exists():
          return []

      for page in wiki_dir.rglob("*.md"):
          if page.name.startswith("."):
              continue
          try:
              text = page.read_text(encoding="utf-8", errors="ignore")
          except OSError:
              continue
          for m in _WIKILINK_RE.finditer(text):
              resolved = normalize_link_target(m.group(1), vault, page)
              if resolved is not None and resolved.resolve() == target:
                  results.append(page)
                  break  # one match per file is enough

      return sorted(results)


  def main() -> int:
      if len(sys.argv) != 3:
          print("Usage: find_backlinks.py <vault_root> <target_page_path>",
                file=sys.stderr)
          return 2

      vault = Path(sys.argv[1])
      target = Path(sys.argv[2])

      if not vault.is_dir():
          print(f"ERROR: vault not found: {vault}", file=sys.stderr)
          return 2
      if not target.exists():
          print(f"ERROR: target not found: {target}", file=sys.stderr)
          return 2

      results = find_backlinks(vault, target)
      if not results:
          return 1
      for r in results:
          print(r)
      return 0


  if __name__ == "__main__":
      sys.exit(main())
  ```

- [ ] **Step 5: Run tests to confirm they pass**

  ```bash
  pytest tests/test_find_backlinks.py -v
  ```
  Expected: all 6 tests pass.

- [ ] **Step 6: Run full test suite to check no regressions**

  ```bash
  pytest tests/ -v
  ```
  Expected: all pass.

- [ ] **Step 7: Commit**

  ```bash
  git add skills/shared/find_backlinks.py tests/test_find_backlinks.py
  git commit -m "feat(merge): add find_backlinks.py — stdlib helper to enumerate wiki backlinks for MERGE"
  ```

---

## Task 2 — Author commands/merge.md (task-0077)

The MERGE command protocol. Defines both the MERGE (two pages → one canonical) and SPLIT (one page → two) operations. This is an LLM-only operation; the command instructs the LLM what steps to follow.

**Files:** Create `commands/merge.md`

- [ ] **Step 1: Examine commands/forget.md for format reference**

  Open `commands/forget.md`. Note the frontmatter schema, step numbering, guards format (fanout >15 stops), and the unattended-refusal block. MERGE uses the same guard pattern.

- [ ] **Step 2: Create commands/merge.md**

  Create `commands/merge.md` with this exact content:

  ```markdown
  ---
  description: Merge two near-duplicate wiki pages into one canonical page, rewriting
    all backlinks. Or split an overgrown page into two focused ones. Used to resolve
    findings from check_duplicates (lint) and contradiction findings from /review.
    Interactive — never available in unattended mode.
  ---

  # /merge — Merge or split wiki pages

  Resolve near-duplicate pages and restructure overgrown ones. The natural
  resolution step for `check_duplicates` lint findings and `/review` contradiction
  findings.

  ## Arguments

  **Merge:** `/merge <page-A> <page-B>`
  - `page-A`: the page to be merged away (will be deleted)
  - `page-B`: the canonical target (kept, updated with merged content)

  **Split:** `/merge split <page>` or `/split <page>`
  - `page`: the page to split into two focused pages

  If invoked without arguments after a lint or review finding, both pages are
  pre-populated from the finding.

  ---

  ## MERGE Protocol

  ### 1. Identify

  Resolve `page-A` and `page-B` to absolute wiki paths. Confirm with the user:
  show the title, creation date, and a one-line summary of each.

  ### 2. Show content diff

  Read both pages. Present a diff-style summary:
  - Overlapping content (same concepts, same entities)
  - Content unique to page-A
  - Content unique to page-B
  - Citations in each

  Ask the user to confirm the merge direction (A into B, or B into A) and
  which content to keep from each.

  ### 3. Check backlink fanout

  Run the backlink helper to find all files linking to page-A:
  ```
  python3 .claude/skills/shared/find_backlinks.py <vault_root> <page-A-path>
  ```

  If the count exceeds **15 files** (Invariant #5 fanout guard):
  - Stop immediately.
  - Report the full list of linking files.
  - Ask the user to either: (a) proceed in multiple passes, or (b) pick a
    subset of backlinks to rewrite now and leave the rest for later.
  - Do NOT proceed without explicit user confirmation of the scope.

  ### 4. Draft merged content

  Draft the merged page content. Guidelines:
  - Keep the title of page-B (or a new title if the user requested one).
  - Combine unique content from both pages, removing true duplicates.
  - Merge the citation lists — a claim cited in page-A should remain cited.
  - Preserve all `[[wikilinks]]` to other pages (neither page-A nor page-B links
    should be lost).

  Show the draft to the user. Ask for approval before writing.

  ### 5. Write merged page

  Write the approved content to page-B (or a new slug if the title changed enough
  to warrant one — ask the user). Update the `updated:` frontmatter date.

  ### 6. Rewrite backlinks

  For each file in the backlink list from Step 3:
  - Open the file.
  - Replace every `[[wiki/pages/page-A]]` and `[[wiki/pages/page-A.md]]`
    (and any variant that resolved to page-A in Step 3) with the new canonical link.
  - Write the updated file.

  Show the user a summary: N files updated, N links rewritten.

  ### 7. Handle views

  Check whether any `wiki/views/` file has page-A in its `based_on:` list:
  - `shareable: false` → update `based_on:` to reference page-B instead.
  - `shareable: true` → do NOT touch. Warn the user that this view is now
    partially unsourced: "View `<slug>` (shareable) references the deleted page.
    Consider issuing a new dated version."

  ### 8. Delete page-A

  Delete `wiki/pages/page-A.md` (or its resolved path). This is irreversible —
  confirm once more with the user before deleting.

  ### 9. Update bookkeeping

  - Remove page-A's entry from `wiki/index.md`.
  - Add or update page-B's entry in `wiki/index.md`.
  - Append to `wiki/log.md`:
    `## [YYYY-MM-DD] merge | <page-A-slug> → <page-B-slug> | N backlinks rewritten`

  ### 10. Verify

  Propose running `/lint` to confirm zero dead links introduced. If any dead
  links remain, they are likely from the views case in Step 7 — note them.

  ---

  ## SPLIT Protocol

  Use when a page has grown to cover multiple distinct topics and would be better
  as two focused pages.

  ### 1. Identify

  Resolve the page to split. Ask the user to name the two new target pages
  (titles and slugs).

  ### 2. Show content

  Display the full page. Ask the user to mark which sections go to which new page.
  A section can go to both if it is shared context.

  ### 3. Write new pages

  Write the two new pages with the assigned content. Add proper frontmatter
  (`type: page`, `created:`, `updated:`, `tags:`). Each new page should cite the
  same sources as the original where those sources support its content.

  ### 4. Rewrite backlinks

  Run the backlink helper to find all files linking to the original page:
  ```
  python3 .claude/skills/shared/find_backlinks.py <vault_root> <original-page-path>
  ```

  For each linking file:
  - If it clearly links for content that went to page-A-new → rewrite to page-A-new.
  - If it clearly links for content that went to page-B-new → rewrite to page-B-new.
  - If ambiguous → show the linking file and ask the user which target to use.

  Apply the fanout guard: if > 15 links, stop and split the rewrite across passes.

  ### 5. Delete the original

  Delete the original page after confirming with the user. Check for
  `shareable: true` views with it in `based_on:` — warn, do not touch.

  ### 6. Update bookkeeping

  - Remove the original entry from `wiki/index.md`.
  - Add entries for both new pages.
  - Append to `wiki/log.md`:
    `## [YYYY-MM-DD] split | <original-slug> → <new-a-slug> + <new-b-slug>`

  ---

  ## Guards

  - **Fanout > 15:** Stop. Report the full link list. Split across passes if needed.
  - **Prose deletion:** Always ask before removing any text. Never auto-discard.
  - **`shareable: true` views:** Never silently modify. Warn and let the user decide.
  - **Confirm before delete:** A final "Delete page-A?" confirmation before Step 8.

  ## Unattended mode

  `/merge` is **not available unattended**. The operation involves irreversible
  page deletions and per-link rewriting decisions that require the user in the
  loop. If invoked unattended, refuse with a clear message.

  ## Report format

  End of MERGE, tell the user:
  ```
  Merged: wiki/pages/<page-A> → wiki/pages/<page-B>
    ✓ Merged content written to wiki/pages/<page-B>
    ✓ Rewrote N backlinks across M files
    ✓ Updated wiki/index.md
    ✓ Deleted wiki/pages/<page-A>
    ⚠ 1 shareable view left as-is (see above)
  Suggest: run /lint to confirm zero dead links
  ```
  ```

- [ ] **Step 3: Verify the file was created**

  ```bash
  head -5 commands/merge.md
  grep -c "###" commands/merge.md
  ```
  Expected: frontmatter starts with `---`; several `###` section headings.

- [ ] **Step 4: Commit**

  ```bash
  git add commands/merge.md
  git commit -m "feat(merge): add /merge command — interactive page merge and split with backlink rewriting"
  ```

---

## Task 3 — Add MERGE operation to CLAUDE.md (task-0078)

Register MERGE as the eleventh operation.

**Files:** Modify `CLAUDE.md`

**Prerequisite:** Phase 2 Task 2 must be done (CLAUDE.md already has 10 operations; MERGE adds the 11th).

- [ ] **Step 1: Add the MERGE section to the operations list**

  In `CLAUDE.md`, find the REFRESH operation section. After it, add:

  ```markdown
  ### MERGE
  User says "merge these pages", "these are duplicates", "split this page", or
  runs `/merge <page-A> <page-B>` or `/merge split <page>` → resolve near-duplicate
  pages by merging them into a canonical page (or splitting an overgrown one),
  with full backlink rewriting. Guards: stops if fanout > 15 files (Invariant #5);
  asks before deleting any prose; never silently touches `shareable: true` views.
  See `commands/merge.md` for the full MERGE and SPLIT protocols.

  Backed by `find_backlinks.py` (installed at `.claude/skills/shared/find_backlinks.py`)
  for enumerating backlinks before rewriting.
  ```

- [ ] **Step 2: Add MERGE to the dispatch table**

  Find the dispatch table. Currently ends with REVIEW (after Phase 2).
  Add after REVIEW:
  ```markdown
  | MERGE     | (LLM only)     | find_backlinks.py              |
  ```

  Update the section heading from "Ten operations" to "Eleven operations".

- [ ] **Step 3: Update unattended mode CANNOT list**

  Find the unattended mode section. Add MERGE to the "CANNOT" list:
  ```
  merge, split pages (structural changes — require user confirmation)
  ```

- [ ] **Step 4: Verify operation count is consistent**

  ```bash
  grep -n "Eleven operations\|Ten operations" CLAUDE.md
  grep -c "^| [A-Z]" CLAUDE.md
  ```
  Expected: heading says "Eleven operations"; table has 11 data rows.

- [ ] **Step 5: Commit**

  ```bash
  git add CLAUDE.md
  git commit -m "feat(merge): register MERGE as the eleventh operation in CLAUDE.md"
  ```

---

## Task 4 — Register merge.md and find_backlinks.py in init_vault.py (task-0079)

Every vault bootstrapped after this change should have MERGE available.

**Files:** Modify `init_vault.py`

- [ ] **Step 1: Add merge.md to COMMANDS**

  Open `init_vault.py`. Find the `COMMANDS` list (after Phase 2 it includes "review"). Add "merge":
  ```python
  COMMANDS = [
      "save", "view", "reflect", "forget", "lint", "promote",
      "refresh", "ingest", "fetch", "hot", "playwright-fetch", "review", "merge",
  ]
  ```

- [ ] **Step 2: Add find_backlinks.py to the shared scripts install**

  Find the `install_skills()` function (around line 340) where `vault_state.py` is copied into `.claude/skills/shared/`. The current code copies a single file. Add `find_backlinks.py` (and `review_scope.py` if not already there from Phase 2) to the same copy step.

  The simplest approach: replace the single-file copy with a loop over a list:
  ```python
  shared_scripts = ["vault_state.py", "review_scope.py", "find_backlinks.py"]
  for script_name in shared_scripts:
      shared_src = script_dir / "skills" / "shared" / script_name
      if shared_src.exists():
          shutil.copy2(
              shared_src,
              vault / ".claude" / "skills" / "shared" / script_name,
          )
          ok(f"shared: {script_name}")
      else:
          warn(f"skills/shared/{script_name} not found in bundle")
  ```

- [ ] **Step 3: Smoke-test bootstrap**

  ```bash
  python init_vault.py /tmp/vault-merge-test
  ls /tmp/vault-merge-test/.claude/commands/ | grep merge
  ls /tmp/vault-merge-test/.claude/skills/shared/
  ```
  Expected: `merge.md` present in commands; `find_backlinks.py` and `vault_state.py` present in shared.

- [ ] **Step 4: Run all tests**

  ```bash
  pytest tests/ -v
  ```
  Expected: all pass.

- [ ] **Step 5: Commit**

  ```bash
  git add init_vault.py
  git commit -m "feat(merge): register merge.md + find_backlinks.py in init_vault.py bootstrap"
  ```

---

## Final verification (Phase 3)

- [ ] All tests pass (including Phase 1 and Phase 2 tests):
  ```bash
  pytest tests/ -v
  ```

- [ ] Bootstrap installs MERGE:
  ```bash
  python init_vault.py /tmp/vault-final-verify
  cat /tmp/vault-final-verify/.claude/commands/merge.md | head -3
  ls /tmp/vault-final-verify/.claude/skills/shared/
  ```
  Expected: `merge.md` installed; `find_backlinks.py` installed alongside `vault_state.py` and `review_scope.py`.

- [ ] CLAUDE.md has 11 operations in the table:
  ```bash
  grep -c "^| [A-Z]" CLAUDE.md
  ```
  Expected: 11.

- [ ] find_backlinks.py fanout count works correctly:
  ```bash
  python skills/shared/find_backlinks.py . skills/shared/find_backlinks.py 2>&1
  ```
  Expected: exit 1 (no backlinks) or a list of files if any currently link to it.

- [ ] No dead links after the full Phase 3 (run on a real vault after deploying):
  ```bash
  python .claude/skills/vault-linter/scripts/lint.py <vault_root>
  ```
  Expected: zero `dead_links` findings.
