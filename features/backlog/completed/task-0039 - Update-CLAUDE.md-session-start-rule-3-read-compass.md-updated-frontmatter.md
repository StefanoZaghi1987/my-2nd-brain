---
id: TASK-0039
title: 'Update CLAUDE.md session-start rule 3: read compass.md updated frontmatter'
status: Done
assignee: []
created_date: '2026-05-28 14:33'
updated_date: '2026-05-28 15:05'
labels: []
milestone: vault-completeness
dependencies: []
references:
  - features/specs/2026-05-28-vault-completeness-design.md
  - features/plans/2026-05-28-vault-completeness-plan.md
modified_files:
  - CLAUDE.md
priority: medium
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace the vague "hasn't been updated" language in Session start rule #3 with an explicit instruction to read the `updated` field from wiki/compass.md frontmatter and compare it to today. This removes ambiguity about where to look (filesystem mtime vs frontmatter) and works correctly across git clones.
<!-- SECTION:DESCRIPTION:END -->
