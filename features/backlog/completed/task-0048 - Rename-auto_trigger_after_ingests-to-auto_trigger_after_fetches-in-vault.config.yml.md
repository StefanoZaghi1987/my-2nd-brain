---
id: TASK-0048
title: >-
  Rename auto_trigger_after_ingests to auto_trigger_after_fetches in
  vault.config.yml
status: Done
assignee: []
created_date: '2026-05-28 16:05'
updated_date: '2026-05-28 16:34'
labels:
  - bug-fix
  - rename
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - vault.config.yml
priority: medium
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The config key `auto_trigger_after_ingests` controls the auto-lint threshold for the fetch counter. Rename it to `auto_trigger_after_fetches` to match the corrected semantics in vault_state.py (the counter tracks fetches, not ingests).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Line `auto_trigger_after_ingests: 5` renamed to `auto_trigger_after_fetches: 5`
- [ ] #2 The inline comment on that line (if any) updated to match
- [ ] #3 File is otherwise unchanged
<!-- AC:END -->
