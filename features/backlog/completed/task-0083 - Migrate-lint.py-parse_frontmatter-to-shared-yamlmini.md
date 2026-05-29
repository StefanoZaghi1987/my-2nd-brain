---
id: TASK-0083
title: Migrate lint.py parse_frontmatter to shared yamlmini
status: Done
assignee: []
created_date: '2026-05-29 21:36'
updated_date: '2026-05-29 23:14'
labels:
  - linter
  - yaml
  - bugfix
milestone: m-4
dependencies:
  - TASK-0081
documentation:
  - features/plans/2026-05-29-correctness-robustness-hardening.md
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
`lint.py` has its own `parse_frontmatter` function (~75 lines). Task 0081 created the shared `yamlmini.parse_frontmatter` which is a superset. This task replaces the local definition with the shared import.

## Repo orientation
Engine repo at `D:\my-2nd-brain`. File to modify: `skills/vault-linter/scripts/lint.py`. Tests: `tests/test_lint.py`.
Import path: `sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))`.
Run: `python -m pytest tests/test_lint.py -v`

## What to change
1. Add `from yamlmini import parse_frontmatter` to the import block in `lint.py` (after the existing `from vault_state` and `from linkutil` lines).
2. Delete the entire local `parse_frontmatter` function (lines 87–162 in the original).
3. `lint.py` callers of `parse_frontmatter(text)` expect `(dict, body_str)` — a 2-tuple — but `yamlmini.parse_frontmatter` returns only the dict. Add a local adapter:
```python
def _parse_frontmatter_with_body(text: str) -> tuple[dict, str]:
    import re as _re
    fm = parse_frontmatter(text)
    m = _re.match(r"^---\n.*?\n---\n?", text, _re.DOTALL)
    body = text[m.end():].lstrip("\n") if m else text
    return fm, body
```
4. Replace the single call site `parse_frontmatter(text)` in `load_wiki` with `_parse_frontmatter_with_body(text)`.

No new tests needed — the existing `test_lint.py` suite provides full regression coverage. All existing tests must pass.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 lint.py no longer defines its own parse_frontmatter function
- [x] #2 All test_lint.py tests pass with no regressions
- [x] #3 Full pytest suite passes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added `from yamlmini import parse_frontmatter` to lint.py. Deleted the 76-line local parse_frontmatter function. Added _parse_frontmatter_with_body() adapter (returns (dict, str) tuple for backward-compat). CRITICAL CORRECTION applied: routed BOTH call sites through the adapter — L169 (load_wiki) AND L639 (check_conversations). The plan said "single call site" but there were two; missing L639 would have caused silent dict-as-tuple mis-unpack. Also removed dead FRONTMATTER_RE constant and the redundant `import re as _re` inside the adapter. Removed obsolete TestDifferentialParity class from test_yamlmini.py.
<!-- SECTION:FINAL_SUMMARY:END -->
