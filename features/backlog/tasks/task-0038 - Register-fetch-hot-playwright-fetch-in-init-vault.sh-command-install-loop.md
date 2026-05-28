---
id: TASK-0038
title: 'Register fetch, hot, playwright-fetch in init-vault.sh command install loop'
status: To Do
assignee: []
created_date: '2026-05-28 14:33'
labels: []
milestone: vault-completeness
dependencies: []
references:
  - features/plans/2026-05-28-vault-completeness-plan.md
modified_files:
  - init-vault.sh
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend the `for cmd in` loop in init-vault.sh to include the three new command names: fetch, hot, playwright-fetch. Without this change, init-vault.sh will not copy the new command files into .claude/commands/ when bootstrapping or updating a vault.
<!-- SECTION:DESCRIPTION:END -->
