---
id: TASK-0011
title: 'Update CLAUDE.md INGEST section: PDF protocol and tags/note propagation'
status: Done
assignee: []
created_date: '2026-05-28 07:32'
updated_date: '2026-05-28 10:40'
labels:
  - feature-a
  - feature-b
  - claude-md
milestone: features
dependencies:
  - TASK-0010
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
modified_files:
  - CLAUDE.md
priority: medium
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend the INGEST operation in CLAUDE.md with two explicit protocol branches:

**PDF ingest branch:** When `source_path` in `raw/` index.md has `fetch_method: pdf`, read `paper.pdf` using the Read tool (pages 1–5 for abstract/intro; last 2 pages if total > 10 pages). Infer title from first visible heading or use the slug. Write `wiki/sources/<slug>.md` with the same schema as web sources plus `fetch_method: pdf`.

**Tags and note propagation:** After reading any raw source (web or PDF), check its `index.md` frontmatter for `tags` and `note`. If `tags` is present, carry it into `wiki/sources/<slug>.md` frontmatter. If `note` is present, treat it as a focus directive: the source summary must explicitly address the note topic.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 CLAUDE.md INGEST section has a clearly marked PDF branch with page-reading instructions
- [x] #2 CLAUDE.md INGEST section has a tags/note propagation step that applies to both web and PDF sources
- [x] #3 The PDF branch specifies exactly which pages to read (1-5 + last 2 if >10 pages)
- [x] #4 The note directive instruction is unambiguous: the summary must address the note topic, not merely acknowledge it
- [x] #5 No other CLAUDE.md sections are modified
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 11** in the implementation plan. Add a "### INGEST — source type branches" subsection to CLAUDE.md covering: (a) web article branch (existing), (b) PDF branch (read pages 1–5 + last 2 via Read tool), (c) tags/note propagation rule (tags carry forward; note is a focus directive the summary must explicitly address). Full markdown text provided. Wave 2 — requires Wave 1 complete.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Inserted a new `### INGEST — source type branches` subsection in CLAUDE.md immediately after the existing INGEST paragraph (line 95). The block adds: (1) explicit web-article branch (no change to existing behavior, now documented), (2) PDF branch with page-read instructions (pages 1–5 + last 2 if >10 pages, infer title, add fetch_method to frontmatter), (3) tags/note propagation rule covering both source types. No other sections were modified. Committed as `33ba138`."
<!-- SECTION:FINAL_SUMMARY:END -->
