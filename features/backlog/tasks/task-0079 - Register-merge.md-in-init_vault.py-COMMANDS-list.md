---
id: TASK-0079
title: Register merge.md in init_vault.py COMMANDS list
status: To Do
assignee: []
created_date: '2026-05-29 11:45'
labels: []
milestone: m-2
dependencies:
  - TASK-0076
  - TASK-0077
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - init_vault.py
priority: medium
ordinal: 5300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add `merge.md` to the `COMMANDS` list in `init_vault.py` so it is installed into every vault bootstrapped after this change. `find_backlinks.py` installation is already handled by task-0076 (the helper task), but verify here that the shared skill install step covers it.

Also confirm that `find_backlinks.py` is listed in the `init_vault.py` shared-scripts install block alongside `vault_state.py` and (after task-0075) `review_scope.py`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 'merge.md' appears in the COMMANDS list in init_vault.py
- [ ] #2 'find_backlinks.py' is installed into .claude/skills/shared/ by init_vault.py
- [ ] #3 Running python init_vault.py <tmp> produces a vault with .claude/commands/merge.md and .claude/skills/shared/find_backlinks.py present
- [ ] #4 Existing bootstrap tests remain green
<!-- AC:END -->
