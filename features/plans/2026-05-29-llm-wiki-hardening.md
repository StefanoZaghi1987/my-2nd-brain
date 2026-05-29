# LLM Wiki Hardening & Portability — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the LLM Wiki template/engine repo by fixing the broken `/split` command, eliminating duplicated link-resolution logic, wiring up the orphaned `review_scope.py`, normalising the Windows Python launcher, making bootstrap non-blocking, fixing the chart output path, and adding the `/retry` feature for failed inbox URLs.

**Architecture:** All changes are in-place patches to existing files — no new subsystems. The only new module (`linkutil.py`) is extracted from code that already exists in two places; the new command files (`split.md`, `retry.md`) follow the exact schema of existing ones. `init_vault.py` is the central deployment control plane and is touched by Tasks 1, 2, 5, and 7.

**Tech Stack:** Python 3, pytest, pathlib, argparse, re. No new dependencies. Markdown for command/skill docs.

---

## Fresh-agent setup

```bash
# 1. Confirm you are in the ENGINE repo (not a deployed vault — no wiki/ or raw/ dirs)
cd D:\my-2nd-brain

# 2. Install test/runtime dependencies
pip install requests trafilatura python-slugify matplotlib pytest

# 3. Run the full suite — must be green before you touch anything
python -m pytest -v

# 4. Branch (create if absent)
git checkout -b feat/hardening-portability   # from feat-hotfix
```

**Sequential constraint — `init_vault.py` is touched by Tasks 1 → 2 → 5 → 7.**
Always run `python -m pytest -v` after each task that touches `init_vault.py` before
starting the next one.

Tasks 3 (wire review_scope) and 6 (chart.py path) are independent and can be done
in any slot.

---

## File Map

| File | Action | Task |
|---|---|---|
| `skills/shared/linkutil.py` | **CREATE** | 1 |
| `tests/test_linkutil.py` | **CREATE** | 1 |
| `tests/test_bootstrap.py` | **CREATE** | 5 |
| `tests/test_chart.py` | **CREATE** | 6 |
| `commands/split.md` | **CREATE** | 2 |
| `commands/retry.md` | **CREATE** | 7 |
| `skills/vault-linter/scripts/lint.py` | MODIFY (import, remove defs) | 1 |
| `skills/shared/find_backlinks.py` | MODIFY (import, remove defs) | 1 |
| `init_vault.py` | MODIFY (COMMANDS, _SHARED_SCRIPTS, --yes) | 1, 2, 5, 7 |
| `commands/merge.md` | MODIFY (remove SPLIT section, cross-link, launcher) | 2, 4 |
| `commands/review.md` | MODIFY (wire review_scope.py, launcher) | 3, 4 |
| `commands/fetch.md` | MODIFY (launcher) | 4 |
| `commands/lint.md` | MODIFY (launcher) | 4 |
| `commands/ingest.md` | MODIFY (launcher) | 4 |
| `commands/refresh.md` | MODIFY (launcher) | 4 |
| `skills/inbox-fetcher/scripts/fetch_inbox.py` | MODIFY (FAILED_PATTERN, retry mode) | 7 |
| `skills/view-builder/templates/chart.py` | MODIFY (--vault arg, output path) | 6 |
| `tests/test_fetch_inbox.py` | EXTEND (retry tests) | 7 |
| `CLAUDE.md` | MODIFY (check count, slash list, path prefixes) | 8 |

---

## Task 1: Extract shared link-resolution into `linkutil.py`

Eliminates the "keep in sync" copy-paste between `lint.py` and `find_backlinks.py`.
Also removes the dead `read_state` import from `lint.py` since we're already touching
the import block. The new module must be added to `init_vault.py:_SHARED_SCRIPTS` or it
won't ship to deployed vaults.

**Files:**
- Create: `skills/shared/linkutil.py`
- Create: `tests/test_linkutil.py`
- Modify: `skills/vault-linter/scripts/lint.py` (lines 37, 60, 168-197)
- Modify: `skills/shared/find_backlinks.py` (lines 29-66)
- Modify: `init_vault.py` (line 361 — `_SHARED_SCRIPTS` list)

- [ ] **Step 1: Write the failing test for linkutil**

Create `tests/test_linkutil.py`:

```python
"""Tests for the shared link-resolution module (linkutil.py)."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
from linkutil import WIKILINK_RE, normalize_link_target


class TestWikilinkRe:
    def test_bare_link(self):
        m = WIKILINK_RE.search("See [[wiki/pages/foo]].")
        assert m is not None
        assert m.group(1) == "wiki/pages/foo"
        assert m.group(2) is None

    def test_aliased_link(self):
        m = WIKILINK_RE.search("See [[wiki/pages/foo|Foo Page]].")
        assert m is not None
        assert m.group(1) == "wiki/pages/foo"
        assert m.group(2) == "Foo Page"

    def test_no_match_on_plain_text(self):
        assert WIKILINK_RE.search("no brackets here") is None

    def test_dot_in_slug(self):
        m = WIKILINK_RE.search("[[wiki/sources/arxiv-2602.20867]]")
        assert m is not None
        assert m.group(1) == "wiki/sources/arxiv-2602.20867"


class TestNormalizeLinkTarget:
    def test_vault_relative_with_md(self, tmp_path):
        page = tmp_path / "wiki" / "pages" / "foo.md"
        page.parent.mkdir(parents=True)
        page.write_text("content")
        source = tmp_path / "wiki" / "pages" / "bar.md"
        result = normalize_link_target("wiki/pages/foo.md", tmp_path, source)
        assert result == page

    def test_vault_relative_without_md(self, tmp_path):
        page = tmp_path / "wiki" / "pages" / "foo.md"
        page.parent.mkdir(parents=True)
        page.write_text("content")
        source = tmp_path / "wiki" / "pages" / "bar.md"
        result = normalize_link_target("wiki/pages/foo", tmp_path, source)
        assert result == page

    def test_dot_slug_no_false_extension(self, tmp_path):
        # arxiv-2602.20867 has a dot but is NOT an extension — should find .md
        page = tmp_path / "wiki" / "sources" / "arxiv-2602.20867.md"
        page.parent.mkdir(parents=True)
        page.write_text("content")
        source = tmp_path / "wiki" / "pages" / "bar.md"
        result = normalize_link_target("wiki/sources/arxiv-2602.20867", tmp_path, source)
        assert result == page

    def test_empty_target_returns_none(self, tmp_path):
        source = tmp_path / "wiki" / "pages" / "bar.md"
        assert normalize_link_target("", tmp_path, source) is None

    def test_whitespace_stripped(self, tmp_path):
        page = tmp_path / "wiki" / "pages" / "foo.md"
        page.parent.mkdir(parents=True)
        page.write_text("content")
        source = tmp_path / "wiki" / "pages" / "bar.md"
        result = normalize_link_target("  wiki/pages/foo  ", tmp_path, source)
        assert result == page
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python -m pytest tests/test_linkutil.py -v
```

Expected: `ModuleNotFoundError: No module named 'linkutil'`

- [ ] **Step 3: Create `skills/shared/linkutil.py`**

```python
#!/usr/bin/env python3
"""linkutil.py — Canonical wikilink regex and path-resolution for the LLM Wiki engine.

Centralises the wikilink pattern and link-target resolution logic so that
both the vault linter and the backlink finder always use the same rules.
Previously these were copy-pasted in two files with a "keep in sync" comment.
"""
from __future__ import annotations
import re
from pathlib import Path

# Alias-aware wikilink regex — matches [[target]] and [[target|display label]].
WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")


def normalize_link_target(target: str, vault_root: Path, source_file: Path) -> Path | None:
    """Resolve a [[link]] target into an absolute path, or None if unresolvable.

    Tries target vault-relative, then source-relative. Also tries with .md
    appended when the path has no .md suffix — slugs like arxiv-2602.20867
    look like they have an extension but don't.
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
            return abs_local.resolve()
    # Return first candidate vault-relative as a fallback for error reporting.
    return vault_root / candidates[0]
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
python -m pytest tests/test_linkutil.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Update `lint.py` — import from linkutil, remove local defs, drop dead import**

In `skills/vault-linter/scripts/lint.py`:

*Change line 37* — remove `read_state` from the import (it is imported but never called):

```python
# Before:
from vault_state import load_config, read_state, write_state as _write_state

# After:
from vault_state import load_config, write_state as _write_state
from linkutil import WIKILINK_RE, normalize_link_target
```

*Remove line 60* — delete the now-redundant local definition:
```python
# DELETE this line:
WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")
```

*Remove lines 168–197* — delete the `normalize_link_target` function body (the entire
function from `def normalize_link_target(...)` through its closing `return` statement).
The import added above replaces it.

- [ ] **Step 6: Update `find_backlinks.py` — import from linkutil, remove local defs**

In `skills/shared/find_backlinks.py`, replace lines 24–66 (the `from __future__`
through the end of the `normalize_link_target` function) with:

```python
from __future__ import annotations
import sys
from pathlib import Path

# linkutil.py lives in the same directory; no extra path manipulation needed.
sys.path.insert(0, str(Path(__file__).parent))
from linkutil import WIKILINK_RE, normalize_link_target
```

The rest of the file (from `def find_backlinks(...)` onward) is unchanged.

- [ ] **Step 7: Add `linkutil.py` to `init_vault.py:_SHARED_SCRIPTS`**

In `init_vault.py`, find line 361:
```python
# Before:
_SHARED_SCRIPTS = ["vault_state.py", "review_scope.py", "find_backlinks.py"]

# After:
_SHARED_SCRIPTS = ["vault_state.py", "review_scope.py", "find_backlinks.py", "linkutil.py"]
```

- [ ] **Step 8: Run the full test suite**

```bash
python -m pytest -v
```

Expected: All tests PASS. Specifically verify `test_lint.py` and
`test_find_backlinks.py` still pass — they exercise the shared functions
now imported from linkutil.

- [ ] **Step 9: Commit**

```bash
git add skills/shared/linkutil.py tests/test_linkutil.py \
        skills/vault-linter/scripts/lint.py \
        skills/shared/find_backlinks.py init_vault.py
git commit -m "refactor: extract shared link-resolution into linkutil.py, drop dead import"
```

---

## Task 2: Create standalone `/split` command

`commands/split.md` must be self-contained (Guards + Unattended copied in) because
the LLM reads one command file at a time. `merge.md` is trimmed to MERGE-only and
gains a cross-link. `"split"` is added to `init_vault.py:COMMANDS` so it deploys.

**Files:**
- Create: `commands/split.md`
- Modify: `commands/merge.md`
- Modify: `init_vault.py` (COMMANDS list, line 88-90)

- [ ] **Step 1: Write a test asserting the split command deploys**

Append to the test file (or create `tests/test_installer.py` if not yet present):

```python
"""Tests for init_vault.py deployment correctness."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import init_vault


class TestCommands:
    def test_split_in_commands(self):
        """Every advertised slash command must be in the COMMANDS list."""
        assert "split" in init_vault.COMMANDS

    def test_split_md_exists(self):
        repo = Path(__file__).parent.parent
        assert (repo / "commands" / "split.md").exists()

    # test_retry_* tests are added in Task 7 after commands/retry.md exists.
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python -m pytest tests/test_installer.py::TestCommands::test_split_in_commands \
                tests/test_installer.py::TestCommands::test_split_md_exists -v
```

Expected: Both FAIL — "split" not in COMMANDS, commands/split.md does not exist.

- [ ] **Step 3: Create `commands/split.md`**

Extract the SPLIT protocol from `commands/merge.md` (starting at `## SPLIT Protocol`
through the end of the file), and write it as a self-contained file. The content below
is verbatim from merge.md with the Guards, Unattended, and a SPLIT-specific report
format added so the file stands alone:

```markdown
---
description: Split an overgrown wiki page into two focused ones, rewriting all
  backlinks so the vault stays consistent. Interactive — never available in
  unattended mode. Triggered by lint duplicate findings or when a single page
  has grown to cover too many distinct concepts.
---

# /split — Split a wiki page into two

Break an overgrown page into two focused ones. Rewrites all backlinks so the
vault stays consistent. Typically triggered by a lint duplicate finding or when
a page has grown to cover too many distinct concepts.

## Arguments

`/split <page> <new-page-A> <new-page-B>` where `<page>` is the original page
to dissolve and the two new slugs name the resulting pages.

- `/split agent-tools agent-tools-builtin agent-tools-custom`

If the target slugs are not supplied, ask the user before proceeding.

---

## SPLIT Protocol

### 1. Identify

User provides the page to split and names the two new target pages.
Resolve the original page to an absolute wiki path. Confirm with the
user: show the page title and the two new slugs.

### 2. Show content and assign sections

Read the original page in full and display it. Ask the user to mark
which sections (or claims) go to which new target page. If any section
is ambiguous, ask explicitly rather than guessing.

Wait for the user to confirm the full assignment before proceeding.

### 3. Check backlink fanout

Run `.claude/skills/shared/find_backlinks.py` against the original page
before writing anything:

```
python3 .claude/skills/shared/find_backlinks.py <vault_root> <path-to-original-page>
```

(Use `python` on Windows, `python3` on macOS/Linux.)

List every file returned. If the fanout exceeds **15 files** — stop
immediately. Report the complete file list and do not proceed. Let the
user choose to continue across multiple passes or stop entirely.

See the Guards section for the full fanout protocol.

### 4. Write two new pages

Write `wiki/pages/<new-page-A>.md` and `wiki/pages/<new-page-B>.md`
with the content assigned in step 2. Apply standard wiki frontmatter
to each. Set `created` and `updated` to today's date for both new
pages. Do not copy claims that belong to the other new page.

### 5. Rewrite backlinks

For each file in the backlink list from step 3, **excluding the
original page itself** (it will be deleted in step 6):

- If the context of the link clearly belongs to one of the two new
  pages (e.g., the surrounding text refers to content that went to
  new-page-A), rewrite the link to that page.
- If the context is ambiguous, ask the user per-link before rewriting.
- If the user chooses neither new page, leave the link unchanged and
  flag it in the final report as requiring manual resolution after
  the split.

Apply the same four-form rewriting rule as in `/merge` step 7 — all link
variants in a given file must be rewritten in one pass:

- Bare slug: `[[page]]` → `[[new-page-A]]` or `[[new-page-B]]`
- Vault-relative without extension: `[[wiki/pages/page]]` → `[[wiki/pages/new-page-A]]`
- With `.md` extension: `[[wiki/pages/page.md]]` → `[[wiki/pages/new-page-A.md]]`
- Aliased form: `[[wiki/pages/page|Display Text]]` → `[[wiki/pages/new-page-A|Display Text]]`

### 6. Delete the original page

Delete `wiki/pages/<original-page>.md` once all backlinks have been
confirmed rewritten.

### 7. Update bookkeeping

- `wiki/index.md`: remove the original page entry; add entries for
  both new pages.
- `wiki/log.md`: append one line:
  `## [YYYY-MM-DD] split <original-page> → <new-page-A>, <new-page-B>`
  with a count of files rewritten.

Propose running `/lint` to confirm no dead links remain.

---

## Guards

**Fanout guard (>15 files):** If `find_backlinks.py` returns more than
15 files, stop immediately. Report the complete file list with counts.
Do not proceed until the user has either picked a subset of files to
rewrite in this pass or explicitly asked to continue across multiple
passes. Never silently exceed invariant #5.

**Prose-deletion guard:** Never delete content from the original page
without the user's approval. Show all assignments in step 2, wait for
explicit confirmation before writing anything.

**Shareable view guard:** For any view in the backlink list with
`shareable: true`, do NOT rewrite the link. Warn the user that the
view still references the deleted original page and let them decide
whether to issue a new dated version.

**Confirm before delete:** Do not delete the original page (step 6)
until all backlink rewrites have been applied and confirmed. Deletion is
irreversible.

## Unattended mode

`/split` is **not available unattended**. The operation involves
irreversible deletions and per-claim assignment decisions that require
the user in the loop. If invoked unattended, refuse with a clear
message and suggest running the command interactively.

## Report format

End of SPLIT operation, tell the user:

```
Split: <original-page> → <new-page-A>, <new-page-B>
  ✓ Wrote: wiki/pages/<new-page-A>.md
  ✓ Wrote: wiki/pages/<new-page-B>.md
  ✓ Rewrote backlinks in N pages
  ⚠ N links left ambiguous (flagged in report above)
  ⚠ N shareable views left as-is (still reference deleted page)
  ✓ Deleted: wiki/pages/<original-page>.md
```
```

- [ ] **Step 4: Trim `commands/merge.md` to MERGE-only**

In `commands/merge.md`:
1. Change the `description:` frontmatter to: `"Merge two near-duplicate wiki pages into one canonical page (rewriting all backlinks). Used to resolve lint duplicates and /review contradictions. Interactive — never available in unattended mode. For splitting a page, see /split."`
2. Change the title from `# /merge — Merge or split wiki pages` to `# /merge — Merge wiki pages`
3. Remove the `## SPLIT Protocol` section (lines ~171-238) — everything from `## SPLIT Protocol` through the end of the SPLIT step 7 block.
4. Retain the `## Guards`, `## Unattended mode`, and `## Report format` sections (they apply to MERGE).
5. Add a cross-link after the `## Arguments` block, before `---`:

```markdown
> **Splitting a page?** See [`/split`](.claude/commands/split.md) — it has its
> own protocol for breaking an overgrown page into two focused ones.
```

- [ ] **Step 5: Add `"split"` to `init_vault.py:COMMANDS`**

```python
# Before (line 88-90):
COMMANDS = [
    "save", "view", "reflect", "forget", "lint",
    "promote", "refresh", "ingest", "fetch", "hot", "playwright-fetch", "review", "merge",
]

# After:
COMMANDS = [
    "save", "view", "reflect", "forget", "lint",
    "promote", "refresh", "ingest", "fetch", "hot", "playwright-fetch", "review", "merge",
    "split",
]
```

- [ ] **Step 6: Run the installer tests**

```bash
python -m pytest tests/test_installer.py::TestCommands::test_split_in_commands \
                tests/test_installer.py::TestCommands::test_split_md_exists -v
```

Expected: Both PASS.

- [ ] **Step 7: Run the full test suite**

```bash
python -m pytest -v
```

Expected: All tests PASS.

- [ ] **Step 8: Commit**

```bash
git add commands/split.md commands/merge.md init_vault.py tests/test_installer.py
git commit -m "feat: add standalone /split command, trim merge.md to MERGE-only"
```

---

## Task 3: Wire `review_scope.py` into `/review`

`review_scope.py` is fully built and tested but the `/review` command describes scope
determination in prose — the script is never invoked. This update makes `/review`
actually call `review_scope.py` for the default scope, the same way `/fetch` calls
`fetch_inbox.py` and `/lint` calls `lint.py`.

**Files:**
- Modify: `commands/review.md` (Protocol step 2)

- [ ] **Step 1: Update Protocol step 2 in `commands/review.md`**

Find the `## Protocol` section. Step 2 currently reads:

```
2. Determine scope (see Scoping table above). For `/review --all`, ask the user
   to confirm before proceeding — state the approximate page count.
```

Replace with:

```markdown
2. **Determine scope.** For the default `changed` scope, run:

   ```bash
   python3 .claude/skills/shared/review_scope.py <vault_root>
   ```

   (Use `python` on Windows, `python3` on macOS/Linux.)

   The script exits 0 and prints one path per line when pages are in scope,
   exits 1 when nothing has changed since last review (report "nothing new —
   skipping"), and exits 2 on error. The printed paths ARE the scope for steps 3–5.

   For `/review <topic-or-tag>`: pages matching that tag, or pages that link to
   the named topic page. Select them from the vault manually.

   For `/review --all`: all pages in `wiki/pages/`. Ask the user to confirm before
   proceeding — state the approximate page count.
```

- [ ] **Step 2: Commit**

```bash
git add commands/review.md
git commit -m "fix: wire review_scope.py into /review Protocol step 2"
```

---

## Task 4: Normalize Python launcher in command docs

Command docs hardcode `python3` (`fetch.md`, `lint.md`, `ingest.md`, `refresh.md`) or
bare `python` (`merge.md`). The fix is a platform-aware callout near the first code
block in each affected file. No code change — docs only.

**Files:**
- Modify: `commands/fetch.md`, `commands/lint.md`, `commands/ingest.md`,
          `commands/refresh.md`, `commands/merge.md`

- [ ] **Step 1: Add Windows note to `commands/fetch.md`**

Insert the following line immediately before the first `\`\`\`bash` block:

```
> **Windows:** replace `python3` with `python` in all commands below.
```

- [ ] **Step 2: Add Windows note to `commands/lint.md`**

Same: insert `> **Windows:** replace \`python3\` with \`python\` in all commands below.`
before the first `\`\`\`bash` block.

- [ ] **Step 3: Add Windows note to `commands/ingest.md`**

Same insertion before the first `\`\`\`bash` block.

- [ ] **Step 4: Add Windows note to `commands/refresh.md`**

Same insertion before the first `\`\`\`bash` block.

- [ ] **Step 5: Fix `commands/merge.md` — normalize `python` → `python3` + Windows note**

In `commands/merge.md`, the `find_backlinks.py` invocation blocks use bare `python`.
Change each `python .claude/skills/...` to `python3 .claude/skills/...` in the code
blocks in `## MERGE Protocol` step 4. Then add the Windows callout before the first
code block.

(Note: `commands/split.md` already has the Windows note added in Task 2 step 3.)

- [ ] **Step 6: Commit**

```bash
git add commands/fetch.md commands/lint.md commands/ingest.md \
        commands/refresh.md commands/merge.md
git commit -m "docs: add Windows python-launcher callout to all command docs"
```

---

## Task 5: Non-blocking bootstrap (`--yes` flag)

`init_vault.py` hangs in CI/automated bootstrap because `init_git()` and
`install_claude_md()` call `input()`. Add `--yes`/`--non-interactive` that takes safe
defaults: skip CLAUDE.md overwrite, skip git commit.

**Files:**
- Create: `tests/test_bootstrap.py`
- Modify: `init_vault.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_bootstrap.py`:

```python
"""Tests for init_vault.py non-interactive bootstrap."""
import sys
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent


class TestNonInteractiveBootstrap:
    def test_yes_flag_completes_without_stdin(self, tmp_path):
        """--yes must bootstrap a vault without reading from stdin."""
        vault = tmp_path / "test-vault"
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "init_vault.py"), str(vault), "--yes"],
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,  # no stdin — hangs if input() called
        )
        assert result.returncode == 0, (
            f"init_vault.py --yes exited {result.returncode}\n"
            f"stdout: {result.stdout[-500:]}\n"
            f"stderr: {result.stderr[-500:]}"
        )

    def test_yes_flag_deploys_commands(self, tmp_path):
        """Commands directory must contain all expected files after --yes bootstrap."""
        vault = tmp_path / "test-vault"
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "init_vault.py"), str(vault), "--yes"],
            capture_output=True, timeout=60, stdin=subprocess.DEVNULL,
        )
        commands_dir = vault / ".claude" / "commands"
        assert (commands_dir / "split.md").exists()
        assert (commands_dir / "fetch.md").exists()
        assert (commands_dir / "lint.md").exists()

    def test_yes_flag_deploys_linkutil(self, tmp_path):
        """linkutil.py must be present in the shared skills directory."""
        vault = tmp_path / "test-vault"
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "init_vault.py"), str(vault), "--yes"],
            capture_output=True, timeout=60, stdin=subprocess.DEVNULL,
        )
        assert (vault / ".claude" / "skills" / "shared" / "linkutil.py").exists()
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python -m pytest tests/test_bootstrap.py::TestNonInteractiveBootstrap::test_yes_flag_completes_without_stdin -v
```

Expected: FAIL — the test hangs because `input()` is called, or exits non-zero.

- [ ] **Step 3: Add `--yes` to `init_vault.py`'s arg parser and thread it through**

In `init_vault.py`, make the following changes:

*1. Change `resolve_vault_dir()` to return `(vault_dir, yes)`:*

```python
def resolve_vault_dir() -> tuple[Path, bool]:
    parser = argparse.ArgumentParser(
        prog="init_vault.py",
        description="Bootstrap a second brain vault.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 init_vault.py                  # ./second-brain-vault\n"
            "  python3 init_vault.py ~/knowledge/X    # explicit path\n"
            "  python3 init_vault.py --here           # current directory\n"
            "  python3 init_vault.py --yes            # non-interactive (CI)\n"
        ),
    )
    parser.add_argument(
        "vault_path", nargs="?", metavar="PATH",
        help="Path to vault root (default: ./second-brain-vault)",
    )
    parser.add_argument(
        "--here", action="store_true",
        help="Use the current directory as the vault root",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Non-interactive: skip all prompts, take safe defaults",
    )
    args = parser.parse_args()

    if args.here:
        vault_dir = Path.cwd()
    elif args.vault_path:
        vault_dir = Path(args.vault_path)
    else:
        vault_dir = Path("second-brain-vault")

    vault_dir.mkdir(parents=True, exist_ok=True)
    return vault_dir.resolve(), args.yes
```

*2. Update `init_git()` to accept `yes`:*

```python
def init_git(vault: Path, yes: bool = False) -> None:
    info("Git")
    if (vault / ".git").is_dir():
        skip("git repo already exists")
        return
    if yes:
        skip("git init skipped (--yes mode)")
        return
    ans = input("  Initialize a git repo? [Y/n] ").strip().lower()
    if ans in ("n", "no"):
        skip("no git")
        return
    # ... rest of function unchanged ...
```

*3. Update `install_claude_md()` to accept `yes`:*

```python
def install_claude_md(vault: Path, script_dir: Path, yes: bool = False) -> None:
    info("Installing CLAUDE.md")
    src = script_dir / "CLAUDE.md"
    dst = vault / "CLAUDE.md"

    if dst.exists():
        if yes:
            skip("keeping existing CLAUDE.md (--yes mode)")
        else:
            ans = input("  CLAUDE.md already exists. Overwrite? [y/N] ").strip().lower()
            if ans not in ("y", "yes"):
                skip("keeping existing CLAUDE.md")
            else:
                shutil.copy2(src, dst)
                ok("CLAUDE.md")
    else:
        shutil.copy2(src, dst)
        ok("CLAUDE.md")
    # ... AGENTS.md symlink logic unchanged ...
```

*4. Update `main()` to unpack and thread `yes`:*

```python
def main() -> None:
    script_dir = Path(__file__).resolve().parent

    print()
    print(_c("1", "Second Brain Vault — init (v4)"))

    vault, yes = resolve_vault_dir()
    print(_c("2", f"target: {vault}"))
    print()

    create_dirs(vault)
    install_claude_md(vault, script_dir, yes=yes)
    write_base_files(vault, script_dir)
    install_skills(vault, script_dir)
    install_commands(vault, script_dir)
    init_git(vault, yes=yes)
    check_deps(vault)
    print_done(vault)
```

- [ ] **Step 4: Run the tests**

```bash
python -m pytest tests/test_bootstrap.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Run the full test suite**

```bash
python -m pytest -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add init_vault.py tests/test_bootstrap.py
git commit -m "feat: add --yes non-interactive flag to init_vault.py bootstrap"
```

---

## Task 6: Fix `chart.py` output path

The chart template writes `OUTPUT_DIR = Path(__file__).parent / "assets"`, landing
PNGs next to the template at `.claude/skills/view-builder/templates/assets/` instead
of `wiki/views/assets/`. Accept `--vault` arg and resolve from vault root.

**Files:**
- Create: `tests/test_chart.py`
- Modify: `skills/view-builder/templates/chart.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_chart.py`:

```python
"""Tests for chart.py output-path resolution."""
import sys
import subprocess
from pathlib import Path
import pytest

CHART_PY = (
    Path(__file__).parent.parent
    / "skills" / "view-builder" / "templates" / "chart.py"
)


class TestChartOutputPath:
    def test_writes_to_vault_views_assets(self, tmp_path):
        """Chart PNG must land in wiki/views/assets/ under the vault root."""
        vault = tmp_path / "vault"
        (vault / "wiki" / "views" / "assets").mkdir(parents=True)
        result = subprocess.run(
            [sys.executable, str(CHART_PY), "--vault", str(vault)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        expected = vault / "wiki" / "views" / "assets" / "chart.png"
        assert expected.exists(), (
            f"Expected PNG at {expected}. stdout: {result.stdout}"
        )

    def test_does_not_write_next_to_template(self, tmp_path):
        """Chart PNG must NOT land next to the template file."""
        vault = tmp_path / "vault"
        (vault / "wiki" / "views" / "assets").mkdir(parents=True)
        subprocess.run(
            [sys.executable, str(CHART_PY), "--vault", str(vault)],
            capture_output=True,
        )
        sidecar = CHART_PY.parent / "assets" / "chart.png"
        assert not sidecar.exists(), "PNG landed next to template — path fix not applied"
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python -m pytest tests/test_chart.py -v
```

Expected: `test_writes_to_vault_views_assets` FAILS (PNG written to wrong location or
import error), `test_does_not_write_next_to_template` PASSES or FAILS.

> **Note:** `matplotlib` must be installed. If not: `pip install matplotlib`

- [ ] **Step 3: Update `skills/view-builder/templates/chart.py`**

Replace the entire file with:

```python
#!/usr/bin/env python3
"""chart.py — Generate a chart PNG for a vault view.

Writes the PNG to wiki/views/assets/ under the vault root so the output
lands alongside other view assets, not next to this template file.

Adapt TITLE, XLABEL, YLABEL, labels, and values for each chart you need.
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def build_chart(vault_root: Path, output_name: str = "chart.png") -> Path:
    """Generate the chart and return the path of the written PNG."""
    output_dir = vault_root / "wiki" / "views" / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Customise below -------------------------------------------------
    TITLE = "Chart title"
    XLABEL = "X"
    YLABEL = "Y"
    labels = ["A", "B", "C"]
    values = [12, 19, 7]
    # --- End customisation -----------------------------------------------

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values)
    ax.set_title(TITLE)
    ax.set_xlabel(XLABEL)
    ax.set_ylabel(YLABEL)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    out = output_dir / output_name
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a chart PNG for a vault view.")
    parser.add_argument(
        "--vault", type=Path, default=Path.cwd(),
        help="Vault root directory (default: current directory)",
    )
    parser.add_argument(
        "--output", default="chart.png",
        help="Output filename (default: chart.png)",
    )
    args = parser.parse_args()
    out = build_chart(args.vault, args.output)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests**

```bash
python -m pytest tests/test_chart.py -v
```

Expected: Both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/view-builder/templates/chart.py tests/test_chart.py
git commit -m "fix: chart.py writes to wiki/views/assets/ instead of next to template"
```

---

## Task 7: Add `/retry` for failed inbox URLs

`fetch_inbox.py` appends `⚠ reason` to failed entries, but `UNCHECKED_PATTERN`
(`\s*$`) no longer matches them — retrying requires manual marker deletion. This adds a
`FAILED_PATTERN`, a `find_failed_entries()` function, extends `update_inbox()` to
handle ⚠-marked lines, and adds a `--retry` CLI mode. A new `commands/retry.md` and
installer entry complete the feature.

**Files:**
- Create: `commands/retry.md`
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py`
- Modify: `init_vault.py` (COMMANDS list)
- Extend: `tests/test_fetch_inbox.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_fetch_inbox.py`:

```python
class TestFailedPattern:
    """FAILED_PATTERN must match ⚠-marked unchecked lines."""

    def test_matches_failed_line(self):
        from fetch_inbox import FAILED_PATTERN
        line = "- [ ] https://example.com ⚠ connection timeout"
        m = FAILED_PATTERN.match(line)
        assert m is not None
        assert m.group(1) == "https://example.com"

    def test_does_not_match_checked_line(self):
        from fetch_inbox import FAILED_PATTERN
        line = "- [x] https://example.com → `raw/web/foo/` (2026-01-01)"
        assert FAILED_PATTERN.match(line) is None

    def test_does_not_match_plain_unchecked(self):
        from fetch_inbox import FAILED_PATTERN
        line = "- [ ] https://example.com"
        assert FAILED_PATTERN.match(line) is None


class TestFindFailedEntries:
    """find_failed_entries should parse ⚠-marked lines into InboxEntry objects."""

    def test_finds_one_failed(self):
        from fetch_inbox import find_failed_entries
        text = "- [ ] https://example.com ⚠ connection timeout\n"
        entries = find_failed_entries(text)
        assert len(entries) == 1
        assert entries[0].url == "https://example.com"

    def test_ignores_plain_unchecked(self):
        from fetch_inbox import find_failed_entries
        text = "- [ ] https://example.com\n"
        assert find_failed_entries(text) == []

    def test_ignores_checked(self):
        from fetch_inbox import find_failed_entries
        text = "- [x] https://example.com → `raw/web/foo/` (2026-01-01)\n"
        assert find_failed_entries(text) == []

    def test_preserves_sub_bullets(self):
        from fetch_inbox import find_failed_entries
        text = (
            "- [ ] https://example.com ⚠ timeout\n"
            "  - tags: ai, research\n"
            "  - note: focus on section 3\n"
        )
        entries = find_failed_entries(text)
        assert entries[0].tags == ["ai", "research"]
        assert entries[0].note == "focus on section 3"

    def test_empty_inbox(self):
        from fetch_inbox import find_failed_entries
        assert find_failed_entries("") == []


class TestUpdateInboxRetry:
    """update_inbox must update ⚠ lines when a retry succeeds or fails."""

    def test_clears_warning_on_success(self, tmp_path):
        from fetch_inbox import update_inbox, FetchResult
        inbox = tmp_path / "inbox.md"
        inbox_text = "- [ ] https://example.com ⚠ connection timeout\n"
        result = FetchResult(
            url="https://example.com", ok=True, kind="html",
            out_path=tmp_path / "raw" / "web" / "example-abc12345",
        )
        new_text = update_inbox(inbox, inbox_text, [result])
        assert "⚠" not in new_text
        assert "[x]" in new_text
        assert "https://example.com" in new_text

    def test_updates_warning_reason_on_failure(self, tmp_path):
        from fetch_inbox import update_inbox, FetchResult
        inbox = tmp_path / "inbox.md"
        inbox_text = "- [ ] https://example.com ⚠ old error\n"
        result = FetchResult(
            url="https://example.com", ok=False, kind="failed",
            reason="new error: 503",
        )
        new_text = update_inbox(inbox, inbox_text, [result])
        assert "new error: 503" in new_text
        assert "old error" not in new_text
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m pytest tests/test_fetch_inbox.py::TestFailedPattern \
                tests/test_fetch_inbox.py::TestFindFailedEntries \
                tests/test_fetch_inbox.py::TestUpdateInboxRetry -v
```

Expected: All FAIL — `FAILED_PATTERN` and `find_failed_entries` don't exist yet.

- [ ] **Step 3: Add `FAILED_PATTERN` and `find_failed_entries` to `fetch_inbox.py`**

After the existing `UNCHECKED_PATTERN` constant (line 81), add:

```python
# Matches an unchecked entry that was previously attempted but failed:
#   - [ ] https://example.com ⚠ reason text
# Used by --retry mode to select only failed entries for re-attempt.
FAILED_PATTERN = re.compile(r"^- \[ \] (https?://\S+) ⚠ .+$")
```

After the `find_unchecked_entries()` function, add:

```python
def find_failed_entries(inbox_text: str) -> list[InboxEntry]:
    """Parse inbox.md and return only previously-failed entries (⚠-marked).

    Picks up sub-bullets (tags/note) so retry context is preserved from
    the original fetch attempt.
    """
    stripped = re.sub(r"<!--.*?-->", "", inbox_text, flags=re.DOTALL)
    lines = stripped.splitlines()
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = FAILED_PATTERN.match(line)
        if match:
            entry = InboxEntry(
                url=match.group(1).strip(),
                line_index=i,
                raw_line=line,
            )
            # Collect indented sub-bullets (tags/note) that may follow.
            j = i + 1
            while j < len(lines):
                sub = lines[j]
                if not sub.startswith(" ") and not sub.startswith("\t"):
                    break
                sub_stripped = sub.strip()
                if sub_stripped.startswith("- tags:"):
                    raw_tags = sub_stripped[len("- tags:"):].strip()
                    entry.tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                elif sub_stripped.startswith("- note:"):
                    entry.note = sub_stripped[len("- note:"):].strip()
                j += 1
            entries.append(entry)
            i = j
        else:
            i += 1
    return entries
```

- [ ] **Step 4: Extend `update_inbox()` to recognise ⚠-marked lines**

In `update_inbox()`, the main loop currently matches only `UNCHECKED_PATTERN`. Add a
secondary match for `FAILED_PATTERN` so retried URLs can be updated:

Find this block inside `update_inbox()`:

```python
        match = UNCHECKED_PATTERN.match(line)
        if not match:
            out_lines.append(line)
            i += 1
            continue

        url = match.group(1).strip()
```

Replace with:

```python
        match = UNCHECKED_PATTERN.match(line)
        failed_match = FAILED_PATTERN.match(line) if not match else None
        if not match and not failed_match:
            out_lines.append(line)
            i += 1
            continue

        url = (match or failed_match).group(1).strip()
```

- [ ] **Step 5: Add `retry` parameter to `process_vault()` and `--retry` to `main()`**

At the top of `process_vault()`, the function signature becomes:

```python
def process_vault(vault: Path, dry_run: bool = False, retry: bool = False) -> int:
```

Inside `process_vault()`, replace:

```python
    entries = find_unchecked_entries(inbox_text)
```

with:

```python
    entries = find_failed_entries(inbox_text) if retry else find_unchecked_entries(inbox_text)
```

And update the "Inbox empty" message to indicate mode:

```python
    if not entries:
        mode_label = "No failed URLs" if retry else "Inbox empty"
        print(f"{mode_label}. Nothing to do.")
        return 0
```

In `main()`, add `--retry` to the argument parser after `--dry-run`:

```python
    parser.add_argument(
        "--retry",
        action="store_true",
        help="Re-attempt only previously-failed (⚠-marked) inbox entries.",
    )
```

And update the `process_vault` call:

```python
    return process_vault(args.vault, dry_run=args.dry_run, retry=args.retry)
```

- [ ] **Step 6: Run the failing tests**

```bash
python -m pytest tests/test_fetch_inbox.py::TestFailedPattern \
                tests/test_fetch_inbox.py::TestFindFailedEntries \
                tests/test_fetch_inbox.py::TestUpdateInboxRetry -v
```

Expected: All PASS.

- [ ] **Step 7: Run the full test suite**

```bash
python -m pytest -v
```

Expected: All tests PASS.

- [ ] **Step 8: Create `commands/retry.md`**

```markdown
---
description: Retry previously-failed inbox URLs. Finds unchecked entries
  marked with ⚠, re-attempts each, and clears the ⚠ marker on success.
  Successful retries are moved to the Processed section; persistent failures
  keep the ⚠ marker with a fresh reason. Does not touch plain unchecked
  entries or already-processed entries.
---

# /retry — Retry failed inbox URLs

## When to use

After `/fetch` marks some URLs with `⚠ reason` — for example after a transient
network error, a temporary server outage, or after adding authentication — when
you want to re-attempt only those specific URLs.

Untouched unchecked entries (`- [ ] url`) and already-processed entries (`[x]`)
are never touched by `/retry`.

## How to run

```bash
python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --retry
```

> **Windows:** replace `python3` with `python` in all commands above.

Or dry-run to preview which failed URLs would be retried:

```bash
python3 .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --retry --dry-run
```

## After running

1. Report the retry summary (✓ cleared, ⚠ still failing counts).
2. For any `⚠ ... — try playwright` URLs, offer to run `/playwright-fetch`
   to retrieve them via the browser.
3. When retried items succeed, offer to run `/ingest` on the newly
   downloaded files.

## What /retry does NOT do

- Does not touch plain unchecked entries (`- [ ] url` without ⚠).
- Does not re-download already-processed (`[x]`) entries.
- Does not bypass walled-domain or PDF-disabled restrictions — those
  failures persist until the user acts on them (Playwright, config change).
```

- [ ] **Step 9: Add `"retry"` to `init_vault.py:COMMANDS`**

```python
# Before:
COMMANDS = [
    "save", "view", "reflect", "forget", "lint",
    "promote", "refresh", "ingest", "fetch", "hot", "playwright-fetch", "review", "merge",
    "split",
]

# After:
COMMANDS = [
    "save", "view", "reflect", "forget", "lint",
    "promote", "refresh", "ingest", "fetch", "hot", "playwright-fetch", "review", "merge",
    "split", "retry",
]
```

- [ ] **Step 10: Extend `tests/test_installer.py` with retry tests**

Append to the `TestCommands` class in `tests/test_installer.py`:

```python
    def test_retry_in_commands(self):
        """retry must be in the COMMANDS list now that commands/retry.md exists."""
        assert "retry" in init_vault.COMMANDS

    def test_retry_md_exists(self):
        repo = Path(__file__).parent.parent
        assert (repo / "commands" / "retry.md").exists()
```

- [ ] **Step 11: Run the installer tests**

```bash
python -m pytest tests/test_installer.py -v
```

Expected: All 4 tests PASS (split and retry variants).

- [ ] **Step 12: Run the full test suite**

```bash
python -m pytest -v
```

Expected: All tests PASS.

- [ ] **Step 13: Commit**

```bash
git add skills/inbox-fetcher/scripts/fetch_inbox.py \
        commands/retry.md init_vault.py tests/test_fetch_inbox.py \
        tests/test_installer.py
git commit -m "feat: add /retry for failed inbox URLs, FAILED_PATTERN + --retry mode"
```

---

## Task 8: CLAUDE.md doc sync

Fix the four discrepancies the audit found. Pure documentation, no code.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Fix C1 — linter check count**

Find the sentence mentioning 4 checks (around line 224). The current text is:
```
Deterministic checks only (dead links, missing frontmatter, naming consistency, view staleness).
```

Replace with:
```
Deterministic checks only (14 checks: dead links, based_on dead links, orphans, duplicates,
missing metadata, inconsistent naming, stale sources, gaps, view staleness, missing
cross-references, PDF index, conversations schema, drop zone, index sync). No LLM cost.
Full check list in `vault-linter/SKILL.md`.
```

- [ ] **Step 2: Fix C2 — add missing commands to the slash command list**

Find the `## Slash commands` section (around lines 314-325). The current list omits
`/ingest`, `/lint`, `/split`, `/retry`. Add them:

```markdown
- `/ingest [slug]` — compile raw sources into wiki pages and sources
- `/lint` — run the 14-check deterministic vault health pass
- `/split <page> <new-page-A> <new-page-B>` — split an overgrown page into two focused ones
- `/retry` — re-attempt previously-failed (⚠) inbox URLs
```

(Insert `/ingest` and `/lint` in alphabetical/logical order among the existing entries,
and add `/split` and `/retry` near the end.)

- [ ] **Step 3: Fix C3 — command path prefixes**

Find the four bare `commands/*.md` references in the Operations section and prepend
`.claude/`. For example:

```markdown
# Before:
See `commands/review.md` for the full protocol with scoping options

# After:
See `.claude/commands/review.md` for the full protocol with scoping options
```

Apply the same fix to `commands/promote.md`, `commands/refresh.md`, and
`commands/merge.md` references (lines ~210, 230, 238, 247 of the original).

- [ ] **Step 4: Fix C4 — sync MERGE/SPLIT references**

Find the section that says the SPLIT protocol lives inside `merge.md` (near line 247 or
wherever "MERGE" is described in the Skill-dispatch table or the MERGE operation
description). Update to reflect that SPLIT now has its own command file:

```markdown
# Before (wherever it references both):
See `commands/merge.md` for the full MERGE and SPLIT protocols.

# After:
See `.claude/commands/merge.md` for MERGE. For SPLIT, see `.claude/commands/split.md`.
```

- [ ] **Step 5: Update `README.md` commands tree**

`README.md` contains a commands/ tree listing (around line 42). Two changes needed:

1. The line `├── merge.md              /merge, /split` now covers MERGE only.
   Replace with two lines:
   ```
   ├── merge.md              /merge
   ├── split.md              /split
   ```

2. Add a new entry for `/retry`:
   ```
   ├── retry.md              /retry
   ```

Also check the "Quick start" section and any other mentions of slash commands in
README.md — add `/retry` and `/split` (as standalone) to any such list.

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: sync CLAUDE.md and README — 14 checks, full slash-command list, path prefixes"
```

---

## Task 9: End-to-end verification

- [ ] **Step 1: Run full test suite — must be all green**

```bash
python -m pytest -v
```

Expected: All tests PASS. No skipped, no errors.

- [ ] **Step 2: Bootstrap a vault non-interactively and verify deployment**

```bash
python init_vault.py --yes /tmp/verify-vault
```

Check outputs:
- `.claude/commands/split.md` exists
- `.claude/commands/retry.md` exists
- `.claude/skills/shared/linkutil.py` exists
- `.claude/skills/shared/find_backlinks.py` exists (unchanged)
- Content of `.claude/commands/fetch.md` contains "Windows" note
- Content of `.claude/commands/review.md` contains `review_scope.py`

- [ ] **Step 3: Verify `--retry` flag works in the deployed vault**

```bash
cd /tmp/verify-vault
echo "- [ ] https://httpstat.us/503 ⚠ 503 Service Unavailable" >> inbox.md
python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py --retry --dry-run
```

Expected output: `Found 1 URL(s) to process. [dry-run] would retry: https://httpstat.us/503`

- [ ] **Step 4: Clean up temp vault**

```bash
rm -rf /tmp/verify-vault
```

- [ ] **Step 5: Commit spec and plan if not already done**

```bash
git add features/specs/2026-05-29-llm-wiki-hardening-design.md \
        features/plans/2026-05-29-llm-wiki-hardening.md
git commit -m "docs: add hardening spec and implementation plan"
```
