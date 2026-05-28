---
id: TASK-0043
title: 'Update commands/refresh.md: add PDF branch to protocol steps 1-3'
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
  - commands/refresh.md
priority: medium
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace the flat steps 1-3 in /refresh with a branching protocol that reads fetch_method from the source frontmatter. Web articles follow the existing re-fetch path. PDF sources prompt the user to choose between re-fetching the original URL and re-summarising from the existing paper.pdf — avoiding unnecessary network fetches for papers that don't change.
<!-- SECTION:DESCRIPTION:END -->
