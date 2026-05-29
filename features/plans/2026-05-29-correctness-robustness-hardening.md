# Correctness & Robustness Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate 8 latent correctness/robustness bugs in the LLM Wiki engine — chiefly the YAML block-list silent-disable trap, Windows console encoding crashes, and a cluster of smaller fixes — all with zero behavior change for correctly-formed existing vaults.

**Architecture:** Three new shared modules (`yamlmini.py`, `console.py`) plus in-place patches to 6 existing scripts and 4 doc files. The YAML work is gated: characterization tests must pass before any caller migrations. Tasks 1–4 (YAML tree) are sequential; Tasks 5–8 (independent fixes) can be done in any order after Task 1 passes.

**Tech Stack:** Python 3.10+, pytest, standard library only. No new runtime dependencies. Existing test import pattern: `sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))`.

---

## Fresh-agent setup

```bash
# Confirm you are in the ENGINE repo (no wiki/ or raw/ here)
cd D:\my-2nd-brain

# Install test dependencies (already present but shown for new agents)
pip install requests trafilatura python-slugify matplotlib pytest

# Verify the suite is green before touching anything
python -m pytest tests/ -v

# You are already on feat-hotfix; no new branch needed
git status
```

---

## File map

| File | Action | Task |
|---|---|---|
| `skills/shared/yamlmini.py` | **CREATE** | 1 |
| `tests/test_yamlmini.py` | **CREATE** | 1 |
| `skills/shared/console.py` | **CREATE** | 5 |
| `skills/shared/vault_state.py` | MODIFY — use yamlmini; fix null round-trip | 2 |
| `skills/vault-linter/scripts/lint.py` | MODIFY — use yamlmini; wire console | 3, 5 |
| `skills/inbox-fetcher/scripts/adopt_drop.py` | MODIFY — use yamlmini; .resolve() | 4 |
| `skills/inbox-fetcher/scripts/fetch_inbox.py` | MODIFY — wire console; .resolve(); CRLF; warn | 5, 6 |
| `skills/shared/review_scope.py` | MODIFY — scope regex to frontmatter block | 7 |
| `skills/view-builder/templates/chart.py` | MODIFY — dep guard | 8 |
| `init_vault.py` | MODIFY — add yamlmini.py + console.py to `_SHARED_SCRIPTS` | 9 |
| `commands/review.md` | MODIFY — remove stale "/merge not yet available" | 10 |
| `CLAUDE.md` | MODIFY — add SPLIT row to dispatch table | 10 |
| `skills/view-builder/SKILL.md` | MODIFY — remove/clarify reveal references | 10 |
| `vault.config.yml` | MODIFY — add enforcement-layer comments; update block-list note | 10 |
| `tests/test_vault_state.py` | EXTEND — null round-trip test | 2 |
| `tests/test_review_scope.py` | EXTEND — body-prose mis-date test | 7 |

**Sequential constraint:** Task 2 (vault_state migration) and Task 3 (lint migration) depend on Task 1 (yamlmini). Task 4 (adopt_drop) depends on Task 1. All others are independent.

---

## Task 1: Create `yamlmini.py` with characterization tests

This is the YAML unification. The new module is a zero-dep superset of both
`vault_state._parse_config_yaml` (2-level nesting + inline lists) and
`lint.parse_frontmatter` (flat + block lists). Build characterization tests FIRST,
then implement to make them pass.

**Files:**
- Create: `skills/shared/yamlmini.py`
- Create: `tests/test_yamlmini.py`

- [ ] **Step 1: Write the failing characterization tests**

Create `tests/test_yamlmini.py`:

```python
"""
Characterization tests for yamlmini.parse_yaml / parse_frontmatter.

Section A: Reproduce vault_state._parse_config_yaml behaviour exactly.
Section B: Reproduce lint.parse_frontmatter behaviour exactly.
Section C: New capability — block lists under a config section (the headline fix).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
from yamlmini import parse_yaml, parse_frontmatter


# ── Section A: vault_state._parse_config_yaml characterisation ──────────────

class TestParseYamlConfig:
    """Mirrors the exact cases from test_vault_state.py::TestLoadConfig."""

    def test_scalar_int(self):
        assert parse_yaml("fetch:\n  html_timeout_seconds: 45\n") == {
            "fetch": {"html_timeout_seconds": 45}
        }

    def test_scalar_bool_false(self):
        assert parse_yaml("fetch:\n  pdf_enabled: false\n") == {
            "fetch": {"pdf_enabled": False}
        }

    def test_scalar_bool_true(self):
        assert parse_yaml("fetch:\n  pdf_enabled: true\n") == {
            "fetch": {"pdf_enabled": True}
        }

    def test_inline_list_under_section(self):
        result = parse_yaml("fetch:\n  walled_domains: [example.com, other.com]\n")
        assert result["fetch"]["walled_domains"] == ["example.com", "other.com"]

    def test_inline_comment_stripped(self):
        result = parse_yaml("lint:\n  stale_source_days: 90  # some comment here\n")
        assert result["lint"]["stale_source_days"] == 90

    def test_two_sections_independent(self):
        text = "fetch:\n  html_timeout_seconds: 20\nlint:\n  stale_source_days: 180\n"
        result = parse_yaml(text)
        assert result["fetch"]["html_timeout_seconds"] == 20
        assert result["lint"]["stale_source_days"] == 180

    def test_override_preserves_sibling_keys(self):
        """Partial override: one key overridden, sibling keys NOT in text are absent."""
        result = parse_yaml("lint:\n  stale_source_days: 90\n")
        assert result["lint"]["stale_source_days"] == 90
        # Other lint keys are NOT in this text; callers merge with defaults separately.
        assert "view_stale_days" not in result["lint"]

    def test_null_scalar(self):
        result = parse_yaml("state:\n  last_lint: null\n")
        assert result["state"]["last_lint"] is None

    def test_empty_inline_list(self):
        result = parse_yaml("fetch:\n  walled_domains: []\n")
        assert result["fetch"]["walled_domains"] == []


# ── Section B: lint.parse_frontmatter characterisation ──────────────────────

class TestParseFrontmatter:
    """Mirrors the frontmatter shapes used across the vault."""

    def test_returns_empty_when_no_frontmatter(self):
        assert parse_frontmatter("No frontmatter here.\n") == {}

    def test_scalar_fields(self):
        fm = parse_frontmatter("---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-05-29\n---\n")
        assert fm["type"] == "page"
        assert fm["created"] == "2026-01-01"
        assert fm["updated"] == "2026-05-29"

    def test_inline_list_tags(self):
        fm = parse_frontmatter("---\ntags: [ai, ml, nlp]\n---\n")
        assert fm["tags"] == ["ai", "ml", "nlp"]

    def test_empty_inline_list(self):
        fm = parse_frontmatter("---\ntags: []\n---\n")
        assert fm["tags"] == []

    def test_block_list_based_on(self):
        text = (
            "---\n"
            "type: view\n"
            "based_on:\n"
            "  - [[wiki/pages/foo]]\n"
            "  - [[wiki/pages/bar]]\n"
            "---\n"
        )
        fm = parse_frontmatter(text)
        assert fm["based_on"] == ["[[wiki/pages/foo]]", "[[wiki/pages/bar]]"]

    def test_block_list_tags(self):
        text = "---\ntags:\n  - ai\n  - ml\n---\n"
        fm = parse_frontmatter(text)
        assert fm["tags"] == ["ai", "ml"]

    def test_quoted_value_with_colon(self):
        fm = parse_frontmatter('---\ntitle: "Deep Learning: A Primer"\n---\n')
        assert fm["title"] == "Deep Learning: A Primer"

    def test_body_is_not_parsed(self):
        """Frontmatter extraction stops at closing ---; body is ignored."""
        text = "---\ntype: page\n---\n\nupdated: 9999-12-31\n"
        fm = parse_frontmatter(text)
        assert fm["type"] == "page"
        # The body's 'updated: ...' must not appear in frontmatter
        assert "updated" not in fm

    def test_shareable_bool(self):
        fm = parse_frontmatter("---\nshareable: false\n---\n")
        assert fm["shareable"] is False


# ── Section C: New capability — block list under a config section ───────────

class TestBlockListUnderSection:
    """The headline regression guard: walled_domains as block list."""

    def test_block_list_under_section(self):
        text = (
            "fetch:\n"
            "  walled_domains:\n"
            "    - x.com\n"
            "    - twitter.com\n"
            "    - linkedin.com\n"
        )
        result = parse_yaml(text)
        assert result["fetch"]["walled_domains"] == ["x.com", "twitter.com", "linkedin.com"]

    def test_block_list_under_section_with_siblings(self):
        """Block list key coexists with scalar siblings in the same section."""
        text = (
            "fetch:\n"
            "  html_timeout_seconds: 20\n"
            "  walled_domains:\n"
            "    - x.com\n"
            "    - twitter.com\n"
            "  pdf_enabled: true\n"
        )
        result = parse_yaml(text)
        assert result["fetch"]["html_timeout_seconds"] == 20
        assert result["fetch"]["walled_domains"] == ["x.com", "twitter.com"]
        assert result["fetch"]["pdf_enabled"] is True

    def test_inline_and_block_produce_same_value(self):
        """Inline syntax and block syntax produce identical results."""
        inline = parse_yaml("fetch:\n  walled_domains: [x.com, twitter.com]\n")
        block = parse_yaml("fetch:\n  walled_domains:\n    - x.com\n    - twitter.com\n")
        assert inline["fetch"]["walled_domains"] == block["fetch"]["walled_domains"]
```

- [ ] **Step 2: Run tests — expect ImportError (module not yet created)**

```bash
python -m pytest tests/test_yamlmini.py -v
```

Expected: `ModuleNotFoundError: No module named 'yamlmini'`

- [ ] **Step 3: Create `skills/shared/yamlmini.py`**

```python
#!/usr/bin/env python3
"""
yamlmini.py — Shared zero-dependency YAML parser for vault scripts.

Handles:
  - Scalars: bool (true/false), null/None/~/empty, int, string
  - Inline lists: key: [a, b, c]
  - Block lists:  key:\n  - a\n  - b
  - Two-level nesting: section:\n  subkey: value
  - Inline comments: key: value  # comment (outside quoted strings)

Does NOT handle: anchors, multi-line strings, 3+ level nesting.

This is the authoritative parser. vault_state and lint delegate to it.
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Scalar coercion
# ---------------------------------------------------------------------------

def _parse_scalar(val: str) -> Any:
    """Coerce a stripped string to the appropriate Python type."""
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


# ---------------------------------------------------------------------------
# Block-list helpers
# ---------------------------------------------------------------------------

def _collect_block_list(lines: list[str], start: int) -> tuple[list[Any], int]:
    """Collect consecutive ``- item`` lines starting from index ``start``.

    Skips blank lines. Stops at the first non-blank non-list line.
    Returns ``(items, next_index)`` where next_index is the first line
    NOT consumed.
    """
    items: list[Any] = []
    j = start
    while j < len(lines):
        nxt = lines[j]
        if not nxt.strip():
            j += 1
            continue
        m = re.match(r"^\s*-\s+(.+)$", nxt)
        if m:
            item = m.group(1).strip()
            # Strip surrounding quotes
            if (item.startswith('"') and item.endswith('"')) or \
               (item.startswith("'") and item.endswith("'")):
                item = item[1:-1]
            items.append(item)
            j += 1
        else:
            break
    return items, j


def _peek_next_line_type(lines: list[str], start: int) -> str:
    """Classify the first non-blank line at or after ``start``.

    Returns one of:
      ``'block-item'``   — line matches ``- value``
      ``'indented-key'`` — line is indented with ``key: value``
      ``'other'``        — top-level line or end of input
    """
    for line in lines[start:]:
        if not line.strip():
            continue
        if re.match(r"^\s+-\s+", line):
            return "block-item"
        if line[:1] in (" ", "\t"):
            return "indented-key"
        return "other"
    return "other"


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_yaml(text: str) -> dict:
    """Parse a two-level YAML-like string and return a nested dict.

    Designed as a strict superset of both:
    - ``vault_state._parse_config_yaml`` (2-level nesting + inline lists)
    - ``lint.parse_frontmatter`` (flat scalars + block lists)
    """
    result: dict = {}
    lines = text.splitlines()
    current_section: str | None = None
    i = 0

    while i < len(lines):
        raw_line = lines[i]
        stripped = raw_line.strip()

        # Skip blank and comment lines
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Skip standalone block-list items (consumed by the block-list handler)
        if re.match(r"^\s*-\s+", raw_line) and ":" not in stripped:
            i += 1
            continue

        if ":" not in stripped:
            i += 1
            continue

        key, _, val_raw = stripped.partition(":")
        key = key.strip()
        val = val_raw.strip()

        # Strip trailing inline comment, but only outside a quoted value
        if not (val.startswith('"') or val.startswith("'")):
            val = val.partition(" #")[0].strip()
            val = val.partition("\t#")[0].strip()

        is_indented = raw_line[:1] in (" ", "\t")

        if not is_indented:
            # ── Top-level key ─────────────────────────────────────────────
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                result[key] = [
                    _parse_scalar(x.strip().strip("\"'"))
                    for x in inner.split(",") if x.strip()
                ]
                current_section = None
                i += 1

            elif val == "":
                # Disambiguate: block-list header vs section header vs empty
                next_type = _peek_next_line_type(lines, i + 1)
                if next_type == "block-item":
                    items, next_i = _collect_block_list(lines, i + 1)
                    result[key] = items
                    current_section = None
                    i = next_i
                elif next_type == "indented-key":
                    result[key] = {}
                    current_section = key
                    i += 1
                else:
                    # Empty key with nothing relevant following
                    result[key] = ""
                    current_section = None
                    i += 1

            else:
                result[key] = _parse_scalar(val)
                current_section = None
                i += 1

        elif current_section is not None:
            # ── Indented key under a known section ────────────────────────
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                result[current_section][key] = [
                    _parse_scalar(x.strip().strip("\"'"))
                    for x in inner.split(",") if x.strip()
                ]
                i += 1

            elif val == "":
                # Block list under a section key
                items, next_i = _collect_block_list(lines, i + 1)
                result[current_section][key] = items if items else ""
                i = next_i

            else:
                result[current_section][key] = _parse_scalar(val)
                i += 1

        else:
            # Indented line with no active section context — skip
            i += 1

    return result


def parse_frontmatter(text: str) -> dict:
    """Extract and parse the YAML frontmatter block from a Markdown string.

    Returns an empty dict when no ``---`` frontmatter block is found.
    The rest of the document (body) is ignored.
    """
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    return parse_yaml(m.group(1))
```

- [ ] **Step 4: Run tests — all should pass**

```bash
python -m pytest tests/test_yamlmini.py -v
```

Expected: all tests PASS (23 tests).

- [ ] **Step 5: Run the full suite — no regressions**

```bash
python -m pytest tests/ -v
```

Expected: all existing tests still PASS. `test_yamlmini.py` adds 23 new passing tests.

- [ ] **Step 6: Commit**

```bash
git add skills/shared/yamlmini.py tests/test_yamlmini.py
git commit -m "feat(shared): add yamlmini.py — unified zero-dep YAML parser with block-list support"
```

---

## Task 2: Migrate `vault_state.py` to yamlmini + fix null round-trip

Replace `_parse_config_yaml` with `yamlmini.parse_yaml` and coerce `read_state`
values through `_parse_scalar` so `null` values survive a read-write-read cycle.

**Files:**
- Modify: `skills/shared/vault_state.py`
- Modify: `tests/test_vault_state.py`

- [ ] **Step 1: Write the failing null round-trip test**

Open `tests/test_vault_state.py` and add this test to `TestWriteState`:

```python
def test_null_value_round_trips_as_none(self, tmp_path):
    """last_lint: null survives write → read as Python None, not the string 'null'."""
    write_state(tmp_path, {"last_lint": None})
    state = read_state(tmp_path)
    assert state["last_lint"] is None

def test_date_string_round_trips_unchanged(self, tmp_path):
    """A date string written and read back remains a string (not coerced)."""
    write_state(tmp_path, {"last_lint": "2026-01-15"})
    state = read_state(tmp_path)
    assert state["last_lint"] == "2026-01-15"
```

Also add to `TestLoadConfig`:

```python
def test_block_list_walled_domains(self, tmp_path):
    """walled_domains written as a YAML block list parses to a real list.

    This is the headline regression guard: before the fix, this silently
    produced an empty list, disabling all walled-domain protection.
    """
    (tmp_path / "vault.config.yml").write_text(
        "fetch:\n"
        "  walled_domains:\n"
        "    - x.com\n"
        "    - twitter.com\n"
        "    - linkedin.com\n"
    )
    config = load_config(tmp_path)
    assert config["fetch"]["walled_domains"] == ["x.com", "twitter.com", "linkedin.com"]
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_vault_state.py -v -k "null_round_trip or block_list"
```

Expected: FAIL — `null_round_trips_as_none` fails (gets `"null"` not `None`); `block_list_walled_domains` fails (gets `[]` not the list).

- [ ] **Step 3: Update `skills/shared/vault_state.py`**

Replace the entire file with:

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

from yamlmini import parse_yaml as _parse_yaml


# ---------------------------------------------------------------------------
# Scalar coercion (kept local — vault_state must not import private yamlmini internals)
# ---------------------------------------------------------------------------

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
        "auto_trigger_after_fetches": 5,
        "auto_trigger_after_days": 7,
        "reflect_reminder_days": 14,
    },
    "ingest": {
        "max_new_pages_before_confirm": 3,
        "max_files_per_operation": 15,
    },
    "drop_zone": {
        "path": "raw/drop",
        "enabled": True,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def load_config(vault_root: Path) -> dict:
    """Load vault.config.yml and deep-merge with built-in defaults.

    Returns defaults silently when the file is absent (backward-compatible).
    Raises ValueError when the file exists but cannot be read or parsed.
    """
    config_path = vault_root / "vault.config.yml"
    if not config_path.exists():
        return _deep_merge(_DEFAULTS, {})
    try:
        text = config_path.read_text(encoding="utf-8")
        parsed = _parse_yaml(text)
    except Exception as exc:
        raise ValueError(f"vault.config.yml cannot be loaded: {exc}") from exc
    return _deep_merge(_DEFAULTS, parsed)


def read_state(vault_root: Path) -> dict:
    """Read .lint/state.yaml into a flat dict with typed values.

    Returns an empty dict when the file is absent.
    Values are coerced: null → None, true/false → bool, integers → int.
    """
    state_path = vault_root / ".lint" / "state.yaml"
    if not state_path.exists():
        return {}
    result: dict = {}
    for line in state_path.read_text(encoding="utf-8").splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, _, v = line.partition(":")
            result[k.strip()] = _parse_scalar(v.strip())
    return result


def write_state(vault_root: Path, updates: dict) -> None:
    """Patch .lint/state.yaml with the given key-value pairs.

    Existing keys not in updates are preserved; new keys are added.
    Creates .lint/ and state.yaml if absent.
    None values are written as empty strings (so they round-trip back as None).
    """
    lint_dir = vault_root / ".lint"
    lint_dir.mkdir(exist_ok=True)
    current = read_state(vault_root)
    for k, v in updates.items():
        current[str(k)] = v
    lines = []
    for k, v in current.items():
        lines.append(f"{k}: {'' if v is None else v}")
    (lint_dir / "state.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run the new tests — should now pass**

```bash
python -m pytest tests/test_vault_state.py -v
```

Expected: all tests PASS including the 3 new ones.

- [ ] **Step 5: Run full suite — no regressions**

```bash
python -m pytest tests/ -v
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add skills/shared/vault_state.py tests/test_vault_state.py
git commit -m "fix(vault_state): migrate to yamlmini; fix null round-trip in read/write_state"
```

---

## Task 3: Migrate `lint.py` to `yamlmini.parse_frontmatter`

Replace `lint.parse_frontmatter` with the shared `yamlmini.parse_frontmatter`.
Add the `import` and delete the local definition.

**Files:**
- Modify: `skills/vault-linter/scripts/lint.py`

- [ ] **Step 1: Run the existing lint tests to establish a green baseline**

```bash
python -m pytest tests/test_lint.py -v
```

Expected: all pass.

- [ ] **Step 2: Update the import block and remove the local `parse_frontmatter`**

In `lint.py`, change the import block (lines 33–35) from:

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from vault_state import load_config, write_state as _write_state
from linkutil import WIKILINK_RE, normalize_link_target
```

to:

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from vault_state import load_config, write_state as _write_state
from linkutil import WIKILINK_RE, normalize_link_target
from yamlmini import parse_frontmatter
```

Then delete the entire `parse_frontmatter` function (lines 87–162 in the original).
It is replaced by the imported `parse_frontmatter` from `yamlmini`.

The `load_wiki` function calls `parse_frontmatter(text)` on line ~237 (returns `(fm, body)`).
But `yamlmini.parse_frontmatter` returns only `dict`, not `(dict, body)`.

To preserve the call site, add a local adapter **replacing** the deleted function:

```python
def _parse_frontmatter_with_body(text: str) -> tuple[dict, str]:
    """Adapter: wraps yamlmini.parse_frontmatter to also return the body.

    lint.py callers expect (frontmatter_dict, body_text). The shared
    parse_frontmatter only returns the dict; extract the body here.
    """
    import re as _re
    fm = parse_frontmatter(text)
    m = _re.match(r"^---\n.*?\n---\n?", text, _re.DOTALL)
    body = text[m.end():].lstrip("\n") if m else text
    return fm, body
```

Then find every call to `parse_frontmatter(text)` in `lint.py` (there is exactly one,
inside `load_wiki`) and replace it with `_parse_frontmatter_with_body(text)`.

- [ ] **Step 3: Run lint tests**

```bash
python -m pytest tests/test_lint.py -v
```

Expected: all pass.

- [ ] **Step 4: Run full suite**

```bash
python -m pytest tests/ -v
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add skills/vault-linter/scripts/lint.py
git commit -m "fix(lint): delegate parse_frontmatter to shared yamlmini"
```

---

## Task 4: Migrate `adopt_drop.py` field extractors + fix `--vault` resolve

Replace `adopt_drop`'s inline frontmatter field extractors with `yamlmini.parse_frontmatter`
and add `.resolve()` to `--vault`.

**Files:**
- Modify: `skills/inbox-fetcher/scripts/adopt_drop.py`
- Modify: `tests/test_adopt_drop.py`

- [ ] **Step 1: Write the failing `--vault` resolve test**

Open `tests/test_adopt_drop.py` and add to an appropriate test class (or create a new one):

```python
def test_vault_path_resolved_to_absolute(self, tmp_path, monkeypatch):
    """process_drop_zone receives an absolute vault Path even when called with relative."""
    # We can't easily test CLI argument parsing in isolation, so test the contract:
    # process_drop_zone should work correctly when given a relative path that
    # resolves to an existing directory. Smoke test only — confirming no crash.
    drop_dir = tmp_path / "raw" / "drop"
    drop_dir.mkdir(parents=True)
    # No files in drop; just confirm it doesn't error on relative paths
    import os
    old_cwd = Path.cwd()
    monkeypatch.chdir(tmp_path)
    from adopt_drop import process_drop_zone
    rc = process_drop_zone(Path("."))  # relative path
    assert rc == 0  # empty drop zone
```

- [ ] **Step 2: Run the test to confirm it passes already (smoke test)**

```bash
python -m pytest tests/test_adopt_drop.py -v -k "vault_path_resolved"
```

Expected: PASS (this is a smoke test, not a failing test — `process_drop_zone` accepts `Path(".")` fine today). The real fix is in the CLI argument parser, not the function.

- [ ] **Step 3: Update `adopt_drop.py`**

**3a. Add `yamlmini` import** — after the existing `sys.path.insert`:

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from vault_state import load_config
from yamlmini import parse_frontmatter as _parse_frontmatter
```

**3b. Replace `extract_title_from_md`** — the current function has its own frontmatter
regex. Replace its body to use `_parse_frontmatter`:

```python
def extract_title_from_md(path: Path) -> str | None:
    """Cascade: frontmatter title: → first # H1 → None."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    fm = _parse_frontmatter(text)
    if fm.get("title"):
        return str(fm["title"])

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()

    return None
```

**3c. Replace `extract_source_url_from_md`** — same pattern:

```python
def extract_source_url_from_md(path: Path) -> str | None:
    """Check frontmatter for source_url, url, link, source keys."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    fm = _parse_frontmatter(text)
    for key in ("source_url", "url", "link", "source"):
        val = fm.get(key)
        if val:
            return str(val)
    return None
```

**3d. Fix `--vault` `.resolve()`** — in `main()`, change:

```python
    if not args.vault.is_dir():
        print(f"ERROR: vault path is not a directory: {args.vault}", file=sys.stderr)
        return 1

    return process_drop_zone(args.vault, dry_run=args.dry_run)
```

to:

```python
    vault = Path(args.vault).resolve()
    if not vault.is_dir():
        print(f"ERROR: vault path is not a directory: {vault}", file=sys.stderr)
        return 1

    return process_drop_zone(vault, dry_run=args.dry_run)
```

- [ ] **Step 4: Run adopt_drop tests**

```bash
python -m pytest tests/test_adopt_drop.py -v
```

Expected: all pass.

- [ ] **Step 5: Run full suite**

```bash
python -m pytest tests/ -v
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add skills/inbox-fetcher/scripts/adopt_drop.py tests/test_adopt_drop.py
git commit -m "fix(adopt_drop): delegate field extraction to yamlmini; resolve --vault path"
```

---

## Task 5: Create `console.py` + wire to `fetch_inbox.py` and `lint.py`

Centralise the UTF-8 stdout guard so `fetch_inbox.py` and `lint.py` don't crash
with `UnicodeEncodeError` on cp1252 Windows consoles.

**Files:**
- Create: `skills/shared/console.py`
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py`
- Modify: `skills/vault-linter/scripts/lint.py`

- [ ] **Step 1: Create `skills/shared/console.py`**

```python
#!/usr/bin/env python3
"""
console.py — Shared console utilities for vault scripts.

Call ensure_utf8_stdout() once at the top of any script that prints
unicode symbols (✓, ⚠, ·, →) to avoid UnicodeEncodeError on
cp1252 Windows consoles.

Note: init_vault.py intentionally keeps its own inline copy of this
logic because it must run BEFORE the shared scripts are installed.
"""

from __future__ import annotations

import io
import sys


def ensure_utf8_stdout() -> None:
    """Reconfigure stdout/stderr to UTF-8 if not already.

    Safe to call multiple times (no-op when encoding is already UTF-8).
    Uses reconfigure() on Python 3.7+ (available on TextIOWrapper).
    Falls back gracefully on AttributeError / OSError.
    """
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")   # type: ignore[union-attr]
            sys.stderr.reconfigure(encoding="utf-8")   # type: ignore[union-attr]
        except (AttributeError, OSError):
            pass
```

- [ ] **Step 2: Wire `fetch_inbox.py`**

In `fetch_inbox.py`, right after the `sys.path.insert` lines (after line 30), add:

```python
from console import ensure_utf8_stdout
ensure_utf8_stdout()
```

The full top-of-file import block should look like this after the edit:

```python
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from vault_state import load_config, read_state, write_state
from console import ensure_utf8_stdout
ensure_utf8_stdout()
```

- [ ] **Step 3: Wire `lint.py`**

In `lint.py`, right after the `from yamlmini import parse_frontmatter` line (added in Task 3), add:

```python
from console import ensure_utf8_stdout
ensure_utf8_stdout()
```

- [ ] **Step 4: Run full suite to confirm nothing broke**

```bash
python -m pytest tests/ -v
```

Expected: all green (console.py has no testable behaviour in a UTF-8 terminal; we trust the unit tests haven't regressed).

- [ ] **Step 5: Commit**

```bash
git add skills/shared/console.py skills/inbox-fetcher/scripts/fetch_inbox.py skills/vault-linter/scripts/lint.py
git commit -m "fix(console): add shared ensure_utf8_stdout(); wire to fetch_inbox and lint"
```

---

## Task 6: Fix `fetch_inbox.py` — `--vault` resolve + CRLF preservation + near-miss warning

Three small inbox-robustness fixes. All in `fetch_inbox.py`.

**Files:**
- Modify: `skills/inbox-fetcher/scripts/fetch_inbox.py`
- Modify: `tests/test_fetch_inbox.py`

- [ ] **Step 1: Write the failing tests**

Open `tests/test_fetch_inbox.py` and add a new test class:

```python
class TestUpdateInboxCRLFAndWarning:
    """Tests for CRLF preservation and near-miss warning in update_inbox."""

    def test_crlf_line_endings_are_preserved(self):
        """CRLF inboxes must not be silently converted to LF on rewrite."""
        from fetch_inbox import update_inbox, FetchResult
        from pathlib import Path
        import tempfile, os

        inbox_text = "# Inbox\r\n\r\n- [ ] https://example.com\r\n"
        result = FetchResult(url="https://example.com", ok=True,
                             kind="html", out_path=Path("raw/web/example"))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                        encoding="utf-8", delete=False) as f:
            f.write(inbox_text)
            tmp = Path(f.name)

        try:
            output = update_inbox(tmp, inbox_text, [result])
            assert "\r\n" in output, "CRLF line endings must be preserved"
        finally:
            tmp.unlink(missing_ok=True)

    def test_near_miss_entry_emits_warning(self):
        """A line that looks like '- [ ] URL note' should produce a warning."""
        from fetch_inbox import update_inbox, FetchResult
        from pathlib import Path
        import tempfile

        # URL with trailing inline note — fails UNCHECKED_PATTERN silently today
        inbox_text = "- [ ] https://example.com my inline note\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                        encoding="utf-8", delete=False) as f:
            f.write(inbox_text)
            tmp = Path(f.name)

        try:
            output = update_inbox(tmp, inbox_text, [])
            assert "⚠" in output or "skipped" in output.lower(), (
                "A near-miss unchecked line must produce a visible warning"
            )
        finally:
            tmp.unlink(missing_ok=True)

    def test_lf_line_endings_are_preserved(self):
        """LF-only inboxes stay LF."""
        from fetch_inbox import update_inbox, FetchResult
        from pathlib import Path
        import tempfile

        inbox_text = "# Inbox\n\n- [ ] https://example.com\n"
        result = FetchResult(url="https://example.com", ok=True,
                             kind="html", out_path=Path("raw/web/example"))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                        encoding="utf-8", delete=False) as f:
            f.write(inbox_text)
            tmp = Path(f.name)

        try:
            output = update_inbox(tmp, inbox_text, [result])
            assert "\r\n" not in output, "LF-only inbox must not gain CRLF"
        finally:
            tmp.unlink(missing_ok=True)
```

- [ ] **Step 2: Run tests — confirm failures**

```bash
python -m pytest tests/test_fetch_inbox.py -v -k "CRLF or near_miss"
```

Expected: `test_crlf_line_endings_are_preserved` FAILS (CRLF is stripped).
`test_near_miss_entry_emits_warning` FAILS (no warning).

- [ ] **Step 3: Fix `--vault` `.resolve()` in `fetch_inbox.py` `main()`**

Change `main()` from:

```python
    if not args.vault.is_dir():
        print(f"ERROR: vault path is not a directory: {args.vault}",
              file=sys.stderr)
        return 1

    return process_vault(args.vault, dry_run=args.dry_run, retry=args.retry)
```

to:

```python
    vault = Path(args.vault).resolve()
    if not vault.is_dir():
        print(f"ERROR: vault path is not a directory: {vault}",
              file=sys.stderr)
        return 1

    return process_vault(vault, dry_run=args.dry_run, retry=args.retry)
```

- [ ] **Step 4: Fix `update_inbox` — CRLF preservation + near-miss warning**

In `update_inbox`, change:

```python
def update_inbox(
    inbox_path: Path,
    inbox_text: str,
    results: list[FetchResult],
    processed_section: str = "## Processed",
) -> str:
    lines = inbox_text.splitlines()
```

to:

```python
# Near-miss pattern: looks like an unchecked entry but has trailing content
_NEAR_MISS_PATTERN = re.compile(r"^- \[ \] https?://\S+\s+\S")


def update_inbox(
    inbox_path: Path,
    inbox_text: str,
    results: list[FetchResult],
    processed_section: str = "## Processed",
) -> str:
    # Detect and preserve the original line separator
    line_sep = "\r\n" if "\r\n" in inbox_text else "\n"
    lines = inbox_text.splitlines()
```

Then in the main loop inside `update_inbox`, add a near-miss check right after the
`match = UNCHECKED_PATTERN.match(line)` block. Find the section that currently does:

```python
        match = UNCHECKED_PATTERN.match(line)
        failed_match = FAILED_PATTERN.match(line) if not match else None
        if not match and not failed_match:
            out_lines.append(line)
            i += 1
            continue
```

Change it to:

```python
        match = UNCHECKED_PATTERN.match(line)
        failed_match = FAILED_PATTERN.match(line) if not match else None
        if not match and not failed_match:
            # Warn on near-miss: looks like an unchecked entry but URL is not alone
            if _NEAR_MISS_PATTERN.match(line):
                out_lines.append(
                    line + " ⚠ skipped: inline text after URL"
                    " — move notes to an indented sub-bullet"
                )
            else:
                out_lines.append(line)
            i += 1
            continue
```

Finally, change the `return` line at the end of `update_inbox` from:

```python
    return "\n".join(final_lines) + ("\n" if inbox_text.endswith("\n") else "")
```

to:

```python
    ending = line_sep if inbox_text.endswith(("\n", "\r\n")) else ""
    return line_sep.join(final_lines) + ending
```

- [ ] **Step 5: Run the new tests — all should pass**

```bash
python -m pytest tests/test_fetch_inbox.py -v -k "CRLF or near_miss"
```

Expected: all 3 new tests PASS.

- [ ] **Step 6: Run full suite**

```bash
python -m pytest tests/ -v
```

Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add skills/inbox-fetcher/scripts/fetch_inbox.py tests/test_fetch_inbox.py
git commit -m "fix(fetch_inbox): preserve CRLF line endings; warn on near-miss inbox entries; resolve --vault"
```

---

## Task 7: Fix `review_scope._parse_updated` — scope to frontmatter block

The current MULTILINE regex matches `updated:` anywhere in the file, including body prose.
Fix: extract the `---...---` block first and apply the regex only to that text.
Preserve the script's intentional self-containment (no import of shared/).

**Files:**
- Modify: `skills/shared/review_scope.py`
- Modify: `tests/test_review_scope.py`

- [ ] **Step 1: Write the failing test**

Open `tests/test_review_scope.py` and add:

```python
def test_body_prose_updated_date_is_ignored(tmp_path):
    """A page with 'updated: 2020-01-01' ONLY in its body must NOT be mis-dated."""
    wiki = tmp_path / "wiki" / "pages"
    wiki.mkdir(parents=True)
    # Frontmatter has NO updated field; body has a misleading one
    (wiki / "tricky.md").write_text(
        "---\ntype: page\ncreated: 2026-01-01\ntags: []\n---\n\n"
        "This note was updated: 2020-01-01 in the old format.\n",
        encoding="utf-8",
    )

    # last_review is 2021-01-01 — if the body date were used, this page
    # would NOT be in scope (2020 < 2021). If correctly scoped to frontmatter,
    # there's no updated date → page is included (first-run behaviour when updated=None).
    result = get_changed_pages(tmp_path, last_review=date(2021, 1, 1))
    # Page has no frontmatter updated field, so _parse_updated returns None.
    # get_changed_pages skips pages where updated is None (not > last_review).
    assert result == [], (
        "A page with updated: only in prose should return None from "
        "_parse_updated, not the prose date"
    )


def test_frontmatter_updated_date_is_used(tmp_path):
    """When frontmatter has 'updated', that date is used correctly."""
    wiki = tmp_path / "wiki" / "pages"
    wiki.mkdir(parents=True)
    (wiki / "normal.md").write_text(
        "---\ntype: page\ncreated: 2026-01-01\nupdated: 2026-05-01\ntags: []\n---\n\n"
        "Body text with no dates.\n",
        encoding="utf-8",
    )
    result = get_changed_pages(tmp_path, last_review=date(2026, 1, 1))
    assert len(result) == 1
    assert result[0].name == "normal.md"
```

- [ ] **Step 2: Run tests — confirm first test fails**

```bash
python -m pytest tests/test_review_scope.py -v -k "body_prose or frontmatter_updated"
```

Expected: `test_body_prose_updated_date_is_ignored` FAILS (body date is currently used).
`test_frontmatter_updated_date_is_used` PASSES.

- [ ] **Step 3: Fix `_parse_updated` in `review_scope.py`**

Replace the entire `_parse_updated` function:

```python
def _parse_updated(text: str) -> date | None:
    """Extract the ``updated: YYYY-MM-DD`` field from YAML frontmatter only.

    The search is scoped to the leading ``---\\n...\\n---`` block so that
    body text containing ``updated:`` is never mis-parsed.
    Self-contained: no import of shared/yamlmini (by design).
    """
    # Extract frontmatter block; return None if none found
    parts = text.split("---", 2)
    # A well-formed frontmatter splits as: ['', ' block text ', ' body...']
    if len(parts) < 3:
        return None
    fm_block = parts[1]
    m = re.search(r"^updated:\s*(\d{4}-\d{2}-\d{2})", fm_block, re.MULTILINE)
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None
```

- [ ] **Step 4: Run tests — all should pass**

```bash
python -m pytest tests/test_review_scope.py -v
```

Expected: all tests PASS including the 2 new ones.

- [ ] **Step 5: Run full suite**

```bash
python -m pytest tests/ -v
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add skills/shared/review_scope.py tests/test_review_scope.py
git commit -m "fix(review_scope): scope _parse_updated regex to frontmatter block only"
```

---

## Task 8: Add dependency guard to `chart.py`

Matches the guard pattern used by `fetch_inbox.py` (lines 34–51).

**Files:**
- Modify: `skills/view-builder/templates/chart.py`

- [ ] **Step 1: Replace the top of `chart.py`**

Replace lines 1–13 (the current top-level matplotlib import) with:

```python
#!/usr/bin/env python3
"""chart.py — Generate a chart PNG for a vault view.

Writes the PNG to wiki/views/assets/ under the vault root so the output
lands alongside other view assets, not next to this template file.

Adapt TITLE, XLABEL, YLABEL, labels, and values for each chart you need.
"""
import argparse
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("chart.py requires matplotlib. Install it with:", file=sys.stderr)
    print("  pip install matplotlib", file=sys.stderr)
    sys.exit(1)
```

- [ ] **Step 2: Run chart tests**

```bash
python -m pytest tests/test_chart.py -v
```

Expected: all pass (chart.py still imports matplotlib in the test environment).

- [ ] **Step 3: Run full suite**

```bash
python -m pytest tests/ -v
```

Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add skills/view-builder/templates/chart.py
git commit -m "fix(chart): add friendly ImportError message for missing matplotlib"
```

---

## Task 9: Update `init_vault.py` — install new shared scripts

Add `yamlmini.py` and `console.py` to `_SHARED_SCRIPTS` so they are copied into
every generated vault's `.claude/skills/shared/` directory.

**Files:**
- Modify: `init_vault.py` (line 365)

- [ ] **Step 1: Edit `_SHARED_SCRIPTS` in `init_vault.py`**

Find line 365:

```python
    _SHARED_SCRIPTS = ["vault_state.py", "review_scope.py", "find_backlinks.py", "linkutil.py"]
```

Change to:

```python
    _SHARED_SCRIPTS = [
        "vault_state.py",
        "yamlmini.py",
        "console.py",
        "review_scope.py",
        "find_backlinks.py",
        "linkutil.py",
    ]
```

- [ ] **Step 2: Run installer tests**

```bash
python -m pytest tests/test_installer.py tests/test_bootstrap.py -v
```

Expected: all pass.

- [ ] **Step 3: Smoke test: bootstrap a vault and confirm shared scripts are installed**

```bash
python init_vault.py ./tmp-test-vault --yes
```

Check:

```bash
ls ./tmp-test-vault/.claude/skills/shared/
```

Expected output includes: `yamlmini.py`, `console.py`, `vault_state.py`, `linkutil.py`, `review_scope.py`, `find_backlinks.py`.

- [ ] **Step 4: Clean up**

```bash
Remove-Item -Recurse -Force ./tmp-test-vault
```

- [ ] **Step 5: Run full suite**

```bash
python -m pytest tests/ -v
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add init_vault.py
git commit -m "fix(installer): add yamlmini.py and console.py to _SHARED_SCRIPTS"
```

---

## Task 10: Documentation corrections

Four targeted doc fixes. No code changes.

**Files:**
- Modify: `commands/review.md`
- Modify: `CLAUDE.md`
- Modify: `skills/view-builder/SKILL.md`
- Modify: `vault.config.yml`

- [ ] **Step 1: Fix `commands/review.md` — remove stale "not yet available" note**

Find line ~149 (inside the "Suggest next actions" step):

```
   - Contradictions → "consider `/merge` to reconcile (Phase 3, not yet available), or edit the claims manually"
```

Replace with:

```
   - Contradictions → "consider `/merge` to reconcile, or edit the claims manually"
```

- [ ] **Step 2: Fix `CLAUDE.md` — add SPLIT row to skill-dispatch table**

Find the dispatch table (the `| MERGE | ...` row, currently the last row):

```
| MERGE     | (LLM only)     | find_backlinks.py              |
```

Add a new row immediately after it:

```
| SPLIT     | (LLM only)     | find_backlinks.py              |
```

- [ ] **Step 3: Fix `skills/view-builder/SKILL.md` — reconcile "reveal" references**

Find the step 8 in the Workflow section:

```
8. Write to `wiki/views/<slug>.md` (or `.html` for reveal).
```

Change to:

```
8. Write to `wiki/views/<slug>.md`.
```

Also find the "For complex kinds (reveal decks, multi-page reports)..." line (~line 61):

```
4. For complex kinds (reveal decks, multi-page reports), propose the
   outline before writing the full file.
```

Change to:

```
4. For multi-page reports, propose the outline before writing the full file.
```

- [ ] **Step 4: Update `vault.config.yml` — add enforcement-layer comments + block-list note**

Replace the entire file content:

```yaml
# vault.config.yml — per-vault configuration for the second brain vault.
#
# All values here are defaults. Override any key in the copy installed
# at your vault root.
#
# List values support both inline syntax:   key: [a, b, c]
# and block (multi-line) syntax:
#   key:
#     - a
#     - b

vault:
  version: 1

inbox:
  processed_section: "## Processed"   # header used by fetch_inbox.py for done entries
  tags_propagation: true              # whether to carry inbox tags into raw frontmatter

# ── Keys below are READ BY fetch_inbox.py (script-enforced) ──────────────────
fetch:
  html_timeout_seconds: 20
  pdf_timeout_seconds: 60
  max_pdf_size_mb: 50
  pdf_enabled: true
  # Both inline and block-list syntax are supported here:
  walled_domains: [x.com, twitter.com, mobile.twitter.com, linkedin.com, www.linkedin.com, threads.net, facebook.com, www.facebook.com, instagram.com, www.instagram.com]

# ── Keys below are READ BY lint.py (script-enforced) ─────────────────────────
lint:
  stale_source_days: 180             # read by lint.py — advisory after N days without update
  view_stale_days: 30                # read by lint.py — days a view can lag its based_on pages
  # The following three keys are honored by the LLM/command layer, NOT by lint.py:
  auto_trigger_after_fetches: 5      # LLM-layer: run lint after N fetches
  auto_trigger_after_days: 7         # LLM-layer: run lint after N days
  reflect_reminder_days: 14          # LLM-layer: suggest /reflect after N days

# ── Keys below are honored by the LLM/command layer, NOT by any script ────────
ingest:
  max_new_pages_before_confirm: 3    # ask before creating more than N new pages
  max_files_per_operation: 15        # invariant #5 enforcement ceiling

drop_zone:
  path: raw/drop
  enabled: true
```

- [ ] **Step 5: Run full suite one final time**

```bash
python -m pytest tests/ -v
```

Expected: all green. No code was changed in this task.

- [ ] **Step 6: Commit all doc changes together**

```bash
git add commands/review.md CLAUDE.md skills/view-builder/SKILL.md vault.config.yml
git commit -m "docs: fix stale /merge note, add SPLIT dispatch row, reconcile reveal refs, annotate config enforcement layers"
```

---

## Final verification

- [ ] **Run full test suite**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: all tests pass. Count should be ~100 existing + ~30 new.

- [ ] **Bootstrap smoke test on Windows**

```bash
python init_vault.py ./tmp-smoke-vault --yes
python ./tmp-smoke-vault/.claude/skills/inbox-fetcher/scripts/fetch_inbox.py --vault ./tmp-smoke-vault --dry-run
python ./tmp-smoke-vault/.claude/skills/vault-linter/scripts/lint.py --vault ./tmp-smoke-vault
Remove-Item -Recurse -Force ./tmp-smoke-vault
```

Expected: No `UnicodeEncodeError`. Unicode symbols (`✓`, `⚠`) render correctly in the terminal.

- [ ] **Config block-list regression guard**

```bash
python -m pytest tests/test_vault_state.py::TestLoadConfig::test_block_list_walled_domains -v
```

Expected: PASS.

- [ ] **Confirm `yamlmini.py` and `console.py` are in the vault after bootstrap**

Both scripts were verified in Task 9 Step 3 smoke test.
