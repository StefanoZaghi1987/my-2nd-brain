---
id: TASK-0035
title: Create commands/fetch.md slash command for inbox processing
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
  - commands/fetch.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create `commands/fetch.md` as the named slash command entry point for the FETCH operation. Every other operation has a slash command file; this closes the gap for FETCH. The file dispatches to the inbox-fetcher skill script and chains to /playwright-fetch and /ingest after running.
<!-- SECTION:DESCRIPTION:END -->
