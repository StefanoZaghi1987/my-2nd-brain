---
id: TASK-0010
title: Change PDF fetch to produce a folder with paper.pdf and index.md
status: To Do
assignee: []
created_date: '2026-05-28 07:32'
updated_date: '2026-05-28 08:25'
labels:
  - feature-a
  - feature-b
  - fetch
  - pdf
milestone: features
dependencies:
  - TASK-0008
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: medium
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replace the flat `raw/papers/<slug>.pdf` output in `fetch_pdf()` with a folder structure mirroring web articles: `raw/papers/<slug>/paper.pdf` and `raw/papers/<slug>/index.md`.

`index.md` contains a YAML frontmatter block with: `source_url`, `title` (inferred from slug or left as "Untitled"), `fetched` (today's date), `fetch_method: pdf`, `tags` (from entry, omitted if empty), `note` (from entry, omitted if None). The body contains a single reference line: `PDF: [[paper.pdf]]`.

`fetch_pdf()` must accept `tags` and `note` parameters (same as `fetch_html()`). `FetchResult.out_path` points to the folder (`raw/papers/<slug>/`), not the PDF file, for consistency with web article results.

Update the call site in `process_vault()` to pass `entry.tags` and `entry.note`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 fetch_pdf creates raw/papers/<slug>/ directory containing paper.pdf and index.md
- [ ] #2 index.md has valid YAML frontmatter with source_url, fetched, fetch_method: pdf
- [ ] #3 tags and note appear in frontmatter when non-empty, are absent when empty/None
- [ ] #4 FetchResult.out_path points to the folder, not the PDF file
- [ ] #5 Inbox processed line shows the folder path (raw/papers/<slug>/) not the file path
- [ ] #6 Existing PDF download logic (streaming, size warning, timeout) is unchanged
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 10** in the implementation plan. Replace `fetch_pdf()` to produce `raw/papers/<slug>/paper.pdf` + `raw/papers/<slug>/index.md` instead of a flat file. Full replacement function provided. `FetchResult.out_path` points to the folder (not the PDF file). Requires `pip install requests-mock` for the test. Wave 2 — depends on Wave 1 and TASK-0004.
<!-- SECTION:NOTES:END -->
