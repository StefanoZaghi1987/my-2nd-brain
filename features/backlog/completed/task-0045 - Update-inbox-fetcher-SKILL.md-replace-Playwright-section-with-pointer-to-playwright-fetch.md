---
id: TASK-0045
title: >-
  Update inbox-fetcher SKILL.md: replace Playwright section with pointer to
  /playwright-fetch
status: Done
assignee: []
created_date: '2026-05-28 14:33'
updated_date: '2026-05-28 15:16'
labels: []
milestone: vault-completeness
dependencies: []
references:
  - features/specs/2026-05-28-vault-completeness-design.md
  - features/plans/2026-05-28-vault-completeness-plan.md
modified_files:
  - skills/inbox-fetcher/SKILL.md
priority: medium
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace the 30-line Playwright fallback protocol in skills/inbox-fetcher/SKILL.md with a 3-line pointer to /playwright-fetch. The protocol now lives in commands/playwright-fetch.md as the single authoritative source. The SKILL.md retains only the routing decision (why URLs get marked ⚠) without owning the response protocol.
<!-- SECTION:DESCRIPTION:END -->
