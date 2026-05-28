---
id: TASK-0028
title: Correct sub-bullet description in inbox-fetcher SKILL.md
status: To Do
assignee: []
created_date: '2026-05-28 12:33'
labels:
  - wave-2
  - docs
milestone: vault-hardening
dependencies: []
modified_files:
  - skills/inbox-fetcher/SKILL.md
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The ## Inbox format section of skills/inbox-fetcher/SKILL.md says indented sub-bullets "are preserved but not parsed". The script actually parses them and writes tags and note into the raw source's index.md frontmatter. The documentation does not reflect the actual behaviour.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §2.1\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 8
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The sentence stating sub-bullets are not parsed is removed
- [ ] #2 Replacement text explains that sub-bullets are parsed and their values written to the raw index.md frontmatter
<!-- AC:END -->
