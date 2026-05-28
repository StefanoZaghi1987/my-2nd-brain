---
id: TASK-0049
title: >-
  Update CLAUDE.md session-start auto-lint condition to reference
  fetches_since_last_lint
status: Done
assignee: []
created_date: '2026-05-28 16:05'
updated_date: '2026-05-28 16:39'
labels:
  - bug-fix
  - rename
milestone: Vault portability
dependencies: []
documentation:
  - features/specs/2026-05-28-portability-design.md
modified_files:
  - CLAUDE.md
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The Session start section of CLAUDE.md contains an auto-lint trigger condition that references `ingests_since_last_lint` and `auto_trigger_after_ingests`. Both names must be updated to match the semantic rename (`fetches_since_last_lint` / `auto_trigger_after_fetches`).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 In the Session start section, `ingests_since_last_lint` is replaced with `fetches_since_last_lint`
- [ ] #2 In the Session start section, `auto_trigger_after_ingests` is replaced with `auto_trigger_after_fetches`
- [ ] #3 No other content in CLAUDE.md changes
<!-- AC:END -->
