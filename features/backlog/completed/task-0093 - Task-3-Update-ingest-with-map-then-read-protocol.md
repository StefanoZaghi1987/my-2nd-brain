---
id: TASK-0093
title: 'Task 3: Update /ingest with map-then-read protocol'
status: Done
assignee: []
created_date: '2026-05-30 22:09'
updated_date: '2026-05-30 22:33'
labels:
  - commands
  - ingest
milestone: m-5
dependencies: []
references:
  - >-
    features/specs/2026-05-30-ingest-depth-coverage-design.md#32-map-then-read-in-ingest-coverage-fix
  - >-
    features/plans/2026-05-30-ingest-depth-coverage.md#task-3--update-ingest-with-map-then-read-protocol
modified_files:
  - commands/ingest.md
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace fixed page-window reads in commands/ingest.md with a map→propose→target-read protocol for all three source types (web articles, PDFs, local-md). Replace the ≤3 new pages guard with concept-list confirmation. Preserve ≤15 files invariant guard.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Web articles: 6-step protocol with Map, Propose, Read backing sections, Write, Propagate
- [x] #2 PDFs: 7-step protocol where map scans ALL pages for headings (no 'pages 1-5' cap)
- [x] #3 Local Markdown: 8-step protocol (map free since file already in context)
- [x] #4 Guards: concept-list confirmation replaces ≤3 new pages; ≤15 files guard preserved
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Map-then-read protocol applied to all 3 source types. Committed aba8083 + fixup 1e0425c (web map label clarification, schema cross-ref added to PDF/local-md branches, Guards step-reference made protocol-name agnostic).
<!-- SECTION:FINAL_SUMMARY:END -->
