---
id: TASK-0070
title: >-
  Reconcile CLAUDE.md: add FORGET to dispatch table and remove stale hooks
  reference
status: To Do
assignee: []
created_date: '2026-05-29 11:44'
labels: []
milestone: m-0
dependencies: []
documentation:
  - features/specs/2026-05-29-vault-review-merge-hardening-design.md
modified_files:
  - CLAUDE.md
priority: medium
ordinal: 1900
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two inconsistencies in `CLAUDE.md` erode it as an authoritative contract:

1. **Missing dispatch table row**: The header says "Nine operations" and the operations section lists all nine (FETCH, INGEST, FORGET, QUERY, VIEW, REFLECT, LINT, PROMOTE, REFRESH), but the "Skill dispatch" table at line ~225 has only 8 rows — FORGET is absent. It has its own `commands/forget.md` and is fully operational; it simply was never added to the table.

2. **Stale hooks claim**: Line 33 lists `.claude/` contents as "Skills, commands, hooks (mechanisms, not content)". No hooks exist anywhere: no `.claude/hooks/` directory, no `hooks` key in any settings file, and `init_vault.py` never installs any hooks. This claim misleads anyone reading the contract.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Skill dispatch table has 9 rows, including a FORGET row: `FORGET | (LLM only) | —`
- [ ] #2 Line 33 (or wherever the .claude/ directory description appears) no longer mentions 'hooks'
- [ ] #3 Grep for 'hooks' in CLAUDE.md returns zero matches in the directory-listing context (non-hooks uses like 'workflow hooks' are fine if present elsewhere)
<!-- AC:END -->
