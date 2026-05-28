---
id: TASK-0059
title: 'feat(ingest): copy-paste PDF ingestion via drop zone'
status: To Do
assignee: []
created_date: '2026-05-28 21:07'
labels:
  - feature
  - ingest
  - pdf
milestone: feat-ingest
dependencies: []
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Enable users to copy-paste PDF files into a dedicated `raw/drop/` folder and have them automatically adopted and ingested into the wiki by running `/ingest`.

**Design decisions (from spec `features/specs/2026-05-28-copy-paste-pdf-ingestion-design.md`):**
- Drop zone: `raw/drop/` (configurable via `vault.config.yml`)
- Storage: `raw/local/<slug>/` — kept separate from `raw/papers/` (URL-fetched) to preserve provenance
- New script `adopt_drop.py` handles raw-layer adoption (scripts write raw/, LLM writes wiki/)
- `fetch_method: local-pdf` distinguishes local PDFs from URL-fetched ones at every layer
- `/ingest` gains a pre-flight block that runs the script and prompts for tags/notes interactively

**Implementation plan:** `features/plans/2026-05-28-copy-paste-pdf-ingestion-plan.md`
<!-- SECTION:DESCRIPTION:END -->
