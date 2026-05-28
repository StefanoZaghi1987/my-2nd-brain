# Vault Portability Implementation Plan

> **Status: IMPLEMENTED** — 2026-05-28, branch `feat-portability`, 28 commits. All task-0046..task-0058 completed.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix a semantic counter naming bug, align the /hot bootstrap template, normalise the python3 command across all documentation, and add a cross-platform Python bootstrap script (`init_vault.py`) so the vault can be initialised on Linux, Windows+WSL, and native Windows.

**Architecture:** Four independent work streams executed in order: (1) rename the state/config keys across Python files and tests, (2) fix the hot.md heredoc in init-vault.sh, (3) update python→python3 in all documentation, (4) create init_vault.py as a stdlib-only port of init-vault.sh.

**Tech Stack:** Python 3.10+ stdlib only (`os`, `sys`, `argparse`, `pathlib`, `shutil`, `subprocess`). No new pip dependencies. Shell (Bash) for init-vault.sh edit. Markdown for documentation edits.

---

## File Map

| File | Action | Responsible for |
|---|---|---|
| `skills/shared/vault_state.py` | Modify | Rename 2 keys in `_DEFAULTS` |
| `skills/inbox-fetcher/scripts/fetch_inbox.py` | Modify | Rename key in `process_vault()` |
| `vault.config.yml` | Modify | Rename config key |
| `CLAUDE.md` | Modify | Update session-start condition text |
| `commands/lint.md` | Modify | Rename key text + python→python3 |
| `tests/test_vault_state.py` | Modify | Rename key string literals |
| `init-vault.sh` | Modify | Fix hot.md heredoc |
| `commands/fetch.md` | Modify | python→python3 |
| `commands/refresh.md` | Modify | python→python3 |
| `skills/inbox-fetcher/SKILL.md` | Modify | python→python3 |
| `skills/vault-linter/SKILL.md` | Modify | python→python3 |
| `README.md` | Modify | Add init_vault.py + Windows python note |
| `GETTING-STARTED.md` | Modify | Add init_vault.py + Windows python note |
| `init_vault.py` | **Create** | Cross-platform vault bootstrap (~200 lines, stdlib only) |

---

## Task 1 — Rename keys in vault_state.py (task-0046)

**Files:** Modify `skills/shared/vault_state.py`

- [ ] **Step 1: Verify the two key locations**

  Open `skills/shared/vault_state.py`. Confirm these exact strings exist:
  - In `_DEFAULTS` (top-level dict): `"ingests_since_last_lint": 0`
  - In `_DEFAULTS["lint"]`: `"auto_trigger_after_ingests": 5`

- [ ] **Step 2: Run the test suite to establish baseline**

  ```bash
  pytest tests/ -v
  ```
  Expected: all tests pass.

- [ ] **Step 3: Apply the two renames**

  In `_DEFAULTS` (around line 21):
  ```python
  # Before
  "ingests_since_last_lint": 0,
  # After
  "fetches_since_last_lint": 0,
  ```

  In `_DEFAULTS["lint"]` (around line 44):
  ```python
  # Before
  "auto_trigger_after_ingests": 5,
  # After
  "auto_trigger_after_fetches": 5,
  ```

- [ ] **Step 4: Run tests to confirm no breakage**

  ```bash
  pytest tests/ -v
  ```
  Expected: all tests still pass. (The tests use explicit key strings, not the defaults, so no test directly exercises the renamed keys — they will be updated in Task 6.)

- [ ] **Step 5: Commit**

  ```bash
  git add skills/shared/vault_state.py
  git commit -m "fix: rename ingests_since_last_lint to fetches_since_last_lint in vault_state.py defaults"
  ```

---

## Task 2 — Rename key in fetch_inbox.py (task-0047)

**Files:** Modify `skills/inbox-fetcher/scripts/fetch_inbox.py`

- [ ] **Step 1: Locate the counter read/write in process_vault()**

  In `fetch_inbox.py`, search for `ingests_since_last_lint`. It appears in `process_vault()` near the bottom:
  ```python
  state = read_state(vault)
  prev = int(state.get("ingests_since_last_lint", 0))
  write_state(vault, {"ingests_since_last_lint": prev + 1})
  ```

- [ ] **Step 2: Apply the rename**

  ```python
  # Before
  prev = int(state.get("ingests_since_last_lint", 0))
  write_state(vault, {"ingests_since_last_lint": prev + 1})

  # After
  prev = int(state.get("fetches_since_last_lint", 0))
  write_state(vault, {"fetches_since_last_lint": prev + 1})
  ```

- [ ] **Step 3: Run tests**

  ```bash
  pytest tests/test_fetch_inbox.py -v
  ```
  Expected: all tests pass.

- [ ] **Step 4: Commit**

  ```bash
  git add skills/inbox-fetcher/scripts/fetch_inbox.py
  git commit -m "fix: rename ingests_since_last_lint to fetches_since_last_lint in fetch_inbox.py"
  ```

---

## Task 3 — Rename config key in vault.config.yml (task-0048)

**Files:** Modify `vault.config.yml`

- [ ] **Step 1: Apply the rename**

  In `vault.config.yml`, under the `lint:` section:
  ```yaml
  # Before
  auto_trigger_after_ingests: 5      # run lint automatically after N ingests

  # After
  auto_trigger_after_fetches: 5      # run lint automatically after N fetches
  ```

- [ ] **Step 2: Run tests (vault_state.py parses this file)**

  ```bash
  pytest tests/test_vault_state.py -v
  ```
  Expected: all tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add vault.config.yml
  git commit -m "fix: rename auto_trigger_after_ingests to auto_trigger_after_fetches in vault.config.yml"
  ```

---

## Task 4 — Update CLAUDE.md session-start condition (task-0049)

**Files:** Modify `CLAUDE.md`

- [ ] **Step 1: Find the Session start section**

  In `CLAUDE.md`, locate the `## Session start` section. It contains:
  ```
  - `ingests_since_last_lint` ≥ `lint.auto_trigger_after_ingests` (from `vault.config.yml`)
  ```

- [ ] **Step 2: Apply the rename**

  ```markdown
  <!-- Before -->
  - `ingests_since_last_lint` ≥ `lint.auto_trigger_after_ingests` (from `vault.config.yml`)

  <!-- After -->
  - `fetches_since_last_lint` ≥ `lint.auto_trigger_after_fetches` (from `vault.config.yml`)
  ```

- [ ] **Step 3: Confirm no other occurrences**

  ```bash
  grep -n "ingests_since_last_lint\|auto_trigger_after_ingests" CLAUDE.md
  ```
  Expected: no output.

- [ ] **Step 4: Commit**

  ```bash
  git add CLAUDE.md
  git commit -m "fix: update CLAUDE.md session-start to reference fetches_since_last_lint"
  ```

---

## Task 5 — Update commands/lint.md: rename keys + python3 (task-0050)

**Files:** Modify `commands/lint.md`

- [ ] **Step 1: Apply key rename in auto-trigger section**

  Locate the `## Auto-trigger` section. It reads:
  ```
  1. `ingests_since_last_lint` ≥ `lint.auto_trigger_after_ingests` (from vault.config.yml)
  ```

  Replace with:
  ```
  1. `fetches_since_last_lint` ≥ `lint.auto_trigger_after_fetches` (from vault.config.yml)
  ```

- [ ] **Step 2: Update python→python3 in all bash code blocks**

  Two code blocks to update:
  ```bash
  # Before
  python .claude/skills/vault-linter/scripts/lint.py

  # After
  python3 .claude/skills/vault-linter/scripts/lint.py
  ```

  (Both the `# From vault root` and `# From outside the vault` blocks.)

- [ ] **Step 3: Verify no stale occurrences**

  ```bash
  grep -n "ingests_since_last_lint\|auto_trigger_after_ingests" commands/lint.md
  grep -n "python " commands/lint.md
  ```
  Expected: no output.

- [ ] **Step 4: Commit**

  ```bash
  git add commands/lint.md
  git commit -m "fix: update commands/lint.md — rename keys and use python3"
  ```

---

## Task 6 — Update test_vault_state.py key references (task-0051)

**Files:** Modify `tests/test_vault_state.py`

- [ ] **Step 1: Find all occurrences**

  ```bash
  grep -n "ingests_since_last_lint" tests/test_vault_state.py
  ```
  Expected: 6 occurrences across 5 test methods.

- [ ] **Step 2: Apply renames**

  Replace every occurrence of `"ingests_since_last_lint"` with `"fetches_since_last_lint"`:

  - `TestReadState.test_parses_existing_state_file`:
    ```python
    # Before
    (tmp_path / ".lint" / "state.yaml").write_text(
        "last_lint: 2026-01-01\ningests_since_last_lint: 3\n"
    )
    state = read_state(tmp_path)
    assert state["ingests_since_last_lint"] == "3"

    # After
    (tmp_path / ".lint" / "state.yaml").write_text(
        "last_lint: 2026-01-01\nfetches_since_last_lint: 3\n"
    )
    state = read_state(tmp_path)
    assert state["fetches_since_last_lint"] == "3"
    ```

  - `TestWriteState.test_creates_file_and_lint_dir_when_absent`:
    ```python
    # Before
    write_state(tmp_path, {"ingests_since_last_lint": 1})
    # After
    write_state(tmp_path, {"fetches_since_last_lint": 1})
    ```

  - `TestWriteState.test_patches_existing_key` (two occurrences):
    ```python
    # Before
    (tmp_path / ".lint" / "state.yaml").write_text(
        "last_lint: 2026-01-01\ningests_since_last_lint: 3\n"
    )
    write_state(tmp_path, {"ingests_since_last_lint": 5})
    assert read_state(tmp_path)["ingests_since_last_lint"] == "5"

    # After
    (tmp_path / ".lint" / "state.yaml").write_text(
        "last_lint: 2026-01-01\nfetches_since_last_lint: 3\n"
    )
    write_state(tmp_path, {"fetches_since_last_lint": 5})
    assert read_state(tmp_path)["fetches_since_last_lint"] == "5"
    ```

  - `TestWriteState.test_preserves_keys_not_in_updates`:
    ```python
    # Before
    .write_text("last_lint: 2026-01-01\ningests_since_last_lint: 3\n")
    write_state(tmp_path, {"ingests_since_last_lint": 5})
    # After
    .write_text("last_lint: 2026-01-01\nfetches_since_last_lint: 3\n")
    write_state(tmp_path, {"fetches_since_last_lint": 5})
    ```

  - `TestWriteState.test_adds_new_key_to_existing_file`:
    ```python
    # Before
    write_state(tmp_path, {"ingests_since_last_lint": 1})
    assert state["ingests_since_last_lint"] == "1"
    # After
    write_state(tmp_path, {"fetches_since_last_lint": 1})
    assert state["fetches_since_last_lint"] == "1"
    ```

- [ ] **Step 3: Run the full test suite**

  ```bash
  pytest tests/ -v
  ```
  Expected: all tests pass.

- [ ] **Step 4: Confirm no stale references**

  ```bash
  grep -rn "ingests_since_last_lint\|auto_trigger_after_ingests" skills/ tests/ vault.config.yml CLAUDE.md commands/lint.md
  ```
  Expected: no output.

- [ ] **Step 5: Commit**

  ```bash
  git add tests/test_vault_state.py
  git commit -m "fix: rename ingests_since_last_lint references in test_vault_state.py"
  ```

---

## Task 7 — Fix init-vault.sh hot.md heredoc (task-0052)

**Files:** Modify `init-vault.sh`

- [ ] **Step 1: Locate the wiki/hot.md heredoc**

  Search for the heredoc block that creates `wiki/hot.md`. It currently starts with:
  ```bash
  if [ ! -f "$VAULT_DIR/wiki/hot.md" ]; then
      cat > "$VAULT_DIR/wiki/hot.md" <<'EOF'
  ---
  type: page
  created: INIT
  ...
  ```

- [ ] **Step 2: Replace the heredoc content**

  Replace the entire content between `<<'EOF'` and `EOF` (preserve the `if` guard and closing `fi`):

  ```bash
  if [ ! -f "$VAULT_DIR/wiki/hot.md" ]; then
      cat > "$VAULT_DIR/wiki/hot.md" <<'EOF'
  ## [INIT]

  Vault just bootstrapped. No sessions yet.
  EOF
      ok "wiki/hot.md"
  else
      skip "wiki/hot.md (exists)"
  fi
  ```

- [ ] **Step 3: Verify the script syntax**

  ```bash
  bash -n init-vault.sh
  ```
  Expected: no output (syntax clean).

- [ ] **Step 4: Commit**

  ```bash
  git add init-vault.sh
  git commit -m "fix: init-vault.sh wiki/hot.md template — remove frontmatter, match /hot output format"
  ```

---

## Task 8 — python3 in commands/fetch.md and commands/refresh.md (task-0054)

**Files:** Modify `commands/fetch.md`, `commands/refresh.md`

- [ ] **Step 1: Update commands/fetch.md**

  ```bash
  # Before
  python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
  # After
  python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
  ```

  Both the main code block and the `--dry-run` variant.

- [ ] **Step 2: Update commands/refresh.md**

  ```bash
  # Before
  python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
  # After
  python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
  ```

- [ ] **Step 3: Verify**

  ```bash
  grep -n "^python " commands/fetch.md commands/refresh.md
  ```
  Expected: no output.

- [ ] **Step 4: Commit**

  ```bash
  git add commands/fetch.md commands/refresh.md
  git commit -m "docs: use python3 in commands/fetch.md and commands/refresh.md"
  ```

---

## Task 9 — python3 in skills/inbox-fetcher/SKILL.md (task-0055)

**Files:** Modify `skills/inbox-fetcher/SKILL.md`

- [ ] **Step 1: Find all bare `python` invocations**

  ```bash
  grep -n "^python " skills/inbox-fetcher/SKILL.md
  ```

- [ ] **Step 2: Replace all with python3**

  In the "How to run it" section, two code blocks:
  ```bash
  # Before
  python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
  python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --vault /path

  # After
  python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
  python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --vault /path
  ```

  Also `python fetch_inbox.py` in any short-form example → `python3 fetch_inbox.py`.

- [ ] **Step 3: Verify**

  ```bash
  grep -n "^python " skills/inbox-fetcher/SKILL.md
  ```
  Expected: no output.

- [ ] **Step 4: Commit**

  ```bash
  git add skills/inbox-fetcher/SKILL.md
  git commit -m "docs: use python3 consistently in inbox-fetcher SKILL.md"
  ```

---

## Task 10 — python3 in skills/vault-linter/SKILL.md (task-0056)

**Files:** Modify `skills/vault-linter/SKILL.md`

- [ ] **Step 1: Apply replacements**

  In the "How to run" section:
  ```bash
  # Before
  python .claude/skills/vault-linter/scripts/lint.py
  python .claude/skills/vault-linter/scripts/lint.py --unattended
  python .claude/skills/vault-linter/scripts/lint.py --vault /path/to/vault

  # After
  python3 .claude/skills/vault-linter/scripts/lint.py
  python3 .claude/skills/vault-linter/scripts/lint.py --unattended
  python3 .claude/skills/vault-linter/scripts/lint.py --vault /path/to/vault
  ```

- [ ] **Step 2: Verify**

  ```bash
  grep -n "^python " skills/vault-linter/SKILL.md
  ```
  Expected: no output.

- [ ] **Step 3: Commit**

  ```bash
  git add skills/vault-linter/SKILL.md
  git commit -m "docs: use python3 in vault-linter SKILL.md"
  ```

---

## Task 11 — Update README.md (task-0057)

**Files:** Modify `README.md`

- [ ] **Step 1: Add init_vault.py to the Quick start section**

  Locate the `## Quick start` bash code block. After the existing lines, add:

  ```markdown
  ## Quick start

  ```bash
  git clone https://github.com/maeste/my-2nd-brain.git
  cd my-2nd-brain
  ./init-vault.sh                    # → ./second-brain-vault  (Unix/macOS/WSL)
  # or — cross-platform (Linux, WSL, Windows):
  python3 init_vault.py              # → ./second-brain-vault
  # or
  python3 init_vault.py ~/knowledge/X      # explicit path
  python3 init_vault.py --here             # current directory
  ```
  ```

- [ ] **Step 2: Add Windows python note under Dependencies**

  In the `## Dependencies` section, after the `pip install` block:
  ```markdown
  > **Windows:** use `python` if `python3` is not recognised.
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add README.md
  git commit -m "docs: add init_vault.py to README quick start and Windows python note"
  ```

---

## Task 12 — Update GETTING-STARTED.md (task-0058)

**Files:** Modify `GETTING-STARTED.md`

- [ ] **Step 1: Update Day 1 bootstrap step**

  In the `## First week` → `**Day 1: bootstrap.**` paragraph, after the `./init-vault.sh` reference, add:

  ```markdown
  **Day 1: bootstrap.** Run `./init-vault.sh` (Unix/macOS/WSL) or
  `python3 init_vault.py` (Windows or any platform with Python). Add 5-10
  URLs to `inbox.md`. Tell the agent: *"process the inbox, then ingest the
  new content"*. You'll have your first few pages and sources.

  > **Windows:** use `python` if `python3` is not recognised.
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add GETTING-STARTED.md
  git commit -m "docs: add init_vault.py bootstrap path and Windows python note to GETTING-STARTED.md"
  ```

---

## Task 13 — init_vault.py: scaffold (task-0053.01)

**Files:** Create `init_vault.py`

- [ ] **Step 1: Create the file with module docstring, imports, color helpers, and arg parsing**

  ```python
  #!/usr/bin/env python3
  """
  init_vault.py — Bootstrap a second brain vault (v4).

  Usage:
      python3 init_vault.py                     # creates ./second-brain-vault
      python3 init_vault.py /path/to/vault      # explicit path
      python3 init_vault.py --here              # use current directory
      python3 init_vault.py --help

  Idempotent: safe to re-run. Asks before overwriting CLAUDE.md.
  """

  from __future__ import annotations

  import argparse
  import os
  import shutil
  import subprocess
  import sys
  from pathlib import Path


  # --- Colors ------------------------------------------------------------------

  _ANSI = sys.stdout.isatty()


  def _c(code: str, text: str) -> str:
      return f"\033[{code}m{text}\033[0m" if _ANSI else text


  def info(msg: str) -> None:
      print(_c("34", f"==> {msg}"))


  def ok(msg: str) -> None:
      print(_c("32", f"  ✓ {msg}"))


  def skip(msg: str) -> None:
      print(_c("2", f"  · {msg}"))


  def warn(msg: str) -> None:
      print(_c("33", f"  ⚠ {msg}"))


  def err(msg: str) -> None:
      print(_c("31", f"  ✗ {msg}"), file=sys.stderr)


  # --- Arg parsing -------------------------------------------------------------

  def resolve_vault_dir() -> Path:
      parser = argparse.ArgumentParser(
          prog="init_vault.py",
          description="Bootstrap a second brain vault.",
          formatter_class=argparse.RawDescriptionHelpFormatter,
          epilog=(
              "Examples:\n"
              "  python3 init_vault.py                  # ./second-brain-vault\n"
              "  python3 init_vault.py ~/knowledge/X    # explicit path\n"
              "  python3 init_vault.py --here           # current directory\n"
          ),
      )
      parser.add_argument(
          "vault_path",
          nargs="?",
          metavar="PATH",
          help="Path to vault root (default: ./second-brain-vault)",
      )
      parser.add_argument(
          "--here",
          action="store_true",
          help="Use the current directory as the vault root",
      )
      args = parser.parse_args()

      if args.here:
          vault_dir = Path.cwd()
      elif args.vault_path:
          vault_dir = Path(args.vault_path)
      else:
          vault_dir = Path("second-brain-vault")

      vault_dir.mkdir(parents=True, exist_ok=True)
      return vault_dir.resolve()


  # --- Entry point (stub — expanded in later subtasks) -------------------------

  def main() -> None:
      script_dir = Path(__file__).resolve().parent

      print()
      print(_c("1", "Second Brain Vault — init (v4)"))

      vault = resolve_vault_dir()
      print(_c("2", f"target: {vault}"))
      print()


  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 2: Verify the script runs and --help works**

  ```bash
  python3 init_vault.py --help
  ```
  Expected: usage message printed, no traceback.

  ```bash
  python3 init_vault.py --here
  ```
  Expected: prints header and target path, exits cleanly.

- [ ] **Step 3: Commit**

  ```bash
  git add init_vault.py
  git commit -m "feat: init_vault.py scaffold — arg parsing, color helpers, entry point"
  ```

---

## Task 14 — init_vault.py: folder structure (task-0053.02)

**Files:** Modify `init_vault.py`

- [ ] **Step 1: Add DIRS and GITKEEP_DIRS constants after imports**

  Insert after the color helper functions:

  ```python
  # --- Constants ---------------------------------------------------------------

  DIRS = [
      "raw/papers",
      "raw/web",
      "wiki/pages",
      "wiki/sources",
      "wiki/views/assets",
      "conversations",
      ".lint",
      ".claude/skills/inbox-fetcher/scripts",
      ".claude/skills/vault-linter/scripts",
      ".claude/skills/view-builder/templates",
      ".claude/skills/shared",
      ".claude/commands",
      ".obsidian",
  ]

  GITKEEP_DIRS = [
      "raw/papers", "raw/web", "wiki/pages", "wiki/sources",
      "wiki/views", "wiki/views/assets", "conversations", ".lint",
  ]
  ```

- [ ] **Step 2: Add create_dirs() function**

  ```python
  def create_dirs(vault: Path) -> None:
      info("Creating folder structure")
      for d in DIRS:
          (vault / d).mkdir(parents=True, exist_ok=True)
      for d in GITKEEP_DIRS:
          gk = vault / d / ".gitkeep"
          if not gk.exists():
              gk.touch()
      ok("directories")
  ```

- [ ] **Step 3: Call it from main()**

  In `main()`, after the `print()`:
  ```python
  create_dirs(vault)
  ```

- [ ] **Step 4: Test on a temp directory**

  ```bash
  python3 init_vault.py /tmp/vault-test-dirs
  ls /tmp/vault-test-dirs/raw/
  ls /tmp/vault-test-dirs/.claude/skills/
  ls /tmp/vault-test-dirs/wiki/
  ```
  Expected: `papers/  web/` in raw/; `inbox-fetcher/  shared/  vault-linter/  view-builder/` in skills/; `pages/  sources/  views/` in wiki/.

  ```bash
  # Re-run — must be idempotent
  python3 init_vault.py /tmp/vault-test-dirs
  ```
  Expected: no errors.

- [ ] **Step 5: Commit**

  ```bash
  git add init_vault.py
  git commit -m "feat: init_vault.py — folder structure creation"
  ```

---

## Task 15 — init_vault.py: CLAUDE.md and AGENTS.md (task-0053.03)

**Files:** Modify `init_vault.py`

- [ ] **Step 1: Add install_claude_md() function**

  ```python
  def install_claude_md(vault: Path, script_dir: Path) -> None:
      info("Installing CLAUDE.md")
      src = script_dir / "CLAUDE.md"
      dst = vault / "CLAUDE.md"

      if dst.exists():
          ans = input("  CLAUDE.md already exists. Overwrite? [y/N] ").strip().lower()
          if ans not in ("y", "yes"):
              skip("keeping existing CLAUDE.md")
          else:
              shutil.copy2(src, dst)
              ok("CLAUDE.md")
      else:
          shutil.copy2(src, dst)
          ok("CLAUDE.md")

      agents = vault / "AGENTS.md"
      if not agents.exists():
          try:
              os.symlink("CLAUDE.md", str(agents))
              ok("AGENTS.md → CLAUDE.md (symlink)")
          except (OSError, NotImplementedError, PermissionError):
              shutil.copy2(dst, agents)
              ok("AGENTS.md (copy)")
  ```

- [ ] **Step 2: Call from main()**

  ```python
  install_claude_md(vault, script_dir)
  ```

- [ ] **Step 3: Test**

  ```bash
  python3 init_vault.py /tmp/vault-test-claude
  ls -la /tmp/vault-test-claude/AGENTS.md
  ```
  Expected: AGENTS.md exists (symlink on Linux/macOS, file on Windows without Dev Mode).

  Re-run and answer `n` when prompted:
  ```bash
  python3 init_vault.py /tmp/vault-test-claude
  ```
  Expected: "keeping existing CLAUDE.md" skip message.

- [ ] **Step 4: Commit**

  ```bash
  git add init_vault.py
  git commit -m "feat: init_vault.py — CLAUDE.md install and AGENTS.md with Windows symlink fallback"
  ```

---

## Task 16 — init_vault.py: base files (task-0053.04)

**Files:** Modify `init_vault.py`

- [ ] **Step 1: Add content constants before main()**

  ```python
  # --- File content constants --------------------------------------------------

  _INBOX_MD = """\
  # Inbox

  URLs to process. The `inbox-fetcher` skill reads this file and pulls
  the URLs into `raw/web/`. Check items after fetching.

  ## To process

  <!-- Add URLs here as a task list:
  - [ ] https://example.com/article
  - [ ] https://arxiv.org/abs/2024.12345
  -->

  ## Processed

  <!-- Automatically moved here after fetch. -->
  """

  _INDEX_MD = """\
  # Index

  Catalog of the vault. Updated on every write operation.

  ## Pages

  <!-- Will be populated as you ingest content. -->

  ## Sources

  <!-- One entry per source. -->

  ## Views

  <!-- Timelines, comparisons, slides, etc. -->
  """

  _LOG_MD = """\
  # Log

  Append-only log of vault operations.

  Format: `## [YYYY-MM-DD] op | title`
  """

  _HOT_MD = """\
  ## [INIT]

  Vault just bootstrapped. No sessions yet.
  """

  _LINT_STATE = """\
  last_lint: null
  fetches_since_last_lint: 0
  last_exit_code: null
  last_findings_count: 0
  """

  _LINT_REPORT = """\
  # Lint Report

  No lint run yet. Run `python3 .claude/skills/vault-linter/scripts/lint.py`
  from the vault root.
  """

  _GITIGNORE = """\
  # System
  .DS_Store
  Thumbs.db

  # Editor
  .vscode/
  .idea/
  *.swp

  # Python
  __pycache__/
  *.pyc
  .venv/
  venv/

  # Obsidian workspace (keep vault files, skip user-specific state)
  .obsidian/workspace*
  .obsidian/cache
  """

  _OBSIDIAN_APP_JSON = """\
  {
    "useMarkdownLinks": false,
    "newLinkFormat": "relative",
    "readableLineLength": true,
    "attachmentFolderPath": "wiki/views/assets"
  }
  """
  ```

- [ ] **Step 2: Add helper and write_base_files() function**

  ```python
  def _write_if_absent(path: Path, content: str, label: str) -> None:
      if not path.exists():
          path.write_text(content, encoding="utf-8")
          ok(label)
      else:
          skip(f"{label} (exists)")


  def write_base_files(vault: Path, script_dir: Path) -> None:
      info("Writing base files")

      cfg = vault / "vault.config.yml"
      if not cfg.exists():
          shutil.copy2(script_dir / "vault.config.yml", cfg)
          ok("vault.config.yml")
      else:
          skip("vault.config.yml (exists — keeping user copy)")

      _write_if_absent(vault / "inbox.md", _INBOX_MD, "inbox.md")
      _write_if_absent(vault / "wiki" / "index.md", _INDEX_MD, "wiki/index.md")
      _write_if_absent(vault / "wiki" / "log.md", _LOG_MD, "wiki/log.md")
      _write_if_absent(vault / "wiki" / "hot.md", _HOT_MD, "wiki/hot.md")
      _write_if_absent(vault / ".lint" / "state.yaml", _LINT_STATE, ".lint/state.yaml")
      _write_if_absent(vault / ".lint" / "report.md", _LINT_REPORT, ".lint/report.md")
      _write_if_absent(vault / ".gitignore", _GITIGNORE, ".gitignore")

      obs_cfg = vault / ".obsidian" / "app.json"
      if not obs_cfg.exists():
          obs_cfg.write_text(_OBSIDIAN_APP_JSON, encoding="utf-8")
          ok(".obsidian/app.json")
      else:
          skip(".obsidian/app.json (exists — keeping user config)")
  ```

- [ ] **Step 3: Call from main()**

  ```python
  write_base_files(vault, script_dir)
  ```

- [ ] **Step 4: Verify hot.md has no frontmatter**

  ```bash
  python3 init_vault.py /tmp/vault-test-files
  cat /tmp/vault-test-files/wiki/hot.md
  ```
  Expected output:
  ```
  ## [INIT]

  Vault just bootstrapped. No sessions yet.
  ```
  (No `---` frontmatter block.)

- [ ] **Step 5: Commit**

  ```bash
  git add init_vault.py
  git commit -m "feat: init_vault.py — base file generation (inbox, wiki, .lint, .gitignore, .obsidian)"
  ```

---

## Task 17 — init_vault.py: skills installation (task-0053.05)

**Files:** Modify `init_vault.py`

- [ ] **Step 1: Add install_skills() function**

  ```python
  def install_skills(vault: Path, script_dir: Path) -> None:
      info("Installing skills")

      for skill_name, py_scripts in [
          ("inbox-fetcher", ["scripts/fetch_inbox.py"]),
          ("vault-linter", ["scripts/lint.py"]),
          ("view-builder", []),
      ]:
          src_dir = script_dir / "skills" / skill_name
          dst_dir = vault / ".claude" / "skills" / skill_name
          if not src_dir.is_dir():
              warn(f"{skill_name} skill not found in bundle")
              continue
          shutil.copy2(src_dir / "SKILL.md", dst_dir / "SKILL.md")
          for rel in py_scripts:
              dst_py = dst_dir / rel
              shutil.copy2(src_dir / rel, dst_py)
              if os.name != "nt":
                  os.chmod(dst_py, 0o755)
          if skill_name == "view-builder":
              templates_src = src_dir / "templates"
              if templates_src.is_dir():
                  for f in templates_src.iterdir():
                      if f.is_file():
                          shutil.copy2(f, dst_dir / "templates" / f.name)
          ok(f"skill: {skill_name}")

      shared_src = script_dir / "skills" / "shared" / "vault_state.py"
      if shared_src.exists():
          shutil.copy2(
              shared_src,
              vault / ".claude" / "skills" / "shared" / "vault_state.py",
          )
          ok("shared: vault_state.py")
      else:
          warn("skills/shared not found in bundle")
  ```

- [ ] **Step 2: Call from main()**

  ```python
  install_skills(vault, script_dir)
  ```

- [ ] **Step 3: Verify**

  ```bash
  python3 init_vault.py /tmp/vault-test-skills
  ls /tmp/vault-test-skills/.claude/skills/inbox-fetcher/scripts/
  ls /tmp/vault-test-skills/.claude/skills/view-builder/templates/
  ```
  Expected: `fetch_inbox.py` in inbox-fetcher/scripts/; template .md files in view-builder/templates/.

- [ ] **Step 4: Commit**

  ```bash
  git add init_vault.py
  git commit -m "feat: init_vault.py — skills and shared utilities installation"
  ```

---

## Task 18 — init_vault.py: commands installation (task-0053.06)

**Files:** Modify `init_vault.py`

- [ ] **Step 1: Add COMMANDS constant**

  ```python
  COMMANDS = [
      "save", "view", "reflect", "forget", "lint",
      "promote", "refresh", "ingest", "fetch", "hot", "playwright-fetch",
  ]
  ```

- [ ] **Step 2: Add install_commands() function**

  ```python
  def install_commands(vault: Path, script_dir: Path) -> None:
      info("Installing slash commands")
      for cmd in COMMANDS:
          src = script_dir / "commands" / f"{cmd}.md"
          dst = vault / ".claude" / "commands" / f"{cmd}.md"
          if src.exists():
              shutil.copy2(src, dst)
              ok(f"command: /{cmd}")
          else:
              warn(f"command {cmd} not found in bundle")
  ```

- [ ] **Step 3: Call from main()**

  ```python
  install_commands(vault, script_dir)
  ```

- [ ] **Step 4: Verify**

  ```bash
  python3 init_vault.py /tmp/vault-test-cmds
  ls /tmp/vault-test-cmds/.claude/commands/
  ```
  Expected: 11 `.md` files.

- [ ] **Step 5: Commit**

  ```bash
  git add init_vault.py
  git commit -m "feat: init_vault.py — slash commands installation"
  ```

---

## Task 19 — init_vault.py: git init and Python dep check (task-0053.07)

**Files:** Modify `init_vault.py`

- [ ] **Step 1: Add init_git() function**

  ```python
  def init_git(vault: Path) -> None:
      info("Git")
      if (vault / ".git").is_dir():
          skip("git repo already exists")
          return
      ans = input("  Initialize a git repo? [Y/n] ").strip().lower()
      if ans in ("n", "no"):
          skip("no git")
          return
      subprocess.run(["git", "init", "-q"], cwd=vault, check=False)
      # Check identity before committing
      name = subprocess.run(
          ["git", "config", "--get", "user.name"],
          cwd=vault, capture_output=True, text=True,
      ).stdout.strip()
      email = subprocess.run(
          ["git", "config", "--get", "user.email"],
          cwd=vault, capture_output=True, text=True,
      ).stdout.strip()
      if not name or not email:
          warn("git user identity not configured — skipping initial commit")
          warn("Set with: git config --global user.name 'Your Name'")
          warn("          git config --global user.email 'you@example.com'")
          return
      subprocess.run(["git", "add", "-A"], cwd=vault, check=False)
      subprocess.run(
          ["git", "commit", "-q", "-m", "initial vault bootstrap (v4)"],
          cwd=vault, check=False,
      )
      ok("git initialized")
  ```

- [ ] **Step 2: Add check_deps() function**

  ```python
  def check_deps(vault: Path) -> None:
      info("Checking Python dependencies")
      version = subprocess.run(
          [sys.executable, "--version"], capture_output=True, text=True
      )
      ok(f"Python found: {(version.stdout or version.stderr).strip()}")

      all_packages: set[str] = set()
      for skill_md in (vault / ".claude" / "skills").rglob("SKILL.md"):
          for line in skill_md.read_text(encoding="utf-8").splitlines():
              line = line.strip()
              if line.startswith("packages:"):
                  inner = line.split("[", 1)[-1].rstrip("]")
                  for pkg in inner.split(","):
                      pkg = pkg.strip().strip("\"'")
                      if pkg:
                          all_packages.add(pkg)

      _IMPORT_MAP = {"python-slugify": "slugify"}
      missing = []
      for pkg in sorted(all_packages):
          import_name = _IMPORT_MAP.get(pkg, pkg)
          r = subprocess.run(
              [sys.executable, "-c", f"import {import_name}"],
              capture_output=True,
          )
          if r.returncode != 0:
              missing.append(pkg)

      if missing:
          warn(f"missing Python packages: {' '.join(missing)}")
          print(f"      install with: pip install {' '.join(missing)}")
      else:
          ok("all Python dependencies installed")
  ```

- [ ] **Step 3: Call from main()**

  ```python
  init_git(vault)
  check_deps(vault)
  ```

- [ ] **Step 4: Test dep check (must detect missing packages)**

  In a venv without trafilatura:
  ```bash
  python3 -m venv /tmp/test-venv
  /tmp/test-venv/bin/python init_vault.py /tmp/vault-dep-test
  ```
  Expected: warning listing `trafilatura requests python-slugify` as missing.

- [ ] **Step 5: Commit**

  ```bash
  git add init_vault.py
  git commit -m "feat: init_vault.py — git init with identity check and Python dep check"
  ```

---

## Task 20 — init_vault.py: done banner and Next Steps (task-0053.08)

**Files:** Modify `init_vault.py`

- [ ] **Step 1: Add print_done() function**

  ```python
  def print_done(vault: Path) -> None:
      py_cmd = "python3" if os.name != "nt" else "python"
      print()
      print(_c("1;32", "Vault ready!"))
      print()
      print(f"  Path: {vault}")
      print()
      print("Next steps:")
      print(f"  1. cd {vault}")
      print( "  2. Add URLs to inbox.md (or drop PDFs in raw/papers/)")
      print( "  3. Open Claude Code (or another CLI) in this folder")
      print( "  4. Ask: \"process the inbox\", then \"ingest the new content\"")
      print( "  5. Use /view to build timelines/comparisons/slides")
      print( "  6. Use /save for important conversations")
      print( "  7. Periodically: /reflect → read wiki/compass.md")
      print()
  ```

- [ ] **Step 2: Call from main()**

  ```python
  print_done(vault)
  ```

- [ ] **Step 3: Full end-to-end test on a clean path**

  ```bash
  python3 init_vault.py /tmp/vault-final-test
  ```
  Expected: complete output with all sections (Creating folder structure → Vault ready!), correct Next Steps with `python3`.

  On Windows (PowerShell):
  ```powershell
  python init_vault.py C:\tmp\vault-final-test
  ```
  Expected: Next Steps shows `python` (not `python3`).

  Re-run test:
  ```bash
  python3 init_vault.py /tmp/vault-final-test
  ```
  Expected: all items show skip() messages (idempotent).

- [ ] **Step 4: Final commit**

  ```bash
  git add init_vault.py
  git commit -m "feat: init_vault.py — done banner and platform-aware Next Steps"
  ```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task(s) |
|---|---|
| Rename `ingests_since_last_lint` in vault_state.py | Task 1 |
| Rename key in fetch_inbox.py | Task 2 |
| Rename key in vault.config.yml | Task 3 |
| Update CLAUDE.md | Task 4 |
| Update commands/lint.md (key + python3) | Task 5 |
| Update tests | Task 6 |
| Fix hot.md heredoc in init-vault.sh | Task 7 |
| python3 in commands/fetch.md + commands/refresh.md | Task 8 |
| python3 in inbox-fetcher/SKILL.md | Task 9 |
| python3 in vault-linter/SKILL.md | Task 10 |
| README.md update | Task 11 |
| GETTING-STARTED.md update | Task 12 |
| init_vault.py scaffold | Task 13 |
| init_vault.py folder structure | Task 14 |
| init_vault.py CLAUDE.md + AGENTS.md symlink fallback | Task 15 |
| init_vault.py base files (hot.md without frontmatter) | Task 16 |
| init_vault.py skills | Task 17 |
| init_vault.py commands | Task 18 |
| init_vault.py git init + dep check | Task 19 |
| init_vault.py banner + platform-aware Next Steps | Task 20 |

All spec requirements covered. No gaps.

**Placeholder scan:** No TBDs, no "implement later", no "similar to Task N". All code blocks are complete. ✅

**Consistency check:**
- `fetches_since_last_lint` used consistently across Tasks 1, 2, 3, 4, 5, 6, and in `_LINT_STATE` constant in Task 16. ✅
- `python3` used consistently in Tasks 8, 9, 10, 11, 12 and in `_LINT_REPORT` constant in Task 16. ✅
- `os.name != "nt"` guard used consistently for chmod (Task 17) and python cmd detection (Task 20). ✅
- symlink exception tuple `(OSError, NotImplementedError, PermissionError)` consistent with spec. ✅
