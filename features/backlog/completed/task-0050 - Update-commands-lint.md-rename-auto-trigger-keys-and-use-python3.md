---
id: TASK-0050
title: 'Update commands/lint.md: rename auto-trigger keys and use python3'
status: Done
assignee: []
created_date: '2026-05-28 16:05'
updated_date: '2026-05-28 16:40'
labels:
  - bug-fix
  - rename
  - docs
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - commands/lint.md
priority: medium
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two changes in commands/lint.md:

1. **Key rename (Item 1):** The auto-trigger section references `ingests_since_last_lint` and `auto_trigger_after_ingests`. Both must be updated to `fetches_since_last_lint` and `auto_trigger_after_fetches` respectively.

2. **python3 normalisation (Item 4):** All bash code blocks use `python`. Change to `python3` for consistency with the canonical command on Linux/macOS.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Auto-trigger section references `fetches_since_last_lint` and `auto_trigger_after_fetches`
- [ ] #2 Every bash code block uses `python3` (not `python`)
- [ ] #3 No other content changes
<!-- AC:END -->
