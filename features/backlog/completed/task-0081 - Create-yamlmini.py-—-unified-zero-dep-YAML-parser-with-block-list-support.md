---
id: TASK-0081
title: Create yamlmini.py — unified zero-dep YAML parser with block-list support
status: Done
assignee: []
created_date: '2026-05-29 21:36'
updated_date: '2026-05-29 23:14'
labels:
  - shared
  - yaml
  - bugfix
milestone: m-4
dependencies: []
documentation:
  - features/specs/2026-05-29-correctness-robustness-hardening-design.md
  - features/plans/2026-05-29-correctness-robustness-hardening.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
The engine has THREE divergent hand-rolled YAML parsers. The critical silent-failure: `vault_state._parse_config_yaml` does NOT support block-list syntax. A user writing `walled_domains:` as a natural YAML block list in `vault.config.yml` gets a silently empty list — disabling all walled-domain protection with no error.

## Repo orientation
Engine repo at `D:\my-2nd-brain` (not a live vault). Key layout:
- `skills/shared/` — shared Python modules installed into every vault
- `tests/` — pytest suite (~100 tests)
- `init_vault.py` — bootstrapper that copies shared scripts to `.claude/skills/shared/`

Test import pattern (used in all test files):
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "shared"))
from yamlmini import parse_yaml, parse_frontmatter
```
Run: `python -m pytest tests/ -v`

## What to build
New file `skills/shared/yamlmini.py` with two public functions:
- `parse_yaml(text: str) -> dict` — superset of both existing parsers: scalars (bool/null/int/string), inline lists `[a, b]`, **block lists** (`- item`), 2-level nesting.
- `parse_frontmatter(text: str) -> dict` — extracts `---…---` block then calls `parse_yaml`. Returns `{}` if no frontmatter.

Built by composing proven logic from `lint.parse_frontmatter` (block lists) and `vault_state._parse_config_yaml` (nesting + scalars). Use a lookahead helper to distinguish a top-level empty key that starts a section header vs one that starts a block list.

## CRITICAL: Write characterization tests FIRST
Before implementing, write `tests/test_yamlmini.py` with three sections:
- Section A: verify `parse_yaml` reproduces `_parse_config_yaml` behavior (nesting, inline lists, scalars, comments)
- Section B: verify `parse_frontmatter` reproduces `lint.parse_frontmatter` behavior (flat scalars, inline lists, block lists, quoted values)
- Section C: NEW capability test — `walled_domains` as a block list under `fetch:` section parses to the correct list (not empty)

Full test and implementation code is in the implementation plan.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 tests/test_yamlmini.py exists with at least 20 tests covering scalars, inline lists, block lists, 2-level nesting, quoted values, and comments
- [x] #2 All characterization tests pass (reproduce exact behavior of both old parsers)
- [x] #3 Headline test passes: walled_domains as a YAML block list under fetch: section parses to the full list, not []
- [x] #4 parse_frontmatter returns {} when no ---...--- block is present
- [x] #5 parse_frontmatter ignores body prose (no leakage past closing ---)
- [x] #6 Full pytest suite passes with no regressions
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Created skills/shared/yamlmini.py (165 lines) — unified zero-dep YAML parser with parse_yaml() and parse_frontmatter(). Handles scalars, inline lists, block lists, 2-level nesting, inline comments. Added tests/test_yamlmini.py with 26 tests (all passing): Sections A/B reproduce old-parser behavior; Section C guards the headline fix (walled_domains as block list → full list, not []). Two bugs caught and fixed during review: empty section header now produces {} not ""; block-list items now go through _parse_scalar (scalar coercion parity with inline lists). Differential parity verified against both old parsers before they were deleted.
<!-- SECTION:FINAL_SUMMARY:END -->
