---
id: TASK-0025
title: Remove unreachable entries from ORPHAN_EXCEPTIONS
status: Done
assignee: []
created_date: '2026-05-28 12:33'
updated_date: '2026-05-28 13:41'
labels:
  - wave-1
  - linter
milestone: vault-hardening
dependencies: []
documentation:
  - features/plans/2026-05-28-vault-hardening-plan.md#task-5
modified_files:
  - skills/vault-linter/scripts/lint.py
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
lint.py ORPHAN_EXCEPTIONS contains "index.md" and "log.md" without the wiki/ prefix. load_wiki() stores all paths as vault-relative strings starting with "wiki/", so these bare entries can never match anything and provide no protection.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §1.4\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 5
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ORPHAN_EXCEPTIONS contains exactly four entries: wiki/hot.md, wiki/compass.md, wiki/index.md, wiki/log.md
- [ ] #2 pytest tests/test_lint.py passes with no regressions
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
In `skills/vault-linter/scripts/lint.py`, find `ORPHAN_EXCEPTIONS` near the top of the file (~line 44). Remove the two entries without the `wiki/` prefix. The set should contain exactly: `"wiki/hot.md"`, `"wiki/compass.md"`, `"wiki/index.md"`, `"wiki/log.md"`. No test changes needed. Verify: `pytest tests/test_lint.py -v`
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Removed `"index.md"` and `"log.md"` from `ORPHAN_EXCEPTIONS` — `load_wiki()` always produces `wiki/`-prefixed paths so bare names were unreachable dead code. No new tests; existing orphan tests remain green. All 51 tests pass. Commit: f52e936.
<!-- SECTION:FINAL_SUMMARY:END -->
