# Vault Hardening — Implementation Plan (Phase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 11 confirmed defects and doc-vs-code inconsistencies so every documented behavior matches code and CLAUDE.md is an honest, internally-consistent contract.

**Architecture:** Eleven independent fixes executed in priority order. Four have Python + test changes (Tasks 3, 4, 5, 6); two are Python-only reshapes (Tasks 7, 8); five are prose-only edits to command/skill/doc files (Tasks 1, 2, 9, 10, 11). No new dependencies. No new abstractions.

**Tech Stack:** Python 3.10+ stdlib, pytest, Markdown. All changes are in `skills/`, `commands/`, `CLAUDE.md`, and `init-vault.sh`.

**Backlog milestone:** m-0 — tasks task-0061 through task-0071.

---

## File Map

| File | Action | Task(s) |
|---|---|---|
| `commands/ingest.md` | Modify line 23: bare path → `.claude/skills/...` | Task 1 |
| `skills/inbox-fetcher/SKILL.md` | Modify lines 93, 164-166: flat PDF path + example paths | Tasks 2, 11 |
| `commands/forget.md` | Modify step 5: add `raw/local/<slug>/` deletion branch | Task 9 |
| `skills/inbox-fetcher/scripts/fetch_inbox.py` | Modify: enforce max_pdf_mb; honour tags_propagation; fix module docstring | Tasks 3, 4, 11 |
| `tests/test_fetch_inbox.py` | Add: 3 new test cases (oversized header, oversized stream, tags disabled) | Tasks 3, 4 |
| `skills/vault-linter/scripts/lint.py` | Modify: wrap all_checks loop in try/except per check | Task 5 |
| `tests/test_lint.py` | Add: 1 new test case (crashing check degrades to advisory) | Task 5 |
| `skills/inbox-fetcher/scripts/adopt_drop.py` | Modify: `Path.rename()` → `shutil.move()` | Task 6 |
| `tests/test_adopt_drop.py` | Add: 1 new test case (cross-device rename fallback) | Task 6 |
| `init-vault.sh` | Replace body with thin shim delegating to `init_vault.py` | Task 7 |
| `CLAUDE.md` | Add FORGET row to dispatch table; remove "hooks" from dir listing | Task 8 |
| `skills/vault-linter/SKILL.md` | Fix "Fifteen" → "Fourteen" in description + table header | Task 10 |

---

## Task 1 — Fix /ingest adopt_drop.py path bug (task-0061) ⚠ HIGH SEVERITY

In a deployed vault, scripts live under `.claude/skills/…` — not the bare `skills/…` path that `commands/ingest.md` currently uses. This means the drop-zone pre-flight silently fails every time `/ingest` is run.

**Files:** Modify `commands/ingest.md`

- [ ] **Step 1: Confirm the current broken line**

  Open `commands/ingest.md` and find line 23. It reads:
  ```
  a. Run: `python3 skills/inbox-fetcher/scripts/adopt_drop.py --vault <vault_root>`
  ```

- [ ] **Step 2: Apply the fix**

  Change line 23 to:
  ```
  a. Run: `python3 .claude/skills/inbox-fetcher/scripts/adopt_drop.py --vault <vault_root>`
  ```

- [ ] **Step 3: Verify no other bare paths remain**

  ```bash
  grep -n "skills/inbox-fetcher/scripts/adopt_drop" commands/ingest.md
  ```
  Expected: every match starts with `.claude/skills/…`

- [ ] **Step 4: Commit**

  ```bash
  git add commands/ingest.md
  git commit -m "fix(ingest): correct adopt_drop.py path for deployed vaults"
  ```

---

## Task 2 — Fix adopt_drop.py example paths in SKILL.md (task-0062)

Same root cause as Task 1 — documentation examples that would fail if copied verbatim in a deployed vault.

**Files:** Modify `skills/inbox-fetcher/SKILL.md`

- [ ] **Step 1: Find the broken examples**

  Open `skills/inbox-fetcher/SKILL.md` and locate lines 164-166. They contain manual-run examples like:
  ```
  python3 skills/inbox-fetcher/scripts/adopt_drop.py --vault /path/to/vault
  ```

- [ ] **Step 2: Apply the fix**

  Change every `skills/inbox-fetcher/scripts/adopt_drop.py` reference in the manual-run examples (lines ~164-166) to `.claude/skills/inbox-fetcher/scripts/adopt_drop.py`.

- [ ] **Step 3: Verify consistency**

  ```bash
  grep -n "adopt_drop.py" skills/inbox-fetcher/SKILL.md
  ```
  Every match should use `.claude/skills/…`. Compare against `fetch_inbox.py` examples in the same file — they already use `.claude/skills/…`.

- [ ] **Step 4: Commit**

  ```bash
  git add skills/inbox-fetcher/SKILL.md
  git commit -m "fix(docs): correct adopt_drop.py example paths in SKILL.md"
  ```

---

## Task 3 — Enforce max_pdf_mb in fetch_inbox.py (task-0064)

Currently `fetch_pdf()` prints a warning when the PDF exceeds `max_pdf_size_mb` but downloads it in full anyway. When `Content-Length` is absent, the check is silently skipped entirely.

**Files:** Modify `skills/inbox-fetcher/scripts/fetch_inbox.py`, add tests to `tests/test_fetch_inbox.py`

- [ ] **Step 1: Run baseline tests**

  ```bash
  pytest tests/test_fetch_inbox.py -v
  ```
  Expected: all existing tests pass.

- [ ] **Step 2: Write the two failing tests**

  Add to `tests/test_fetch_inbox.py` (the project uses `requests_mock` pytest fixture,
  which is already a project dependency — no new imports needed):
  ```python
  class TestFetchPdfSizeLimit:
      def test_rejects_oversized_with_content_length(self, tmp_path, requests_mock):
          """PDF fetch must fail fast when Content-Length exceeds the limit."""
          from fetch_inbox import fetch_pdf
          papers_dir = tmp_path / "papers"
          papers_dir.mkdir(parents=True)

          # 60 MB declared via Content-Length; limit is 50 MB
          requests_mock.get(
              "https://example.com/big.pdf",
              content=b"%PDF-1.4 fake",
              headers={"Content-Type": "application/pdf",
                       "Content-Length": str(60 * 1024 * 1024)},
          )
          result = fetch_pdf("https://example.com/big.pdf",
                             papers_dir, max_pdf_mb=50)

          assert not result.ok
          assert "too large" in result.reason.lower()
          # No paper.pdf should have been written
          assert not list(papers_dir.rglob("paper.pdf"))

      def test_rejects_oversized_discovered_mid_stream(self, tmp_path, requests_mock):
          """PDF fetch must abort and clean up when size limit exceeded mid-stream."""
          from fetch_inbox import fetch_pdf
          papers_dir = tmp_path / "papers"
          papers_dir.mkdir(parents=True)

          # No Content-Length header; body exceeds the limit
          big_body = b"\x00" * (60 * 1024 * 1024)
          requests_mock.get(
              "https://example.com/huge.pdf",
              content=big_body,
              headers={"Content-Type": "application/pdf"},
              # No Content-Length header
          )
          result = fetch_pdf("https://example.com/huge.pdf",
                             papers_dir, max_pdf_mb=50)

          assert not result.ok
          assert "too large" in result.reason.lower()
          # Partial file must be cleaned up — no paper.pdf anywhere
          assert not list(papers_dir.rglob("paper.pdf"))
  ```

- [ ] **Step 3: Run tests to confirm they fail**

  ```bash
  pytest tests/test_fetch_inbox.py::test_fetch_pdf_rejects_oversized_with_content_length \
         tests/test_fetch_inbox.py::test_fetch_pdf_rejects_oversized_mid_stream -v
  ```
  Expected: both FAIL (current code downloads regardless).

- [ ] **Step 4: Implement the fix in fetch_pdf()**

  In `skills/inbox-fetcher/scripts/fetch_inbox.py`, replace the current size-check block (lines ~186-196) with:

  ```python
  size = int(r.headers.get("Content-Length", 0))
  max_bytes = max_pdf_mb * 1024 * 1024

  # Fail fast when the server declares the size upfront
  if size > max_bytes:
      return FetchResult(url=url, ok=False, kind="failed",
                         reason=f"PDF too large ({size // 1024 // 1024} MB > {max_pdf_mb} MB limit)")

  slug = slug_override or slug_from(url, None)
  out_dir = papers_dir / slug
  out_dir.mkdir(parents=True, exist_ok=True)
  pdf_file = out_dir / "paper.pdf"

  # Stream to disk, abort and clean up if we exceed the limit mid-download
  # (handles servers that omit Content-Length)
  accumulated = 0
  try:
      with open(pdf_file, "wb") as f:
          for chunk in r.iter_content(chunk_size=8192):
              accumulated += len(chunk)
              if accumulated > max_bytes:
                  f.close()
                  pdf_file.unlink(missing_ok=True)
                  try:
                      out_dir.rmdir()
                  except OSError:
                      pass
                  return FetchResult(url=url, ok=False, kind="failed",
                                     reason=f"PDF too large (exceeded {max_pdf_mb} MB mid-stream)")
              f.write(chunk)
  except Exception as e:
      pdf_file.unlink(missing_ok=True)
      try:
          out_dir.rmdir()
      except OSError:
          pass
      return FetchResult(url=url, ok=False, kind="failed",
                         reason=f"pdf download failed: {e}")
  ```

  Remove the original `with open(out_dir / "paper.pdf", "wb") as f:` block that follows.

- [ ] **Step 5: Run tests to confirm they pass**

  ```bash
  pytest tests/test_fetch_inbox.py -v
  ```
  Expected: all tests including the two new ones pass.

- [ ] **Step 6: Commit**

  ```bash
  git add skills/inbox-fetcher/scripts/fetch_inbox.py tests/test_fetch_inbox.py
  git commit -m "fix(fetch): enforce max_pdf_mb limit — fail fast on header, abort on stream overflow"
  ```

---

## Task 4 — Honour inbox.tags_propagation config flag (task-0065)

`fetch_inbox.py` always propagates `tags`/`note` sub-bullets into `raw/` frontmatter. The `inbox.tags_propagation` config key exists but is never checked.

**Files:** Modify `skills/inbox-fetcher/scripts/fetch_inbox.py`, add test to `tests/test_fetch_inbox.py`

- [ ] **Step 1: Write the failing tests**

  Add to `tests/test_fetch_inbox.py` as a new class (uses `requests_mock` fixture):
  ```python
  class TestTagsPropagation:
      def test_tags_omitted_when_propagation_disabled(self, tmp_path, requests_mock):
          """With tags_propagation: false, tags must not appear in raw/ index.md."""
          from fetch_inbox import fetch_pdf
          papers_dir = tmp_path / "papers"
          papers_dir.mkdir(parents=True)

          requests_mock.get(
              "https://arxiv.org/pdf/2501.00001.pdf",
              content=b"%PDF-1.4 test",
              headers={"Content-Type": "application/pdf"},
          )
          result = fetch_pdf(
              "https://arxiv.org/pdf/2501.00001.pdf",
              papers_dir,
              slug_override="arxiv-2501-00001",
              tags=["ai", "llm"],
              note="read section 2",
              propagate_tags=False,   # the new parameter
          )

          assert result.ok
          index_text = (result.out_path / "index.md").read_text()
          assert "tags: [ai, llm]" not in index_text
          assert "note:" not in index_text

      def test_tags_present_when_propagation_enabled(self, tmp_path, requests_mock):
          """Default behaviour (propagate_tags=True) must still work."""
          from fetch_inbox import fetch_pdf
          papers_dir = tmp_path / "papers"
          papers_dir.mkdir(parents=True)

          requests_mock.get(
              "https://arxiv.org/pdf/2501.00002.pdf",
              content=b"%PDF-1.4 test",
              headers={"Content-Type": "application/pdf"},
          )
          result = fetch_pdf(
              "https://arxiv.org/pdf/2501.00002.pdf",
              papers_dir,
              slug_override="arxiv-2501-00002",
              tags=["rl"],
              note="check experiments",
              propagate_tags=True,
          )

          assert result.ok
          index_text = (result.out_path / "index.md").read_text()
          assert "tags: [rl]" in index_text
          assert "check experiments" in index_text
  ```

  Note: these tests use `propagate_tags=False/True` — a new parameter added to `fetch_pdf()` in Step 3.

- [ ] **Step 2: Identify the propagation block in fetch_html and fetch_pdf**

  In `fetch_inbox.py`, search for where `tags` and `note` are written into `fm_lines`. In `fetch_pdf()` this is around lines 212-215:
  ```python
  if tags:
      fm_lines.append(f"tags: [{', '.join(tags)}]")
  if note:
      fm_lines.append(f"note: {yaml_escape(note)}")
  ```
  The same pattern appears in `fetch_html()`.

- [ ] **Step 3: Add a helper and the guard**

  At module level (near the top, after constants), add:
  ```python
  def _should_propagate_tags(config: dict) -> bool:
      """Return True when inbox tag/note propagation is enabled (default: True)."""
      return bool(config.get("inbox", {}).get("tags_propagation", True))
  ```

  In `process_vault()`, read the flag once from config (line ~407 area, alongside the other config reads):
  ```python
  propagate_tags = _should_propagate_tags(cfg)
  ```

  Pass `propagate_tags` to both `fetch_pdf()` and `fetch_html()` as a new parameter:
  ```python
  def fetch_pdf(url, papers_dir, ..., propagate_tags: bool = True, ...) -> FetchResult:
  ```
  ```python
  def fetch_html(url, web_dir, ..., propagate_tags: bool = True, ...) -> FetchResult:
  ```

  In each function body, wrap the tags/note block:
  ```python
  if propagate_tags:
      if tags:
          fm_lines.append(f"tags: [{', '.join(tags)}]")
      if note:
          fm_lines.append(f"note: {yaml_escape(note)}")
  ```

- [ ] **Step 4: Run all tests**

  ```bash
  pytest tests/test_fetch_inbox.py -v
  ```
  Expected: all pass.

- [ ] **Step 5: Commit**

  ```bash
  git add skills/inbox-fetcher/scripts/fetch_inbox.py tests/test_fetch_inbox.py
  git commit -m "fix(fetch): honour inbox.tags_propagation config flag (was always propagating)"
  ```

---

## Task 5 — Graceful degradation in lint.py (task-0067)

A single crashing check aborts the whole lint run with exit 2. One bad check kills the full health report.

**Files:** Modify `skills/vault-linter/scripts/lint.py`, add test to `tests/test_lint.py`

- [ ] **Step 1: Write the failing test**

  Add to `tests/test_lint.py` (note: the file already has `sys.path.insert` for
  `skills/vault-linter/scripts` at line 5 — the import below works with that setup):

  ```python
  class TestLintGracefulDegradation:
      def test_crashing_check_produces_advisory_not_exit_2(self, tmp_path):
          """A check that raises must produce an advisory, not abort the whole run."""
          import unittest.mock as mock
          import lint as lint_mod
          from lint import run_lint

          # Minimal valid vault with wiki/ structure
          (tmp_path / "wiki" / "pages").mkdir(parents=True)
          (tmp_path / "wiki" / "sources").mkdir(parents=True)
          (tmp_path / ".lint").mkdir(parents=True)

          # Patch an existing check function at module level to raise.
          # check_gaps() is a pure-pages check with no vault arg — easy to patch.
          with mock.patch.object(lint_mod, "check_gaps",
                                 side_effect=RuntimeError("intentional test crash")):
              exit_code = run_lint(tmp_path, quiet=True)

          # Must continue to exit 1 (findings), not 2 (catastrophic abort)
          assert exit_code == 1

          # The report must mention the crash
          report = (tmp_path / ".lint" / "report.md").read_text()
          assert "check_gaps" in report or "intentional test crash" in report
  ```

- [ ] **Step 2: Locate the all_checks loop**

  Open `skills/vault-linter/scripts/lint.py`. The loop is at line ~805:
  ```python
  for name, fn in all_checks:
      try:
          if name in ("dead_links", "orphans", ...):
              out = fn(pages, vault)
          ...
      except Exception as e:
          print(f"ERROR in check '{name}': {e}", file=sys.stderr)
          return 2
      findings.extend(out)
  ```

- [ ] **Step 3: Replace the abort-on-exception with a crash advisory**

  Replace the `except` block in the loop. The key changes: initialize `out = []`
  *before* the try (so `len(out)` is always valid in the print), build the crash
  advisory as a `Finding` with `detail=` (the actual field name — NOT `message`):

  ```python
  findings: list[Finding] = []
  completed = 0
  for name, fn in all_checks:
      out: list[Finding] = []   # always valid; overwritten on success
      try:
          if name in ("dead_links", "orphans", "based_on_dead_links", "index_sync"):
              out = fn(pages, vault)
          elif name in ("pdf_index", "conversations", "drop_zone"):
              out = fn(vault)
          else:
              out = fn(pages)
      except Exception as e:
          # A crashing check is recorded as an advisory finding so the rest of
          # the report remains useful rather than being lost entirely.
          crash_detail = f"check '{name}' raised an unexpected error: {e}"
          print(f"  ⚠ {crash_detail}", file=sys.stderr)
          out = [Finding(
              severity="advisory",
              check=name,
              file="(linter)",
              detail=crash_detail,
          )]
      findings.extend(out)
      completed += 1
      if not quiet:
          print(f"  {name}: {len(out)} finding(s)")
  ```

  After the loop, add the catastrophic-failure guard and remove the old `return 2`
  that was inside the loop:
  ```python
  if completed == 0:
      print("ERROR: no checks completed — vault may be unreadable", file=sys.stderr)
      return 2
  ```

- [ ] **Step 4: Run all lint tests**

  ```bash
  pytest tests/test_lint.py -v
  ```
  Expected: all pass, including the new crash-advisory test.

- [ ] **Step 5: Commit**

  ```bash
  git add skills/vault-linter/scripts/lint.py tests/test_lint.py
  git commit -m "fix(lint): degrade gracefully when a check crashes instead of aborting the whole run"
  ```

---

## Task 6 — Replace Path.rename() with shutil.move() in adopt_drop.py (task-0068)

`Path.rename()` fails with `OSError: [Errno 18] Invalid cross-device link` when source and destination are on different filesystems. This affects Windows multi-volume setups and Linux mount configurations.

**Files:** Modify `skills/inbox-fetcher/scripts/adopt_drop.py`, add test to `tests/test_adopt_drop.py`

- [ ] **Step 1: Write the failing test**

  Add to `tests/test_adopt_drop.py`:
  ```python
  def test_adopt_pdf_uses_shutil_move_for_cross_device_safety(tmp_path, monkeypatch):
      """adopt_pdf must succeed even when rename() would fail cross-device."""
      import shutil
      from pathlib import Path
      from skills.inbox_fetcher.scripts.adopt_drop import adopt_pdf

      drop_dir = tmp_path / "drop"
      local_dir = tmp_path / "local"
      drop_dir.mkdir()
      local_dir.mkdir()

      pdf = drop_dir / "my-paper.pdf"
      pdf.write_bytes(b"%PDF-1.4 test")

      # Simulate cross-device rename failure
      original_rename = Path.rename
      def failing_rename(self, target):
          raise OSError(18, "Invalid cross-device link", str(self))
      monkeypatch.setattr(Path, "rename", failing_rename)

      # shutil.move should be used as the fallback
      result = adopt_pdf(pdf, local_dir)
      assert result.ok, f"Expected ok but got: {result.reason}"
      assert (local_dir / result.slug / "paper.pdf").exists()
  ```

- [ ] **Step 2: Run test to confirm it fails**

  ```bash
  pytest tests/test_adopt_drop.py::test_adopt_pdf_uses_shutil_move_for_cross_device_safety -v
  ```
  Expected: FAIL (current code uses `rename()` which the monkeypatch breaks).

- [ ] **Step 3: Apply the fix**

  In `skills/inbox-fetcher/scripts/adopt_drop.py`:

  Add `import shutil` at the top (alongside existing imports).

  Find the two `rename()` calls — one in `adopt_pdf()` (line ~147) and one in `adopt_md()` (similar pattern):

  ```python
  # Before — in adopt_pdf():
  try:
      pdf_path.rename(out_dir / "paper.pdf")
  except Exception:
      # rename failed after index.md written — undo index and dir.
      index_path.unlink(missing_ok=True)
      out_dir.rmdir()
      raise

  # After:
  try:
      # shutil.move handles cross-filesystem moves transparently;
      # Path.rename() raises OSError on cross-device moves.
      shutil.move(str(pdf_path), str(out_dir / "paper.pdf"))
  except Exception:
      index_path.unlink(missing_ok=True)
      out_dir.rmdir()
      raise
  ```

  Apply the same change for `adopt_md()` (where `md_path` is moved to `content.md`):
  ```python
  # Before:
  md_path.rename(out_dir / "content.md")
  # After:
  shutil.move(str(md_path), str(out_dir / "content.md"))
  ```

- [ ] **Step 4: Run all adopt_drop tests**

  ```bash
  pytest tests/test_adopt_drop.py -v
  ```
  Expected: all pass.

- [ ] **Step 5: Commit**

  ```bash
  git add skills/inbox-fetcher/scripts/adopt_drop.py tests/test_adopt_drop.py
  git commit -m "fix(adopt): replace Path.rename with shutil.move to handle cross-filesystem drop zones"
  ```

---

## Task 7 — Collapse init-vault.sh to a thin shim (task-0069)

The bash bootstrapper has diverged from `init_vault.py` (missing `adopt_drop.py`, missing directories, stale text). Rather than re-syncing two bootstrappers, collapse the bash script to a shim — one source of truth forever.

**Files:** Replace body of `init-vault.sh`

- [ ] **Step 1: Verify init_vault.py works as the canonical path**

  ```bash
  python init_vault.py --help
  ```
  Expected: shows usage/help text without error.

- [ ] **Step 2: Replace init-vault.sh**

  Replace the entire contents of `init-vault.sh` with:
  ```bash
  #!/usr/bin/env bash
  # Thin shim — delegates to the canonical Python bootstrapper (init_vault.py).
  # Kept so users who reach for a .sh script by habit get the same result.
  # All logic lives in init_vault.py; edit that file, not this one.
  set -euo pipefail
  python3 "$(dirname "$0")/init_vault.py" "$@"
  ```

- [ ] **Step 3: Confirm it stays executable**

  On Linux/macOS:
  ```bash
  chmod +x init-vault.sh
  ls -la init-vault.sh
  ```
  Expected: `-rwxr-xr-x`

  On Windows: the executable bit is preserved in git regardless of this step.

- [ ] **Step 4: Smoke-test both paths produce identical output**

  ```bash
  python init_vault.py /tmp/vault-py-test --dry-run 2>&1 | head -5
  ./init-vault.sh /tmp/vault-sh-test --dry-run 2>&1 | head -5
  ```
  Expected: same output lines.

- [ ] **Step 5: Commit**

  ```bash
  git add init-vault.sh
  git commit -m "fix(bootstrap): collapse init-vault.sh to a shim — one bootstrapper to maintain"
  ```

---

## Task 8 — Reconcile CLAUDE.md: FORGET row + remove hooks claim (task-0070)

Two inconsistencies make CLAUDE.md untrustworthy as a contract: the dispatch table omits FORGET, and line 33 promises "hooks" that have never existed.

**Files:** Modify `CLAUDE.md`

- [ ] **Step 1: Add FORGET row to dispatch table**

  Open `CLAUDE.md`. Find the dispatch table (around line 225):
  ```markdown
  | Operation | Skill          | Backed by                      |
  |-----------|----------------|--------------------------------|
  | FETCH     | inbox-fetcher  | scripts/fetch_inbox.py         |
  | LINT      | vault-linter   | scripts/lint.py                |
  | VIEW      | view-builder   | templates/ + LLM               |
  | INGEST    | (LLM only)     | adopt_drop.py (pre-flight)     |
  | QUERY     | (LLM only)     | —                              |
  | REFLECT   | (LLM only)     | —                              |
  | PROMOTE   | (LLM only)     | —                              |
  | REFRESH   | (LLM only)     | —                              |
  ```

  Add the FORGET row after REFRESH:
  ```markdown
  | FORGET    | (LLM only)     | —                              |
  ```

- [ ] **Step 2: Remove the "hooks" claim from the directory listing**

  Find line 33 (or the `.claude/` directory description):
  ```
  .claude/              Skills, commands, hooks (mechanisms, not content)
  ```

  Change to:
  ```
  .claude/              Skills, commands, settings (mechanisms, not content)
  ```

- [ ] **Step 3: Verify counts are consistent**

  ```bash
  grep -n "Nine operations\|Ten operations\|Eleven operations" CLAUDE.md
  grep -c "^| [A-Z]" CLAUDE.md
  ```
  After this task: heading should say "Nine operations", table should have 9 data rows.

- [ ] **Step 4: Verify hooks is gone from the dir listing**

  ```bash
  grep -n "hooks" CLAUDE.md
  ```
  Expected: zero matches in the vault-structure directory listing context.

- [ ] **Step 5: Commit**

  ```bash
  git add CLAUDE.md
  git commit -m "fix(docs): add FORGET to dispatch table; remove vestigial hooks claim from dir listing"
  ```

---

## Task 9 — Add raw/local deletion branch to /forget (task-0063)

`commands/forget.md` step 5 deletes `raw/web/` and `raw/papers/` but not `raw/local/` — added in a later phase. Local sources are orphaned after forget.

**Files:** Modify `commands/forget.md`

- [ ] **Step 1: Locate the deletion step**

  Open `commands/forget.md`. Find step 5 ("Delete the source"), which currently reads:
  ```markdown
  - Delete `wiki/sources/<slug>.md`. Delete the entire raw folder:
    - Web sources: `raw/web/<slug>/` (includes `index.md` and `assets/`).
    - PDF sources: `raw/papers/<slug>/` (includes `paper.pdf` and `index.md`).
  ```

- [ ] **Step 2: Apply the fix**

  Replace that block with:
  ```markdown
  - Delete `wiki/sources/<slug>.md`. Delete the entire raw folder:
    - Web sources: `raw/web/<slug>/` (includes `index.md` and `assets/`).
    - PDF sources (URL-fetched): `raw/papers/<slug>/` (includes `paper.pdf` and `index.md`).
    - Local PDF sources: `raw/local/<slug>/` (includes `paper.pdf` and `index.md`).
    - Local Markdown sources: `raw/local/<slug>/` (includes `content.md` and `index.md`).

  This is the one case where writing to `raw/` (as deletion) is allowed —
  invariant #1 covers creation, not user-directed removal.
  ```

- [ ] **Step 3: Cross-check against CLAUDE.md**

  Open `CLAUDE.md` FORGET step 5 (around line 160-163). Confirm the wording in `commands/forget.md` is now consistent with it.

- [ ] **Step 4: Commit**

  ```bash
  git add commands/forget.md
  git commit -m "fix(forget): add raw/local deletion branch for copy-paste PDF/MD sources"
  ```

---

## Task 10 — Fix check count in vault-linter SKILL.md (task-0071)

SKILL.md says "Fifteen deterministic checks"; the code has 14.

**Files:** Modify `skills/vault-linter/SKILL.md`

- [ ] **Step 1: Confirm the count in code**

  ```bash
  grep -c "^    (\"" skills/vault-linter/scripts/lint.py
  ```
  Expected: 14 (the 14 tuples in `all_checks`).

- [ ] **Step 2: Fix the description line**

  In `skills/vault-linter/SKILL.md` line ~3 (the YAML `description:` field), change:
  ```
  ...dead links, orphan pages, duplicates, missing metadata, inconsistent naming, stale sources, gaps, view staleness, missing cross-references, view based_on dead links, PDF index integrity, conversation schema, source index sync, local PDF index integrity, drop zone not empty) and writes a report...
  ```
  This already lists 14 check categories correctly in the description text. The word "Fifteen" appears in the prose below — find and fix it.

- [ ] **Step 3: Fix the prose header**

  Find the line that says:
  ```
  Fifteen deterministic checks. Each produces findings with concrete paths.
  ```
  Change to:
  ```
  Fourteen deterministic checks. Each produces findings with concrete paths.
  ```

- [ ] **Step 4: Verify**

  ```bash
  grep -n "Fifteen\|fifteen" skills/vault-linter/SKILL.md
  ```
  Expected: zero matches.

- [ ] **Step 5: Commit**

  ```bash
  git add skills/vault-linter/SKILL.md
  git commit -m "fix(docs): correct check count in vault-linter SKILL.md (14, not 15)"
  ```

---

## Task 11 — Fix stale flat-PDF documentation (task-0066)

Two places still describe the old flat-file PDF layout (`raw/papers/<slug>.pdf`) that the linter now flags as legacy.

**Files:** Modify `skills/inbox-fetcher/scripts/fetch_inbox.py` (module docstring), `skills/inbox-fetcher/SKILL.md` (step 2)

- [ ] **Step 1: Fix fetch_inbox.py module docstring**

  Open `fetch_inbox.py`. Line 12 reads:
  ```
  PDFs go to raw/papers/<slug>.pdf.
  ```
  Change to:
  ```
  PDFs go to raw/papers/<slug>/paper.pdf with a companion index.md.
  ```

- [ ] **Step 2: Fix SKILL.md step 2**

  Open `skills/inbox-fetcher/SKILL.md` line ~93:
  ```
  2. **PDF detection.** If the (rewritten) URL path ends in `.pdf` or the server returns `Content-Type: application/pdf`, download as-is to `raw/papers/<slug>.pdf`.
  ```
  Change to:
  ```
  2. **PDF detection.** If the (rewritten) URL path ends in `.pdf` or the server returns `Content-Type: application/pdf`, download into `raw/papers/<slug>/paper.pdf` with a companion `index.md`.
  ```

- [ ] **Step 3: Verify no flat-file references remain**

  ```bash
  grep -rn "raw/papers/<slug>\.pdf" skills/inbox-fetcher/
  ```
  Expected: zero matches.

- [ ] **Step 4: Commit**

  ```bash
  git add skills/inbox-fetcher/scripts/fetch_inbox.py skills/inbox-fetcher/SKILL.md
  git commit -m "fix(docs): update stale flat-PDF path references to current folder layout"
  ```

---

## Final verification (Phase 1)

- [ ] Full test suite passes:
  ```bash
  pytest tests/ -v
  ```
  Expected: all tests green, including the new tests added in Tasks 3, 4, 5, 6.

- [ ] Bootstrap smoke-test:
  ```bash
  python init_vault.py /tmp/vault-test
  ls /tmp/vault-test/.claude/skills/inbox-fetcher/scripts/
  ```
  Expected: `adopt_drop.py` is present.

- [ ] CLAUDE.md count check:
  ```bash
  grep -c "^| [A-Z]" CLAUDE.md
  ```
  Expected: 9 (FETCH, LINT, VIEW, INGEST, QUERY, REFLECT, PROMOTE, REFRESH, FORGET).

- [ ] No bare adopt_drop paths in commands:
  ```bash
  grep -rn "skills/inbox-fetcher/scripts/adopt_drop" commands/ skills/
  ```
  Expected: every match starts with `.claude/skills/…`
