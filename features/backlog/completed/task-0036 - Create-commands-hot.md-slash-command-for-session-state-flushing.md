---
id: TASK-0036
title: Create commands/hot.md slash command for session state flushing
status: Done
assignee: []
created_date: '2026-05-28 14:33'
updated_date: '2026-05-28 14:52'
labels: []
milestone: vault-completeness
dependencies: []
references:
  - features/specs/2026-05-28-vault-completeness-design.md
  - features/plans/2026-05-28-vault-completeness-plan.md
modified_files:
  - commands/hot.md
priority: medium
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create `commands/hot.md` as the explicit slash command for writing wiki/hot.md at session end. Defines what to write (what we did, what's open, what's next), the replace-not-append contract, and when to call it. CLAUDE.md will reference this command in its session-end instruction.
<!-- SECTION:DESCRIPTION:END -->
