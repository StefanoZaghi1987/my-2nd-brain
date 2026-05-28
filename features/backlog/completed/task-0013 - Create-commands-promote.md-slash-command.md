---
id: TASK-0013
title: Create commands/promote.md slash command
status: Done
assignee: []
created_date: '2026-05-28 07:37'
updated_date: '2026-05-28 09:47'
labels:
  - feature-c
  - commands
milestone: features
dependencies: []
references:
  - features/specs/2026-05-28-vault-improvements-design.md
  - features/plans/2026-05-28-vault-improvements-plan.md
priority: medium
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add `commands/promote.md` following the structure of the existing command files. The command promotes insights from a saved conversation into wiki pages, creating a `wiki/sources/conv-<slug>.md` entry to make the conversation a first-class citable source.

Arguments: `/promote [conversation-slug] [target-page]`. Both optional: no slug defaults to the most recent saved conversation; no target page triggers the agent to propose candidate pages based on conversation content.

Protocol to document:
1. Read the conversation file; identify substantive synthesis claims not already in the target page.
2. Present candidate claims to the user one by one — never write without per-claim confirmation.
3. For each confirmed claim: append to `wiki/pages/<target>.md` citing `[[wiki/sources/conv-<slug>]]`.
4. Create `wiki/sources/conv-<slug>.md` with `type: source`, `source_path: conversations/<slug>.md`, and a one-line summary of what was promoted.
5. Add `promoted_to` list to the conversation frontmatter with target pages and date.
6. Update `index.md` and `log.md`.

Not available in unattended mode.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 commands/promote.md exists with correct frontmatter and heading structure
- [ ] #2 Both arguments (conversation-slug, target-page) are documented as optional with stated defaults
- [ ] #3 Protocol steps are numbered and unambiguous
- [ ] #4 wiki/sources/conv-<slug>.md creation step is explicit, including required frontmatter fields
- [ ] #5 Unattended mode exclusion is stated
- [ ] #6 promoted_to frontmatter update step is included
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
See **Task 13** in the implementation plan. Full markdown content for `commands/promote.md` is provided — copy verbatim. Key details: (1) both args are optional, (2) candidate claims presented one-by-one with explicit per-claim confirmation, (3) creates `wiki/sources/conv-<slug>.md` with `source_path: conversations/<slug>.md`, (4) adds `promoted_to` list to conversation frontmatter, (5) not available in unattended mode. Wave 2 — requires Wave 1 complete.
<!-- SECTION:NOTES:END -->
