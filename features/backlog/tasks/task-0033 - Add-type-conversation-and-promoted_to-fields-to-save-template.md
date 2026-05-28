---
id: TASK-0033
title: 'Add type:conversation and promoted_to fields to /save template'
status: To Do
assignee: []
created_date: '2026-05-28 12:34'
updated_date: '2026-05-28 12:42'
labels:
  - wave-2
  - commands
milestone: vault-hardening
dependencies:
  - TASK-0026
documentation:
  - features/plans/2026-05-28-vault-hardening-plan.md#task-13
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
In `commands/save.md`, find the `## Template` section. Inside the fenced code block, find the frontmatter block that starts with `---` and has `date:` as the first field. Add `type: conversation` as the first field (before `date:`), and add `promoted_to: []` as the last field before the closing `---`. The `promoted_to` field is populated by /promote and read by /reflect. This task depends on TASK-0026 (check_conversations expects type:conversation; save.md is the authoritative source for the schema). No tests needed.
<!-- SECTION:NOTES:END -->
