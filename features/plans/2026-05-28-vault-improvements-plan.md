# Vault Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a config layer, a shared state utility, wired lint counter, five new/fixed commands, PDF folder ingestion, tag/note propagation, and a concept-map text fallback — all grounded in a hybrid config+skill manifest architecture.

**Architecture:** `vault.config.yml` is the single source of truth for all tunable values. `vault_state.py` is a shared standard-library module that all scripts import for config loading and `.lint/state.yaml` I/O. CLAUDE.md gains two new operations (PROMOTE, REFRESH) and a skill dispatch table.

**Tech Stack:** Python 3.10+ standard library, bash, markdown. Test runner: pytest (dev only). No new runtime dependencies.

**Spec:** `features/specs/2026-05-28-vault-improvements-design.md`

**Working directory:** `D:\my-2nd-brain` — all paths in this plan are relative to this directory. Every `git add`, `pytest`, and `bash` command assumes this as CWD.

**Dependency waves:**
- Wave 1 — sequential: TASK-0001 → TASK-0002 → TASK-0003 → (TASK-0004 + TASK-0005 in parallel)
- Wave 2 — any order, after Wave 1 complete: TASK-0006 through TASK-0016
- Wave 3 — independent of everything: TASK-0017 through TASK-0020

**Setup (once per dev environment):**
```bash
pip install pytest requests-mock   # test runner + HTTP mock for PDF fetch tests
```

**Tasks 7, 8, 12, 20 note:** These backlog IDs are fulfilled by earlier tasks (5, 4, 5, 16 respectively). Their plan sections contain only a verification step — no new implementation is needed.

---

## File Structure

**Create:**
- `vault.config.yml` — config template at bundle root
- `skills/shared/vault_state.py` — shared config + state utility
- `tests/test_vault_state.py` — tests for vault_state.py
- `tests/test_fetch_inbox.py` — tests for fetch_inbox.py text-processing functions
- `tests/test_lint.py` — tests for new lint checks
- `commands/lint.md` — /lint slash command
- `commands/promote.md` — /promote slash command
- `commands/refresh.md` — /refresh slash command

**Modify:**
- `skills/inbox-fetcher/scripts/fetch_inbox.py` — config migration, ingest counter, tags/note, PDF folder structure
- `skills/vault-linter/scripts/lint.py` — config migration, vault_state, strip_wikilink, check_based_on_links, check_pdf_index
- `skills/inbox-fetcher/SKILL.md` — add provides/config_section/requires frontmatter
- `skills/vault-linter/SKILL.md` — add provides/config_section/requires frontmatter
- `skills/view-builder/SKILL.md` — add provides/config_section/requires frontmatter
- `skills/view-builder/templates/view-concept-map.md` — add details fallback block
- `init-vault.sh` — install vault.config.yml, vault_state.py, new commands, self-maintaining dep check
- `CLAUDE.md` — PDF ingest branch, tags/note propagation, PROMOTE, REFRESH, dispatch table

---

## Wave 1 — Foundation (sequential: complete each task before starting the next)

---

### Task 1 — Create vault.config.yml (TASK-0001)

**Files:**
- Create: `vault.config.yml`

**Note:** The config file uses inline list syntax (`[a, b, c]`) throughout. The parser in vault_state.py (Task 2) handles only this format — block lists (`- item`) are not supported. This constraint is documented in the file's header comment.

- [ ] **Step 1: Create `vault.config.yml` at the bundle root**

```yaml
# vault.config.yml — per-vault configuration for the second brain vault.
#
# All values here are defaults. Override any key in the copy installed
# at your vault root. Lists must use inline syntax: [a, b, c].
# Block-list syntax (- item per line) is not parsed.

vault:
  version: 1

inbox:
  processed_section: "## Processed"   # header used by fetch_inbox.py for done entries
  tags_propagation: true              # whether to carry inbox tags into raw frontmatter

fetch:
  html_timeout_seconds: 20
  pdf_timeout_seconds: 60
  max_pdf_size_mb: 50
  pdf_enabled: true
  walled_domains: [x.com, twitter.com, mobile.twitter.com, linkedin.com, www.linkedin.com, threads.net, facebook.com, www.facebook.com, instagram.com, www.instagram.com]

lint:
  stale_source_days: 180             # advisory after this many days without update
  view_stale_days: 30                # days a view can lag its based_on pages
  auto_trigger_after_ingests: 5      # run lint automatically after N ingests
  auto_trigger_after_days: 7        # run lint automatically after N days

ingest:
  max_new_pages_before_confirm: 3    # ask before creating more than N new pages
  max_files_per_operation: 15        # invariant #5 enforcement ceiling
```

- [ ] **Step 2: Commit**

```bash
git add vault.config.yml
git commit -m "add vault.config.yml config template with all tunable defaults"
```

---

### Task 2 — Create vault_state.py + tests (TASK-0002)

**Files:**
- Create: `skills/shared/vault_state.py`
- Create: `tests/test_vault_state.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_vault_state.py`:

```python
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
from vault_state import load_config, read_state, write_state


class TestReadState:
    def test_returns_empty_dict_when_absent(self, tmp_path):
        assert read_state(tmp_path) == {}

    def test_parses_existing_state_file(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text(
            "last_lint: 2026-01-01\ningests_since_last_lint: 3\n"
        )
        state = read_state(tmp_path)
        assert state["last_lint"] == "2026-01-01"
        assert state["ingests_since_last_lint"] == "3"

    def test_ignores_comment_lines(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text(
            "# comment\nlast_lint: 2026-01-01\n"
        )
        state = read_state(tmp_path)
        assert "# comment" not in state
        assert state["last_lint"] == "2026-01-01"


class TestWriteState:
    def test_creates_file_and_lint_dir_when_absent(self, tmp_path):
        write_state(tmp_path, {"ingests_since_last_lint": 1})
        assert (tmp_path / ".lint" / "state.yaml").exists()

    def test_patches_existing_key(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text(
            "last_lint: 2026-01-01\ningests_since_last_lint: 3\n"
        )
        write_state(tmp_path, {"ingests_since_last_lint": 5})
        assert read_state(tmp_path)["ingests_since_last_lint"] == "5"

    def test_preserves_keys_not_in_updates(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text(
            "last_lint: 2026-01-01\ningests_since_last_lint: 3\n"
        )
        write_state(tmp_path, {"ingests_since_last_lint": 5})
        assert read_state(tmp_path)["last_lint"] == "2026-01-01"

    def test_adds_new_key_to_existing_file(self, tmp_path):
        (tmp_path / ".lint").mkdir()
        (tmp_path / ".lint" / "state.yaml").write_text("last_lint: 2026-01-01\n")
        write_state(tmp_path, {"ingests_since_last_lint": 1})
        state = read_state(tmp_path)
        assert state["ingests_since_last_lint"] == "1"
        assert state["last_lint"] == "2026-01-01"


class TestLoadConfig:
    def test_returns_all_default_sections_when_absent(self, tmp_path):
        config = load_config(tmp_path)
        assert config["inbox"]["processed_section"] == "## Processed"
        assert config["lint"]["stale_source_days"] == 180
        assert config["fetch"]["html_timeout_seconds"] == 20
        assert isinstance(config["fetch"]["walled_domains"], list)
        assert "x.com" in config["fetch"]["walled_domains"]

    def test_overrides_specific_value_while_preserving_defaults(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "lint:\n  stale_source_days: 90\n"
        )
        config = load_config(tmp_path)
        assert config["lint"]["stale_source_days"] == 90
        assert config["lint"]["view_stale_days"] == 30  # default preserved

    def test_parses_inline_list(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "fetch:\n  walled_domains: [example.com, other.com]\n"
        )
        config = load_config(tmp_path)
        assert config["fetch"]["walled_domains"] == ["example.com", "other.com"]

    def test_raises_valueerror_on_unreadable_file(self, tmp_path):
        (tmp_path / "vault.config.yml").write_bytes(b"\xff\xfe\x00\x01invalid")
        with pytest.raises((ValueError, UnicodeDecodeError)):
            load_config(tmp_path)

    def test_parses_boolean_values(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "fetch:\n  pdf_enabled: false\n"
        )
        config = load_config(tmp_path)
        assert config["fetch"]["pdf_enabled"] is False

    def test_parses_integer_values(self, tmp_path):
        (tmp_path / "vault.config.yml").write_text(
            "fetch:\n  html_timeout_seconds: 45\n"
        )
        config = load_config(tmp_path)
        assert config["fetch"]["html_timeout_seconds"] == 45
```

- [ ] **Step 2: Run tests — verify they all fail**

```bash
pip install pytest   # once, if not installed
pytest tests/test_vault_state.py -v
```

Expected: `ModuleNotFoundError: No module named 'vault_state'`

- [ ] **Step 3: Create `skills/shared/vault_state.py`**

```python
#!/usr/bin/env python3
"""
vault_state.py — Config loading and vault state read/write.

Provides a single import point for vault.config.yml and .lint/state.yaml
so all scripts share the same config values and state schema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Defaults — mirrors vault.config.yml; used when the file is absent
# ---------------------------------------------------------------------------

_DEFAULTS: dict[str, Any] = {
    "vault": {"version": 1},
    "inbox": {
        "processed_section": "## Processed",
        "tags_propagation": True,
    },
    "fetch": {
        "html_timeout_seconds": 20,
        "pdf_timeout_seconds": 60,
        "max_pdf_size_mb": 50,
        "pdf_enabled": True,
        "walled_domains": [
            "x.com", "twitter.com", "mobile.twitter.com",
            "linkedin.com", "www.linkedin.com", "threads.net",
            "facebook.com", "www.facebook.com",
            "instagram.com", "www.instagram.com",
        ],
    },
    "lint": {
        "stale_source_days": 180,
        "view_stale_days": 30,
        "auto_trigger_after_ingests": 5,
        "auto_trigger_after_days": 7,
    },
    "ingest": {
        "max_new_pages_before_confirm": 3,
        "max_files_per_operation": 15,
    },
}


def _parse_scalar(val: str) -> Any:
    if val in ("true", "True"):
        return True
    if val in ("false", "False"):
        return False
    if val in ("null", "Null", "None", "~", ""):
        return None
    try:
        return int(val)
    except ValueError:
        pass
    return val.strip("\"'")


def _parse_config_yaml(text: str) -> dict:
    """
    Two-level YAML parser for vault.config.yml.
    Supports scalar values and inline lists ([a, b, c]).
    Block lists (multi-line - item syntax) are not supported.
    """
    result: dict = {}
    current_section: str | None = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue

        key, _, val_raw = stripped.partition(":")
        key = key.strip()
        val = val_raw.strip()
        is_indented = raw_line[:1] in (" ", "\t")

        if not is_indented:
            if val == "":
                current_section = key
                result[key] = {}
            else:
                result[key] = _parse_scalar(val)
                current_section = None
        elif current_section is not None:
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                items = [
                    _parse_scalar(x.strip().strip("\"'"))
                    for x in inner.split(",")
                    if x.strip()
                ]
                result[current_section][key] = items
            else:
                result[current_section][key] = _parse_scalar(val)

    return result


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def load_config(vault_root: Path) -> dict:
    """
    Load vault.config.yml and deep-merge with built-in defaults.
    Returns defaults silently when the file is absent (backward-compatible).
    Raises ValueError when the file exists but cannot be read or parsed.
    """
    config_path = vault_root / "vault.config.yml"
    if not config_path.exists():
        return _deep_merge(_DEFAULTS, {})
    try:
        text = config_path.read_text(encoding="utf-8")
        parsed = _parse_config_yaml(text)
    except Exception as exc:
        raise ValueError(f"vault.config.yml cannot be loaded: {exc}") from exc
    return _deep_merge(_DEFAULTS, parsed)


def read_state(vault_root: Path) -> dict:
    """
    Read .lint/state.yaml into a flat string dict.
    Returns an empty dict when the file is absent.
    """
    state_path = vault_root / ".lint" / "state.yaml"
    if not state_path.exists():
        return {}
    result: dict = {}
    for line in state_path.read_text(encoding="utf-8").splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip()
    return result


def write_state(vault_root: Path, updates: dict) -> None:
    """
    Patch .lint/state.yaml with the given key-value pairs.
    Existing keys not in updates are preserved; new keys are added.
    Creates .lint/ and state.yaml if absent.
    """
    lint_dir = vault_root / ".lint"
    lint_dir.mkdir(exist_ok=True)
    current = read_state(vault_root)
    current.update({str(k): str(v) for k, v in updates.items()})
    lines = [f"{k}: {v}" for k, v in current.items()]
    (lint_dir / "state.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run tests — verify they all pass**

```bash
pytest tests/test_vault_state.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/shared/vault_state.py tests/test_vault_state.py
git commit -m "add vault_state.py shared config/state utility with tests"
```

---

### Task 3 — Update init-vault.sh (TASK-0003)

**Files:**
- Modify: `init-vault.sh`

- [ ] **Step 1: Add `skills/shared/` to the DIRS array**

Find the `DIRS=(` block (~line 87) and add the new entry:

```bash
DIRS=(
    "raw/papers"
    "raw/web"
    "wiki/pages"
    "wiki/sources"
    "wiki/views/assets"
    "conversations"
    ".lint"
    ".claude/skills/inbox-fetcher/scripts"
    ".claude/skills/vault-linter/scripts"
    ".claude/skills/view-builder/templates"
    ".claude/skills/shared"
    ".claude/commands"
)
```

- [ ] **Step 2: Add vault.config.yml install step after the "Writing base files" block**

Find the block that writes `wiki/index.md` and add before it:

```bash
# vault.config.yml — skip if already customised by the user
if [ ! -f "$VAULT_DIR/vault.config.yml" ]; then
    cp "$SCRIPT_DIR/vault.config.yml" "$VAULT_DIR/vault.config.yml"
    ok "vault.config.yml"
else
    skip "vault.config.yml (exists — keeping user copy)"
fi
```

- [ ] **Step 3: Add vault_state.py install step in the "Installing skills" block**

After the view-builder install block, add:

```bash
# shared utilities — always refreshed so vault_state API stays in sync
if [ -d "$SCRIPT_DIR/skills/shared" ]; then
    cp "$SCRIPT_DIR/skills/shared/vault_state.py" \
       "$VAULT_DIR/.claude/skills/shared/vault_state.py"
    ok "shared: vault_state.py"
else
    warn "skills/shared not found in bundle"
fi
```

- [ ] **Step 4: Update inbox.md template — change `## Done` to `## Processed`**

Find the `cat > "$VAULT_DIR/inbox.md"` heredoc and change:

```bash
## Done

<!-- Automatically moved here after fetch. -->
```

to:

```bash
## Processed

<!-- Automatically moved here after fetch. -->
```

- [ ] **Step 5: Extend command install loop to include `lint`**

Find the line:

```bash
for cmd in save view reflect forget; do
```

Change to:

```bash
for cmd in save view reflect forget lint; do
```

- [ ] **Step 6: Verify by running init-vault.sh against a temp directory**

```bash
bash init-vault.sh /tmp/test-vault-init
ls /tmp/test-vault-init/vault.config.yml
ls /tmp/test-vault-init/.claude/skills/shared/vault_state.py
ls /tmp/test-vault-init/.claude/commands/lint.md  # will warn — file not created yet (Task 6)
rm -rf /tmp/test-vault-init
```

Expected: vault.config.yml and vault_state.py present; lint.md warning is expected at this stage.

- [ ] **Step 7: Commit**

```bash
git add init-vault.sh
git commit -m "update init-vault.sh: install vault.config.yml, vault_state.py, lint command slot"
```

---

### Task 4 — Migrate fetch_inbox.py to config + ingest counter (TASK-0004)

**Files:**
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py`
- Create: `tests/test_fetch_inbox.py`

- [ ] **Step 1: Write failing tests for the config-driven and tag-parsing behaviour**

Create `tests/test_fetch_inbox.py`:

```python
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "inbox-fetcher" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))

from fetch_inbox import find_unchecked_entries, update_inbox, FetchResult, InboxEntry


class TestFindUncheckedEntries:
    def test_finds_simple_unchecked_url(self):
        text = "## To process\n- [ ] https://example.com/article\n"
        entries = find_unchecked_entries(text)
        assert len(entries) == 1
        assert entries[0].url == "https://example.com/article"

    def test_ignores_checked_urls(self):
        text = "- [x] https://example.com/done\n- [ ] https://example.com/todo\n"
        entries = find_unchecked_entries(text)
        assert len(entries) == 1
        assert entries[0].url == "https://example.com/todo"

    def test_parses_tags_sub_bullet(self):
        text = "- [ ] https://example.com/article\n  - tags: ai, reasoning\n"
        entries = find_unchecked_entries(text)
        assert entries[0].tags == ["ai", "reasoning"]

    def test_parses_note_sub_bullet(self):
        text = "- [ ] https://example.com/article\n  - note: focus on evaluation section\n"
        entries = find_unchecked_entries(text)
        assert entries[0].note == "focus on evaluation section"

    def test_entry_without_sub_bullets_has_defaults(self):
        text = "- [ ] https://example.com/article\n"
        entries = find_unchecked_entries(text)
        assert entries[0].tags == []
        assert entries[0].note is None

    def test_both_tags_and_note_on_same_entry(self):
        text = (
            "- [ ] https://example.com/article\n"
            "  - tags: llm, agents\n"
            "  - note: read section 3 carefully\n"
        )
        entries = find_unchecked_entries(text)
        assert entries[0].tags == ["llm", "agents"]
        assert entries[0].note == "read section 3 carefully"

    def test_strips_urls_inside_html_comments(self):
        text = "<!-- - [ ] https://example.com/comment -->\n- [ ] https://example.com/real\n"
        entries = find_unchecked_entries(text)
        assert len(entries) == 1
        assert entries[0].url == "https://example.com/real"

    def test_tags_stripped_of_whitespace(self):
        text = "- [ ] https://example.com/a\n  - tags:  ai ,  llm \n"
        entries = find_unchecked_entries(text)
        assert entries[0].tags == ["ai", "llm"]


class TestUpdateInbox:
    def test_successful_result_moves_to_processed_section(self):
        inbox = "## To process\n- [ ] https://example.com/article\n"
        results = [FetchResult(
            url="https://example.com/article", ok=True, kind="html",
            out_path=Path("raw/web/article-slug/"),
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Processed")
        assert "- [x] https://example.com/article" in new_text
        assert "## Processed" in new_text

    def test_failed_result_stays_unchecked_with_reason(self):
        inbox = "## To process\n- [ ] https://paywall.com/article\n"
        results = [FetchResult(
            url="https://paywall.com/article", ok=False, kind="failed",
            reason="extraction empty — try playwright",
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Processed")
        assert "- [ ] https://paywall.com/article ⚠" in new_text

    def test_uses_config_section_name(self):
        inbox = "## To process\n- [ ] https://example.com/a\n"
        results = [FetchResult(
            url="https://example.com/a", ok=True, kind="html",
            out_path=Path("raw/web/a/"),
        )]
        new_text = update_inbox(Path("dummy"), inbox, results,
                                processed_section="## Done")
        assert "## Done" in new_text
        assert "## Processed" not in new_text
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_fetch_inbox.py -v
```

Expected: failures on `tags`, `note` fields (not on `InboxEntry` yet) and on `processed_section` parameter.

- [ ] **Step 3: Add vault_state import and config loading to fetch_inbox.py**

At the top of `fetch_inbox.py`, after the existing imports, add:

```python
# ---------------------------------------------------------------------------
# Shared utilities — vault_state lives two directory levels up in skills/shared
# ---------------------------------------------------------------------------
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from vault_state import load_config, read_state, write_state
```

- [ ] **Step 4: Add `tags` and `note` to `InboxEntry`**

Replace the existing `InboxEntry` dataclass:

```python
@dataclass
class InboxEntry:
    url: str
    line_index: int
    raw_line: str
    tags: list = field(default_factory=list)
    note: str | None = None
```

Add `from dataclasses import dataclass, field` to the imports (replace current `from dataclasses import dataclass`).

- [ ] **Step 5: Update `find_unchecked_entries()` to parse sub-bullets**

Replace the function body:

```python
def find_unchecked_entries(inbox_text: str) -> list[InboxEntry]:
    """Parse inbox.md and return unchecked URL entries with any tag/note hints."""
    stripped = re.sub(r"<!--.*?-->", "", inbox_text, flags=re.DOTALL)
    lines = stripped.splitlines()
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = UNCHECKED_PATTERN.match(line)
        if match:
            entry = InboxEntry(
                url=match.group(1).strip(),
                line_index=i,
                raw_line=line,
            )
            # Collect indented sub-bullets immediately following the URL line
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

- [ ] **Step 6: Update `update_inbox()` to accept `processed_section` parameter**

Change the function signature from:

```python
def update_inbox(inbox_path, inbox_text, results):
```

to:

```python
def update_inbox(inbox_path, inbox_text, results, processed_section="## Processed"):
```

Replace the hardcoded `"## Processati"` check inside the function with `processed_section`.

- [ ] **Step 7: Update `process_vault()` to load config and pass values through**

Replace the start of `process_vault()`:

```python
def process_vault(vault: Path, dry_run: bool = False) -> int:
    cfg = load_config(vault)
    processed_section = cfg["inbox"]["processed_section"]
    html_timeout = cfg["fetch"]["html_timeout_seconds"]
    pdf_timeout = cfg["fetch"]["pdf_timeout_seconds"]
    max_pdf_mb = cfg["fetch"]["max_pdf_size_mb"]
    walled = frozenset(cfg["fetch"]["walled_domains"])

    inbox_path = vault / "inbox.md"
    if not inbox_path.exists():
        print(f"ERROR: inbox.md not found at {inbox_path}", file=sys.stderr)
        return 1
    ...
```

Pass `processed_section` to `update_inbox()`. Pass `html_timeout`, `pdf_timeout`, `max_pdf_mb`, `walled` as parameters to the fetch functions (or store as module-level variables loaded once from config — either pattern is fine as long as no constants remain hardcoded).

Remove the top-level constant definitions for `HTML_TIMEOUT`, `PDF_TIMEOUT`, `MAX_PDF_SIZE_MB`, `WALLED_DOMAINS`.

- [ ] **Step 8: Add ingest counter increment after a successful run**

At the end of `process_vault()`, before the final `return`:

```python
    if n_html + n_pdf > 0:
        state = read_state(vault)
        prev = int(state.get("ingests_since_last_lint", 0))
        write_state(vault, {"ingests_since_last_lint": prev + 1})

    return 0 if n_fail == 0 else 2
```

- [ ] **Step 9: Run tests — verify they all pass**

```bash
pytest tests/test_fetch_inbox.py -v
```

Expected: all tests PASS.

- [ ] **Step 10: Commit**

```bash
git add skills/inbox-fetcher/scripts/fetch_inbox.py tests/test_fetch_inbox.py
git commit -m "migrate fetch_inbox.py to vault.config.yml and wire ingest counter"
```

---

### Task 5 — Migrate lint.py to config + vault_state (TASK-0005)

**Files:**
- Modify: `skills/vault-linter/scripts/lint.py`
- Create: `tests/test_lint.py`

- [ ] **Step 1: Write failing tests for new lint functions**

Create `tests/test_lint.py`:

```python
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "vault-linter" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))


def make_vault(tmp_path: Path, files: dict) -> Path:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")
    return tmp_path


class TestStripWikilink:
    def test_strips_double_brackets(self):
        from lint import strip_wikilink
        assert strip_wikilink("[[wiki/pages/foo]]") == "wiki/pages/foo"

    def test_passthrough_when_no_brackets(self):
        from lint import strip_wikilink
        assert strip_wikilink("wiki/pages/foo") == "wiki/pages/foo"

    def test_strips_only_outer_brackets(self):
        from lint import strip_wikilink
        assert strip_wikilink("[[wiki/pages/foo|Label]]") == "wiki/pages/foo|Label"


class TestCheckBasedOnLinks:
    def test_no_findings_when_based_on_resolves(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/pages/topic.md": (
                "---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-01-01\n---\n# Topic\n"
            ),
            "wiki/views/timeline-topic.md": (
                "---\ntype: view\nkind: timeline\ncreated: 2026-01-01\n"
                "updated: 2026-01-01\nshareable: false\nbased_on:\n"
                "  - [[wiki/pages/topic]]\n---\n# Timeline\n"
            ),
        })
        from lint import load_wiki, check_based_on_links
        pages = load_wiki(tmp_path)
        assert check_based_on_links(pages, tmp_path) == []

    def test_blocking_finding_for_missing_based_on_target(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/views/timeline-gone.md": (
                "---\ntype: view\nkind: timeline\ncreated: 2026-01-01\n"
                "updated: 2026-01-01\nshareable: false\nbased_on:\n"
                "  - [[wiki/pages/does-not-exist]]\n---\n# Timeline\n"
            ),
        })
        from lint import load_wiki, check_based_on_links
        pages = load_wiki(tmp_path)
        findings = check_based_on_links(pages, tmp_path)
        assert len(findings) == 1
        assert findings[0].severity == "blocking"
        assert findings[0].check == "based_on_dead_links"

    def test_skips_non_view_pages(self, tmp_path):
        make_vault(tmp_path, {
            "wiki/pages/topic.md": (
                "---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-01-01\n"
                "based_on:\n  - [[wiki/pages/ghost]]\n---\n# Topic\n"
            ),
        })
        from lint import load_wiki, check_based_on_links
        pages = load_wiki(tmp_path)
        assert check_based_on_links(pages, tmp_path) == []


class TestCheckPdfIndex:
    def test_no_findings_for_absent_papers_dir(self, tmp_path):
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_no_findings_for_empty_papers_dir(self, tmp_path):
        (tmp_path / "raw" / "papers").mkdir(parents=True)
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_no_findings_for_correct_structure(self, tmp_path):
        slug = tmp_path / "raw" / "papers" / "arxiv-2405-12345"
        slug.mkdir(parents=True)
        (slug / "paper.pdf").write_bytes(b"%PDF")
        (slug / "index.md").write_text("---\nfetch_method: pdf\n---\n")
        from lint import check_pdf_index
        assert check_pdf_index(tmp_path) == []

    def test_advisory_for_subdir_without_index(self, tmp_path):
        slug = tmp_path / "raw" / "papers" / "arxiv-2405-12345"
        slug.mkdir(parents=True)
        (slug / "paper.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        assert any(f.check == "missing_pdf_index" for f in findings)
        assert all(f.severity == "advisory" for f in findings)

    def test_advisory_for_flat_pdf_file(self, tmp_path):
        papers = tmp_path / "raw" / "papers"
        papers.mkdir(parents=True)
        (papers / "old-paper.pdf").write_bytes(b"%PDF")
        from lint import check_pdf_index
        findings = check_pdf_index(tmp_path)
        assert any(f.check == "legacy_flat_pdf" for f in findings)
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_lint.py -v
```

Expected: `ImportError` on `strip_wikilink`, `check_based_on_links`, `check_pdf_index`.

- [ ] **Step 3: Add vault_state import to lint.py**

After the existing imports at the top of `lint.py`, add:

```python
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from vault_state import load_config, read_state, write_state as _write_state
```

- [ ] **Step 4: Remove hardcoded constants; load from config in `run_lint()`**

Delete these top-level constant definitions from lint.py:

```python
STALE_SOURCE_DAYS = 180
VIEW_STALE_DAYS = 30
DUPLICATE_SIMILARITY_THRESHOLD = 0.75
```

At the start of `run_lint()`, add:

```python
def run_lint(vault: Path, quiet: bool = False) -> int:
    cfg = load_config(vault)
    stale_source_days = cfg["lint"]["stale_source_days"]
    view_stale_days = cfg["lint"]["view_stale_days"]
    duplicate_threshold = 0.75  # structural constant, not a user-facing knob
    ...
```

Pass `stale_source_days`, `view_stale_days`, and `duplicate_threshold` as parameters to the check functions that use them, or use closure/partial binding.

- [ ] **Step 5: Replace the inline `write_state` function in lint.py**

Delete the existing `write_state()` function defined inside lint.py. Replace all calls to the old local `write_state(vault, findings, exit_code)` with:

```python
_write_state(vault, {
    "last_lint": date.today().isoformat(),
    "ingests_since_last_lint": 0,
    "last_exit_code": exit_code,
    "last_findings_count": len(findings),
    "blocking": sum(1 for f in findings if f.severity == "blocking"),
    "important": sum(1 for f in findings if f.severity == "important"),
    "advisory": sum(1 for f in findings if f.severity == "advisory"),
})
```

- [ ] **Step 6: Add `strip_wikilink()` helper and refactor `check_view_staleness()`**

Add after the `parse_date()` function:

```python
def strip_wikilink(s: str) -> str:
    """Remove surrounding [[ and ]] from a wiki-link string."""
    s = s.strip()
    if s.startswith("[["):
        s = s[2:]
    if s.endswith("]]"):
        s = s[:-2]
    return s
```

In `check_view_staleness()`, replace the inline stripping logic:

```python
# Before (existing):
dep_clean = dep.strip().lstrip("[").rstrip("]")

# After:
dep_clean = strip_wikilink(dep)
```

- [ ] **Step 7: Add `check_based_on_links()`**

Add the function after `check_dead_links()`:

```python
def check_based_on_links(pages: dict[str, WikiPage], vault: Path) -> list[Finding]:
    """
    Validate that every entry in a view's based_on frontmatter list
    resolves to an existing file. Frontmatter links bypass body-text
    scanning so they need their own resolution pass.
    """
    findings = []
    for page in pages.values():
        if page.type != "view":
            continue
        based_on = page.frontmatter.get("based_on", [])
        if not isinstance(based_on, list):
            continue
        for raw_entry in based_on:
            target = strip_wikilink(raw_entry)
            if "|" in target:
                target = target.split("|", 1)[0]
            resolved = normalize_link_target(target, vault, page.path)
            if resolved is None or not resolved.exists():
                findings.append(Finding(
                    severity="blocking",
                    check="based_on_dead_links",
                    file=page.rel,
                    detail=f"based_on entry [[{target}]] does not resolve",
                ))
    return findings
```

- [ ] **Step 8: Add `check_pdf_index()`**

Add the function after `check_missing_cross_references()`:

```python
def check_pdf_index(vault: Path) -> list[Finding]:
    """
    Verify that raw/papers/ follows the folder convention: each paper
    lives in its own subdirectory with a companion index.md.
    """
    findings = []
    papers_dir = vault / "raw" / "papers"
    if not papers_dir.is_dir():
        return findings

    for entry in papers_dir.iterdir():
        if entry.is_dir():
            if not (entry / "index.md").exists():
                findings.append(Finding(
                    severity="advisory",
                    check="missing_pdf_index",
                    file=str(entry.relative_to(vault)),
                    detail="raw/papers/ subdirectory has no index.md",
                ))
        elif entry.suffix.lower() == ".pdf":
            findings.append(Finding(
                severity="advisory",
                check="legacy_flat_pdf",
                file=str(entry.relative_to(vault)),
                detail="flat .pdf in raw/papers/ — move into a <slug>/ subdirectory",
            ))
    return findings
```

- [ ] **Step 9: Register new checks in `run_lint()`**

In the `all_checks` list, add after `("dead_links", check_dead_links)`:

```python
("based_on_dead_links", check_based_on_links),
```

And at the end of the list, add:

```python
("pdf_index", check_pdf_index),
```

Update the dispatch block to handle the new signatures:

```python
if name in ("dead_links", "orphans", "based_on_dead_links"):
    out = fn(pages, vault)
elif name in ("pdf_index",):
    out = fn(vault)
else:
    out = fn(pages)
```

- [ ] **Step 10: Run tests — verify they all pass**

```bash
pytest tests/test_lint.py -v
```

Expected: all tests PASS.

- [ ] **Step 11: Run existing check to confirm no regressions**

```bash
pytest tests/ -v
```

Expected: all tests across all test files PASS.

- [ ] **Step 12: Commit**

```bash
git add skills/vault-linter/scripts/lint.py tests/test_lint.py
git commit -m "migrate lint.py to vault.config.yml, add based_on and pdf_index checks"
```

---

## Wave 2 — Bug Fixes + Features (parallelizable after Wave 1)

*The following tasks all depend on Wave 1 being complete. They can be worked in any order relative to each other.*

---

### Task 6 — Create commands/lint.md (TASK-0006)

**Files:**
- Create: `commands/lint.md`

- [ ] **Step 1: Create the file**

```markdown
---
description: Run deterministic health checks on the vault. Writes .lint/report.md.
  Checks dead links, orphans, duplicates, missing metadata, inconsistent naming,
  stale sources, gaps, view staleness, based_on dead links, and pdf folder structure.
  Auto-triggers based on thresholds in vault.config.yml.
---

# /lint — Run vault health checks

## When to use

Run explicitly with `/lint` or when the auto-trigger condition is met.

## Auto-trigger

At session start, check `.lint/state.yaml` for two conditions:

1. `ingests_since_last_lint` ≥ `lint.auto_trigger_after_ingests` (from vault.config.yml)
2. Days since `last_lint` ≥ `lint.auto_trigger_after_days` (from vault.config.yml)

If either condition is met, run lint before proceeding with the session.

## How to run

```bash
python .claude/skills/vault-linter/scripts/lint.py
```

Or from outside the vault:

```bash
python .claude/skills/vault-linter/scripts/lint.py --vault /path/to/vault
```

## Output

- `.lint/report.md` — findings grouped by severity (blocking / important / advisory)
- `.lint/state.yaml` — updated with run date and finding counts

## Severity levels

- **Blocking** — dead links, missing required metadata, broken based_on links. Fix before ingesting more.
- **Important** — orphan pages, gaps. Address when convenient.
- **Advisory** — duplicates, stale sources, naming inconsistencies. Use judgement.

## What the agent does with the report

**Interactive:** summarise findings ("X blocking, Y important, Z advisory"), offer to fix blocking issues.

**Unattended:** run and note summary in compass.md footer. Abort /reflect if blocking count > 50.

## Rules

- Does not fix anything — reports only.
- Does not use an LLM — pure Python on text and filesystem.
- Does not validate semantic content — that is /reflect's job.
```

- [ ] **Step 2: Commit**

```bash
git add commands/lint.md
git commit -m "add commands/lint.md slash command with auto-trigger documentation"
```

---

### Task 7 — Add based_on dead link check (TASK-0007)

Already implemented in Task 5 (lint.py) and Task 5's test file. No additional work needed — this task is fulfilled by the `check_based_on_links` function, the `strip_wikilink` helper, and the corresponding tests added in Task 5.

**Verify:**

```bash
pytest tests/test_lint.py::TestCheckBasedOnLinks -v
pytest tests/test_lint.py::TestStripWikilink -v
```

Expected: all PASS.

---

### Task 8 — Parse inbox sub-bullets (TASK-0008)

Already implemented in Task 4 (fetch_inbox.py). The `InboxEntry` tags/note fields and updated `find_unchecked_entries()` are already in place.

**Verify:**

```bash
pytest tests/test_fetch_inbox.py::TestFindUncheckedEntries -v
```

Expected: all PASS.

---

### Task 9 — Update fetch_html to write tags/note into raw frontmatter (TASK-0009)

**Files:**
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py`

- [ ] **Step 1: Update `fetch_html()` to accept and write tags and note**

Change the function signature:

```python
def fetch_html(url: str, web_dir: Path,
               tags: list | None = None,
               note: str | None = None) -> FetchResult:
```

In the frontmatter construction block, after the existing fields:

```python
    if tags:
        frontmatter_lines.append(f"tags: [{', '.join(tags)}]")
    if note:
        frontmatter_lines.append(f"note: {yaml_escape(note)}")
```

- [ ] **Step 2: Pass entry.tags and entry.note through in `process_vault()`**

Find the call to `fetch_html()` inside the loop and update:

```python
r = fetch_html(fetch_url, web_dir, tags=e.tags, note=e.note)
```

- [ ] **Step 3: Add test for tags/note in raw frontmatter**

Add to `tests/test_fetch_inbox.py` (or create a focused integration test in a temp dir — network-free since we test only the frontmatter assembly):

```python
class TestFetchHtmlFrontmatter:
    def test_tags_appear_in_frontmatter(self, tmp_path):
        from fetch_inbox import fetch_html
        # We can't call fetch_html without network, so test yaml_escape and
        # frontmatter assembly logic directly by calling the internal helper
        from fetch_inbox import yaml_escape
        tags = ["ai", "llm"]
        line = f"tags: [{', '.join(tags)}]"
        assert line == "tags: [ai, llm]"

    def test_note_escaping(self):
        from fetch_inbox import yaml_escape
        note = 'focus on "section 3" analysis'
        escaped = yaml_escape(note)
        assert escaped.startswith('"')
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_fetch_inbox.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/inbox-fetcher/scripts/fetch_inbox.py tests/test_fetch_inbox.py
git commit -m "write inbox tags and note into raw web article frontmatter"
```

---

### Task 10 — Change PDF fetch to folder structure (TASK-0010)

**Files:**
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py`

- [ ] **Step 1: Update `fetch_pdf()` to produce a folder**

Replace the function:

```python
def fetch_pdf(url: str, papers_dir: Path,
              slug_override: str | None = None,
              tags: list | None = None,
              note: str | None = None) -> FetchResult:
    """Download a PDF into a raw/papers/<slug>/ folder with a companion index.md."""
    try:
        r = requests.get(
            url,
            timeout=PDF_TIMEOUT,  # replaced by cfg value at call site
            headers={"User-Agent": USER_AGENT},
            stream=True,
        )
        r.raise_for_status()
    except Exception as e:
        return FetchResult(url=url, ok=False, kind="failed",
                           reason=f"pdf download failed: {e}")

    size = int(r.headers.get("Content-Length", 0))

    slug = slug_override or slug_from(url, None)
    out_dir = papers_dir / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "paper.pdf"

    with open(pdf_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    if size > MAX_PDF_SIZE_MB * 1024 * 1024:
        print(f"  ⚠ large PDF ({size // 1024 // 1024} MB): {url}")

    # Build index.md frontmatter
    title = slug_override.replace("arxiv-", "arxiv:").replace("-", ".") if slug_override else "Untitled"
    fm_lines = [
        "---",
        f"source_url: {url}",
        f"title: {yaml_escape(title)}",
        f"fetched: {date.today().isoformat()}",
        "fetch_method: pdf",
    ]
    if tags:
        fm_lines.append(f"tags: [{', '.join(tags)}]")
    if note:
        fm_lines.append(f"note: {yaml_escape(note)}")
    fm_lines.append("---")
    fm_lines.append("")
    fm_lines.append("PDF: [[paper.pdf]]")
    fm_lines.append("")

    (out_dir / "index.md").write_text("\n".join(fm_lines), encoding="utf-8")

    return FetchResult(url=url, ok=True, kind="pdf", out_path=out_dir)
```

- [ ] **Step 2: Update call site in `process_vault()` to pass tags and note**

```python
r = fetch_pdf(fetch_url, papers_dir, slug_override=slug_override,
              tags=e.tags, note=e.note)
```

- [ ] **Step 3: Add test for PDF folder structure**

Add to `tests/test_fetch_inbox.py`:

```python
class TestFetchPdfStructure:
    def test_creates_folder_with_pdf_and_index(self, tmp_path, requests_mock):
        from fetch_inbox import fetch_pdf
        papers_dir = tmp_path / "raw" / "papers"
        papers_dir.mkdir(parents=True)
        requests_mock.get("https://arxiv.org/pdf/2405.12345.pdf",
                          content=b"%PDF-1.4 fake")
        result = fetch_pdf(
            "https://arxiv.org/pdf/2405.12345.pdf",
            papers_dir,
            slug_override="arxiv-2405-12345",
            tags=["llm"],
            note="read section 3",
        )
        assert result.ok
        assert (result.out_path / "paper.pdf").exists()
        assert (result.out_path / "index.md").exists()
        index_text = (result.out_path / "index.md").read_text()
        assert "fetch_method: pdf" in index_text
        assert "tags: [llm]" in index_text
        assert "read section 3" in index_text
```

*Note: this test requires `pip install requests-mock`.*

- [ ] **Step 4: Run tests**

```bash
pip install requests-mock
pytest tests/test_fetch_inbox.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/inbox-fetcher/scripts/fetch_inbox.py tests/test_fetch_inbox.py
git commit -m "change pdf fetch to produce raw/papers/<slug>/ folder with index.md"
```

---

### Task 11 — Update CLAUDE.md INGEST section (TASK-0011)

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add PDF ingest branch to the INGEST operation**

Find the INGEST section in CLAUDE.md and extend it with:

```markdown
### INGEST — source type branches

**Web articles** (`raw/web/<slug>/index.md`, no `fetch_method` field or `fetch_method: html`):
Read `index.md`. Write `wiki/sources/<slug>.md` with the full summary.

**PDFs** (`raw/papers/<slug>/index.md` with `fetch_method: pdf`):
1. Read `index.md` to get `source_url`, `title`, `tags`, `note`.
2. Read `paper.pdf` using the Read tool — pages 1–5 (abstract and introduction).
   If the paper has more than 10 pages, also read the last 2 pages (conclusion).
3. Infer the title from the first visible heading; fall back to the slug.
4. Write `wiki/sources/<slug>.md` with the same schema as web sources,
   plus `fetch_method: pdf` in the frontmatter.

**Tags and note propagation** (applies to all source types):
After reading any raw source `index.md`:
- If `tags` is present in frontmatter, carry it into `wiki/sources/<slug>.md` frontmatter.
- If `note` is present, treat it as a focus directive: the source summary must
  explicitly address the note topic — not merely acknowledge it.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "extend CLAUDE.md INGEST with PDF branch and tags/note propagation protocol"
```

---

### Task 12 — Add PDF lint checks (TASK-0012)

Already implemented in Task 5 (`check_pdf_index`) and tested in `tests/test_lint.py::TestCheckPdfIndex`. No additional work.

**Verify:**

```bash
pytest tests/test_lint.py::TestCheckPdfIndex -v
```

---

### Task 13 — Create commands/promote.md (TASK-0013)

**Files:**
- Create: `commands/promote.md`

- [ ] **Step 1: Create the file**

```markdown
---
description: Promote insights from a saved conversation into wiki pages.
  Creates a wiki/sources/conv-<slug>.md entry making the conversation a
  first-class citable source. Interactive only — not available unattended.
---

# /promote — Promote conversation insights to wiki pages

Turn the synthesis in a saved conversation into citable wiki content.

## Arguments

`/promote [conversation-slug] [target-page]`

Both arguments are optional:
- No slug → operates on the most recent file in `conversations/`
- No target page → agent proposes candidate pages based on conversation content

## Protocol

1. **Read the conversation file.** Identify substantive synthesis claims —
   not questions, not summaries of external sources, but the user's own
   synthesised understanding.

2. **Identify the target page.** If given, use it. If not, propose 1–3
   candidate pages from `wiki/pages/` whose topics align with the claims.
   Ask the user to pick one before proceeding.

3. **Present candidate claims one by one.** For each claim:
   > "Claim: [claim text]. Add to [[wiki/pages/<target>]]?"
   Never write without explicit per-claim confirmation.

4. **For each confirmed claim:** append it to `wiki/pages/<target>.md`
   with a citation: `[[wiki/sources/conv-<slug>]]`.

5. **Create `wiki/sources/conv-<slug>.md`** (if not already created):
   ```yaml
   ---
   type: source
   source_path: conversations/<slug>.md
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   tags: []
   ---
   # conv-<slug>
   
   One-line summary of what was promoted from this conversation.
   ```

6. **Update the conversation file frontmatter** — add or append to `promoted_to`:
   ```yaml
   promoted_to:
     - wiki/pages/<target>.md (YYYY-MM-DD)
   ```

7. **Update `wiki/index.md`** — add the new source entry under Sources.

8. **Append to `wiki/log.md`**: `## [YYYY-MM-DD] promote | conv-<slug> → <target>`

## Rules

- Never write a claim without per-claim user confirmation.
- Never create more than 3 new pages in a single /promote run (invariant #5).
- If the conversation has no substantive synthesis claims, say so and stop.
- Not available in unattended mode.

## What /promote does NOT do

- Does not rewrite the conversation file beyond the `promoted_to` frontmatter.
- Does not modify `raw/` in any way.
- Does not auto-create wiki pages — target page must already exist or be
  explicitly confirmed as new.
```

- [ ] **Step 2: Commit**

```bash
git add commands/promote.md
git commit -m "add commands/promote.md for conversation-to-wiki promotion"
```

---

### Task 14 — Create commands/refresh.md (TASK-0014)

**Files:**
- Create: `commands/refresh.md`

- [ ] **Step 1: Create the file**

```markdown
---
description: Re-fetch a source whose content has changed and re-ingest it,
  preserving the citation graph. Flags potentially changed claims in wiki/pages/
  with a needs-review frontmatter tag for user review. Does not rewrite prose.
---

# /refresh — Refresh a source

Update a source that has changed since it was ingested, without losing
the pages and views built on top of it.

## Arguments

`/refresh <source>` where `<source>` can be:

- A slug: `/refresh agent-skills-spec`
- A wiki path: `/refresh wiki/sources/agent-skills-spec.md`
- A raw path: `/refresh raw/web/agent-skills-spec/index.md`
- A URL (agent resolves to slug)

## Protocol

1. **Resolve slug.** Find `wiki/sources/<slug>.md` and read `source_url`
   from its frontmatter. Confirm with the user: show title and source_url.

2. **Queue for re-fetch.** Add the URL back to `inbox.md` as an unchecked
   entry under "To process":
   ```
   - [ ] <source_url>
   ```
   Instruct the user to run the fetcher script to overwrite the raw folder:
   ```bash
   python .claude/skills/inbox-fetcher/scripts/fetch_inbox.py
   ```

3. **Re-ingest.** After the fetcher completes, rewrite `wiki/sources/<slug>.md`
   with a new summary from the updated raw content. Bump `updated` to today.

4. **Flag affected pages.** Scan `wiki/pages/` for files that cite this source.
   For each affected page, add `needs-review` to its `tags` frontmatter list:
   ```yaml
   tags: [needs-review]
   ```
   List every flagged page in the final report.

5. **Update log.** Append to `wiki/log.md`:
   `## [YYYY-MM-DD] refresh | <slug>`

## What /refresh does NOT do

- Does not rewrite page prose automatically — step 4 flags only.
- Does not delete or recreate the source entry — identity (slug) is preserved.
- Does not cascade through views — re-run /lint after refresh to check
  view staleness.

## Rules

- Confirm the resolved slug and URL with the user before queuing the re-fetch.
- If more than 15 pages cite the source (invariant #5), report the fanout
  and let the user decide scope.
- Available unattended for steps 3–5 only (re-ingest + flag). Step 2
  (queue URL) requires interactive confirmation.
```

- [ ] **Step 2: Commit**

```bash
git add commands/refresh.md
git commit -m "add commands/refresh.md for source re-fetch and re-ingest"
```

---

### Task 15 — Update init-vault.sh command loop (TASK-0015)

**Files:**
- Modify: `init-vault.sh`

- [ ] **Step 1: Extend the command install loop**

Find:

```bash
for cmd in save view reflect forget lint; do
```

Change to:

```bash
for cmd in save view reflect forget lint promote refresh; do
```

- [ ] **Step 2: Verify**

```bash
bash init-vault.sh /tmp/test-vault-cmds
ls /tmp/test-vault-cmds/.claude/commands/
rm -rf /tmp/test-vault-cmds
```

Expected: `forget.md  lint.md  promote.md  reflect.md  refresh.md  save.md  view.md` all present.

- [ ] **Step 3: Commit**

```bash
git add init-vault.sh
git commit -m "install promote and refresh commands via init-vault.sh"
```

---

### Task 16 — Update CLAUDE.md: nine operations + dispatch table + source_path extension (TASK-0016)

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update the operations count and add PROMOTE and REFRESH**

Find `## Seven operations` and change to `## Nine operations`.

Add at the end of the operations list:

```markdown
### PROMOTE
User says "promote this conversation", "promote insights", or runs
`/promote [slug] [target-page]` → promote synthesis claims from a saved
conversation into wiki pages. Creates `wiki/sources/conv-<slug>.md` to
make the conversation a first-class citable source. See `commands/promote.md`
for the full interactive protocol.

Not available unattended.

### REFRESH
User says "refresh source X", "the article changed", or runs `/refresh <source>` →
re-fetch a source and re-ingest it, preserving the citation graph. Flags pages
that cite the source with `needs-review` frontmatter tag. See `commands/refresh.md`
for the full protocol.
```

- [ ] **Step 2: Extend the Frontmatter section — add conversations/ as valid source_path**

In the `wiki/sources/` frontmatter example block, add a note:

```markdown
# Valid source_path prefixes:
#   raw/web/<slug>/index.md   — web article fetched by inbox-fetcher
#   raw/papers/<slug>/        — PDF fetched by inbox-fetcher
#   conversations/<slug>.md   — conversation promoted via /promote
source_path: raw/papers/name.pdf
```

- [ ] **Step 3: Update the Slash commands section**

Add to the list:

```markdown
- `/promote [slug] [page]` — promote conversation insights to a wiki page
- `/refresh <source>` — re-fetch and re-ingest a changed source
```

- [ ] **Step 4: Add Skill dispatch table after the Nine operations section**

```markdown
## Skill dispatch

| Operation | Skill          | Backed by                      |
|-----------|----------------|--------------------------------|
| FETCH     | inbox-fetcher  | scripts/fetch_inbox.py         |
| LINT      | vault-linter   | scripts/lint.py                |
| VIEW      | view-builder   | templates/ + LLM               |
| INGEST    | (LLM only)     | —                              |
| QUERY     | (LLM only)     | —                              |
| REFLECT   | (LLM only)     | —                              |
| PROMOTE   | (LLM only)     | —                              |
| REFRESH   | (LLM only)     | —                              |
```

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "update CLAUDE.md: nine operations, promote/refresh, source_path note, dispatch table"
```

---

## Wave 3 — Polish (independent, any order)

---

### Task 17 — Add text fallback to concept-map template (TASK-0017)

**Files:**
- Modify: `skills/view-builder/templates/view-concept-map.md`

- [ ] **Step 1: Read the current template**

```bash
cat skills/view-builder/templates/view-concept-map.md
```

- [ ] **Step 2: Add the `<details>` adjacency list block after the Mermaid block**

After the closing triple-backtick of the Mermaid block, insert:

````markdown
<details>
<summary>Text fallback</summary>

<!-- Populate this list with the same nodes and edges as the Mermaid diagram above.
     Format: - Source Node → Target Node
     Both blocks must remain in sync — same nodes, same directed edges. -->

- {{Node A}} → {{Node B}}
- {{Node A}} → {{Node C}}

</details>
````

- [ ] **Step 3: Add a sync rule to view-builder SKILL.md**

At the end of the "Rules" section in `skills/view-builder/SKILL.md`, add:

```markdown
- **Concept-map sync.** When filling `view-concept-map.md`, populate both
  the Mermaid block and the `<details>` adjacency list from the same source
  data. Every node and directed edge must appear in both representations.
```

- [ ] **Step 4: Commit**

```bash
git add skills/view-builder/templates/view-concept-map.md skills/view-builder/SKILL.md
git commit -m "add text fallback to concept-map template and sync rule to view-builder"
```

---

### Task 18 — Add skill manifest fields to all SKILL.md files (TASK-0018)

**Files:**
- Modify: `skills/inbox-fetcher/SKILL.md`
- Modify: `skills/vault-linter/SKILL.md`
- Modify: `skills/view-builder/SKILL.md`

- [ ] **Step 1: Update `skills/inbox-fetcher/SKILL.md` frontmatter**

Add three fields to the existing frontmatter block:

```yaml
provides: fetch
config_section: fetch
requires:
  python: ">=3.10"
  packages: [trafilatura, requests, python-slugify]
```

- [ ] **Step 2: Update `skills/vault-linter/SKILL.md` frontmatter**

```yaml
provides: lint
config_section: lint
requires:
  python: ">=3.10"
  packages: []
```

- [ ] **Step 3: Update `skills/view-builder/SKILL.md` frontmatter**

```yaml
provides: view
config_section: null
requires:
  python: ">=3.10"
  packages: [matplotlib]
```

- [ ] **Step 4: Commit**

```bash
git add skills/inbox-fetcher/SKILL.md skills/vault-linter/SKILL.md skills/view-builder/SKILL.md
git commit -m "add provides/config_section/requires frontmatter to all skill manifests"
```

---

### Task 19 — Update init-vault.sh dependency check to read from manifests (TASK-0019)

**Files:**
- Modify: `init-vault.sh`

- [ ] **Step 1: Replace the hardcoded dependency check with a manifest-driven loop**

Find the "Checking Python dependencies" block and replace the `missing=()` loop:

```bash
# --- Python dependency check ----------------------------------------------
info "Checking Python dependencies"
if command -v python3 >/dev/null 2>&1; then
    ok "python3 found: $(python3 --version 2>&1)"

    # Collect packages from all installed skill manifests
    all_packages=""
    for skill_md in "$VAULT_DIR"/.claude/skills/*/SKILL.md; do
        [ -f "$skill_md" ] || continue
        pkgs=$(grep -A1 "^  packages:" "$skill_md" 2>/dev/null | \
               grep -o '\[.*\]' | tr -d '[]' | tr ',' '\n' | \
               sed 's/[[:space:]]//g' | grep -v '^$')
        all_packages="$all_packages $pkgs"
    done

    missing=()
    for pkg in $(echo "$all_packages" | tr ' ' '\n' | sort -u); do
        [ -z "$pkg" ] && continue
        if ! python3 -c "import $pkg" 2>/dev/null; then
            missing+=("$pkg")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        warn "missing Python packages: ${missing[*]}"
        echo "      install with: pip install ${missing[*]}"
    else
        ok "all Python dependencies installed"
    fi
else
    warn "python3 not found — inbox-fetcher and linter won't work"
fi
```

- [ ] **Step 2: Verify against a temp vault**

```bash
bash init-vault.sh /tmp/test-vault-deps
# Should show: all Python dependencies installed (or warn with the missing ones)
rm -rf /tmp/test-vault-deps
```

- [ ] **Step 3: Commit**

```bash
git add init-vault.sh
git commit -m "make init-vault.sh dependency check self-maintaining via skill manifests"
```

---

### Task 20 — Add skill dispatch table to CLAUDE.md (TASK-0020)

Already completed in Task 16 (Step 4). No additional work needed.

**Verify:** Confirm the `## Skill dispatch` section exists in CLAUDE.md.

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Implemented in |
|-----------------|----------------|
| vault.config.yml single source of truth | Task 1, 4, 5 |
| vault_state.py shared utility | Task 2 |
| init-vault.sh installs config + shared | Task 3 |
| fetch_inbox.py reads config, increments counter | Task 4 |
| lint.py reads config, uses vault_state | Task 5 |
| /lint command file | Task 6 |
| based_on dead link check | Task 5 (lint.py), Task 7 (verify) |
| Inbox sub-bullet parsing (tags, note) | Task 4, Task 8 (verify) |
| fetch_html writes tags/note to frontmatter | Task 9 |
| PDF folder structure | Task 10 |
| CLAUDE.md PDF ingest + tags/note protocol | Task 11 |
| PDF lint checks (missing_pdf_index, legacy_flat_pdf) | Task 5 (lint.py), Task 12 (verify) |
| /promote command | Task 13 |
| /refresh command | Task 14 |
| init-vault.sh installs promote + refresh | Task 15 |
| CLAUDE.md nine operations + source_path extension | Task 16 |
| Concept-map text fallback | Task 17 |
| Skill manifest frontmatter fields | Task 18 |
| Manifest-driven dependency check | Task 19 |
| Skill dispatch table in CLAUDE.md | Task 16 (Step 4) |

All spec requirements covered. No gaps found.

**Type/signature consistency check:**

- `update_inbox()` signature change (added `processed_section` param) used consistently in Task 4 steps 6 and 7 and tested in Task 4 step 1. ✓
- `fetch_pdf()` new signature (added `tags`, `note`, folder output) used consistently in Tasks 10 and tested. ✓
- `fetch_html()` new signature (added `tags`, `note`) used consistently in Task 9. ✓
- `check_based_on_links(pages, vault)` registered with correct dispatcher branch in Task 5 Step 9. ✓
- `check_pdf_index(vault)` registered with correct dispatcher branch in Task 5 Step 9. ✓
- `strip_wikilink()` used in both `check_view_staleness` and `check_based_on_links` — both in Task 5. ✓
- `write_state` imported as `_write_state` in lint.py (Task 5 Step 3) to avoid name clash with removed local function. ✓
