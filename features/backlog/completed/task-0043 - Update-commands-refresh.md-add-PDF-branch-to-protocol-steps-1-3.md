---
id: TASK-0043
title: 'Update commands/refresh.md: add PDF branch to protocol steps 1-3'
status: Done
assignee: []
created_date: '2026-05-28 14:33'
updated_date: '2026-05-28 15:13'
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

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Replaced steps 1-3 of /refresh protocol with branching logic based on fetch_method frontmatter.

**Changes:**
- Step 1 now reads `fetch_method` in addition to `source_url`
- Step 2 branches: web articles (fetch_method absent or 'html') follow the existing re-fetch queue; PDFs (fetch_method: pdf) prompt user to choose between re-fetching the original URL or re-summarising from the existing paper.pdf
- Step 3 remains as before, re-ingesting the updated summary

**Rationale:** PDFs rarely change and re-fetching the original URL can be skipped if the user only wants to refresh the summary. This avoids unnecessary network activity while preserving the full re-fetch option when needed.

**Commit:** feat-brainstorming 563c6c1 "add PDF branch to /refresh: ask before re-fetching unchanged papers"
<!-- SECTION:FINAL_SUMMARY:END -->
