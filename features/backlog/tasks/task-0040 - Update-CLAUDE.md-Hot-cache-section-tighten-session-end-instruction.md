---
id: TASK-0040
title: 'Update CLAUDE.md Hot cache section: tighten session-end instruction'
status: To Do
assignee: []
created_date: '2026-05-28 14:33'
labels: []
milestone: vault-completeness
dependencies: []
references:
  - features/specs/2026-05-28-vault-completeness-design.md
  - features/plans/2026-05-28-vault-completeness-plan.md
modified_files:
  - CLAUDE.md
priority: medium
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace "if we touched meaningful content" (undefined) and "at session end" (no hook) in the Hot cache section with an actionable rule that references /hot and defines "written to" precisely: any ingest, promote, view, reflect, forget, or refresh that produced file changes — not queries.
<!-- SECTION:DESCRIPTION:END -->
