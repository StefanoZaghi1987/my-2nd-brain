---
id: TASK-0098
title: 'Task 2: Register EXPAND operation across CLAUDE.md (6 points)'
status: Done
assignee: []
created_date: '2026-05-30 22:09'
updated_date: '2026-05-30 22:25'
labels:
  - docs
  - claude-md
milestone: m-5
dependencies:
  - TASK-0092
references:
  - >-
    features/specs/2026-05-30-ingest-depth-coverage-design.md#34-wire-expand-into-system-docs-claudemd
  - >-
    features/plans/2026-05-30-ingest-depth-coverage.md#task-2--register-expand-throughout-claudemd
modified_files:
  - CLAUDE.md
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Six registration points in CLAUDE.md: rename header to 'Twelve operations', add EXPAND op entry (after REFRESH, before MERGE), add EXPAND row to skill dispatch table, add 'expand' to /hot trigger list, add 'expand' to unattended CANNOT list, add /expand to slash commands list. Depends on Task 1 (renames Eleven→Twelve).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Header reads '## Twelve operations'
- [x] #2 EXPAND operation entry present between REFRESH and MERGE
- [x] #3 EXPAND row in skill dispatch table
- [x] #4 'expand' in hot-cache trigger sentence
- [x] #5 'expand' in unattended CANNOT list
- [x] #6 '/expand <page>' in slash commands list
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
All 6 EXPAND registration points applied to CLAUDE.md: header renamed to Twelve operations, EXPAND op block inserted between REFRESH and MERGE, dispatch table row added, hot-cache trigger updated, unattended CANNOT list updated, slash-command entry added. Committed as 4fddde2. Code review noted REFRESH is missing its own 'Not available unattended' marker (pre-existing gap, out of scope).
<!-- SECTION:FINAL_SUMMARY:END -->
