---
id: TASK-0015
title: Update init-vault.sh to install promote and refresh commands
status: To Do
assignee: []
created_date: '2026-05-28 07:37'
updated_date: '2026-05-28 08:26'
labels:
  - feature-c
  - feature-d
  - bootstrap
milestone: features
dependencies:
  - TASK-0003
  - TASK-0013
  - TASK-0014
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: medium
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add `promote` and `refresh` to the command install loop in `init-vault.sh`. The loop currently iterates over `save view reflect forget` — extend it to `save view reflect forget lint promote refresh`.

This is a one-line change to the loop variable. No other changes to the script are needed; the existing install pattern handles the new commands identically.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 init-vault.sh install loop includes promote and refresh
- [ ] #2 Running init-vault.sh copies commands/promote.md to .claude/commands/promote.md
- [ ] #3 Running init-vault.sh copies commands/refresh.md to .claude/commands/refresh.md
- [ ] #4 The lint command is also included in the loop (from TASK-0006)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 15** in the implementation plan. One-line change in init-vault.sh: extend the command install loop from `for cmd in save view reflect forget lint; do` to also include `promote refresh`. Verify with `bash init-vault.sh /tmp/test-vault-cmds` and check all 7 command files appear in `.claude/commands/`. Wave 2 — depends on TASK-0013 and TASK-0014.
<!-- SECTION:NOTES:END -->
