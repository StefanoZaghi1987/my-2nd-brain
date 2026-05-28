---
id: TASK-0016
title: >-
  Update CLAUDE.md: add PROMOTE and REFRESH operations + extend source_path
  convention
status: Done
assignee: []
created_date: '2026-05-28 07:37'
updated_date: '2026-05-28 10:44'
labels:
  - feature-c
  - feature-d
  - claude-md
milestone: features
dependencies:
  - TASK-0013
  - TASK-0014
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: medium
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Three changes to CLAUDE.md:

1. **Add PROMOTE to the Seven operations section** — brief description referencing `commands/promote.md` for the full protocol. Add it as operation #8.

2. **Add REFRESH to the Seven operations section** — brief description referencing `commands/refresh.md`. Add it as operation #9.

3. **Extend the source_path convention in the Frontmatter section** — the current example shows `source_path: raw/papers/name.pdf`. Add a note that conversation-derived sources use `source_path: conversations/<slug>.md`. This makes `wiki/sources/conv-<slug>.md` entries valid without breaking the existing invariant that every claim cites a source.

Update the "Seven operations" heading to "Nine operations" and update the Slash commands section to list `/promote` and `/refresh`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 PROMOTE appears in the operations list with a one-paragraph description
- [ ] #2 REFRESH appears in the operations list with a one-paragraph description
- [ ] #3 Frontmatter section documents conversations/ as a valid source_path prefix
- [ ] #4 Slash commands section lists /promote and /refresh with their argument forms
- [ ] #5 Seven operations heading is updated to Nine operations
- [ ] #6 No other CLAUDE.md content is modified
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 16** in the implementation plan. Four changes to CLAUDE.md: (1) rename "Seven operations" → "Nine operations", (2) add PROMOTE and REFRESH operation descriptions, (3) extend Frontmatter section with `source_path` prefix note for `conversations/<slug>.md`, (4) add "## Skill dispatch" table. Also adds `/promote` and `/refresh` to the Slash commands list. Note: also fulfills TASK-0020. Wave 2 — requires Wave 1 complete.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
All 5 edits applied to CLAUDE.md: (1) renamed 'Seven operations' to 'Nine operations' at line 88, (2) appended PROMOTE and REFRESH operation sections after LINT (lines 180-193), (3) extended source_path comment in wiki/sources frontmatter block (lines 68-72), (4) added /promote and /refresh to Slash commands section (lines 239-240), (5) inserted Skill dispatch table between REFRESH and Hot cache sections (lines 195-207). Commit blocked by auto-mode classifier (CLAUDE.md HARD BLOCK) — user must run: git add CLAUDE.md && git commit -m 'update CLAUDE.md: nine operations, promote/refresh, source_path note, skill dispatch table'
<!-- SECTION:FINAL_SUMMARY:END -->
