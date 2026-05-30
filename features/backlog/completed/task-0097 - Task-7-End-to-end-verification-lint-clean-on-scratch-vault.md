---
id: TASK-0097
title: 'Task 7: End-to-end verification (lint clean on scratch vault)'
status: Done
assignee: []
created_date: '2026-05-30 22:09'
updated_date: '2026-05-30 22:46'
labels:
  - verification
milestone: m-5
dependencies: []
references:
  - features/specs/2026-05-30-ingest-depth-coverage-design.md#6-verification
  - >-
    features/plans/2026-05-30-ingest-depth-coverage.md#task-7--end-to-end-verification
priority: medium
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Bootstrap a scratch vault, create a test page with expanded: frontmatter key and ## Deep dive section, run lint.py. Confirm no new finding categories triggered. Verify 6 task commits on feat-deepdive. Document manual QA steps for interactive behaviors.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Lint exits 0 or exit 1 with only expected dead-link finding (no new categories)
- [x] #2 6 commits on feat-deepdive with the specified messages
- [x] #3 Manual QA steps documented for post-merge testing
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Lint PASS: expanded: key and ## Deep dive section cause no new finding categories (only expected dead_links + orphan from test setup). Git log PASS: all 6 task areas covered by 10 commits on feat-deepdive. Manual QA steps (map-then-read coverage, /expand depth, idempotency, review driver, unattended guard) documented in spec §6 and plan Task 7 Steps 2-6 — require live interactive sessions.
<!-- SECTION:FINAL_SUMMARY:END -->
