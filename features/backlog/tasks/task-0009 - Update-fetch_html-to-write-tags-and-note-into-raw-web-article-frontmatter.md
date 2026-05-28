---
id: TASK-0009
title: Update fetch_html to write tags and note into raw web article frontmatter
status: To Do
assignee: []
created_date: '2026-05-28 07:31'
updated_date: '2026-05-28 08:25'
labels:
  - feature-b
  - fetch
milestone: features
dependencies:
  - TASK-0008
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: medium
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend `fetch_html()` in `fetch_inbox.py` to accept `tags: list[str]` and `note: str | None` parameters. When either is non-empty, append them to the YAML frontmatter block written to `raw/web/<slug>/index.md`.

Frontmatter format for tags: `tags: [tag1, tag2]` (inline list). For note: `note: "..."` (quoted string). Both fields are omitted entirely when empty/None — no empty `tags: []` noise in the output.

Update the call site in `process_vault()` to pass `entry.tags` and `entry.note` through to `fetch_html()`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 fetch_html accepts tags and note parameters
- [ ] #2 Non-empty tags appear as an inline YAML list in the frontmatter
- [ ] #3 Non-empty note appears as a quoted YAML string in the frontmatter
- [ ] #4 Empty tags and None note produce no frontmatter keys
- [ ] #5 Existing frontmatter fields (source_url, title, author, fetched, etc.) are unaffected
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 9** in the implementation plan. Changes to `fetch_html()`: add `tags` and `note` optional parameters; write them into the index.md frontmatter using `yaml_escape()` for note. Update the call site in `process_vault()` to pass `e.tags` and `e.note`. Tests provided in `TestFetchHtmlFrontmatter` class. Wave 2 — depends on Wave 1 and TASK-0004 (tags/note already parsed into InboxEntry).
<!-- SECTION:NOTES:END -->
