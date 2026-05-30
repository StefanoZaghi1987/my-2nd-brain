---
id: TASK-0092
title: 'Task 1: Add page & source structure schema to CLAUDE.md'
status: Done
assignee: []
created_date: '2026-05-30 22:08'
updated_date: '2026-05-30 22:23'
labels:
  - docs
  - claude-md
milestone: m-5
dependencies: []
references:
  - >-
    features/specs/2026-05-30-ingest-depth-coverage-design.md#31-page--source-structure-schema
  - >-
    features/plans/2026-05-30-ingest-depth-coverage.md#task-1--add-page--source-structure-schema-to-claudemd
modified_files:
  - CLAUDE.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Insert the adaptive page/source structure schema section between the Frontmatter `---` separator and `## Eleven operations` in CLAUDE.md. This is the missing generation contract — the equivalent of view-builder's 7 templates for pages and sources.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 New 'Page & source structure' section appears between Frontmatter separator and '## Eleven operations'
- [x] #2 Both wiki/sources/ and wiki/pages/ body templates present with indented code examples
- [x] #3 No other content in CLAUDE.md was changed
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Inserted the adaptive page/source structure schema section between the Frontmatter separator and ## Eleven operations. Both wiki/sources/ and wiki/pages/ body templates present with 4-space indented bodies. Committed as 5b14fc7 + fixup c113dbc (placeholder normalization flagged by code quality review).
<!-- SECTION:FINAL_SUMMARY:END -->
