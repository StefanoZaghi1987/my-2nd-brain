---
id: TASK-0007
title: Add based_on dead link check to lint.py
status: Done
assignee: []
created_date: '2026-05-28 07:25'
updated_date: '2026-05-28 09:25'
labels:
  - bug-fix
  - lint
milestone: bug-fixes
dependencies:
  - TASK-0005
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: high
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend `lint.py` with two changes:

1. Extract a `strip_wikilink(s)` helper that removes leading `[[` and trailing `]]` from a string. This logic currently exists inline in `check_view_staleness()` — move it to a shared helper used by both that function and the new check.

2. Add `check_based_on_links(pages, vault)` that iterates all view pages, reads each entry in their `based_on` frontmatter list, strips wiki-link brackets via `strip_wikilink()`, and resolves each via the existing `normalize_link_target()`. Unresolvable entries produce a **blocking** finding under a new check name `based_on_dead_links`.

Register the new check in the `all_checks` list in `run_lint()`, after `dead_links` (same signature: takes `pages` and `vault`).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 strip_wikilink() helper exists and is used by both check_view_staleness and check_based_on_links
- [ ] #2 check_based_on_links produces blocking findings for based_on entries that do not resolve to existing files
- [ ] #3 check_based_on_links produces no findings when all based_on entries resolve correctly
- [ ] #4 The new check appears in the lint report under section 'based_on_dead_links'
- [ ] #5 Existing check_view_staleness behaviour is unchanged after the strip_wikilink refactor
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**ALREADY FULFILLED by TASK-0005.** `strip_wikilink()` and `check_based_on_links()` are implemented in Task 5 of the plan (lint.py migration). See **Task 7** in the plan — it contains only a verification step. Run `pytest tests/test_lint.py::TestCheckBasedOnLinks tests/test_lint.py::TestStripWikilink -v` to confirm. No new code to write.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Verification only — check_based_on_links and strip_wikilink implemented in TASK-0005. TestCheckBasedOnLinks (3 tests) and TestStripWikilink (3 tests) all pass.
<!-- SECTION:FINAL_SUMMARY:END -->
