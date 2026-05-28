---
id: TASK-0008
title: Parse inbox sub-bullets into InboxEntry tags and note fields
status: Done
assignee: []
created_date: '2026-05-28 07:31'
updated_date: '2026-05-28 09:25'
labels:
  - feature-b
  - fetch
  - inbox
milestone: features
dependencies:
  - TASK-0004
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: medium
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend `InboxEntry` in `fetch_inbox.py` with two optional fields: `tags: list[str]` (default empty) and `note: str | None` (default None).

Update `find_unchecked_entries()` to scan indented lines immediately following each unchecked URL line. A line matching `  - tags: ...` populates `tags` (comma-split, stripped). A line matching `  - note: ...` populates `note`. Stop scanning when a non-indented line or another URL line is encountered.

The parsed values are attached to the `InboxEntry` and passed through to `fetch_html()` and `fetch_pdf()` so they can write them into the raw output.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 InboxEntry has tags (list[str]) and note (str | None) fields
- [ ] #2 find_unchecked_entries correctly parses tags and note from indented sub-bullets
- [ ] #3 Entries with no sub-bullets have empty tags and None note
- [ ] #4 Sub-bullets that are not tags or note lines are ignored without error
- [ ] #5 HTML comment stripping applied before sub-bullet parsing
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**ALREADY FULFILLED by TASK-0004.** InboxEntry tags/note fields and updated `find_unchecked_entries()` are implemented in Task 4 of the plan. See **Task 8** in the plan — verification only. Run `pytest tests/test_fetch_inbox.py::TestFindUncheckedEntries -v` to confirm. No new code to write.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Verification only — sub-bullet parsing implemented in TASK-0004. TestFindUncheckedEntries (8 tests) all pass.
<!-- SECTION:FINAL_SUMMARY:END -->
