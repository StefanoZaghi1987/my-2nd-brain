---
id: TASK-0033
title: 'Add type:conversation and promoted_to fields to /save template'
status: To Do
assignee: []
created_date: '2026-05-28 12:34'
labels:
  - wave-2
  - commands
milestone: vault-hardening
dependencies:
  - TASK-0026
modified_files:
  - commands/save.md
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The /save command template frontmatter has date and tags but no type field. The new check_conversations linter check (TASK-0026) expects type: conversation. The promoted_to field is populated by /promote and consulted by /reflect to identify unincorporated insights.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §2.6\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 13
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Template frontmatter block includes type: conversation as the first field
- [ ] #2 Template frontmatter block includes promoted_to: []
<!-- AC:END -->
