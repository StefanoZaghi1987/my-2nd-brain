---
id: TASK-0028
title: Correct sub-bullet description in inbox-fetcher SKILL.md
status: To Do
assignee: []
created_date: '2026-05-28 12:33'
updated_date: '2026-05-28 12:41'
labels:
  - wave-2
  - docs
milestone: vault-hardening
dependencies: []
documentation:
  - features/plans/2026-05-28-vault-hardening-plan.md#task-8
modified_files:
  - skills/inbox-fetcher/SKILL.md
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The ## Inbox format section of skills/inbox-fetcher/SKILL.md says indented sub-bullets "are preserved but not parsed". The script actually parses them and writes tags and note into the raw source's index.md frontmatter. The documentation does not reflect the actual behaviour.\n\nSpec: `features/specs/2026-05-28-vault-hardening-design.md` §2.1\nPlan: `features/plans/2026-05-28-vault-hardening-plan.md` Task 8
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The sentence stating sub-bullets are not parsed is removed
- [ ] #2 Replacement text explains that sub-bullets are parsed and their values written to the raw index.md frontmatter
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
In `skills/inbox-fetcher/SKILL.md`, find the `## Inbox format` section. Locate the bullet that says: "Indented sub-bullets (tags, notes) are preserved but not parsed — they're hints for the ingest step." Replace that single sentence with: "Indented sub-bullets (`- tags: tag1, tag2` and `- note: focus on X`) are parsed by the script and written into the raw source's `index.md` frontmatter. The ingest step reads them from there via tag/note propagation." No tests needed — prose-only change.
<!-- SECTION:NOTES:END -->
