---
id: TASK-0067
title: Graceful degradation when a lint check throws in lint.py
status: To Do
assignee: []
created_date: '2026-05-29 11:43'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - skills/vault-linter/scripts/lint.py
  - tests/test_lint.py
priority: medium
ordinal: 1600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In `skills/vault-linter/scripts/lint.py`, the `all_checks` loop (line ~805) runs each check function without a try/except. If any single check raises an uncaught exception, the entire lint run aborts with exit code 2 — one edge-case check kills the whole health report.

Wrap each check invocation in a try/except so a crashing check is recorded as an advisory finding (`"check crashed: <check_name>: <exc>"`) and the loop continues. Exit code 2 should be reserved for catastrophic failure (e.g., vault path doesn't exist, no checks completed at all).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 When one check function raises an exception, the lint run continues and other checks produce results
- [ ] #2 The crashed check appears in the report as an advisory finding with the check name and exception message
- [ ] #3 Exit code is 1 (findings present) when some checks pass and one crashes; not 2
- [ ] #4 Exit code 2 is only returned when no checks complete at all (e.g., vault missing)
- [ ] #5 One new test injects a mock check that raises; asserts exit 1 and the crash advisory in output
<!-- AC:END -->
