---
id: TASK-0087
title: Fix review_scope._parse_updated to scope regex to frontmatter block only
status: Done
assignee: []
created_date: '2026-05-29 21:37'
updated_date: '2026-05-29 23:14'
labels:
  - shared
  - review
  - bugfix
milestone: m-4
dependencies: []
documentation:
  - features/plans/2026-05-29-correctness-robustness-hardening.md
priority: medium
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Context
`review_scope._parse_updated` uses `re.search(r"^updated:...", text, re.MULTILINE)` which matches `updated:` **anywhere** in the file, including body prose and code blocks. A page that mentions "this note was updated: 2020-01-01 in the old format" in its body will be mis-dated.

**Important design constraint:** `review_scope.py` is intentionally self-contained (docstring lines 7-9: "Uses a self-contained frontmatter parser so this script can run as a standalone utility regardless of where the other skill scripts live"). Do NOT import from `shared/` — fix the regex scoping inline.

## Repo orientation
Engine repo at `D:\my-2nd-brain`. File: `skills/shared/review_scope.py` (standalone script — no shared imports). Tests: `tests/test_review_scope.py`.
Run: `python -m pytest tests/test_review_scope.py -v`

## Fix
Replace `_parse_updated` with a version that extracts the frontmatter block first:
```python
def _parse_updated(text: str) -> date | None:
    """Extract updated: from YAML frontmatter block only. Self-contained."""
    parts = text.split("---", 2)
    # Well-formed frontmatter: ['', ' block text ', ' body...']
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

## Tests to add (write before implementing)
```python
def test_body_prose_updated_date_is_ignored(tmp_path): ...
def test_frontmatter_updated_date_is_used(tmp_path): ...
```
Full test code is in the implementation plan (Task 7, Step 1).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A page with 'updated: 2020-01-01' only in its body prose returns None from _parse_updated (not the body date)
- [x] #2 A page with 'updated: 2026-05-01' in its frontmatter returns that date correctly
- [x] #3 review_scope.py still has NO imports from skills/shared/ (self-contained constraint preserved)
- [ ] #4 All existing test_review_scope.py tests pass
- [ ] #5 Full pytest suite passes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Fixed _parse_updated in review_scope.py: extract frontmatter block via text.split("---", 2) first, apply updated: regex only to parts[1]. Returns None when len(parts) < 3. Script remains self-contained (no shared/ import). Added test_body_prose_updated_date_is_ignored (regression guard) and test_frontmatter_updated_date_is_used (positive case).
<!-- SECTION:FINAL_SUMMARY:END -->
