---
id: TASK-0091
title: 'feat: ingest depth & coverage — /expand command and map-then-read protocol'
status: Done
assignee: []
created_date: '2026-05-30 21:57'
updated_date: '2026-05-30 22:51'
labels:
  - depth
  - coverage
  - ingest
  - expand
milestone: m-5
dependencies: []
references:
  - features/specs/2026-05-30-ingest-depth-coverage-design.md
  - features/plans/2026-05-30-ingest-depth-coverage.md
documentation:
  - features/specs/2026-05-30-ingest-depth-coverage-design.md
  - features/plans/2026-05-30-ingest-depth-coverage.md
modified_files:
  - CLAUDE.md
  - commands/ingest.md
  - commands/expand.md
  - commands/review.md
  - README.md
  - GETTING-STARTED.md
  - features/prompts/expand-command-template.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix two independent failures that make ingested wiki pages feel thin:

1. **Shallow treatment (depth):** `/ingest` has no structure contract — pages are whatever length the model defaults to. The `view-builder` has 7 view templates; pages/sources have none.
2. **Missing concepts (coverage):** PDF ingest reads only pages 1–5 (+ last 2). A 30-page paper is summarized from a 7-page window; mid-document concepts never enter the vault.

**Solution:**
- Add an adaptive page/source structure schema to `CLAUDE.md` (the missing template)
- Replace the fixed page-window read in `/ingest` with a map-then-read protocol (cheap skim → concept proposal → targeted reads)
- Create `/expand <page>` command: reads sources in full, appends `## Deep dive` to existing pages on demand

**Spec:** `features/specs/2026-05-30-ingest-depth-coverage-design.md`
**Plan:** `features/plans/2026-05-30-ingest-depth-coverage.md`
**Branch:** `feat-deepdive`

**Repo note:** `D:\my-2nd-brain` is the template repo, NOT a live vault. Changes here affect every vault bootstrapped from this template via `python init_vault.py <target-dir>`. There is no `wiki/`, `raw/`, or `inbox.md` in this directory.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
All 8 subtasks complete. 10 commits on feat-deepdive covering: adaptive page/source schema (CLAUDE.md), EXPAND registration (12th op), map-then-read ingest protocol (3 source types), /expand command, review Check C wiring, doc sync (README + GETTING-STARTED). Lint clean on scratch vault. Manual QA steps documented in spec §6 for post-merge live-session verification.

Post-implementation fix (commit 9ab1c2f): CLAUDE.md INGEST source-type branches still described the old fixed-page-window protocol (pages 1-5). Synced all four branches (web articles, PDFs, local PDFs, local Markdown) to the new map-then-read language. Also removed stale '>3 new pages' guard note from the INGEST headline.
<!-- SECTION:FINAL_SUMMARY:END -->
