---
id: TASK-0042
title: 'Update commands/ingest.md: add pre-ingest deduplication check'
status: Done
assignee: []
created_date: '2026-05-28 14:33'
updated_date: '2026-05-28 15:10'
labels: []
milestone: vault-completeness
dependencies: []
references:
  - features/specs/2026-05-28-vault-completeness-design.md
  - features/plans/2026-05-28-vault-completeness-plan.md
modified_files:
  - commands/ingest.md
priority: medium
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a "### Pre-ingest check" subsection inside ## Protocol, before the Web articles and PDFs branches. The check instructs the agent to scan wiki/pages/ for similar concept names before creating new pages, and to update existing pages rather than creating duplicates. Also covers the cross-source dedup case when multiple sources are ingested in the same session.
<!-- SECTION:DESCRIPTION:END -->
