# LLM Wiki — Correctness Fixes + Documentation Restructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix correctness gaps in the vault engine and restructure the three documentation files around a single-source-of-truth model to permanently stop drift.

**Architecture:** Pure editing — no new modules or abstractions. Changes are isolated to 7–8 files: two Python files (init_vault.py, vault_state.py), one YAML config, one test file, and three documentation files. The order is independence-first: config fix → installer → all-CLAUDE.md → GETTING-STARTED → README → verify.

**Tech Stack:** Python 3.10+, pytest. All doc edits are plain Markdown. No new dependencies.

---

## Repo orientation (read before starting)

This repo is the **template/installer** — NOT a live vault. `init_vault.py` mints deployed vaults into `./second-brain-vault/` (gitignored). The source tree has no `raw/`, `wiki/`, or `inbox.md`.

Critical file map:

| File | Role |
|---|---|
| `init_vault.py` | Bootstrapper. `install_skills()` lines 338–382 has hardcoded script lists. `print_done()` line 472 has a banner with a broken compass.md reference. |
| `skills/shared/vault_state.py` | Config loader. `_DEFAULTS` dict (lines 42–75) mirrors **all** config sections — including LLM-layer-only ones. `review:` must be added here. |
| `vault.config.yml` | Config template (45 lines). `ingest:` block at lines 38–40 is the last section; `review:` goes after it. |
| `tests/test_installer.py` | 4 simple assertions. New auto-discovery tests go here. |
| `CLAUDE.md` | 442-line agent contract. `## Six invariants` line 42; `## Twelve operations` line 144; `## Session start` step 3 lines 357–359; dispatch table lines 317–333; Backlog block line 414. |
| `GETTING-STARTED.md` | 260-line human onboarding. `## Twelve operations` line 75; `## Sixteen slash commands` line 97; `## Six rules the agent follows` line 206. |
| `README.md` | 212-line landing page. `## Design principles` line 127; quick-start section ends ~line 110. |

Run all tests with: `python -m pytest tests/ -v` (from repo root `D:\my-2nd-brain`).

---

## Task 1: A3 — Document `review.max_faithfulness_pages` in config

**Files:**
- Modify: `vault.config.yml`
- Modify: `skills/shared/vault_state.py`

**Why:** `commands/review.md` reads `vault.config.review.max_faithfulness_pages` (defaults to 10 if absent). There is no `review:` section in `vault.config.yml` or `_DEFAULTS` — the knob is invisible to users who customize the config. Every other config section (including LLM-layer-only ones like `ingest:`) is mirrored in `_DEFAULTS`, so `review:` must be added to both.

- [ ] **Step 1: Add `review:` block to `vault.config.yml`**

  Open `vault.config.yml`. The file currently ends at line 45:
  ```yaml
  drop_zone:
    path: raw/drop
    enabled: true
  ```
  
  Append after the `drop_zone:` block (at the end of file):
  ```yaml
  
  # ── Keys below are honored by the LLM/command layer, NOT by any script ────────
  review:
    # Max pages to run the claim-faithfulness check against per /review run.
    # Increase for thorough audits; decrease to control token spend.
    max_faithfulness_pages: 10
  ```

  **After:** the file ends with:
  ```yaml
  drop_zone:
    path: raw/drop
    enabled: true

  # ── Keys below are honored by the LLM/command layer, NOT by any script ────────
  review:
    # Max pages to run the claim-faithfulness check against per /review run.
    # Increase for thorough audits; decrease to control token spend.
    max_faithfulness_pages: 10
  ```

- [ ] **Step 2: Mirror `review:` in `_DEFAULTS` in `vault_state.py`**

  Open `skills/shared/vault_state.py`. Find `_DEFAULTS` (line 42). Currently the last entry is `"drop_zone"`. Add `"review"` after it:
  
  Find this exact block (lines 71–75):
  ```python
      "drop_zone": {
          "path": "raw/drop",
          "enabled": True,
      },
  }
  ```
  
  Replace with:
  ```python
      "drop_zone": {
          "path": "raw/drop",
          "enabled": True,
      },
      "review": {
          "max_faithfulness_pages": 10,
      },
  }
  ```

- [ ] **Step 3: Run the full test suite to confirm no regressions**

  ```bash
  cd D:\my-2nd-brain
  python -m pytest tests/test_vault_state.py tests/test_installer.py -v
  ```
  
  Expected: all existing tests pass. No new failures.

- [ ] **Step 4: Commit**

  ```bash
  git add vault.config.yml skills/shared/vault_state.py
  git commit -m "config: add documented review: block to vault.config.yml and _DEFAULTS"
  ```

---

## Task 2: A2 — Installer script auto-discovery

**Files:**
- Modify: `init_vault.py`
- Modify: `tests/test_installer.py`

**Why:** `install_skills()` enumerates exact script filenames. Add a new `.py` under `skills/` without updating the list → silently omitted. Replace with auto-discovery that copies every `.py` directly under each skill's `scripts/` dir (excluding `test_*.py` and `*_test.py`).

- [ ] **Step 1: Write the failing test (auto-discovery picks up new script)**

  Open `tests/test_installer.py`. Add at the end of the file:

  ```python
  
  
  class TestAutoDiscover:
      """Tests for script auto-discovery in install_skills."""
  
      def _minimal_bundle(self, tmp_path, extra_scripts=None, excluded_scripts=None):
          """Create a minimal bundle with inbox-fetcher skill only."""
          bundle = tmp_path / "bundle"
          skill_scripts = bundle / "skills" / "inbox-fetcher" / "scripts"
          skill_scripts.mkdir(parents=True)
          (bundle / "skills" / "inbox-fetcher" / "SKILL.md").write_text("# Skill\npackages: []")
          # Always include the real script so install_skills has something
          (skill_scripts / "fetch_inbox.py").write_text("# fetch")
          for name in (extra_scripts or []):
              (skill_scripts / name).write_text(f"# {name}")
          for name in (excluded_scripts or []):
              (skill_scripts / name).write_text(f"# {name}")
          # Stubs for other skills so install_skills doesn't warn
          for skill in ["vault-linter", "view-builder"]:
              (bundle / "skills" / skill).mkdir(parents=True)
              (bundle / "skills" / skill / "SKILL.md").write_text("# Skill\npackages: []")
          (bundle / "skills" / "shared").mkdir(parents=True)
          return bundle
  
      def _minimal_target(self, tmp_path):
          """Create a minimal target vault with required .claude/ dirs."""
          target = tmp_path / "vault"
          for d in [
              ".claude/skills/inbox-fetcher/scripts",
              ".claude/skills/vault-linter/scripts",
              ".claude/skills/view-builder/templates",
              ".claude/skills/shared",
          ]:
              (target / d).mkdir(parents=True)
          return target
  
      def test_auto_discovers_new_script(self, tmp_path):
          """A new .py file in scripts/ is installed even if not in any hardcoded list."""
          bundle = self._minimal_bundle(tmp_path, extra_scripts=["_probe.py"])
          target = self._minimal_target(tmp_path)
  
          init_vault.install_skills(target, bundle)
  
          installed = target / ".claude" / "skills" / "inbox-fetcher" / "scripts" / "_probe.py"
          assert installed.exists(), "_probe.py was not installed"
  
      def test_original_scripts_still_installed(self, tmp_path):
          """Existing scripts are still installed after switching to auto-discovery."""
          bundle = self._minimal_bundle(tmp_path)
          target = self._minimal_target(tmp_path)
  
          init_vault.install_skills(target, bundle)
  
          assert (target / ".claude" / "skills" / "inbox-fetcher" / "scripts" / "fetch_inbox.py").exists()
  
      def test_test_files_excluded(self, tmp_path):
          """test_*.py files are NOT installed."""
          bundle = self._minimal_bundle(tmp_path, excluded_scripts=["test_probe.py"])
          target = self._minimal_target(tmp_path)
  
          init_vault.install_skills(target, bundle)
  
          excluded = target / ".claude" / "skills" / "inbox-fetcher" / "scripts" / "test_probe.py"
          assert not excluded.exists(), "test_probe.py was incorrectly installed"
  ```

- [ ] **Step 2: Run the new tests to confirm they FAIL**

  ```bash
  python -m pytest tests/test_installer.py::TestAutoDiscover -v
  ```
  
  Expected: `test_auto_discovers_new_script` FAILS because current code uses hardcoded list and `_probe.py` is not in it. `test_test_files_excluded` passes (coincidentally, since `test_probe.py` also isn't in the hardcoded list). Note which tests fail.

- [ ] **Step 3: Add `_discover_scripts` helper to `init_vault.py`**

  Open `init_vault.py`. Find the line (around line 325):
  ```python
  def install_commands(vault: Path, script_dir: Path) -> None:
  ```
  
  Insert the new helper function BEFORE `install_commands`:
  ```python
  def _discover_scripts(scripts_dir: Path) -> list[Path]:
      """Return .py files directly in scripts_dir, excluding test files.
  
      Only files at the top level of scripts_dir are included (no subdirs).
      Excluded: test_*.py and *_test.py patterns.
      """
      if not scripts_dir.is_dir():
          return []
      return sorted(
          f for f in scripts_dir.iterdir()
          if f.is_file()
          and f.suffix == ".py"
          and not f.name.startswith("test_")
          and not f.name.endswith("_test.py")
      )
  
  
  ```

- [ ] **Step 4: Replace `install_skills` with auto-discovery version**

  In `init_vault.py`, replace the entire `install_skills` function (lines 338–382) with:

  ```python
  def install_skills(vault: Path, script_dir: Path) -> None:
      info("Installing skills")
  
      for skill_name in ["inbox-fetcher", "vault-linter", "view-builder"]:
          src_dir = script_dir / "skills" / skill_name
          dst_dir = vault / ".claude" / "skills" / skill_name
          if not src_dir.is_dir():
              warn(f"{skill_name} skill not found in bundle")
              continue
          shutil.copy2(src_dir / "SKILL.md", dst_dir / "SKILL.md")
  
          scripts_src = src_dir / "scripts"
          if scripts_src.is_dir():
              py_files = _discover_scripts(scripts_src)
              if not py_files:
                  warn(f"{skill_name}/scripts/ exists but has no installable .py files")
              for src_py in py_files:
                  dst_py = dst_dir / "scripts" / src_py.name
                  shutil.copy2(src_py, dst_py)
                  if os.name != "nt":
                      os.chmod(dst_py, 0o755)
  
          if skill_name == "view-builder":
              templates_src = src_dir / "templates"
              if templates_src.is_dir():
                  for f in templates_src.iterdir():
                      if f.is_file():
                          shutil.copy2(f, dst_dir / "templates" / f.name)
  
          ok(f"skill: {skill_name}")
  
      # Shared utilities — auto-discover from skills/shared/
      shared_src = script_dir / "skills" / "shared"
      shared_dst = vault / ".claude" / "skills" / "shared"
      py_files = _discover_scripts(shared_src)
      if not py_files:
          warn("skills/shared/ has no installable .py files")
      for src_py in py_files:
          shutil.copy2(src_py, shared_dst / src_py.name)
          ok(f"shared: {src_py.name}")
  ```

- [ ] **Step 5: Run all installer tests**

  ```bash
  python -m pytest tests/test_installer.py -v
  ```
  
  Expected: ALL 7 tests pass (4 original + 3 new). If any original test fails, investigate — the existing tests are `test_split_in_commands`, `test_split_md_exists`, `test_retry_in_commands`, `test_retry_md_exists` which test the `COMMANDS` list and source files, not `install_skills` — they should be unaffected.

- [ ] **Step 6: Run the full test suite**

  ```bash
  python -m pytest tests/ -v
  ```
  
  Expected: all 11 test modules green.

- [ ] **Step 7: Commit**

  ```bash
  git add init_vault.py tests/test_installer.py
  git commit -m "feat(installer): auto-discover scripts in install_skills instead of hardcoded list"
  ```

---

## Task 3: All CLAUDE.md changes

**Files:**
- Modify: `CLAUDE.md`

**Covers:** A1 (session-start compass conditional), A4 (heading rename), B1 (tiered invariants), B3 (template note), B4 (dispatch table paths + tooling separator).

Do all edits in one pass on this file. Each step is one Edit call.

- [ ] **Step 1: Add template-vs-vault note at top of Vault structure section (B3)**

  Find this line in `CLAUDE.md` (line 15):
  ```
  ## Vault structure
  ```
  
  Replace with:
  ```markdown
  ## Vault structure
  
  > *Note: paths beginning with `.claude/` refer to the deployed vault layout after
  > `init_vault.py` installs commands and skills there — not to this template repository.*
  ```

- [ ] **Step 2: Replace "Six invariants" with tiered invariants section (B1)**

  Find this entire block (lines 42–58):
  ```
  ## Six invariants — never break these
  
  1. **Never write to `raw/`.** Only scripts add files there: `fetch_inbox.py`
     writes to `raw/papers/` and `raw/web/`; `adopt_drop.py` writes to
     `raw/local/`. The LLM never writes to `raw/` except for one case:
     during `/ingest` pre-flight the LLM may update `raw/local/<slug>/index.md`
     to apply user-supplied tags and notes before reading the PDF.
  2. **Every claim cites a source.** Either a wiki page link `[[wiki/...]]`
     or a `raw/` path. No orphan claims.
  3. **Paraphrase, don't copy.** Summaries must be in your own words.
  4. **User curates, you maintain.** No auto-ingesting new sources, no
     auto-applying structural changes, no creating views without asking.
  5. **Touch ≤15 files per operation.** If more are needed, tell the user
     and let them choose what matters.
  6. **Update `wiki/index.md` and `wiki/log.md`** after any writing operation —
     add new source/page/view entries to `wiki/index.md`; append an operation line
     to `wiki/log.md`.
  ```
  
  Replace with:
  ```markdown
  ## Invariants and operating rules
  
  ### Hard invariants — never break these
  
  These are integrity guarantees. Violating them corrupts the vault's truthfulness.
  
  1. **Never write to `raw/`.** Only scripts add files there: `fetch_inbox.py`
     writes to `raw/papers/` and `raw/web/`; `adopt_drop.py` writes to
     `raw/local/`. The LLM never writes to `raw/` except for one case:
     during `/ingest` pre-flight the LLM may update `raw/local/<slug>/index.md`
     to apply user-supplied tags and notes before reading the PDF.
  2. **Every claim cites a source.** Either a wiki page link `[[wiki/...]]`
     or a `raw/` path. No orphan claims.
  3. **Paraphrase, don't copy.** Summaries must be in your own words.
  
  ### Operating rules
  
  These govern how the agent works. They are firm defaults, not absolute
  constraints — deviating requires an explicit user instruction.
  
  - **User curates, agent maintains.** No auto-ingesting new sources, no
    auto-applying structural changes, no creating views without asking.
  - **Touch ≤15 files per operation.** If more are needed, tell the user
    and let them choose what matters.
  - **Update `wiki/index.md` and `wiki/log.md`** after any writing operation —
    add new source/page/view entries to `wiki/index.md`; append an operation line
    to `wiki/log.md`.
  - **`shareable: true` views are frozen.** Don't silently update a frozen view.
    When `shareable: false` (default), the view evolves in place.
  ```

- [ ] **Step 3: Rename "Twelve operations" heading (A4)**

  Find (line 144):
  ```
  ## Twelve operations
  ```
  Replace with:
  ```
  ## Operations
  ```

- [ ] **Step 4: Fix FORGET's invariant cross-references (consequence of B1)**

  The FORGET section references `invariant #5` and `invariant #6` by number. After the tiered restructure, these are no longer numbered. Update them to prose references.
  
  Find:
  ```
  6. Update `wiki/index.md` and `wiki/log.md` (invariant #6).
  7. Run `vault-linter` to confirm zero dead links remain.
  
  If the source is cited by >15 files, the cascade exceeds invariant #5
  — stop, report the fanout, let the user pick scope (full cascade over
  multiple passes, or leave citations dangling for the linter).
  ```
  
  Replace with:
  ```
  6. Update `wiki/index.md` and `wiki/log.md` (operating rule: update after writes).
  7. Run `vault-linter` to confirm zero dead links remain.
  
  If the source is cited by >15 files, the cascade exceeds the 15-file operating rule
  — stop, report the fanout, let the user pick scope (full cascade over
  multiple passes, or leave citations dangling for the linter).
  ```

- [ ] **Step 5: Fix MERGE's invariant cross-reference (consequence of B1)**

  Find in the MERGE section:
  ```
  resolve near-duplicate pages by merging them into a canonical page (or splitting
  an overgrown one), with full backlink rewriting. Guards: stops if fanout > 15
  files (Invariant #5); asks before deleting any prose; never silently touches
  `shareable: true` views. See `.claude/commands/merge.md` for MERGE. For SPLIT, see `.claude/commands/split.md`.
  ```
  
  Replace with:
  ```
  resolve near-duplicate pages by merging them into a canonical page (or splitting
  an overgrown one), with full backlink rewriting. Guards: stops if fanout > 15
  files (15-file operating rule); asks before deleting any prose; never silently
  touches `shareable: true` views. See `.claude/commands/merge.md` for MERGE. For SPLIT, see `.claude/commands/split.md`.
  ```

- [ ] **Step 6: Fix dispatch table to use full repo-relative paths (B4)**

  Find this entire table (lines 317–333):
  ```
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
  | EXPAND    | (LLM only)     | —                              |
  | FORGET    | (LLM only)     | —                              |
  | REVIEW    | (LLM only)     | —                              |
  | MERGE     | (LLM only)     | find_backlinks.py              |
  | SPLIT     | (LLM only)     | find_backlinks.py              |
  ```
  
  Replace with:
  ```
  | Operation | Skill          | Backed by                                               |
  |-----------|----------------|---------------------------------------------------------|
  | FETCH     | inbox-fetcher  | skills/inbox-fetcher/scripts/fetch_inbox.py             |
  | LINT      | vault-linter   | skills/vault-linter/scripts/lint.py                     |
  | VIEW      | view-builder   | skills/view-builder/templates/ + LLM                    |
  | INGEST    | (LLM only)     | skills/inbox-fetcher/scripts/adopt_drop.py (pre-flight) |
  | QUERY     | (LLM only)     | —                                                       |
  | REFLECT   | (LLM only)     | —                                                       |
  | PROMOTE   | (LLM only)     | —                                                       |
  | REFRESH   | (LLM only)     | —                                                       |
  | EXPAND    | (LLM only)     | —                                                       |
  | FORGET    | (LLM only)     | —                                                       |
  | REVIEW    | (LLM only)     | —                                                       |
  | MERGE     | (LLM only)     | skills/shared/find_backlinks.py                         |
  | SPLIT     | (LLM only)     | skills/shared/find_backlinks.py                         |
  ```

- [ ] **Step 7: Fix session-start step 3 for compass.md (A1)**

  Find (lines 357–359):
  ```
  3. Read the `updated` field from `wiki/compass.md` frontmatter. If the file is
     absent or its `updated` date is more than `lint.reflect_reminder_days` days
     ago, suggest running `/reflect`.
  ```
  
  Replace with:
  ```
  3. Check whether `wiki/compass.md` exists.
     - **If absent** (e.g. fresh vault, `/reflect` not yet run): suggest running
       `/reflect` to create it. No further action needed this step.
     - **If present**: read its `updated` frontmatter field. If `updated` is more
       than `lint.reflect_reminder_days` days ago, suggest running `/reflect`.
  ```

- [ ] **Step 8: Add tooling separator before Backlog block (B4)**

  Find (line 414):
  ```
  <!-- BACKLOG.MD MCP GUIDELINES START -->
  ```
  
  Replace with:
  ```
  <!-- ───── Tooling config below — not part of the vault contract ───── -->
  <!-- BACKLOG.MD MCP GUIDELINES START -->
  ```

- [ ] **Step 9: Quick visual check of CLAUDE.md**

  Run:
  ```bash
  python -c "
  text = open('CLAUDE.md', encoding='utf-8').read()
  assert '## Six invariants' not in text, 'Old heading still present'
  assert '## Invariants and operating rules' in text, 'New heading missing'
  assert '## Twelve operations' not in text, 'Old count heading still present'
  assert '## Operations' in text, 'Renamed heading missing'
  assert 'skills/inbox-fetcher/scripts/fetch_inbox.py' in text, 'Dispatch table not fixed'
  assert 'If absent' in text, 'Session-start compass fix missing'
  print('CLAUDE.md checks passed')
  "
  ```
  
  Expected output: `CLAUDE.md checks passed`

- [ ] **Step 10: Commit**

  ```bash
  git add CLAUDE.md
  git commit -m "docs(CLAUDE.md): tiered invariants, heading renames, dispatch paths, compass conditional, template note"
  ```

---

## Task 4: GETTING-STARTED.md changes

**Files:**
- Modify: `GETTING-STARTED.md`

**Covers:** A4 (heading renames), B1 (remove numbered rules, add narrative), B2 (curate command list, remove duplicate Karpathy framing).

- [ ] **Step 1: Trim the duplicate Karpathy intro (B2)**

  Find the "What this is" section (lines 7–14):
  ```
  A personal knowledge vault, maintained by an AI agent, based on
  [Andrej Karpathy's LLM Wiki idea](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
  
  You curate sources. The agent reads them, compiles a wiki, answers
  your questions, builds timelines and slides when you ask, and
  periodically reflects on where your thinking is going.
  
  The agent does the bookkeeping. You do the thinking.
  ```
  
  Replace with:
  ```
  A personal knowledge vault, maintained by an AI agent. You curate
  sources. The agent reads them, compiles a wiki, answers your questions,
  builds timelines and slides when you ask, and periodically reflects on
  where your thinking is going.
  
  The agent does the bookkeeping. You do the thinking.
  
  For the origin story, installation instructions, and update path, see [README.md](README.md).
  ```

- [ ] **Step 2: Rename "Twelve operations" heading (A4)**

  Find (line 75):
  ```
  ## Twelve operations
  
  The agent knows how to do twelve things. You trigger them in plain
  language or with a slash command.
  ```
  
  Replace with:
  ```
  ## Operations
  
  The agent knows a set of operations. You trigger them in plain language
  or with a slash command.
  ```

- [ ] **Step 3: Add operations-vs-commands reconciliation sentence (A4)**

  The operations table ends just before `## Sixteen slash commands`. Find:
  ```
  | 12 | **EXPAND** | `/expand <page>` or *"expand this page"* | Read cited source(s) in full and append a `## Deep dive` section to the page for in-depth treatment. Overview sections remain unchanged. Interactive only; never available unattended |
  
  ---
  
  ## Sixteen slash commands
  ```
  
  Replace with:
  ```
  | 12 | **EXPAND** | `/expand <page>` or *"expand this page"* | Read cited source(s) in full and append a `## Deep dive` section to the page for in-depth treatment. Overview sections remain unchanged. Interactive only; never available unattended |
  
  Four commands — `/retry`, `/save`, `/hot`, `/playwright-fetch` — are utilities
  and sub-steps rather than top-level operations; that's why the slash-command count
  is higher than the operation count.
  
  ---
  
  ## Slash commands
  ```

- [ ] **Step 4: Replace the full 16-command list with a curated core list (B2)**

  Find the entire "Sixteen slash commands" content block (lines 99–146 after the heading rename):
  ```
  - **`/fetch`** — process the URL queue in `inbox.md`. Run this before
    `/ingest` — ingest needs the raw files that fetch downloads.
  - **`/retry`** — re-attempt only previously-failed (`⚠`-marked) inbox
    entries. Use after a transient network failure or once a blocked URL
    becomes accessible. Never touches plain unchecked or already-processed
    entries.
  - **`/ingest [slug]`** — compile raw sources into the wiki. Without a
    slug, first adopts any PDFs or Markdown files waiting in `raw/drop/` (prompts once for
    tags/notes), then discovers all uningested sources and confirms before starting.
  - **`/playwright-fetch`** — retrieve walled, paywalled, or JS-rendered
    URLs that `/fetch` couldn't download. One URL at a time, with your
    confirmation per URL.
  - **`/save [name]`** — save the current conversation to
    `conversations/`. These feed `/reflect` and `/promote` later.
  - **`/view [kind] [topic]`** — build a view. Kinds: `timeline`,
    `comparison`, `concept-map`, `chart`, `slides`, `report`, `post`.
  - **`/reflect`** — write `compass.md`: where my thinking is going,
    what I'm not looking at, one question worth sitting with.
  - **`/forget <source>`** — cascade-remove a source. Interactive:
    per-claim decisions, never deletes prose without asking.
  - **`/lint`** — run deterministic vault health checks. Also triggers
    automatically after 5 fetches or 7 days.
  - **`/promote [slug] [page]`** — lift synthesis claims from a saved
    conversation into a wiki page, with full citation. Interactive only.
  - **`/refresh <source>`** — re-fetch a source whose content has
    changed, re-ingest it, and flag pages that may need review.
  - **`/expand <page>`** — deepen an existing page by reading its cited
    source(s) in full and appending a `## Deep dive` section. Leaves
    the overview sections intact. Interactive only. Use `/review` to
    discover which pages are thin enough to benefit.
  - **`/review [scope]`** — semantic health pass: checks for
    contradictions between pages, claims that don't trace to their
    source, and thin/copied summaries. Report-only (proposes fixes,
    never applies them). Scoped to changed pages by default; use
    `/review --all` for a full sweep (expensive, asks to confirm).
  - **`/merge <page-A> <page-B>`** — merge two near-duplicate pages
    into one canonical page with full backlink rewriting. Interactive:
    shows a content diff, asks for direction and title, checks fanout
    (stops if >15 files linked), rewrites all link forms including
    aliased `[[page|Display]]` links. Closes the loop on `check_duplicates`
    lint findings and `/review` contradiction findings.
  - **`/split <page> <new-page-A> <new-page-B>`** — split an overgrown
    page into two focused ones. Fanout check before any writes; asks
    per-link when the destination is ambiguous. Inverse of `/merge`.
  - **`/hot`** — flush session state to `wiki/hot.md`. The agent runs
    this automatically at the end of any writing session.
  
  For everything else, just ask in plain language.
  ```
  
  Replace with:
  ```
  The commands you'll use most in the first weeks:
  
  - **`/fetch`** — process the URL queue in `inbox.md`. Run this before
    `/ingest` — ingest needs the raw files that fetch downloads.
  - **`/ingest [slug]`** — compile raw sources into the wiki. Without a
    slug, first adopts any PDFs or Markdown files waiting in `raw/drop/`
    (prompts once for tags/notes), then discovers all uningested sources
    and confirms before starting.
  - **`/save [name]`** — save the current conversation to
    `conversations/`. These feed `/reflect` and `/promote` later.
  - **`/reflect`** — write `compass.md`: where my thinking is going,
    what I'm not looking at, one question worth sitting with.
  - **`/lint`** — run deterministic vault health checks. Also triggers
    automatically after 5 fetches or 7 days.
  - **`/expand <page>`** — deepen an existing page by reading its cited
    source(s) in full and appending a `## Deep dive` section. Leaves
    the overview sections intact. Interactive only.
  - **`/review [scope]`** — semantic health pass: contradictions, claim
    faithfulness, thin summaries. Report-only; scoped to changed pages
    by default.
  
  For the complete reference — including `/retry`, `/playwright-fetch`,
  `/forget`, `/promote`, `/refresh`, `/merge`, `/split`, `/view`, and
  `/hot` — see [CLAUDE.md — Slash commands](CLAUDE.md#slash-commands).
  
  For everything else, just ask in plain language.
  ```

- [ ] **Step 5: Replace "Six rules the agent follows" with narrative (B1)**

  Find the entire "Six rules" section (lines 206–219):
  ```
  ## Six rules the agent follows
  
  These are invariants. The agent won't break them. Good to know they
  exist:
  
  1. **`raw/` is immutable.** Scripts write there (`fetch_inbox.py`, `adopt_drop.py`) — the agent generally doesn't.
  2. **Every claim cites a source.** No orphan claims in the wiki.
  3. **Paraphrase, don't copy.** Summaries are in the agent's words.
  4. **You curate, it maintains.** No auto-fetching, no silent
     structural changes, no views without your request.
  5. **`shareable: true` views are frozen.** New version = new dated
     file. Everything else can evolve in place.
  6. **Touch ≤15 files per operation.** If more are needed, the agent
     stops and asks — split across sessions.
  ```
  
  Replace with:
  ```
  ## How the agent behaves
  
  The agent follows a set of hard invariants and operating rules defined
  in [CLAUDE.md — Invariants and operating rules](CLAUDE.md#invariants-and-operating-rules).
  
  The short version: it keeps `raw/` immutable, cites every claim,
  paraphrases rather than copies, and asks before making structural
  changes. It touches at most 15 files in a single operation and keeps
  `wiki/index.md` and `wiki/log.md` up to date after every write.
  `shareable: true` views are frozen snapshots the agent won't silently
  change.
  
  If the agent does something unexpected, it's worth checking those
  rules — they're designed to be strict.
  ```

- [ ] **Step 6: Verify no old count-headings remain**

  ```bash
  python -c "
  text = open('GETTING-STARTED.md', encoding='utf-8').read()
  assert 'Twelve operations' not in text, 'Old count heading still present'
  assert 'Sixteen slash commands' not in text, 'Old count heading still present'
  assert 'Six rules' not in text, 'Old six-rules section still present'
  assert 'Operations' in text, 'Operations heading missing'
  assert 'Slash commands' in text, 'Slash commands heading missing'
  assert 'CLAUDE.md' in text, 'Link to CLAUDE.md missing'
  print('GETTING-STARTED.md checks passed')
  "
  ```
  
  Expected: `GETTING-STARTED.md checks passed`

- [ ] **Step 7: Anti-hollowing check — read the file as its target audience**

  Read through `GETTING-STARTED.md` as a new user who just installed the vault.
  Confirm it still provides:
  - The concept diagram (diagram should be intact)
  - The three-type model table (should be intact)
  - The operations table (should be intact with 12 rows)
  - A usable subset of commands for the first week (the 7-command curated list)
  - First week / first month guidance (should be intact)
  - Common questions FAQ (should be intact)
  
  The file should NOT feel hollow or redirect-only. Adjust if it does.

- [ ] **Step 8: Commit**

  ```bash
  git add GETTING-STARTED.md
  git commit -m "docs(GETTING-STARTED): remove duplicated invariants/command lists, add links to CLAUDE.md"
  ```

---

## Task 5: README.md changes

**Files:**
- Modify: `README.md`

**Covers:** B1 (replace numbered "six invariants" with unnumbered teaser + link), B2 (trim duplicate Karpathy framing), B3 (add template-vs-vault section).

- [ ] **Step 1: Add the "template, not a vault" section (B3)**

  The quick-start section ends and the "The core idea" section starts at line ~113. Find:
  ```
  ## The core idea, in one paragraph
  ```
  
  Insert a new section BEFORE it:
  ```markdown
  ## This repo is the template, not a vault
  
  Cloning this repo gives you the **engine**. Live content — `raw/`, `wiki/`,
  `inbox.md` — exists only in a *deployed vault* created by `init_vault.py`
  (default target: `./second-brain-vault/`, gitignored).
  
  The `.claude/...` paths that appear throughout `CLAUDE.md` (e.g.
  `.claude/commands/ingest.md`, `.claude/skills/vault-linter/`) refer to the
  deployed vault layout after `init_vault.py` installs commands and skills
  there — not to this template repository.
  
  `AGENTS.md` is generated at bootstrap as a copy of (or symlink to) `CLAUDE.md`.
  It is not committed to this repo.
  
  ---
  
  ## The core idea, in one paragraph
  ```

- [ ] **Step 2: Replace "Design principles" with unnumbered teaser + link (B1)**

  Find the entire "Design principles" section (lines 127–139):
  ```
  ## Design principles
  
  Six invariants:
  
  1. **Raw is immutable.** If the wiki is corrupted, it's recompilable
     from `raw/` alone. Scripts (`fetch_inbox.py`, `adopt_drop.py`) write
     to `raw/` — the agent doesn't.
  2. **Every claim cites a source.** No orphan claims in the wiki.
  3. **Paraphrase, don't copy.** Summaries are in the agent's words.
  4. **You curate, the agent maintains.** No auto-fetching, no
     auto-structural changes, no views without your request.
  5. **`shareable: true` views are frozen.** Anything else evolves.
  6. **Touch ≤15 files per operation.** If more are needed, stop and ask — split the work across sessions.
  ```
  
  Replace with:
  ```markdown
  ## Design principles
  
  The vault is governed by a small set of rules the agent follows strictly.
  Hard invariants are integrity guarantees (raw is immutable, every claim
  cites a source, summaries are paraphrased). Operating rules cover how the
  agent works (you curate, it maintains; ≤15 files per operation; `wiki/index.md`
  and `wiki/log.md` updated after every write; `shareable: true` views are frozen).
  
  The authoritative set — with operating rules distinguished from hard invariants —
  is in [CLAUDE.md — Invariants and operating rules](CLAUDE.md#invariants-and-operating-rules).
  ```

- [ ] **Step 3: Verify README is not hollow**

  Read README.md from top to bottom as a GitHub visitor deciding whether to install this tool. Confirm it still provides:
  - What the project is (one-liner + intro)
  - The bundle directory tree
  - Quick start and update instructions
  - The "template not a vault" explainer (new)
  - The core idea paragraph
  - Design principles teaser + link
  - Dependencies
  - Troubleshooting
  - AGENTS.md note (should now be in both troubleshooting and the new template section)
  
  It should NOT be hollow. If trimming B2 removed useful framing, restore it.

- [ ] **Step 4: Verify no old count-headings remain**

  ```bash
  python -c "
  text = open('README.md', encoding='utf-8').read()
  assert 'Six invariants' not in text, 'Old six-invariants text still present'
  assert 'template, not a vault' in text, 'New template section missing'
  assert 'CLAUDE.md' in text, 'Link to CLAUDE.md missing'
  print('README.md checks passed')
  "
  ```
  
  Expected: `README.md checks passed`

- [ ] **Step 5: Commit**

  ```bash
  git add README.md
  git commit -m "docs(README): add template-vs-vault section, replace numbered invariants with teaser+link"
  ```

---

## Task 6: init_vault.py banner fix (A1)

**Files:**
- Modify: `init_vault.py`

**Why:** `print_done()` step 7 says `"  7. Periodically: /reflect → read wiki/compass.md"`. On a fresh vault, `compass.md` doesn't exist yet — `/reflect` creates it. The banner should tell users to *run* `/reflect`, not read a file that isn't there.

- [ ] **Step 1: Fix the banner**

  Find in `init_vault.py` `print_done()` (line 472):
  ```python
      print( "  7. Periodically: /reflect → read wiki/compass.md")
  ```
  
  Replace with:
  ```python
      print( "  7. Periodically: run /reflect to track your thinking and write wiki/compass.md")
  ```

- [ ] **Step 2: Smoke-test bootstrap on temp dir (A1 verification)**

  ```bash
  python init_vault.py D:\temp-vault-smoke --yes
  ```
  
  Expected:
  - Vault scaffolded successfully
  - Banner step 7 does NOT say "read wiki/compass.md"
  - `wiki/hot.md`, `wiki/index.md`, `wiki/log.md` exist
  - `wiki/compass.md` does NOT exist (correct for fresh vault)
  - No error output
  
  Then clean up:
  ```bash
  Remove-Item -Recurse -Force D:\temp-vault-smoke
  ```

- [ ] **Step 3: Run full test suite**

  ```bash
  python -m pytest tests/ -v
  ```
  
  Expected: all green.

- [ ] **Step 4: Commit**

  ```bash
  git add init_vault.py
  git commit -m "fix(installer): banner step 7 — point to /reflect, not to non-existent compass.md"
  ```

---

## Task 7: Verification — doc consistency + full suite

- [ ] **Step 1: Full pytest**

  ```bash
  python -m pytest tests/ -v
  ```
  
  Expected: 11 test modules, all green. Note the count — it should be more than before (we added 3 test cases in Task 2).

- [ ] **Step 2: Grep for old count-headings across all three docs**

  ```bash
  python -c "
  import re, pathlib
  docs = ['CLAUDE.md', 'README.md', 'GETTING-STARTED.md']
  old_patterns = ['Six invariants', 'Twelve operations', 'Sixteen slash commands',
                  'six invariants', 'twelve operations', 'sixteen slash commands',
                  'Six rules']
  found = []
  for doc in docs:
      text = pathlib.Path(doc).read_text(encoding='utf-8')
      for pat in old_patterns:
          if pat in text:
              found.append(f'{doc}: found \"{pat}\"')
  if found:
      print('DRIFT RISK:')
      for f in found:
          print(' ', f)
  else:
      print('No old count-heading strings found — drift eliminated.')
  "
  ```
  
  Expected: `No old count-heading strings found — drift eliminated.`

- [ ] **Step 3: Confirm single authoritative invariants list**

  ```bash
  python -c "
  import pathlib
  claude = pathlib.Path('CLAUDE.md').read_text(encoding='utf-8')
  gs = pathlib.Path('GETTING-STARTED.md').read_text(encoding='utf-8')
  readme = pathlib.Path('README.md').read_text(encoding='utf-8')
  
  # CLAUDE.md must have the canonical tiered section
  assert '## Invariants and operating rules' in claude, 'CLAUDE.md missing tiered invariants'
  assert '### Hard invariants' in claude, 'CLAUDE.md missing hard-invariants subheading'
  assert '### Operating rules' in claude, 'CLAUDE.md missing operating-rules subheading'
  
  # Others must link to CLAUDE.md, not re-enumerate
  assert '## Invariants and operating rules' not in gs, 'GS re-defines invariants'
  assert '## Invariants and operating rules' not in readme, 'README re-defines invariants'
  assert 'CLAUDE.md' in gs, 'GS does not link to CLAUDE.md'
  assert 'CLAUDE.md' in readme, 'README does not link to CLAUDE.md'
  
  print('Single-source-of-truth invariants: OK')
  "
  ```
  
  Expected: `Single-source-of-truth invariants: OK`

- [ ] **Step 4: Link check — no obviously broken markdown links**

  ```bash
  python -c "
  import re, pathlib
  docs = ['CLAUDE.md', 'README.md', 'GETTING-STARTED.md']
  # Check that any CLAUDE.md#anchor links reference anchors that exist
  anchor_pattern = re.compile(r'\[.*?\]\(CLAUDE\.md#([\w-]+)\)')
  claude_text = pathlib.Path('CLAUDE.md').read_text(encoding='utf-8')
  
  for doc in docs:
      text = pathlib.Path(doc).read_text(encoding='utf-8')
      for m in anchor_pattern.finditer(text):
          anchor = m.group(1)  # e.g. 'invariants-and-operating-rules'
          # Convert anchor to heading text (rough heuristic)
          heading_text = anchor.replace('-', ' ')
          # Check that CLAUDE.md has a heading containing these words
          if not any(heading_text.lower() in line.lower() for line in claude_text.splitlines() if line.startswith('#')):
              print(f'WARNING: {doc} links to CLAUDE.md#{anchor} but heading may not exist')
  print('Link check complete (warnings above if any)')
  "
  ```

- [ ] **Step 5: Anti-hollowing read — CLAUDE.md as the agent**

  Read `CLAUDE.md` in full (or open it in an editor). Confirm:
  - Vault structure diagram: intact
  - Hard invariants (3 numbered): all present with full prose
  - Operating rules (4 bulleted): all present with full prose
  - All 13 operation H3s (FETCH through MERGE/SPLIT): intact
  - Session start 3 steps: intact with new compass conditional
  - Unattended mode: intact
  - Slash commands: full list of 16 intact
  - "When in doubt": intact

- [ ] **Step 6: Final git status check**

  ```bash
  git status
  git log --oneline -8
  ```
  
  Expected: clean working tree. Log shows 5 new commits from this feature work.

---

## Post-implementation: Backlog task decomposition

After all tasks above are complete and verified, create atomic Backlog.md tasks covering
the implementation steps above. Per project mandate (CLAUDE.md CRITICAL_INSTRUCTION and
project memory), ALL task tracking uses Backlog.md MCP.

Before creating tasks:
1. Read `backlog://workflow/overview` or call `backlog.get_backlog_instructions()`.
2. Search existing tasks to avoid duplicates.
3. Create one task per logical unit above (one per Task 1–6 above, plus verification).

---

## Spec and plan locations

- **Spec:** `features/specs/2026-05-31-llm-wiki-correctness-docs-design.md`
- **Plan:** `features/plans/2026-05-31-llm-wiki-correctness-docs-plan.md` (this file)
- **Branch:** `feat-hotfix`
